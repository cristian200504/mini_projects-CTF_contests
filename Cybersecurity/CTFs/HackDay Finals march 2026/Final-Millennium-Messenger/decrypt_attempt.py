from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Ciphertext from PCAP hex dump (string representation)
ct_hex = "336879c45d3b02dcd2048688541269206e496787d0a0e77995e57df88391b40427b64eec09d0634ccb684d3ffb6e52561c3d99cb5cc23d5794e0f396d52ee9fd9a6483024ec36ca5180c7988579fa43a"
ciphertext = bytes.fromhex(ct_hex)

# IV from zsteg output
iv = b"Y2K_BuG_19990101"

# Potential key 1: from stack pos 3 (0123...?)
key1 = b"0123456789:;<=>?"

def decrypt(key, iv, ct):
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()
    except Exception as e:
        return str(e)

print("=== Decryption Attempt 1 (Key: 0123456789:;<=>?) ===")
res = decrypt(key1, iv, ciphertext)
print(f"Result: {repr(res)}")

# Potential key 2: "ProjectEpoch1999" (16 bytes)
key2 = b"ProjectEpoch1999"
print("\n=== Decryption Attempt 2 (Key: ProjectEpoch1999) ===")
print(f"Result: {repr(decrypt(key2, iv, ciphertext))}")

# Maybe the IV is the key?
print("\n=== Decryption Attempt 3 (Key: Y2K_BuG_19990101, IV: zeros) ===")
print(f"Result: {repr(decrypt(iv, b'0'*16, ciphertext))}")
