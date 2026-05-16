import requests
import json

BASE = "https://ctf.umasscybersec.org"
s = requests.Session()
s.verify = False

import urllib3
urllib3.disable_warnings()

# Check if registration is still open
print("[1] Checking CTFd status...")
r = s.get(f"{BASE}/")
# Look for registration link
if "register" in r.text.lower():
    print("  Registration page exists")
if "login" in r.text.lower():
    print("  Login page exists")

# Check the settings
print("\n[2] Checking CTFd configuration...")
r = s.get(f"{BASE}/api/v1/configs", timeout=10)
print(f"  /api/v1/configs: {r.status_code}")
if r.status_code == 200:
    try:
        data = r.json()
        print(f"  {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"  {r.text[:500]}")

# Try to register a new user/team
print("\n[3] Trying to register...")
# First get the registration page
r = s.get(f"{BASE}/register", timeout=10)
print(f"  /register: {r.status_code}")
if r.status_code == 200 and "nonce" in r.text:
    import re
    nonce_match = re.search(r"'csrfNonce':\s*\"([^\"]+)\"", r.text)
    nonce = nonce_match.group(1) if nonce_match else ""
    print(f"  CSRF nonce found: {nonce[:20]}...")
    
    # Try to register
    reg_data = {
        "name": "antigravity_solver",
        "email": "antigravity@test.com",
        "password": "TestPassword123!",
        "_submit": "Submit",
        "nonce": nonce
    }
    r = s.post(f"{BASE}/register", data=reg_data, timeout=10, allow_redirects=True)
    print(f"  Registration response: {r.status_code}")
    if "already" in r.text.lower():
        print("  Registration error: possibly already taken or closed")
    if "token" in r.text.lower() or "ctfd_" in r.text.lower():
        print("  TOKEN FOUND in response!")
        print(f"  {r.text[:500]}")
    # Check if we're now logged in
    r2 = s.get(f"{BASE}/api/v1/users/me", timeout=10)
    print(f"  /api/v1/users/me: {r2.status_code}")
    if r2.status_code == 200:
        print(f"  User data: {r2.text[:500]}")
elif "closed" in r.text.lower() or "ended" in r.text.lower():
    print("  Registration is closed")
else:
    print(f"  Page content: {r.text[:300]}")

# Try to login with test credentials
print("\n[4] Checking team endpoints...")
r = s.get(f"{BASE}/api/v1/teams?page=1&per_page=1", timeout=10)
if r.status_code == 200:
    data = r.json()
    if data.get("data"):
        team = data["data"][0]
        print(f"  First team: id={team.get('id')} name={team.get('name')}")

# Check if there's a way to generate tokens
print("\n[5] Checking API for token generation...")
for endpoint in ["/api/v1/tokens", "/api/v1/users/me/tokens", "/settings"]:
    r = s.get(f"{BASE}{endpoint}", timeout=10)
    print(f"  {endpoint}: {r.status_code} | {r.text[:200]}")
