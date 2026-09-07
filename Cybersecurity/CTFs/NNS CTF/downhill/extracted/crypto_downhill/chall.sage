from random import sample
from hashlib import shake_256, sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

flag = os.getenv("FLAG", "NNS{fake_flag}").encode()

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
    return (a*f+b*F) % phi

key = sha256(bytes(f[i] for i in range(N))).digest()
ct = AES.new(key,AES.MODE_ECB).encrypt(pad(flag,16))

print(f"pk = {h.lift().list()}")
print(f"ct = {ct.hex()}")

n_sigs = 500
for _ in range(n_sigs):
    print(sign(input("sign> ").encode()).list())
