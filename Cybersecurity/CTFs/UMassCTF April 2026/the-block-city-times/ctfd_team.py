import requests
import json
import re

BASE = "https://ctf.umasscybersec.org"
s = requests.Session()
s.verify = False

import urllib3
urllib3.disable_warnings()

# Login
r = s.get(f"{BASE}/login", timeout=10)
nonce_match = re.search(r"'csrfNonce':\s*\"([^\"]+)\"", r.text)
nonce = nonce_match.group(1) if nonce_match else ""

r = s.post(f"{BASE}/login", data={
    "name": "antigravity_solver",
    "password": "TestPassword123!",
    "_submit": "Submit",
    "nonce": nonce
}, timeout=10, allow_redirects=True)
print(f"Logged in. URL: {r.url}")

# Get fresh nonce
r = s.get(f"{BASE}/teams/new", timeout=10)
nonce_match = re.search(r"'csrfNonce':\s*\"([^\"]+)\"", r.text)
nonce = nonce_match.group(1) if nonce_match else ""
print(f"Nonce: {nonce[:20]}...")

# Extract form fields
print(f"\nTeam creation page title: {'new' in r.url}")
# Look for form fields
if "create" in r.text.lower() or "team" in r.text.lower():
    print("Team creation form found")

# Try creating team via form POST (not API)
r2 = s.post(f"{BASE}/teams/new", data={
    "name": "antigravity_team_99",
    "password": "teampass123",
    "_submit": "Submit",
    "nonce": nonce
}, timeout=10, allow_redirects=True)
print(f"\nTeam creation via form: {r2.status_code} | url={r2.url}")

# Check if we now have a team
r3 = s.get(f"{BASE}/api/v1/users/me", timeout=10)
me = r3.json()
team_id = me.get("data", {}).get("team_id")
print(f"Team ID: {team_id}")

if team_id:
    print("\n[+] Team created successfully!")
    
    # Now get the team access token
    # Need to get fresh nonce
    r4 = s.get(f"{BASE}/settings", timeout=10)
    nonce_match = re.search(r"'csrfNonce':\s*\"([^\"]+)\"", r4.text)
    nonce = nonce_match.group(1) if nonce_match else ""
    
    # Generate token
    r5 = s.post(f"{BASE}/api/v1/tokens", json={
        "type": "team", 
        "expiration": "2026-12-31"
    }, headers={
        "CSRF-Token": nonce,
        "Content-Type": "application/json"
    }, timeout=10)
    print(f"Token API: {r5.status_code} | {r5.text[:300]}")
    
    # Also check team settings page for existing token
    r6 = s.get(f"{BASE}/team", timeout=10)
    token_match = re.search(r'ctfd_[a-zA-Z0-9_]+', r6.text)
    if token_match:
        print(f"\n[!!!] TEAM TOKEN: {token_match.group(0)}")
    
    # Check settings page
    r7 = s.get(f"{BASE}/settings", timeout=10)
    token_match = re.search(r'ctfd_[a-zA-Z0-9_]+', r7.text)
    if token_match:
        print(f"\n[!!!] TOKEN FROM SETTINGS: {token_match.group(0)}")
    
    # Find all tokens
    r8 = s.get(f"{BASE}/api/v1/tokens", timeout=10)
    print(f"\nTokens: {r8.text[:500]}")
    
    # Try team-specific token endpoint
    r9 = s.get(f"{BASE}/api/v1/teams/{team_id}", timeout=10)
    print(f"Team data: {r9.text[:500]}")
else:
    print("Failed to create team")
    # Check the response for error messages
    for line in r2.text.split('\n'):
        if 'error' in line.lower() or 'alert' in line.lower() or 'invalid' in line.lower():
            clean = re.sub(r'<[^>]+>', '', line).strip()
            if clean:
                print(f"  Error: {clean}")
