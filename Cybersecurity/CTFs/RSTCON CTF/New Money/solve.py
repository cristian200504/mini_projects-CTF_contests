#!/usr/bin/env python3
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import cv2

import os

# Step 1: Detect QR code in the image
script_dir = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(script_dir, "bottlecap.jpg")
img = cv2.imread(img_path)
detector = cv2.QRCodeDetector()
url, _, _ = detector.detectAndDecode(img)
print(f"[*] Decoded QR code from {img_path}: {url}")

# Step 2: LCG Parameters from the slot machine web page
A = 1664525
C = 1013904223
M = 4294967296
SEED = 3405691582
POOL = [0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5]

IV = base64.b64decode("Ap89oAD+nv/sLj5m")
CT = base64.b64decode("M8KK2DP+IYuYMvu3PgAT581HZkdj5F62u2rmdu7z6ld32sZWuboj096hbO5n0q/mK1RH3A==")

# Step 3: Fast-forward LCG until the first jackpot (three 0s)
t = SEED

def S():
    global t
    t = (A * t + C) % M
    return POOL[t % len(POOL)]

print("[*] Simulating LCG spins to find the first jackpot...")
spin = 0
while True:
    spin += 1
    r1 = S()
    r2 = S()
    r3 = S()
    n = t
    if r1 == 0 and r2 == 0 and r3 == 0:
        print(f"[+] Jackpot hit on spin {spin}! LCG state (serial): {n}")
        break

# Step 4: Decrypt AES-GCM using SHA-256(serial)
key = hashlib.sha256(str(n).encode("utf-8")).digest()
aesgcm = AESGCM(key)
flag = aesgcm.decrypt(IV, CT, None).decode("utf-8")

print(f"[+] Recovered Flag: {flag}")
