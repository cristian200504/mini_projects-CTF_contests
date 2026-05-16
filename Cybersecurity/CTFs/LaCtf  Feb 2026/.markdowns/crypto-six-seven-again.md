# six-seven-again (LACTF 2026) Writeup

## Summary

This is another RSA challenge similar to "six-seven", but with a twist. The modulus `n` is much larger, and the structure of the primes is different or partially known. The primes are formed by a specific pattern of 6s and 7s.

## Solution

The primes `p` and `q` satisfy a property where a large part of them is known or they share a common structure. Specifically, the solver uses Coppersmith's method for finding small roots of modular polynomials.

The `sage solve.txt` script indicates that:
1. A base part `p_base` is constructed using 67 repetitions of digits '6' and '7'.
2. It assumes `p` has the form `p_base + x0 * 10^67`, where `x0` is small.
3. It constructs a polynomial `f(x) = x + p_base * (10^67)^(-1) mod n`.
4. It uses `f.small_roots()` to find `x0`.
5. Once `x0` is found, `p` is fully recovered.

This is a **Stereotyped Prefix Attack** (or suffix/pattern attack) on RSA, solved using lattice reduction (LLL) via SageMath's `small_roots`.

## Code

`sage solve.txt`

```python
# ================== public data ==================
n = 1917606379092010442240895259281087506518953213064946102685271869792222395229323181992324207006351336407709271558095371910911509984941851479631451767077619434096195229724325785080342785869270964048132278524850285522364041917384798365228481427082711397335412607200839380440434235694895914538601572720691355553863265984872536131888140564748410142408927715485805727019286131883726243062646319774672317643779

c = 110391667868121173909483296481106277518878592322619386800111427106897381851751004329387793881253685082171202870157608458119648488326218470171891113545680162523502095280014482775507087086028093347821633610433798507594836409547203444620734434884812015268551039928640302824786972195454098860541395226829179897356798824905156213676916968446335141249118907643808744538906047926868755739678245109463833649057

e = 65537
# =================================================


# ---------- reconstruct the prime structure ----------
A = Integer(int("6"*67))
B = Integer(int("7"*67))

p_base = A * (10^134) + B


# ---------- Coppersmith small-root setup ----------
R.<x> = PolynomialRing(Zmod(n))

inv = inverse_mod(10^67, n)
f = x + p_base * inv    # monic polynomial

X = 10^67
roots = f.small_roots(X=X, beta=0.4)

if not roots:
    raise ValueError("No root found — try beta=0.3..0.49")

x0 = Integer(roots[0])


# ---------- recover RSA primes ----------
p = p_base + x0 * (10^67)
if n % p != 0:
    raise ValueError("Recovered p does not divide n")

q = n // p


# ---------- optional sanity check ----------
mid = str((p // (10^67)) % (10^67)).zfill(67)
assert set(mid).issubset(set("67"))


# ---------- decrypt ----------
phi = (p - 1) * (q - 1)
d = inverse_mod(e, phi)

m = power_mod(c, d, n)
flag = Integer(m).to_bytes((m.nbits() + 7) // 8, "big")

print(flag)
```

## Flag

lactf{n_h4s_1337_b1ts_b3c4us3_667+670=1337}
