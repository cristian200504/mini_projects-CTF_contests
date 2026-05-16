import requests
import re
import urllib3
urllib3.disable_warnings()

CTFD_TOKEN = "ctfd_4b7fe72a32b2ce5acb180015421c7ec5bf472ea7211a615e86069895385cbbb2"
TARGET_URL = "http://blockcitytimes.web.ctf.umasscybersec.org:5000"

session = requests.Session()

# Authenticate
r = session.get(f"{TARGET_URL}/", timeout=30)
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
proxy_csrf = csrf_match.group(1) if csrf_match else ""

auth_resp = session.post(f"{TARGET_URL}/", data={
    "csrf_token": proxy_csrf,
    "ctfd_team_access_token": CTFD_TOKEN
}, timeout=30, allow_redirects=True)

print(f"Auth response URL: {auth_resp.url}")
print(f"Auth status: {auth_resp.status_code}")
# Save to file to avoid encoding issues
with open("instance_page.html", "w", encoding="utf-8") as f:
    f.write(auth_resp.text)
print("Saved instance page to instance_page.html")

# Look for URLs in the page
urls = re.findall(r'https?://[^\s<>"\']+', auth_resp.text)
print(f"\nURLs found: {urls}")

# Look for IP:port patterns
ip_ports = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', auth_resp.text)
print(f"IP:port patterns: {ip_ports}")

# Look for any href/src links
links = re.findall(r'(?:href|src|action)=["\']([^"\']+)["\']', auth_resp.text)
print(f"Links: {links}")

# Also check headers
print(f"\nResponse headers: {dict(auth_resp.headers)}")
print(f"Cookies: {dict(session.cookies)}")

# Try /instance directly
r2 = session.get(f"{TARGET_URL}/instance", timeout=30)
with open("instance_page2.html", "w", encoding="utf-8") as f:
    f.write(r2.text)
# Look for instance URL
instance_urls = re.findall(r'https?://[^\s<>"\']+', r2.text)
print(f"\nInstance page URLs: {instance_urls}")
ip_ports2 = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r2.text)
print(f"Instance IP:port: {ip_ports2}")
