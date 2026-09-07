"""Derive and test f from an exact (or rotation/sign equivalent) F,G pair.

Usage: sage verify_exact_fg.sage <data.json> <fg.json>
`fg.json` contains {'F': [...], 'G': [...]}.
"""
import json
import sys
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

data = json.load(open(sys.argv[1]))
# The optional local-test shortcut lets the recovery algebra be verified
# against the challenge generator's recorded ground truth before it is used
# on a recovered remote candidate.
candidate = ({"F": data["true_F"], "G": data["true_G"]}
             if sys.argv[2] == "--groundtruth"
             else json.load(open(sys.argv[2])))
N, q = data["N"], data["q"]
ct = bytes.fromhex(data["ct"])

R = PolynomialRing(ZZ, "x")
x = R.gen()
Qy = PolynomialRing(QQ, "y")
y = Qy.gen()
K = Qy.quotient(y**N - 1, "z")
phi = x**N - 1

def gen_particular(p, w):
    rp, a, _ = p.xgcd(phi)
    rw, b, _ = w.xgcd(phi)
    if rp.degree() > 0 or rw.degree() > 0 or gcd(ZZ(rp), q) != 1:
        return None
    d, u, v = xgcd(ZZ(rp), ZZ(rw))
    if abs(d) != 1:
        return None
    u, v = u / d, v / d
    return (-q * v * b) % phi, (q * u * a) % phi

def test_f(poly):
    coeffs = [int(c) for c in poly.list()] + [0] * N
    coeffs = coeffs[:N]
    for sign in (1, -1):
        signed = [(sign * c) % 256 for c in coeffs]
        for shift in range(N):
            rotated = signed[-shift:] + signed[:-shift] if shift else signed
            plain = AES.new(sha256(bytes(rotated)).digest(), AES.MODE_ECB).decrypt(ct)
            try:
                flag = unpad(plain, 16)
            except ValueError:
                continue
            if flag.startswith(b"NNS{") and flag.endswith(b"}") and flag.isascii():
                return flag
    return None

for sign in (1, -1):
    F = sign * R(candidate["F"])
    G = sign * R(candidate["G"])
    result = gen_particular(G, F)
    if result is None:
        print("not coprime for sign", sign)
        continue
    g0, f0 = result
    c = R([round(coef) for coef in K(Qy(list(f0))) / K(Qy(list(F)))])
    f = (f0 - c * F) % phi
    coeffs = [int(value) for value in f.list()] + [0] * N
    print("sign", sign, "f range", min(coeffs), max(coeffs), "weight", sum(v == 1 for v in coeffs))
    flag = test_f(f)
    if flag:
        print("FLAG:", flag.decode())
        sys.exit(0)
print("no flag")
