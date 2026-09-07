# NNS International Lounge — solve

## Vulnerability

The application signs QR-ticket fields with:

```python
TICKET_SECRET = hashlib.sha256(b"lounge").digest()
```

This is a hard-coded, fully predictable HMAC key. Anyone with the challenge source can therefore create a valid signature for arbitrary ticket fields.

The scan endpoint has a special first-visit check:

```python
activating_bonus = user["visits_used"] == 0 and encoded_remaining > VISIT_ALLOWANCE
```

When this is true, the usual stale-pass validation is skipped. A ticket containing a visit count greater than `4` is accepted for a member who has not visited yet.

## Exploit

The solver registered a normal account and obtained its ticket fields:

```text
LS/060926/0609260029/0609270029/8113828958702446/NNS/201/solver1788654594 test/4
```

It replaced the final `4` with `5`, then recomputed the six-character MAC exactly as the server does:

```python
import hashlib
import hmac

fields = [
    "LS", "060926", "0609260029", "0609270029", "8113828958702446",
    "NNS", "201", "solver1788654594 test", "5",
]
secret = hashlib.sha256(b"lounge").digest()
mac = hmac.new(secret, "/".join(fields).encode(), hashlib.sha256).hexdigest()[:6]
payload = "/".join(fields + [mac])
```

The solver encoded `payload` as a QR image and uploaded it to `/lounge`. The first scan was accepted, setting the account to four remaining visits while recording one visit used. It then downloaded and scanned the freshly signed official pass four more times. At five total visits, the server returned the flag.

## Flag

```text
NNS{i_loVe_hackin6_10uN6es_aNd_get71n6_4cc3s5_to_plaC35_i_5hoU1d_n07_rea11Y_B3_iN}
```
