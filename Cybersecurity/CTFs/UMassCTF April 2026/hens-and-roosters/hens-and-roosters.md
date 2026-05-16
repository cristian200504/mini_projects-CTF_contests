# Hens and Roosters - UMass CTF Writeup

## Challenge Overview
**Category:** Crypto / Web (Medium)
**Challenge Description:** "Please help me buy more Legos! The store has such aggressive rate limiting I can't even get an ID!"

We are given a web application that implements rate limiting via HAProxy and a custom backend API built with Flask. The application relies on an Unbalanced Oil and Vinegar (UOV) signature scheme using SageMath to issue and verify free "studs" (currency). The objective is to accumulate exactly 7 studs for a given randomly generated `uid` to "buy" a Lego set, which rewards the flag.

---

## Technical Analysis

### 1. Reverse Engineering the Rate Limiter Bypass
When inspecting the provided `haproxy.cfg`, we find the following rate-limiting configuration:

```haproxy
stick-table type string len 2048 size 100k expire 20s store http_req_rate(20s)
http-request track-sc0 url
http-request deny deny_status 429 if { sc_http_req_rate(0) gt 1 }
```

The issue here lies in `http-request track-sc0 url`. Because HAProxy tracks the full URL (including the query parameters) as distinct entries in the stick-table rather than just the URI path or the client IP, we can effortlessly bypass the strict rate limit by appending random query strings to every request. 
For example, `GET /?bypass=abc` and `GET /?bypass=def` are treated completely independently by HAProxy.

### 2. Identifying the API Workflow
The normal workflow of the API is as follows:
- `GET /` -> Returns a random hex `uid`. Initially sets `studs` to 0.
- `GET /buy?uid=XYZ` -> Grants a free UOV signature for the payload string `"0|XYZ"`.
- `POST /work` -> Submits our `uid` and a `sig`. If the signature checks out via `uov.verify()`, the server bumps our `studs` count by 1 and returns a new signature for the next stud tier (`"1|XYZ"`).

The catch? When our `studs` counter hits `3`, the application forcibly returns `"You're not getting any more free studs!"` and deliberately refuses to generate a valid signature for the `"3|XYZ"` payload. Since UOV math cannot be trivially forged to create the `3`, `4`, `5`, and `6` tier signatures, standard logical progression is solidly blocked.

### 3. Understanding the Verification logic and Caching
In `POST /work`, the server utilizes a Redis cache mechanism to check previously verified signatures to save on expensive UOV verification calculations:

```python
value = r.get(str(sig))
if value is None:
    r.set(sig, b'-', ex=240)
    verified = uov.verify(payload, sig_bytes)
    if verified:
        r.set(sig, payload, ex=240)
elif value == b'-':
    return "The signature is still being processed, please send a request later!"
else:
    verified = value.decode() == payload
```

*If* the signature string maps directly to the payload we're requesting, `verified` instantly returns True. Shortly after, the `uid` tier is incremented: `studs = r.incr(uid)`.

While a race condition seems immediately obvious (sending multiple threads simultaneously to increment `studs`), the cache explicitly blocks it. The first completed thread instantly enters `r.set(sig, payload)`. When subsequent threads retrieve that cached value, they check if `value.decode() == payload`. Because Thread 1 already incremented the studs, Thread 2's target `payload` has changed from `"0|XYZ"` to `"1|XYZ"`. The cache check fails (`"0|XYZ" == "1|XYZ"` is `False`), completely dodging the `r.incr(uid)`.

### 4. The UOV TOCTOU Vulnerability
In Python, executing `bytes.fromhex(sig)` is completely case-insensitive. A hex signature of `abc` yields identical raw bytes to `ABC`. However, Redis key storage is completely **case-sensitive**.

This logical discrepancy breaks the application:
1. We obtain the legitimate free signature for tier 0 (`"0|XYZ"`).
2. We derive multiple visually unique string variations of the same signature by selectively changing the case of characters (e.g., swapping `a` to `A`).
3. We concurrently blast the `/work` endpoint using these varied signatures.

Because Redis treats each case variation as a distinctly new key, it finds no cached `value` for any of them. The application skips the fast `value.decode() == payload` check and falls back into the notoriously CPU-intensive `uov.verify()` for all parallel threads.

Because `uov.verify()` execution takes a generous amount of time, a massive Time-of-Check to Time-of-Use (TOCTOU) window is artificially widened. 
All of the concurrent threads will execute `studs = r.get(uid)` finding `studs` safely resting at 0. Their generated `payload` values all become `"0|XYZ"`. All threads successfully evaluate the UOV verification because `bytes.fromhex()` normalizes the case variants back to the original valid mathematical signature. 
Once verification organically finishes for all instances, they line up and blast `studs = r.incr(uid)` back-to-back, easily pushing us to the required 7 studs. 

---

## Exploit Script Reference
A complete and working exploit script (`solve_v2.py`) was constructed to:
1. Generate an ID and bypass HAProxy.
2. Obtain the initial free signature.
3. Rapidly mutate string indices from `a-f` to uppercase variants.
4. Execute parallel threads requesting validation. 
5. Fetch the flag via `/buy`.

## The Flag
`UMASS{oil_does_mix_with_oil_but_roosters_dont}`
