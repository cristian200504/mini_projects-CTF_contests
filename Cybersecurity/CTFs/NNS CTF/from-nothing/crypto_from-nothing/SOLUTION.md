# NNS CTF 2026 — `from-nothing` (Crypto) — Full Solution Write-up

> *"the wise seek not what is present, but what is absent"*

## Flag

```
NNS{4nd_th3_g1ft3d_c4n_m4k3_s0m3th1ng_fr0m_n0th1ng}
```

---

## Overview

The challenge implements a discrete-log-based encryption scheme on the **Jacobian of a genus-5 hyperelliptic curve** with Complex Multiplication (CM) by the cyclotomic ring Z[ζ₁₁]. The key vulnerability is the **omission of the v-polynomial** from the ciphertext output — "what is absent" guides the entire attack.

### Files

| File | Role |
|---|---|
| `chall.sage` | Challenge source — generates keys and encrypts the flag |
| `output.txt` | Challenge output — contains p, D_u, u, v (but NOT D_v!) |
| `find_order.sage` | Step 1 solver — finds the true Jacobian group order via CM/LLL |
| `get_flag_from_order.sage` | Step 2 solver — recovers 8 candidate e values, decrypts the flag |
| `solve_challenge.sage` | Combined single-file solver (runs both steps) |
| `true_order.txt` | Computed Jacobian group order N |
| `flag.txt` | The recovered flag |

---

## Challenge Structure

```sage
n = 11
p = next(p for p in iter(lambda: random_prime(2^512), 0) if p % n == 1)

R.<x> = PolynomialRing(FiniteField(p))
H = HyperellipticCurve(x^n, 1, "u,v")   # v^2 + v = x^11 over F_p
J = H.jacobian()(J.base_ring())

x = next(x for x in iter(GF(p).random_element, 0) if (1+4*x^n).is_square())
D = randint(2, p) * J(H.lift_x(x))
e = int(D[1][0])    # <-- scalar = constant coefficient of the v-polynomial of D

P = H.lift_x(Integer(int(b"NNS{??...}".hex(), 16)))
ct = e * J(P)

print(f"D_u = {D[0].list()}")   # u-polynomial only — D_v is ABSENT
print(f"u = {ct[0].list()}")
print(f"v = {ct[1].list()}")
```

Key observations:
- The plaintext flag is embedded as the x-coordinate of a curve point `P`.
- The encryption scalar `e` is the **constant term of the v-polynomial** of the divisor `D`.
- `D_u` (the u-polynomial of `D`) is revealed, but `D_v` is kept secret.
- Because `ct = e * J(P)`, recovery requires finding `e` and the group order `N` to compute `d = e⁻¹ mod N`.

---

## Attack

### Step 1: Recover Candidate Values of `e`

In **Mumford representation**, every divisor `D = (u(x), v(x))` on a genus-g hyperelliptic curve `y² + y = x^11` satisfies the fundamental relation:

```
v(x)² + v(x) ≡ x^11  (mod u(x))
```

Completing the square:

```
(v + 1/2)² ≡ x^11 + 1/4  (mod u(x))
```

**The challenge gives us `D_u` but omits `D_v`.** We solve for `D_v` by factoring `D_u` over F_p:

```
D_u = (linear) * (quadratic₁) * (quadratic₂)
```

Since `D_u` splits into 3 factors, by CRT:

```
F_p[x]/(D_u) ≅ F_p × F_{p²} × F_{p²}
```

In each component the quadratic `y² + y - x^11 = 0` has exactly **2 roots** (since we can take ±√). By CRT there are exactly **2³ = 8** possible polynomials `D_v`, and thus **8 candidate values** for `e = D_v[0]`.

```sage
Du = R(D_u)
factors = [q for q, _ in Du.factor()]  # three irreducible factors

def solve_quadratic_mod(Q):
    if Q.degree() == 1:
        x_val = -Q[0]
        C = x_val^11 + GF(p)(1)/GF(p)(4)
        sq = C.sqrt()
        return [R([sq - GF(p)(1)/GF(p)(2)]), R([-sq - GF(p)(1)/GF(p)(2)])]
    else:
        K_ext.<t> = GF(p).extension(Q)
        C = t^11 + K_ext(1)/K_ext(4)
        sq = C.sqrt()
        return [R(list(sq - K_ext(1)/K_ext(2))), R(list(-sq - K_ext(1)/K_ext(2)))]

from itertools import product
roots_per_factor = [solve_quadratic_mod(Q) for Q in factors]
all_combos = list(product(*roots_per_factor))
e_candidates = [int(CRT(list(combo), factors)[0]) for combo in all_combos]
```

### Step 2: Compute the Jacobian Order via Stickelberger's Theorem + LLL

Because `p ≡ 1 (mod 11)`, the curve `H: v² + v = u^11` has an order-11 automorphism `u ↦ ζ₁₁ u`. This gives `J(H)` **Complex Multiplication (CM) by Z[ζ₁₁]**, making the Jacobian order computable algebraically—without any slow point-counting.

#### Theory: Frobenius is a Jacobi Sum

