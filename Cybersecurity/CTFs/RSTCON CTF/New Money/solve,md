# New Money - Solve & Writeup

## Challenge Information
- **Category:** Steganography / Web / Cryptography
- **Points:** 80
- **Author:** Veryyes
- **Files Provided:** `bottlecap.jpg`
- **Description:** 
  > Vault-Tec's Caps Lotto-Matic takes your bottlecaps and promises a fortune. The odds are terrible and the jackpot never seems to land -- almost like the wheels were decided before you ever pulled the lever.
  > 
  > The photo attached seems old, but leads to to something new

---

## 1. Finding the Hidden Link

We begin by analyzing `bottlecap.jpg`. Scanning the image for barcodes / QR codes:

```python
import cv2
img = cv2.imread("bottlecap.jpg")
detector = cv2.QRCodeDetector()
url, _, _ = detector.detectAndDecode(img)
print(url)
```

**Output:**
```text
https://rstcon.org/bottle-cap
```

The photo contains a QR code that redirects to an interactive Vault-Tec web terminal: **Caps Lotto-Matic**.

---

## 2. Analyzing the Caps Lotto-Matic Web Application

Examining the source code of `https://rstcon.org/bottle-cap/`, we find the client-side game logic implemented in JavaScript:

```javascript
var e = {
    A: 1664525,
    C: 1013904223,
    M: 4294967296,
    SEED: 3405691582,
    POOL: [0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5],
    IV: "Ap89oAD+nv/sLj5m",
    CT: "M8KK2DP+IYuYMvu3PgAT581HZkdj5F62u2rmdu7z6ld32sZWuboj096hbO5n0q/mK1RH3A=="
};
var t = e.SEED;
var n = 0;

function S() {
    return t = (e.A * t + e.C) % e.M, e.POOL[t % e.POOL.length];
}
```

### Game Mechanics:
1. **Pseudo-Random Number Generator (PRNG):** 
   - A standard Linear Congruential Generator (LCG) with parameters from *Numerical Recipes*:
     $$t_{k+1} = (1664525 \cdot t_k + 1013904223) \pmod{2^{32}}$$
     $$\text{initial seed} = 3405691582$$
   - Each reel value is selected by mapping $t \pmod{|\text{POOL}|}$ to `POOL`.
   - The symbol `0` corresponds to the bottlecap icon (the jackpot symbol). Notice `0` appears only once out of 21 elements in `POOL` ($\approx 4.76\%$ per reel).
2. **Spinning the Reels:**
   - Each spin calls `S()` 3 times: `var e = [S(), S(), S()]; n = t;`.
3. **Jackpot Condition:**
   - When all three reels hit `0` (three caps), a jackpot is awarded ($250$ caps).
   - The machine fills the redemption ticket input with the current LCG internal state $n$ (`String(n)`).
4. **Flag Decryption (`G(t)`):**
   - The ticket string $n$ is hashed using **SHA-256**.
   - The SHA-256 digest serves as a 256-bit AES key.
   - The ciphertext `e.CT` is decrypted using **AES-GCM** with nonce `e.IV`.
   - If decryption succeeds, the plaintext is displayed: `"GRAND PRIZE UNLOCKED → " + flag`.

---

## 3. Exploit & Solution

Because the PRNG state is deterministic and seeded statically:
1. We simulate the LCG forward in Python.
2. We detect the very first spin where all 3 reels hit `0`.
3. The first jackpot lands on **spin 32,472**, with LCG state:
   $$n = 680287398$$
4. We derive the AES-GCM key from $\text{SHA-256}(\text{"680287398"})$ and decrypt the ciphertext `e.CT`.

### Solve Script (`solve.py`)

```python
#!/usr/bin/env python3
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import cv2

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
```

---

## 4. Flag

```text
rstcon{th3_wh33ls_w3r3_n3v3r_r4nd0m}
```
