from Crypto.Util.number import bytes_to_long

flag = b"NNS{???????????????????}"

p = random_prime(2^256)
a,b = [randrange(p) for _ in range(2)]
E = EllipticCurve(GF(p), [a,b])

P = E.random_point()
Q = 2*P
R = 2*Q

print(f"P = {P.xy()}")
print(f"Q = {Q.xy()}")
print(f"R = {R.xy()}")

F = E.lift_x(Integer(bytes_to_long(flag)))
C = next_prime(0x133713371337) * F
print(f"C = {C.xy()}")