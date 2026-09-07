# crypto-party-2 — Solution

**Category:** Crypto (ECDSA nonce bias / Extended Hidden Number Problem)
**Flag:** `NNS{bu7_uu1ds_4r3_r4nd0m!!_2070186dff}`

## Challenge description

> Thanks to whoever forged invites last year, now this year's budget is ruined. We have patched the invitation system. You can still bring some friends this year, but don't push it!

Instance: `ncat --ssl crypto-party-2-<id>.chall.nnsc.tf 1337`

Source: [crypto_crypto-party-2/chall.py](crypto_crypto-party-2/chall.py)

## 1. The service

```python
MAX_INVITES = 6
G = curves.NIST256p.generator
n = curves.NIST256p.order
secret_key = secrets.randbelow(n - 1) + 1

key = long_to_bytes(secret_key, 32)
cipher = AES.new(key, AES.MODE_ECB)
ct = bytes_to_long(cipher.encrypt(pad(flag, 16)))     # printed immediately

def invite(m):
    h = bytes_to_long(sha256(m.encode()).digest())
    k = bytes_to_long(str(uuid.uuid4())[:32].encode())   # <-- the nonce
    P = k * G
    r = P.x() % n
    s = (pow(k, -1, n) * (h + r * secret_key)) % n
    return r, s
```

The flag is AES‑ECB‑encrypted directly with the ECDSA private key (`secret_key`), printed up front as `ct`. The service then lets you request up to **6** ECDSA signatures over messages (friend names) *you* choose. Goal: recover `secret_key` from ≤6 signatures, then decrypt `ct`.

## 2. The bug: the nonce isn't random bytes, it's random *text*

`k = bytes_to_long(str(uuid.uuid4())[:32].encode())`. Instead of 32 random bytes, this takes the **36-character hyphenated string form** of a UUID4, truncates to 32 characters, and interprets those ASCII characters as a big-endian integer. That's a huge structural leak:

- UUID4's canonical layout is `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` (`x`=random hex, the `4` is the fixed version nibble, `y`∈{8,9,a,b} is the variant). Truncating to 32 chars keeps everything except the last 4 hex digits.
- That means **4 hyphen characters** (`-` = `0x2D`) and the **version character `'4'`** (`0x34`) sit at fixed string positions (8, 13, 14, 18, 23) — verified empirically over 500k samples in [nonce_model.py](solve/nonce_model.py), 0 mismatches.
- Every *other* character is an ASCII hex digit (`'0'-'9'` or `'a'-'f'`), and **every ASCII hex digit is < 0x80** — so the top bit of every one of those bytes is always known to be 0.

So per signature, out of 256 bits of "nonce," 5 whole bytes (40 bits) are exactly known, and the remaining 27 bytes each have 1 known bit + 7 unknown bits. This is a nonce-bias problem — but a much messier one than the textbook "known MSBs" case.

## 3. Why a naive lattice attack doesn't work here

The classic ECDSA lattice attack (Howgrave-Graham–Smart / Boneh–Venkatesan Hidden Number Problem) bounds each signature's nonce uncertainty with a *single* bound and needs roughly `256/m` known bits per signature for `m` signatures. With `m=6` that's ~43 bits/signature needed — we only have 40 *exactly* known bits/signature this way, and critically the leaked bytes are **scattered** (hyphens/version sit in the middle of the string), not contiguous MSBs/LSBs. Worse, the single most significant byte (positions 0-7, the very top of the 256-bit value) is *completely unconstrained* text, so any attempt to fold "27 free bytes" into one combined per-signature bound is dominated by that top byte and the naive bound ends up almost as large as `n` itself — useless.

