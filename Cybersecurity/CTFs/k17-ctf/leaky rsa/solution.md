# Leaky RSA — CTF Solution

**Flag:** `K17{th3_t1tan1c_sh0uldv3_us3d_duct_t4p3}`

---

## Challenge Overview

We are given a standard RSA encryption setup with a critical information leak: instead of exposing `dp` or `dq` directly, the challenge leaks their **sum** `dp + dq`.

### Given (`out.txt`)

| Parameter | Value |
|-----------|-------|
| `N` | 2048-bit RSA modulus |
| `e` | `257` |
| `leak` | `dp + dq` |
| `c` | ciphertext |

### Challenge Code (`chal.py`)

```python
e = 257
phi = (P - 1) * (Q - 1)
N = P * Q
d = pow(e, -1, phi)

m = bytes_to_long(FLAG)
c = pow(m, e, N)

dp = d % (P - 1)   # CRT exponent for P
dq = d % (Q - 1)   # CRT exponent for Q

dsum = dp + dq     # <-- this is the leak
```

---

## Mathematical Analysis

### Step 1 — CRT exponent definitions

By definition of `dp` and `dq`:

```
e · dp ≡ 1  (mod P-1)   →   e · dp = k(P-1) + 1   for some integer k
e · dq ≡ 1  (mod Q-1)   →   e · dq = l(Q-1) + 1   for some integer l
```

Since `e = 257` and `d < phi`, both `k` and `l` are bounded:

```
1 ≤ k ≤ e-1 = 256
1 ≤ l ≤ e-1 = 256
```

This gives us at most **256 × 256 = 65,536** candidate pairs — small enough to brute force.

### Step 2 — Combine the leak

Adding the two CRT equations:

```
e · dp + e · dq = k(P-1) + 1 + l(Q-1) + 1
e · (dp + dq)   = kP - k + lQ - l + 2
e · leak        = kP + lQ - (k+l) + 2
```

Rearranging:

```
kP + lQ = e·leak + k + l - 2
```

Let `S = e·leak + k + l - 2`, so:

```
kP + lQ = S
```

### Step 3 — Reduce to a quadratic

We also know `P · Q = N`, so `Q = N / P`. Substituting:

```
kP + l·(N/P) = S
kP² - S·P + lN = 0
```

This is a standard quadratic in `P`. The discriminant is:

```
Δ = S² - 4klN
```

For this to yield an integer solution for `P`, **Δ must be a perfect square**.

Solving:

```
P = (S ± √Δ) / (2k)
```

### Step 4 — Verify and decrypt

For each `(k, l)` pair:
1. Compute `S`, then `Δ`
2. Check if `√Δ` is an exact integer
3. Compute both candidate values of `P`
4. Check if `P` divides `N` exactly
5. If so, recover `Q = N/P`, recompute `phi`, `d`, and decrypt

The correct pair was found at **k = 135, l = 230**.

---

## Solution Script (`solve.py`)

```python
#!/usr/bin/env python3

from math import isqrt
from Crypto.Util.number import long_to_bytes

N = 13110050439165744390844047365994832977957785624031506061492246788930407628897985680761641758832878633991262713539741387371859860786247593029278393446890378429416250956468456071288622278390131858415515017824285344483699033444039243475945869007529117733055624002687708127296726553790218870005341236517697093430634885226644976687337857761382349408254866253201576856867163450366307962768280593251095602615445432646239295559870032022377895775730169398487540194412600669513504057917441683252355316703453923892760869441350628389391059888307727365977349613564953264540628607883258908171265378994048309845777033275826817277051
e = 257
leak = 173039628521230421486125480450097646128184672395715510223662687958418979921652061997662907473530878446360029009008226135214081843439647616651851406837199720854947637541932878950181903720963129489413607802590151409501982163003389169577230964996085846188366605687194836304711780857265989102044080343739490109646
c = 11645793248515717026962436858873684549250497577366948889118175808799446143134773451937173471002509969304949386074071202970728539074765909939799134639801922075411357021488107892541216813797026001306775099362261687923638670587025826814715995677942572638385357796197571445283606629854202814098991473183353374982356702069082918241068303423524428431894409845900002299069484070950920144099671011053235001074659216431182053997898642591182928204287602367543710301790522481405579592220440720474656197707726401356520172993899452164183502786241730772935132538882670986569616175268645160841460180375334654928011063510949641364268

found = False
for k in range(1, e):
    for l in range(1, e):
        S = e * leak + k + l - 2
        disc = S * S - 4 * k * l * N
        if disc < 0:
            continue
        sqrt_disc = isqrt(disc)
        if sqrt_disc * sqrt_disc != disc:
            continue
        for sign in [1, -1]:
            num = S + sign * sqrt_disc
            den = 2 * k
            if num % den != 0:
                continue
            P = num // den
            if P <= 1 or P >= N:
                continue
            if N % P == 0:
                Q = N // P
                phi = (P - 1) * (Q - 1)
                d = pow(e, -1, phi)
                m = pow(c, d, N)
                flag = long_to_bytes(m)
                print(f"[+] Found! k={k}, l={l}")
                print(f"FLAG: {flag.decode()}")
                found = True
                break
        if found:
            break
    if found:
        break
```

**Output:**
```
[+] Found! k=135, l=230
FLAG: K17{th3_t1tan1c_sh0uldv3_us3d_duct_t4p3}
```

---

## Why This Works

The vulnerability comes from leaking any linear combination of `dp` and `dq`. Because `e` is small (257), the hidden multipliers `k` and `l` are tightly bounded to `[1, e-1]`. This turns the problem into a brute-force search over ~65K candidates, each reducible to a simple integer quadratic — solvable in seconds.

Had `e` been large (e.g., 65537), this approach would have `65536² ≈ 4 billion` candidates and would require a smarter lattice-based attack instead.
