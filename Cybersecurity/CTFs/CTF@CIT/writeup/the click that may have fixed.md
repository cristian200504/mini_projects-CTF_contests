# CTF@CIT 2026 — "The click that may have fixed" Writeup

## Challenge Info

- **Category:** Digital Forensics
- **Description:** A CTF player tried to download more RAM and got pwned. They visited one website where a captcha required them to run some PowerShell. Find the last time that website was visited.
- **Flag Format:** `CIT{YYYY-MM-DDThh:mm:ssZ}`

## Solution

### 1. Extract the archive

The challenge provides `challenge.zip`, which contains a Windows user profile backup for user `kurt`.

```
challenge_extracted/kurt_backup/
```

### 2. Identify the browser

Inside `AppData/Local/Microsoft/Edge/User Data/Default/` there's a `History` file — a SQLite database used by Microsoft Edge to store browsing history.

### 3. Query the history

Copied the `History` file to avoid any lock issues, then queried it with Python:

```python
import sqlite3, datetime

db = sqlite3.connect('history_copy.db')
cur = db.cursor()
cur.execute('SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50')
for row in cur.fetchall():
    url, title, lvt = row
    # Chrome/Edge epoch: microseconds since Jan 1, 1601
    ts = datetime.datetime(1601,1,1) + datetime.timedelta(microseconds=lvt)
    print(ts.strftime('%Y-%m-%dT%H:%M:%SZ'), '|', url, '|', title)
db.close()
```

### 4. Results

The top entries revealed the victim's browsing trail:

| Timestamp | URL | Title |
|---|---|---|
| `2026-04-18T07:07:26Z` | `https://23.179.17.92:5067/` | Download More RAM! |
| `2026-04-18T07:07:00Z` | bing search: `free ram for me` | — |
| `2026-04-18T07:06:50Z` | `https://ctf.cyber-cit.club/` | CTF@CIT |
| `2026-04-18T07:05:40Z` | `https://downloadmoreram.com/` | DownloadMoreRAM.com |

The malicious site with the fake CAPTCHA / PowerShell lure is `https://23.179.17.92:5067/`, last visited at **2026-04-18T07:07:26Z**.

Also notable: two suspicious executables were found in `AppData/Roaming/` (`e9fje2.exe`, `fj3493.exe`), consistent with the user having been pwned after running the PowerShell payload.

## Flag

```
CIT{2026-04-18T07:07:26Z}
```
