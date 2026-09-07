# begineRSA - CTF Challenge Writeup

## The Vulnerability
Looking at the `chall.py` source code, we see how the two moduli, `N1` and `N2`, are generated:
```python
p = getPrime(512)
q = getPrime(512)
N1 = p * q
N2 = q * getPrime(512)
```
The vulnerability here is a classic RSA weakness known as a **Common Factor Attack** (or Common Modulus vulnerability variant). Both moduli `N1` and `N2` share the exact same prime factor, `q`. 

Because both moduli are publicly known (provided in `output.txt`), an attacker can easily find this shared prime factor by computing the **Greatest Common Divisor (GCD)** of `N1` and `N2`.

## The Math (In-Depth Solution)
1. **Find the common prime ($q$):**
   $q = \gcd(N1, N2)$

2. **Find the other prime ($p$) for $N1$:**
   Since $N1 = p \times q$, we can simply divide to retrieve $p$:
   $p = \frac{N1}{q}$

3. **Calculate Euler's Totient ($\phi$) for $N1$:**
   $\phi(N1) = (p - 1) \times (q - 1)$

4. **Calculate the private exponent ($d$):**
   Using the public exponent $e$ (which is `0x10001` or 65537), we calculate the modular inverse:
   $d = e^{-1} \pmod{\phi(N1)}$

5. **Decrypt the ciphertext ($c1$):**
   With the private key recovered, we can decrypt $c1$:
   $m = c1^d \pmod{N1}$

Converting the numerical message $m$ to bytes yields the flag.

## The Flag
`NSS{n3v3r_3v3r_r3u53_4_pr1m3!}`
