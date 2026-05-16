from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

ct_hex = "336879c45d3b02dcd2048688541269206e496787d0a0e77995e57df88391b40427b64eec09d0634ccb684d3ffb6e52561c3d99cb5cc23d5794e0f396d52ee9fd9a6483024ec36ca5180c7988579fa43a"
ciphertext = bytes.fromhex(ct_hex)

# Clue 1: Y2K_BuG_19990101 (16 chars from PNG)
clue1 = b"Y2K_BuG_19990101"

# Clue 2: Minesweeper (8 rows)
rows = [
    0b01110000, # 0x70
    0b10000000, # 0x80
    0b10000110, # 0x86
    0b10000101, # 0x85
    0b01110111, # 0x77
    0b00000000, # 0x00
    0b00100010, # 0x22
    0b00100010, # 0x22
]
iv_from_board = bytes(rows) + bytes(rows) # Repeat to 16 bytes

def decrypt(key, iv, ct):
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()
    except Exception as e:
        return str(e)

print("=== Attempt A: Key=Y2K_BuG_19990101, IV=Board*2 ===")
res = decrypt(clue1, iv_from_board, ciphertext)
print(f"Result: {repr(res)}")

print("\n=== Attempt B: Key=Board*2, IV=Y2K_BuG_19990101 ===")
res = decrypt(iv_from_board, clue1, ciphertext)
print(f"Result: {repr(res)}")

# Wait, "The key lives in volatile memory". This means it's not the PNG string.
# The PNG string "Y2K_BuG_19990101" is likely the IV (hides in plain sight).
# So I still need the key from memory.

# Let's try to look for the key at 0x08049530 again.
# Earlier I saw: 0x30 0x95 0x04 0x08 ...
# 0x08049530 is 134518064 in decimal.
# Is it possible the key is the string representation of an address? No.

# Let's try: Key = extracted 16 bytes from a specific address.
# I will use the format string to find where "Project Epoch" classified data is.
