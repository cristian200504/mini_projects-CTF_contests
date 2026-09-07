from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256
from ecdsa import curves
import os, secrets, uuid

MAX_INVITES = 6
G = curves.NIST256p.generator
n = curves.NIST256p.order
secret_key = secrets.randbelow(n - 1) + 1

flag = os.getenv("FLAG", "NNS{fake_flag}").encode()
key = long_to_bytes(secret_key, 32)
cipher = AES.new(key, AES.MODE_ECB)
ct = bytes_to_long(cipher.encrypt(pad(flag, 16)))

def invite(m):
    h = bytes_to_long(sha256(m.encode()).digest())
    k = bytes_to_long(str(uuid.uuid4())[:32].encode())
    P = k * G
    r = P.x() % n
    s = (pow(k, -1, n) * (h + r * secret_key)) % n
    return r, s

print(f"ct: {ct}")
print(f"You can invite up to {MAX_INVITES} friends.")
for _ in range(MAX_INVITES):
    m = input("Enter the name of your friend: ").strip()
    r, s = invite(m)
    print(f"Here is {m}'s invite code:")
    print(f"Invitation code = {r}:{s}")
