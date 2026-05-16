# six-seven (LACTF 2026) Writeup

## Summary

This is a crypto challenge involving RSA. The modulus `n` is constructed from two primes `p` and `q`. The challenge name and the provided code hint that the digits of `p` and `q` consist only of 6s and 7s.

## Solution

The solution exploits the structure of the primes. Since `p` and `q` are composed only of digits 6 and 7, and their last digits are known (product ends in 9, so 7*7=49), we can factor `n` by exploring the tree of possible digits for `p` and `q` from the least significant digit upwards.

The solver script `solve.py` implements this "meet-in-the-middle" or digit-by-digit search (lifting) to reconstruct `p` and `q`. Specifically:
1. It maintains a set of possible `(p, q)` pairs modulo `10^k`.
2. At each step `k`, it tries appending 6 or 7 to the current `p` and `q` prefixes.
3. It keeps the pairs that satisfy `(p * q) % 10^(k+1) == n % 10^(k+1)`.
4. This quickly prunes the search space, allowing efficient factorization.

Once `p` and `q` are found, the RSA decryption is standard: compute `phi`, `d`, and decipher `c`.

## Code

`solve.py`

```python
from Crypto.Util.number import long_to_bytes

e = 65537

n = 44585356991671485001896074168540258292053928487038062931888644806568424201745662495504159485747427608458767109060325974965991350098904391357324144976944343874465905261038692436198938342267680539591989446687383960546321312142543653994078374521935830523426655430095856063153689801282241139004069871858141384670130907896601986816821304689121323577133751872465880289191191458059546698023404266119755204486741250475124708614291935904969172409068115303352538428907226266271025768051816075161469808059171471273780267729

c = 8497917205964537167764404828464723593514582535997849192275775375524370812760713242200050091134074663695616648678969839644758537528637832268862343050261282929217982773154400106104532542958912657241554753009635484147439375740810442537905422390616405619915160978450397210336369604700623124624241947652421094008553766306365955020898341987442046161542846538350646037861109789310333513546820272291472350556014484239716656379333296259161649986787578409920456758018038938590357756723075290659790541166419547000399184948

def factor_67_rsa_decimal(n, digits=256):
    # p,q digits only {6,7}, last digit = 7
    assert n % 10 == 9  # 7*7 = 49

    states = {(7, 7)}  # (p mod 10^k, q mod 10^k)

    for k in range(1, digits):
        mod = 10 ** (k + 1)
        target = n % mod
        tenk = 10 ** k
        new_states = set()

        for p, q in states:
            for dp in (6, 7):
                p2 = p + dp * tenk
                for dq in (6, 7):
                    q2 = q + dq * tenk
                    if (p2 * q2) % mod == target:
                        new_states.add((p2, q2))

        if not new_states:
            raise RuntimeError("No valid states left")
        states = new_states

    for p, q in states:
        if p * q == n:
            return p, q

    raise RuntimeError("Factorization failed")

# factor n
p, q = factor_67_rsa_decimal(n)

# decrypt
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
m = pow(c, d, n)

print(long_to_bytes(m).decode())
```

## Flag

lactf{wh4t_67s_15_blud_f4ct0r1ng_15_blud_31nst31n}