By the theory of Jacobi sums and Stickelberger's theorem, the characteristic polynomial of the Frobenius endomorphism `φ_p` on `J(H)` has all its roots among the conjugates of a single algebraic integer π ∈ Z[ζ₁₁] satisfying:

```
π · π̄ = p   (where π̄ = complex conjugate)
```

The Jacobian order is then:

```
N = |J(H)(F_p)| = Norm_{Q(ζ₁₁)/Q}(1 - π)
```

#### Stickelberger's Theorem and the Lattice

The element π generates a principal ideal in Z[ζ₁₁] that factors into exactly the **5 prime ideals above p corresponding to the Stickelberger set S = {6, 7, 8, 9, 10}**:

```
(π) = P_6 · P_7 · P_8 · P_9 · P_10
```

where `P_t = (p, ζ₁₁ - r^t)` and r is any primitive 11th root of unity mod p.

An element f(ζ₁₁) ∈ Z[ζ₁₁] lies in this ideal if and only if f(x) is divisible mod p by:

```
M(x) = ∏_{t∈S} (x - r^t)  ∈  F_p[x]   (degree 5 polynomial)
```

This gives a **10-dimensional integer lattice** of determinant p⁵:

```
Basis = { p·x^i }_{i=0..4}  ∪  { x^j · M(x) }_{j=0..4}
```

encoded as a 10×10 integer matrix.

#### LLL in ~0.08 seconds

Running LLL on this 10×10 matrix finds the shortest vector in the lattice, which is exactly the coefficient vector of π:

```sage
Fp = GF(p)
r = Fp(1)
while r == 1:
    r = Fp.random_element()^((p-1)//11)
r = int(r)

roots_of_S = [pow(r, t, p) for t in [6, 7, 8, 9, 10]]
Rx = GF(p)['x']
M = prod(Rx.gen() - rt for rt in roots_of_S)

mat = Matrix(ZZ, 10, 10)
for i in range(5):
    mat[i, i] = p                          # rows 0-4: p*x^i
for i in range(5):
    poly = Rx.gen()^i * M
    coeffs = poly.list()
    for j, c in enumerate(coeffs):
        mat[5 + i, j] = int(c)             # rows 5-9: x^i * M(x)

L = mat.LLL()
v_pi = K(list(L[0]))                       # π as element of Q(ζ₁₁)
assert v_pi * v_pi.conjugate() == p        # ✓ confirms π·π̄ = p
```

Since π is only determined up to the 22 units ±ζ₁₁^k (k = 0..10), we compute all 22 candidate norms:

```sage
K.<z> = CyclotomicField(11)
candidate_orders = []
for s in [1, -1]:
    for k in range(11):
        pi = s * z^k * v_pi
        N = Integer((1 - pi).norm())
        candidate_orders.append(N)
```

This yields at most **22 distinct candidate orders**. The true order satisfies `N * ct == 0` on the Jacobian and can be identified in under a minute of Jacobian scalar multiplications.

### Step 3: Decrypt the Flag

With the true order `N` and the 8 candidate `e` values:

```sage
ct_pt = J((R(u), R(v)))

for e_val in e_candidates:
    try:
        d = inverse_mod(e_val, N)       # e⁻¹ mod N
        pt = d * ct_pt                  # d * (e * J(P)) = J(P)
        if pt[0].degree() == 1:
            flag_int = int(-pt[0][0])   # x-coord of P
            flag = bytes.fromhex(hex(flag_int)[2:])
            print(f"FLAG: {flag.decode()}")
    except Exception:
        pass
```

A valid decryption produces a degree-1 Mumford divisor `(x - m, ...)` where m is the integer encoding of the flag bytes.

---

## Complexity Summary

| Step | Method | Time |
|---|---|---|
| Factor D_u over F_p | Berlekamp / Cantor-Zassenhaus | < 1 second |
| Solve 3 quadratics (CRT) → 8 e-candidates | Square roots in F_p and F_{p²} | < 1 second |
| Compute π via Stickelberger lattice | LLL on 10×10 matrix | ~0.08 seconds |
| Identify true order from 22 candidates | 22 scalar multiplications on J | ~9 seconds |
| Decrypt ciphertext | ≤ 8 scalar multiplications on J | ~4 seconds |
| **Total** | | **~15 seconds** |

---

## Running the Solver

Requires SageMath (tested with the `sage` conda environment in WSL):

```bash
# Two-step approach:
sage find_order.sage           # writes true_order.txt
sage get_flag_from_order.sage  # reads true_order.txt, writes flag.txt

# Or all-in-one:
sage solve_challenge.sage
```

---

## Key Mathematical Takeaways

1. **The absent D_v is recoverable** — knowing D_u and the curve equation constrains D_v to only 8 possibilities via the Mumford relation and CRT.

2. **CM curves have algebraically computable Jacobian orders** — for curves with full CM by Z[ζ_n], Stickelberger's theorem gives the Frobenius element up to unit, reducing order computation to LLL on a small lattice.

3. **The "from nothing" title is the hint** — the Stickelberger set S = {6,7,8,9,10} represents what is *absent* from {1,...,10}; LLL on the lattice defined by these absent indices directly yields π and hence the group order.
