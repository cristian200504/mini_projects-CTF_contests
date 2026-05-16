#!/usr/bin/env python3

BLOCK_SIZE = 8  # DES block size

# Hardcoded ciphertext returned from ultra secure v2
HEX_VALUE = "424954534354467b35757033725f6433355f317a5f6e30375f3533637572337d08080808080808083b2c81123deb4de2"

def pkcs7_unpad(data: bytes, block_size: int = BLOCK_SIZE) -> bytes:
    pad = data[-1]
    if pad < 1 or pad > block_size:
        raise ValueError("Invalid padding length")
    if data[-pad:] != bytes([pad]) * pad:
        raise ValueError("Invalid padding bytes")
    return data[:-pad]

def main():
    raw = bytes.fromhex(HEX_VALUE)

    # Find valid PKCS#7 padded prefix
    for i in range(len(raw), 0, -BLOCK_SIZE):
        candidate = raw[:i]
        if len(candidate) % BLOCK_SIZE != 0:
            continue
        try:
            flag = pkcs7_unpad(candidate)
            print(flag.decode())
            return
        except:
            continue

    print("Failed to decode")

if __name__ == "__main__":
    main()