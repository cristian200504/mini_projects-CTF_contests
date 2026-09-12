# Shamir Secret Spilling — Solution Writeup

**Flag:** `K17{0ur_cl1ent5_r3ally_d0nt_like_r0tating_their_keys!}`

---

## Challenge Overview

An organisation leaked their Shamir Secret Sharing scheme. A well-meaning intern ("minibolt") upgraded it from a 16-share scheme to a 32-share scheme while keeping the old shares backwards-compatible. We are given:

- `MOD` — a 512-bit prime
- `B` — a 273-bit bound (~2^273, much smaller than MOD)
- `known` — 16 (x, y) pairs valid for **both** the old polynomial P and the new polynomial Q
- `new` — 8 (x, y) pairs valid only for Q

The flag is `Q(0)` (the constant term of Q).

The key constraint the intern introduced:

```python
for pc, qc in zip(P + [0]*16, Q):
    assert abs(centered(qc - pc)) < B
```

Every coefficient of Q differs from the corresponding coefficient of P by less than B. This "compatibility" requirement is the vulnerability.

---

## Mathematical Structure

### Polynomials

- **P**: degree-15, 16 coefficients. Recovered exactly from the 16 known shares via Lagrange interpolation.
- **Q**: degree-31, 32 coefficients. FLAG = Q(0).
- **R = Q − P**: degree-31, 32 coefficients. All coefficients satisfy `|centered(R[k])| < B` (tiny vs MOD).

Since B/MOD ≈ 2^(273−512) = 2^(−239), the coefficients of R are genuinely tiny integers — not just "small mod MOD".

### Vanishing Polynomial

R vanishes at all 16 known x-values (since Q(x) = P(x) = y there), so:

```
R(x) = V(x) · L(x)
```

where **V** = ∏(x − known_xᵢ) is a known monic degree-16 polynomial, and **L** is an unknown degree-15 polynomial.

### Parameterising L

From the 8 new shares we compute 8 evaluations of L:

```
L(xᵢ) = (Q(xᵢ) − P(xᵢ)) / V(xᵢ)   mod MOD
```

A degree-15 polynomial has 16 coefficients but we only have 8 constraints, so the solution space is 8-dimensional. We write:

```
L = L_part + W · C
```

where:
- **L_part** = degree-7 Lagrange interpolation through the 8 known L-evaluations (particular solution)
- **W** = ∏(x − new_xᵢ), monic degree-8 (vanishes at all 8 new points)
- **C** = degree-7 polynomial with 8 unknown coefficients c₀…c₇

### Reducing to a Short Vector Problem

Substituting back:

```
R = V · L_part + V · W · C = R_part + G · C   (mod MOD)
```

where **R_part** = V · L_part (known, 32 coefficients) and **G** = V · W (known, 25 coefficients).

The small-coefficient constraint becomes:

```
|centered(R_part[k] + (G·C)[k])| < B   for all k = 0..31
```

This is a **Closest Vector Problem (CVP)**: find an integer vector C such that G·C lands within distance B of −R_part modulo MOD.

---

## Lattice Attack (Kannan Embedding)

### Lattice Construction

We build a (41 × 41) integer matrix using the **Kannan embedding** technique.

Let:
- `nc = 8` (c-variables)
- `ne = 32` (output/error variables)
- `S = MOD // B ≈ 2^239` (scaling factor to balance norms)

**Row j (j = 0..7):**
```
[0...1...0  |  G[0-j]*S, G[1-j]*S, ..., G[31-j]*S]
     ^j                  (Toeplitz row of G, scaled)
```

**Row 8+k (k = 0..31):**
```
[0...0  |  0...MOD·S...0]
               ^(8+k)
```
These rows allow modular reduction in the e-part.

**Row 40 (embedding row):**
```
[0...0  |  -R_part[0]·S, ..., -R_part[31]·S  |  MOD]
```
The large tag `MOD` in the last column identifies this row after LLL reduction.

### Why It Works

The target short vector is:
```
v = (c₀, ..., c₇, e₀·S, ..., e₃₁·S, 0)
```
after subtracting the embedding row, where eₖ = centered(R_part[k] + Σⱼ G[k−j]·cⱼ).

The norms balance because:
- c-part: |cⱼ| ~ MOD, contributes ~ √8 · MOD ~ 2^514
- e-part scaled: |eₖ| · S ~ B · (MOD/B) = MOD, contributes ~ √32 · MOD ~ 2^516

Both are comparable, making the target vector genuinely short in the lattice, and LLL finds it reliably in a 41-dimensional lattice.

### Extracting the Flag

After LLL reduction, find the row with last coordinate ±MOD (the shifted embedding row). Extract c₀…c₇, then:

1. **Reconstruct L**: `L = L_part + W · C`
2. **Reconstruct R**: `R = V · L`
3. **Reconstruct Q**: `Q[k] = (P_padded[k] + R[k]) mod MOD`
4. **Extract flag**: `FLAG = long_to_bytes(Q[0])`

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install fpylll cysignals pycryptodome
python solve.py
```

---

## Key Takeaway

The intern's "backwards compatibility" requirement — keeping all 32 coefficients of Q within B of P — was the fatal mistake. It reduced the freedom of Q to an 8-dimensional search space, making it recoverable via LLL lattice reduction despite Q requiring 32 shares to reconstruct normally. The lesson: rotating cryptographic keys should produce entirely independent keys, not ones that are arithmetically close to the originals.
