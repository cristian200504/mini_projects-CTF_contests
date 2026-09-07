# nostalgia - CTF Challenge Writeup

## The Vulnerability
Looking at `chall.py`, the core of the issue lies in how the initial seed is generated and handled:
```python
seed = time.time() # nanosecond precision, you will never find the seed muahahaha

for _ in range(1337):
	seed = lcg(seed)
```
The author assumes that `time.time()` provides an unguessable seed due to its fractional nanosecond precision. However, looking at the `lcg` function:
```python
def lcg(s):
	return (16843009*int(s)+826366247)%(2**32)
```
The `int(s)` conversion completely truncates the fractional part of the float! The effective initial seed is just the UNIX epoch timestamp (in seconds) of when the script was executed.

## The Solution
Instead of an infinite search space of floats, we only have to guess the Unix timestamp in seconds. The CTF file timestamps suggest it was created around September 2026 (epoch time `~1788590000`).

We can brute-force this small range of timestamps. To make this extremely fast, we can mathematically "fast-forward" the Linear Congruential Generator (LCG). Since the LCG transition is a linear function `s_next = (A * s + C) % M`, 1337 iterations can be collapsed into a single step:
`s_1337 = (A_1337 * s_0 + C_1337) % M`

1. Calculate the compound `A` and `C` for 1337 iterations.
2. Iterate through Unix timestamps `s_0` starting near the challenge's creation date.
3. Compute the `final_seed` in $O(1)$ time.
4. Hash the seed with SHA256 to derive the AES key.
5. Decrypt the first 16 bytes of the ciphertext and check if it starts with `NNS{`.

## The Result
Running the brute-force script instantly finds the correct initial timestamp (`1788275074`), deriving the AES key and decrypting the ciphertext.

**Flag:**
`NNS{th3_b3st_t1m3_t0_m4k3_m3m0r13s_15_n0w}`
