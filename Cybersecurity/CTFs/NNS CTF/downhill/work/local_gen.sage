from random import sample
from hashlib import shake_256, sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json

flag = b"NNS{test_flag_for_local_dev_of_downhill}"

N,q,df,dg = 251,128,73,71

R.<x> = ZZ[]
Q.<y> = QQ[]
K.<z> = Q.quotient(y^N-1)
Rq.<w> = Zmod(q)[]
Rq = Rq.quotient(w^N-1)
phi = x^N-1

def keygen():
    while True:
        f,g = [sum(x^i for i in sample(range(N),d)) for d in (df,dg)]
        rf,a,_ = f.xgcd(phi)
        rg,b,_ = g.xgcd(phi)

        if gcd(ZZ(rf),q) != 1:
            continue

        d,u,v = xgcd(ZZ(rf),ZZ(rg))
        if abs(d) != 1:
            continue

        u = u/d
        v = v/d
        F = (-q*v*b) % phi
        G = ( q*u*a) % phi
        k = R([round(c) for c in K(Q(F))/K(Q(f))])

        F = (F-k*f) % phi
        G = (G-k*g) % phi
        h = Rq(g*a*inverse_mod(ZZ(rf),q))
        return f,g,F,G,h

f,g,F,G,h = keygen()

def sign(msg):
    m = R([c&127 for c in shake_256(msg).digest(N)])
    a = (-m*F) % phi
    b = ( m*f) % phi
    a = R([(QQ(a[i])/q).round("away") for i in range(N)])
    b = R([(QQ(b[i])/q).round("away") for i in range(N)])
    sig = (a*f+b*F) % phi
    t_val = (a*g+b*G) % phi
    return sig, t_val

key = sha256(bytes(f[i] for i in range(N))).digest()
ct = AES.new(key,AES.MODE_ECB).encrypt(pad(flag,16))

def coeffs(poly, n=N):
    L = [int(c) for c in poly.list()]
    return L + [0]*(int(n)-len(L))

n_sigs = 3000
sigs = []
for i in range(n_sigs):
    msg = f"friend{i}".encode()
    s, t_val = sign(msg)
    sigs.append({"msg": msg.hex(), "sig": coeffs(s), "true_t": coeffs(t_val)})

out = {
    "N": int(N), "q": int(q), "df": int(df), "dg": int(dg),
    "pk_h": coeffs(h.lift()),
    "ct": ct.hex(),
    "flag": flag.decode(),
    "true_f": coeffs(f),
    "true_g": coeffs(g),
    "true_F": coeffs(F),
    "true_G": coeffs(G),
    "sigs": sigs,
}
def sanitize(o):
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [sanitize(v) for v in o]
    if isinstance(o, (int, str, float, bool)) or o is None:
        return o
    return int(o)

with open("local_data.json", "w") as fp:
    json.dump(sanitize(out), fp)

print("wrote local_data.json,", len(sigs), "signatures")
print("true f has", sum(1 for c in out["true_f"] if c==1), "ones (expect", df, ")")
print("true g has", sum(1 for c in out["true_g"] if c==1), "ones (expect", dg, ")")
print("F range:", min(out["true_F"]), max(out["true_F"]))
print("G range:", min(out["true_G"]), max(out["true_G"]))
