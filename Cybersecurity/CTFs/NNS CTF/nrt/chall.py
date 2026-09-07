from Crypto.Util.number import getPrime, bytes_to_long

SMALL_BITS = 256

e = 0x10001


def genModulus():
    N = 1
    while N.bit_length() <= SMALL_BITS:
        p = getPrime(24)
        assert (p - 1) % e != 0
        if N % p != 0:
            N *= p
    while N.bit_length() <= 4096:
        p = getPrime(N.bit_length())
        N *= p
    return N


flag = b"NNS{fake_flag}"
assert len(flag) * 8 < SMALL_BITS

N = genModulus()
ct = pow(bytes_to_long(flag), e, N)
print(f"{N=}")
print(f"{e=}")
print(f"{ct=}")
