import urllib.request
import urllib.error
import json
import re

HOST = 'http://18.215.143.250:8080'

def get(path, data=None, method=None):
    req = urllib.request.Request(
        HOST + path,
        data=data,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
        method=method or ("POST" if data else "GET")
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read().decode('utf-8', errors='replace')
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return e.code, body
    except Exception as e:
        return None, str(e)

# ── /api/flag ────────────────────────────────────────────────────────────────
print("=== GET /api/flag ===")
code, body = get('/api/flag')
print(f"  {code}: {body[:500]}")

print("\n=== POST /api/flag (empty) ===")
code, body = get('/api/flag', b'{}')
print(f"  {code}: {body[:500]}")

# ── /api/solve ───────────────────────────────────────────────────────────────
print("\n=== GET /api/solve ===")
code, body = get('/api/solve')
print(f"  {code}: {body[:500]}")

print("\n=== POST /api/solve (empty) ===")
code, body = get('/api/solve', b'{}')
print(f"  {code}: {body[:500]}")

print("\n=== POST /api/solve (with rungs) ===")
payload = json.dumps({"rungs": []}).encode()
code, body = get('/api/solve', payload)
print(f"  {code}: {body[:500]}")

# ── JS deeper analysis ───────────────────────────────────────────────────────
req = urllib.request.Request(
    f"{HOST}/assets/index-CnN86lsh.js",
    headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode('utf-8', errors='replace')

# Find the /api/solve and /api/flag usage context
print("\n=== Context around /api/solve ===")
idx = js.find('/api/solve')
if idx >= 0:
    print(repr(js[max(0,idx-300):idx+300]))

print("\n=== Context around /api/flag ===")
idx = js.find('/api/flag')
if idx >= 0:
    print(repr(js[max(0,idx-300):idx+300]))

# Find the scenario/puzzle definition (M array or similar)
print("\n=== Scenario/puzzle data ===")
# Look for arrays with 'given', 'coil', 'description', 'brief' keys
scenarios = re.findall(r'\{[^{}]*(?:brief|coil|given|description)[^{}]*\}', js)
for s in scenarios[:20]:
    if len(s) < 500:
        print(f"  {s}")
