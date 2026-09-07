from Crypto.Util.number import long_to_bytes

def crt(mods, rems):
    total = 0
    prod = 1
    for m in mods: 
        prod *= m
    for m_i, r_i in zip(mods, rems):
        p = prod // m_i
        total += r_i * pow(p, -1, m_i) * p
    return total % prod

# Load N, e, ct from output.txt
with open('output.txt') as f:
    lines = f.read().splitlines()
    N = int(lines[0].split('=')[1])
    e = int(lines[1].split('=')[1])
    ct = int(lines[2].split('=')[1])

print('Sieving primes up to 2^24...')
limit = 2**24
sieve = [True] * limit
for p in range(2, int(limit**0.5) + 1):
    if sieve[p]:
        for i in range(p*p, limit, p):
            sieve[i] = False

# The primes used are exactly 24 bits (between 2^23 and 2^24)
primes = [p for p in range(2**23, limit) if sieve[p]]

print('Finding 24-bit factors of N...')
factors = []
for p in primes:
    if N % p == 0:
        factors.append(p)

print(f'Found {len(factors)} small prime factors: {factors}')

# Decrypt modulo each small prime
rems = []
mods = []
for p in factors:
    c_i = ct % p
    d_i = pow(e, -1, p - 1)
    m_i = pow(c_i, d_i, p)
    rems.append(m_i)
    mods.append(p)

# Combine using Chinese Remainder Theorem
print('Combining with CRT...')
m = crt(mods, rems)

print('Flag:', long_to_bytes(int(m)).decode())
