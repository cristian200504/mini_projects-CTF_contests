# smol-cats (LACTF 2026) Writeup

## Summary

This is a crypto challenge named "smol-cats" (likely "small cats" -> "small primes"). It provides an RSA modulus `n` and a ciphertext `c`.

## Solution

The modulus `n` is relatively small (around 60 decimal digits). This is too small to be secure against modern factorization algorithms like the Elliptic Curve Method (ECM) or Quadratic Sieve (GNFS).

The solution simply involves factoring `n` into primes `p` and `q` using a tool like Alpertron, yafu, or rigorous use of ECM. The solver script `solve.py` has the factors hardcoded, implying they were found using such an external tool.

Once `p` and `q` are known, the private key `d` is computed, and the ciphertext `c` is decrypted to reveal the flag.

## Code

`solve.py`

```python
# Factors from Alpertron
p = 719947714226556643019526109967
q = 1068624914924289197468236882633
#used https://www.alpertron.com.ar/ECM.HTM to find p and q
# Challenge values
n = 769354064865290564164425378603970188569192452378897230503111
e = 65537
c = 212967529139680494690514452291681489543567899034079183966045

# Sanity check
assert p * q == n, "p*q != n (copied p or q wrong)"

phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)      # modular inverse (Python 3.8+)
m = pow(c, d, n)

print(m)
```

## Flag

lactf{sm0l_pr1m3s_4r3_n0t_s3cur3}
