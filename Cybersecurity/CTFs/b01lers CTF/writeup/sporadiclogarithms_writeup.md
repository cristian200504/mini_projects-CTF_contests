# sporadiclogarithms — CTF Writeup

**Category:** crypto  
**Points:** 186  
**Solves:** 149  
**Flag:** `bctf{th3_m0n5t3r_gr0up_w45_t0_1mpr4ct1c4l_:(}`

---

## Challenge

> I heard the discrete logarithm problem can be solved efficiently in all sporadic groups without even knowing the group. Can you prove it to me?

We're given a black-box oracle over SSL. The server runs 5 rounds. Each round we must find an integer `x ∈ [0, 262144]` such that:

```
h = s_{g,φ}(x)
```

where `φ(a) = c·a·c⁻¹` (conjugation by `c`) and the group is `GL(3, 65537)`.

The oracle exposes: `mul`, `inv`, `phi`, `eq`, and `submit` — all operating on opaque integer handles. We get at most **10,000 queries** per round.

---

## Understanding the Math

The function `s_{g,φ}(x)` is computed via `hol_pow((g, c), x)` — exponentiation in the **holomorph** (semidirect product) of `GL(n,p)` by the automorphism `φ`.

The holomorph multiplication is:
```
(a, c^i) * (b, c^j) = (a · c^i·b·c^{-i},  c^{i+j})
```

So the first component of `(g, c)^x` is:
```
S(x) = g · φ(g) · φ²(g) · … · φ^{x-1}(g)
```

with the recurrence `S(0) = I`, `S(x) = S(x-1) · φ^{x-1}(g)`.

The key structural property: **`c` has small order `k ≤ 8`**, so `φ^k = id`. The sequence `φ^i(g)` is periodic with period `k`.

---

## Attack: Twisted Baby-Step Giant-Step

Write `x = i·m + j` with `m = ⌈√262144⌉ = 513`.

From the holomorph multiplication rule:
```
S(i·m + j) = S(i·m) · φ^{i·m}(S(j))
```

So:
```
h = S(i·m) · φ^{i·m}(S(j))
S(i·m)⁻¹ · h = φ^{i·m}(S(j))
```

Define `T(i) = S(i·m)⁻¹ · h`. We need `T(i) = φ^r(S(j))` where `r = (i·m) mod k`.

### Algorithm

**Baby steps** — precompute `S(j)` for `j = 0..m-1` using the recurrence (512 `mul` queries):
```
S(0) = I
S(j) = S(j-1) · φ^{(j-1) mod k}(g)
```

**Build twisted tables** — for each `r ∈ {0..k-1}`, store `φ^r(S(j)) → j` (at most `512 × 8 = 4096` `phi` queries):
```
tables[r][φ^r(S(j))] = j
```

**Giant steps** — iterate `i = 0, 1, 2, …`, maintaining:
```
T(0) = h
T(i+1) = φ^{(i·m) mod k}(S(m))⁻¹ · T(i)
```

At each step, look up `T(i)` in `tables[(i·m) mod k]`. A hit gives `x = i·m + j`.

### Query Budget

| Phase | Queries |
|---|---|
| Find phi period | ~16 |
| Precompute `φ^r(g)` | k−1 ≤ 7 |
| Baby steps | m = 513 |
| Build twisted tables | m×(k−1) ≤ 3591 |
| Compute `S(m)` + phi variants | k+1 ≤ 9 |
| Invert `φ^r(S(m))` | k ≤ 8 |
| Giant steps | ≤ m = 513 |
| **Total (worst case, k=8)** | **~4700** |

Well within the 10,000 query limit.

---

## Solve Script

```python
# remote_solve_v3.py (key excerpt)

def solve_round(conn):
    # ... parse one, g, c, h, bound from server ...

    # Step 1: find phi period k
    k = find_phi_period(bb, g)

    # Step 2: precompute phi^r(g) for r = 0..k-1
    phi_g = [g]
    for r in range(1, k):
        phi_g.append(bb.phi(phi_g[-1]))

    # Step 3: baby steps — S(j) for j = 0..m-1
    m = isqrt(bound) + 1
    S = [one]
    cur = one
    for j in range(1, m):
        cur = bb.mul(cur, phi_g[(j-1) % k])
        S.append(cur)

    # Step 4: build twisted tables[r][handle] = j
    tables = [{} for _ in range(k)]
    for j in range(m):
        cur = S[j]
        tables[0][cur] = j
        for r in range(1, k):
            cur = bb.phi(cur)
            tables[r][cur] = j

    # Step 5: compute S(m) and its phi-twisted inverses
    s_m = bb.mul(S[-1], phi_g[(m-1) % k])
    phi_sm_inv = [bb.inv(s_m)]
    cur = s_m
    for r in range(1, k):
        cur = bb.phi(cur)
        phi_sm_inv.append(bb.inv(cur))

    # Step 6: giant steps
    T = h
    for i in range(bound // m + 2):
        r = (i * m) % k
        if T in tables[r]:
            x = i * m + tables[r][T]
            bb.submit(x)
            return True
        T = bb.mul(phi_sm_inv[(i * m) % k], T)
```

---

## Results

All 5 rounds solved in a single connection:

| Round | k | x found | Queries used |
|---|---|---|---|
| 1 | 4 | 72171 | 2210 |
| 2 | 2 | 42722 | 1117 |
| 3 | 8 | 225291 | 4581 |
| 4 | 4 | 151371 | 2365 |
| 5 | 8 | 128452 | 4392 |

```
bctf{th3_m0n5t3r_gr0up_w45_t0_1mpr4ct1c4l_:(}
```
