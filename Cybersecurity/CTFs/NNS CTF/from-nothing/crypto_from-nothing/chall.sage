n = 11
p = next(p for p in iter(lambda: random_prime(2^512), 0) if p % n == 1)
print(f"p = {p}")

R.<x> = PolynomialRing(FiniteField(p))
H = HyperellipticCurve(x^n, 1, "u,v")
J = H.jacobian()
J = J(J.base_ring())

x = next(x for x in iter(GF(p).random_element, 0) if (1+4*x^n).is_square())
D = randint(2,p) * J(H.lift_x(x))
e = int(D[1][0])

P = H.lift_x(Integer(int(b"NNS{??????????????????????????????????????????????}".hex(), 16)))
ct = e*J(P)

print(f"D_u = {D[0].list()}")
print(f"u = {ct[0].list()}")
print(f"v = {ct[1].list()}")
