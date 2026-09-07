from random import sample
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

n, p, q = 256, 3, 367
du, df, dg, dm, dz = 90, 88, 60, 110, 96

R.<x> = ZZ[]
Pp.<xp> = GF(p)[]
Rp = Pp.quotient(xp^n + 1)
Pq.<xq> = GF(q)[]
Rq = Pq.quotient(xq^n + 1)

def ternary(a, b=None):
    b = a if b is None else b
    I = sample(range(n), a+b)
    return sum((x^i for i in I[:a]), R(0)) - sum((x^i for i in I[a:]), R(0))

def center(a, m):
    return R([((ZZ(a[i]) + m//2) % m) - m//2 for i in range(n)])

def keygen():
    while True:
        u = ternary(du, du+1)
        f = u + p*ternary(df)
        g = u + p*ternary(dg)
        if Rp(u).is_unit() and Rq(f).is_unit():
            return f, g, u

def sign(f,g,u,m):
    u_inv = Rp(u)^-1
    y = center(u_inv*Rp(m),p)
    z = ternary(dz)
    w = y + p*z
    s = center(Rq(f*w),q)
    t = center(Rq(g*w),q)
    Dev_s = center(s-m,p)
    Dev_t = center(t-m,p)
    e = R([-Dev_s[i] if Dev_s[i] == Dev_t[i] else 0 for i in range(n)])
    e_prime = center(u_inv*Rp(e),p)
    w += e_prime
    return Rq(f*w)

f, g, u = keygen()
pk = Rq(g)/Rq(f)
messages = [ternary(dm) for _ in range(10)]
sigs = [sign(f, g, u, message) for message in messages]

flag = b"NNS{????????????????????????????????????????}"
key = sha256(bytes(ZZ(f[i]) % 256 for i in range(n))).digest()
ct = AES.new(key, AES.MODE_ECB).encrypt(pad(flag, AES.block_size))

with open("output.py", "w") as out:
    out.write(f"pk = {[ZZ(pk[i]) for i in range(n)]}\n")
    out.write(f"sigs = {[([ZZ(m[i]) for i in range(n)], [ZZ(s[i]) for i in range(n)]) for m, s in zip(messages, sigs)]}\n")
    out.write(f"ct = '{ct.hex()}'\n")
