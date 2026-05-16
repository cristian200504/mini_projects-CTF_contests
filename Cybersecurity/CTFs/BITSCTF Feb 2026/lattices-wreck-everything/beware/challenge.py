import sys
import os
import random
import json
import hashlib
import numpy as np

from lwe_gen import falconGen

def encrypt_flag(f, flag):
    key = hashlib.sha256(f.tobytes()).digest()
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(flag.encode())])
    return encrypted.hex()

def main():
    N = 512
    num_hints = 436
    
    print(f"Generating Falcon-{N} keys...")
    A, f, g_neg, q = falconGen(N)
    
    print("Selecting hints...")
    indices = random.sample(range(N), num_hints)
    hints = [[int(i), int(f[i])] for i in indices]
    b = (f.dot(A) + g_neg) % q
    
    if not np.all(b == 0):
        print("Warning: b is not all zeros. This might happen if rotMatrix or falconGen has different conventions.")
        print(f"Non-zero elements in b: {np.count_nonzero(b)}")
    
    data = {
        "q": int(q),
        "n": int(N),
        "A": A.tolist(),
        "b": b.tolist(),
        "hints": hints
    }
    
    flag = "BITSCTF{REDACTED}"
    encrypted_flag = encrypt_flag(f, flag)
    
    print(f"Challenge generated successfully!")
    print(f"Leaked {num_hints} coefficients of f.")

if __name__ == "__main__":
    main()
