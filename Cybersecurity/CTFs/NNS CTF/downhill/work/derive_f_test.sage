import json

data = json.load(open("local_data_500.json"))
N, q = data["N"], data["q"]
true_f = data["true_f"]
true_g = data["true_g"]
true_F = data["true_F"]
true_G = data["true_G"]

R.<x> = ZZ[]
Qy.<y> = QQ[]
K.<z> = Qy.quotient(y^N - 1)
phi = x^N - 1

F = R(true_F)
G = R(true_G)
f_true = R(true_f)
g_true = R(true_g)

# sanity: verify the relation holds for the true key
lhs = (f_true*G - g_true*F) % phi
print("f*G - g*F mod phi (should be constant q):", lhs)

# Step 1: particular solution via ordinary polynomial xgcd (NOT mod phi) of G, F
print("running xgcd(G, F) over Q[x] ...")
d, alpha, beta = G.change_ring(QQ).xgcd(F.change_ring(QQ))
print("gcd d =", d)
# alpha*G + beta*F = d  =>  reduce mod phi (keep as QQ for exactness)
alpha_mod = Qy(alpha.list()) % Qy(phi.list())
beta_mod = Qy(beta.list()) % Qy(phi.list())
d_val = QQ(d[0]) if d.degree() <= 0 else None
print("d as constant:", d_val)

# u = alpha_mod, v = -beta_mod  =>  u*G - v*F = d
# scale by q/d to get f0*G - g0*F = q
scale = QQ(q) / d_val
f0 = alpha_mod * scale
g0 = (-beta_mod) * scale
print("f0, g0 computed (rational, should actually be integer polynomials)")
print("f0 max denom:", max(c.denominator() for c in f0.list()))
print("g0 max denom:", max(c.denominator() for c in g0.list()))

f0_int = R([Integer(c) for c in f0.list()])
g0_int = R([Integer(c) for c in g0.list()])

# verify particular solution
check = (f0_int*G - g0_int*F) % phi
print("verify f0*G - g0*F mod phi:", check)

# Step 2: round c = round(-f0 / F) using K = Q[y]/(y^N-1), matching keygen()'s own trick
c_poly = R([round(coef) for coef in K(Qy(f0_int)) / (-K(Qy(F)))])
print("c_poly computed, degree:", c_poly.degree())

f_cand = (f0_int + c_poly*F) % phi
g_cand = (g0_int + c_poly*G) % phi

print("f_cand vs true_f match:", f_cand == f_true or f_cand == -f_true)
print("f_cand coeffs sample:", f_cand.list()[:20])
print("true_f coeffs sample:", f_true.list()[:20])
ones = sum(1 for c in f_cand.list() if c == 1)
print("f_cand num ones:", ones, "(expect 73)")
