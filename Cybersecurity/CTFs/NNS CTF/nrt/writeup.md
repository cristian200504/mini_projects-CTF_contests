# NRT - CTF Challenge Writeup

## The Vulnerability
In `chall.py`, the RSA modulus `N` is generated in two phases:
1. It multiplies random 24-bit primes together until the product exceeds 256 bits. Let's call the product of these small primes $N_{small}$.
2. It then generates increasingly larger primes and multiplies them into $N$ until $N$ exceeds 4096 bits.

Because $N$ is just the product of all these primes, $N_{small}$ perfectly divides $N$. The script also guarantees that the flag is smaller than 256 bits (`len(flag) * 8 < SMALL_BITS`).

Since the flag is smaller than 256 bits and $N_{small}$ is greater than 256 bits, we know that $flag < N_{small}$.

## The Solution
We don't need to factor the entire 8000+ bit modulus `N`. We only need to find the small 24-bit prime factors that make up $N_{small}$.
Since $2^{24}$ is approximately 16.7 million, it is computationally trivial to generate all primes in this range and perform trial division against `N`.

1. **Sieve Primes:** Generate all primes up to $2^{24}$.
2. **Trial Division:** For each 24-bit prime $p$, check if $N \pmod p == 0$. We will find multiple small prime factors.
3. **Local Decryption:** For each found prime $p_i$, calculate $c_i = ct \pmod{p_i}$. We can easily decrypt this to find $m_i = c_i^{d_i} \pmod{p_i}$, where $d_i$ is the local private exponent $e^{-1} \pmod{p_i - 1}$.
4. **Chinese Remainder Theorem:** We now know the value of $flag \pmod{p_i}$ for several primes. By combining them using the Chinese Remainder Theorem (CRT), we can recover $flag \pmod{N_{small}}$.

Since we know $flag < N_{small}$, the combined result is the exact numerical value of the flag.

## The Result
Running the solve script successfully recovers 11 small prime factors. Reconstructing the message via CRT gives us the flag:

**Flag:**
`NNS{n0_n33d_f0r_4ll_pr1m35}`
