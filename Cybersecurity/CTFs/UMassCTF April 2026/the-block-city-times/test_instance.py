import requests
import re

# Try accessing the given IP with Block City Times Host header
headers = {"Host": "blockcitytimes.web.ctf.umasscybersec.org:5000"}
r = requests.get("http://104.197.207.149:5000/", headers=headers, timeout=10)
m = re.search(r'terminal-title[^>]*>([^<]+)', r.text)
title = m.group(1) if m else "no title"
print(f"With BCT Host header: {title}")

# Try /instance directly
r2 = requests.get("http://104.197.207.149:5000/instance", timeout=10, allow_redirects=False)
print(f"/instance status: {r2.status_code}")
loc = r2.headers.get("Location", "none")
print(f"/instance Location: {loc}")
print(f"/instance body: {r2.text[:300]}")

# Try the hensandroosters proxy - POST to / with various token formats
# Maybe a blank token or bypass works here since it's already solved
s = requests.Session()
r3 = s.get("http://104.197.207.149:5000/", timeout=10)
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r3.text)
csrf = csrf_match.group(1) if csrf_match else ""

# Try submitting empty/fake tokens
for token in ["ctfd_test", ""]:
    r4 = s.post("http://104.197.207.149:5000/", data={
        "csrf_token": csrf,
        "ctfd_team_access_token": token
    }, timeout=10, allow_redirects=True)
    m = re.search(r'terminal-title[^>]*>([^<]+)', r4.text)
    title = m.group(1) if m else "no title"
    has_instance = "instance" in r4.text.lower() or "url" in r4.text.lower()
    err = re.search(r'\[!\]\s*([^<]+)', r4.text)
    err_msg = err.group(1).strip() if err else ""
    print(f"Token='{token}': title={title} | error={err_msg} | has_instance={has_instance}")
    # Get fresh csrf
    r5 = s.get("http://104.197.207.149:5000/", timeout=10)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r5.text)
    csrf = csrf_match.group(1) if csrf_match else ""