The fix is to give **each unknown byte its own lattice dimension** instead of one crude combined bound per signature — this is exactly the **Extended Hidden Number Problem (EHNP)**, formalized by Hlaváč & Rosa, *"Extended Hidden Number Problem and Its Cryptanalytic Applications"* (Section 4). We used the reference implementation from [jvdsn/crypto-attacks](https://github.com/jvdsn/crypto-attacks) (`attacks/hnp/extended_hnp.py`, `shared/partial_integer.py`, `shared/lattice.py`), copied locally as [extended_hnp.py](solve/extended_hnp.py), [partial_integer.py](solve/partial_integer.py), [lattice_shared.py](solve/lattice_shared.py).

`PartialInteger` models an integer as a sequence of known-value / unknown-bit-width components (MSB→LSB). `dsa_known_bits(N, h, r, s, x, k)` builds a lattice of dimension `D = d + m + L` where `d` = number of signatures, `m` = number of unknown chunks in the private key (1, since it's fully unknown), and `L` = total unknown *chunks* summed across all nonces — each chunk gets its own scaled lattice dimension (`delta / 2^chunk_width`), independent of that chunk's bit-position/significance. That positional-independence is exactly what defeats the "dominated by the top byte" problem above.

## 4. Building the nonce model

[nonce_model.py](solve/nonce_model.py) builds the `PartialInteger` for `k`, iterating string positions **31 down to 0** (`PartialInteger` appends components LSB-first, and index 0 of the string is the most-significant byte of `k`):

- Positions `{8, 13, 18, 23}` → `add_known(0x2D, 8)` (the hyphens)
- Position `14` → `add_known(0x34, 8)` (the uuid4 version nibble)
- All 27 other positions → `add_unknown(7)` then `add_known(0, 1)` (7 free bits, then the always-0 top bit of an ASCII hex digit)

Per signature this gives **27 unknown chunks of width 7** (`L_per_sig = 27`). With `d=6` signatures and `m=1` (private key fully unknown, 256-bit): `L = 162`, `D = 6 + 1 + 162 = 169` — a 169-dimensional lattice.

## 5. A Sage bug along the way

Running the reference code as-is crashed:

```
File "sage/matrix/matrix_rational_dense.pyx", line 994, in _clear_denom
cysignals.signals.SignalError: Illegal instruction
```

Reproduced this at a tiny 13×13 scale — Sage's `Matrix_rational_dense.LLL()` chokes on matrices whose rational entries span an extreme dynamic range (our matrix mixes ~2²⁵⁶-scale integers with ~2⁻³⁰⁰-scale `delta`s, an inherent feature of the EHNP construction). The fix, in [lattice_shared.py](solve/lattice_shared.py): manually compute the LCM of all entry denominators, scale the whole matrix to exact integers ourselves, run `.LLL()` on that (Sage's *integer*-matrix LLL is solid), then divide back down. This sidesteps Sage's buggy rational `_clear_denom` path entirely.

## 6. Local verification before touching the remote

[local_server.py](solve/local_server.py) is a byte-for-byte reproduction of `chall.py`'s crypto logic, but with a known `secret_key` for verification. [solve_local.py](solve/solve_local.py) generates 6 signatures, runs the attack, and checks the recovered key against ground truth.

Run inside a SageMath container (needed for exact-rational linear algebra and `.LLL()`):

```sh
docker run -d --name hnp_sage -v "<repo>/solve:/work" -w /work sagemath/sagemath:latest sleep infinity
docker exec hnp_sage sage -pip install pycryptodome ecdsa
docker exec hnp_sage sage -python solve_local.py
```

Result: **4/4 successful runs**, ~20–30 seconds each, first candidate always correct:

```
TRUE secret_key = 65379143423197818906853957632515833354006824548891912241875463878225279400446
[extended_hnp] d=6 m=1 L=162 D=169 KD~=3.339e+13 delta~=1.498e-14
[1] MATCH! candidate == true secret_key
done in 30.4s, candidates checked = 1, found = True
```

## 7. Talking to the real server

Two snags with the live instance:

1. **Instance provisioning** — the challenge is spun up on demand; connecting before starting it from the platform returns an `HTTP/1.1 400 Bad Request` from the ingress, not the challenge banner.
2. **Buffered stdout** — the Dockerfile runs `socat TCP-LISTEN:3000,fork,reuseaddr EXEC:uv run chall.py` with no `-u`/`PYTHONUNBUFFERED`. Since stdout isn't a TTY under `socat EXEC`, Python fully buffers it — nothing arrives until the process exits (after all 6 inputs are consumed) and flushes on exit. [remote_client.py](solve/remote_client.py) sends all 6 chosen names **blind**, then reads the entire buffered burst at the end and parses `ct` plus all 6 `r:s` invite codes with regex.

[remote_data.json](solve/remote_data.json) is the actual captured data from the live instance. [solve_remote.py](solve/solve_remote.py) feeds it into the same attack and AES-ECB-decrypts `ct` with the recovered key:

```
[extended_hnp] d=6 m=1 L=162 D=169 KD~=3.339e+13 delta~=1.498e-14
[1] candidate secret_key = 11200096334417330951583543143934603873887843327662311890659129015802917290578
[1] DECRYPT SUCCESS: b'NNS{bu7_uu1ds_4r3_r4nd0m!!_2070186dff}'
done in 20.5s, candidates checked = 1
```

Solved on the very first lattice candidate — no brute forcing needed.

## Key takeaway

`uuid.uuid4()` genuinely is a good source of randomness. The bug is entirely in how it's *consumed*: converting its printable string form into an integer nonce throws away almost all of that randomness' natural bit-packing and replaces it with a highly structured, mostly-ASCII-hex-digit integer. Naive "count the leaked bits" reasoning suggested 6 signatures shouldn't be enough — but by giving each of the 162 individually-bounded unknown byte-chunks (across 6 signatures) its own dimension in a 169-dimensional Extended-HNP lattice, rather than crudely combining them per-signature, the private key falls out on the first candidate every time.
