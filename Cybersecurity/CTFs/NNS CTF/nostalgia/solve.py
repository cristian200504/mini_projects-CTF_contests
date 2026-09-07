from Crypto.Cipher import AES
from hashlib import sha256
from Crypto.Util.Padding import unpad

# Given ciphertext
ct = bytes.fromhex('85c43735b8442a69843bdc2ca0fb2d41eb548057c43b912704abdf2e27a8d8bc97017ec30b5d100498f12183c9e2ebed')
prefix = b'NNS{'

# LCG parameters
M = 2**32
A = 16843009
C = 826366247

# Fast forward the LCG 1337 iterations
# Since LCG is linear: s_n = (A * s_{n-1} + C) % M
# We can find the compound multiplier and increment
a_n = 1
c_n = 0
for _ in range(1337):
    a_n = (a_n * A) % M
    c_n = (c_n * A + C) % M

# a_n is 586823937
# c_n is 3067822255

# We know the seed is roughly around the challenge creation time (September 2026)
# Epoch time for early Sep 2026 is around 1788000000.
print("Brute-forcing timestamps...")
for s0 in range(1788000000, 1789000000):
    # Calculate the 1337th seed in O(1) time
    final_seed = (a_n * s0 + c_n) % M
    
    # Hash and decrypt the first block
    key = sha256(str(final_seed).encode()).digest()
    pt_block = AES.new(key, AES.MODE_ECB).decrypt(ct[:16])
    
    # Check if we hit the flag format
    if pt_block.startswith(prefix):
        print(f"[+] Found original timestamp: {s0}")
        print(f"[+] Found final LCG seed: {final_seed}")
        
        # Decrypt the full ciphertext
        pt_full = AES.new(key, AES.MODE_ECB).decrypt(ct)
        flag = unpad(pt_full, AES.block_size).decode()
        print(f"[+] Flag: {flag}")
        break
else:
    print("[-] Not found in range.")
