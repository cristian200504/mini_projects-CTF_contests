from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

state = [0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1]
taps = [63, 61, 60, 58]
ct = bytes.fromhex("8f0e6d0f5b0dc1db201948b9e0cebd8f9195f08c0c8364a8741150da8e5bc72838338e7e04fbddef0c6260a4eb758417")

def step(s):
    fb = s[63] ^ s[61] ^ s[60] ^ s[58]
    out = s[0]
    s = s[1:] + [fb]
    return s, out

bits = []
for _ in range(128):
    state, b = step(state)
    bits.append(b)

key = bytes(
    int("".join(map(str, bits[i:i+8])), 2)
    for i in range(0, 128, 8)
)

cipher = Cipher(algorithms.AES(key), modes.ECB())
dec = cipher.decryptor()
pt = dec.update(ct) + dec.finalize()

print("key =", key.hex())
print("plaintext =", pt)
print("flag =", pt[:-pt[-1]].decode())  # PKCS#7 unpad