from Crypto.Util.number import getPrime, bytes_to_long

flag = bytes_to_long(b"NSS{?????????????????????????}")
notflag = bytes_to_long(b"welcome to NNS ctf 2026!")
p = getPrime(512)
q = getPrime(512)
N1 = p * q
N2 = q * getPrime(512)

e = 0x10001
c1 = pow(flag, e, N1)
c2 = pow(notflag, e, N2)

print(f"N1 = {N1}")
print(f"N2 = {N2}")
print(f"c1 = {c1}")
print(f"c2 = {c2}")
