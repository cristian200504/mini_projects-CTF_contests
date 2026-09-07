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

def gen_particular(p, w, qval, phi):
    """Same construction as chall.sage's keygen(): returns (X,Y) with
    p*Y - w*X = qval (exact identity mod phi)."""
    rp, a, _ = p.xgcd(phi)
    rw, b, _ = w.xgcd(phi)
    if gcd(ZZ(rp), qval) != 1:
        return None
    d, u, v = xgcd(ZZ(rp), ZZ(rw))
    if abs(d) != 1:
        return None
    u = u / d
    v = v / d
    X = (-qval * v * b) % phi
    Y = (qval * u * a) % phi
    return X, Y

# want f0*G - g0*F = q  <=>  G*f0 - F*g0 = q  <=>  match p=G, w=F, output (X,Y)=(g0,f0)
result = gen_particular(G, F, q, phi)
print("gen_particular result is None:", result is None)
if result is not None:
    g0, f0 = result  # X=g0, Y=f0 per the p*Y - w*X = qval pattern (G*f0 - F*g0 = q)
    check = (f0 * G - g0 * F) % phi
    print("verify f0*G - g0*F mod phi (should be", q, "):", check)

    # size-reduce f0 modulo F (same trick as keygen's own size-reduction step)
    c_poly = R([round(coef) for coef in K(Qy(f0)) / K(Qy(F))])
    f_cand = (f0 - c_poly * F) % phi
    g_cand = (g0 - c_poly * G) % phi

    print("f_cand == true_f:", f_cand == f_true)
    print("f_cand == -true_f:", f_cand == -f_true)
    ones = sum(1 for c in f_cand.list() if c == 1)
    print("f_cand num ones:", ones, "(expect", 73 if f_cand == f_true else "?", ")")
    print("f_cand range:", min(f_cand.list()), max(f_cand.list()))
    print("f_cand sample:", f_cand.list()[:20])
    print("true_f  sample:", f_true.list()[:20])
