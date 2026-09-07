"""
Faithful local reproduction of chall.py, but importable as a library so we can
generate signatures AND know the ground-truth secret_key for verifying our
attack before ever touching the remote.
"""
from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256
from ecdsa import curves
import secrets, uuid

MAX_INVITES = 6
G = curves.NIST256p.generator
n = curves.NIST256p.order


class Party:
    def __init__(self, secret_key=None, flag=b"NNS{test_flag_for_local_dev}"):
        self.secret_key = secret_key if secret_key is not None else secrets.randbelow(n - 1) + 1
        self.flag = flag
        key = long_to_bytes(self.secret_key, 32)
        cipher = AES.new(key, AES.MODE_ECB)
        self.ct = bytes_to_long(cipher.encrypt(pad(self.flag, 16)))

    def invite(self, m):
        h = bytes_to_long(sha256(m.encode()).digest())
        k = bytes_to_long(str(uuid.uuid4())[:32].encode())
        P = k * G
        r = P.x() % n
        s = (pow(k, -1, n) * (h + r * self.secret_key)) % n
        return r, s
