from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Ciphertext from PCAP
ct_hex = "336879c45d3b02dcd2048688541269206e496787d0a0e77995e57df88391b40427b64eec09d0634ccb684d3ffb6e52561c3d99cb5cc23d5794e0f396d52ee9fd9a6483024ec36ca5180c7988579fa43a"
ciphertext = bytes.fromhex(ct_hex)

# IV from zsteg
iv = b"Y2K_BuG_19990101"

# Key from msn_epoch.key download
key = b"M1ll3nn1um_K3y!!"

def decrypt(key, iv, ct):
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()
    except Exception as e:
        return str(e)

print(f"KEY: {key}")
print(f"IV:  {iv}")
print(f"CT_LEN: {len(ciphertext)}")

res = decrypt(key, iv, ciphertext)
print(f"\nDECRYPTED RESULT:\n{res.decode('ascii', errors='replace')}")

# If result contains a flag, output it.
if b"HACKDAY" in res:
    print(f"\n--- FLAG FOUND ---\n{res.split(b'HACKDAY')[1].split(b'}')[0].decode('ascii') if b'}' in res else 'N/A'}")
