from Crypto.Util.number import long_to_bytes

# The given values from output.txt
P = (8556657727707208274959688356215492073697687136731745904584838792512887432513, 10499616004036352077827577187299579257617217465469948797372067456761225952316)
Q = (88180657532143901179801400727618544475583986813868807456575952256533937646251, 63821392431022588399657934703280620258227322035271046362557270025043176928410)
R = (2884294645399294720380774151786063792855454467820790044049756771962549273576, 45546238707907282017604068308740273108250809871556283061080241644830449119761)
C = (88072115282803413386990359870648890974288047092544455066184535919493069001195, 78478175560432097877707550454665012326974806492122263197710261539872842646450)
m = next_prime(0x133713371337)

# Step 1: Recover the curve parameters
# We use Q = 2P and R = 2Q to establish the algebraic relationships and solve for a, b, and p.
x1, y1 = P; x2, y2 = Q; x3, y3 = R

# Tangent line relationships for doubling points:
V1 = (y2 + y1)^2 - (x2 + 2*x1) * (x1 - x2)^2
V2 = (y3 + y2)^2 - (x3 + 2*x2) * (x2 - x3)^2

# The prime p must divide both, so we can take the GCD
p = gcd(abs(V1), abs(V2))
# (Optionally remove any small factors from the GCD if it isn't strictly prime)
while p % 2 == 0: p //= 2

# We can then solve for a and b
lam = (y2 + y1) * inverse_mod(x1 - x2, p) % p
a = (2 * y1 * lam - 3 * x1 * x1) % p
b = (y1^2 - x1^3 - a*x1) % p

print(f"Recovered p = {p}")
print(f"Recovered a = {a}")
print(f"Recovered b = {b}")

# Step 2: Establish the curve and compute the group order
E = EllipticCurve(GF(p), [a, b])
N = E.order() # Schoof's algorithm finds the order quickly in Sage

print(f"Curve Order = {N}")

# Step 3: Divide C by m to get F
C_point = E(C[0], C[1])
# We want F such that m * F = C_point
# This means F = m^-1 * C_point
d = inverse_mod(m, N)
F = d * C_point

# The flag is the x-coordinate of F
flag_int = int(F.xy()[0])
print("Flag:", long_to_bytes(flag_int).decode())
