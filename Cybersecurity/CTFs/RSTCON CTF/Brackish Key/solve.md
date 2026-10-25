# Brackish Key — CTF Challenge Writeup

## Challenge Information
- **Name:** Brackish Key
- **Points:** 10
- **Author:** f8al
- **Description:** `We pulled a note off a SecurityShrimp engagement box. Whoever wrote it did a little something to it. Provided: cipher.txt`
- **Flag:** `rstcon{cr1b_dragging_the_brackish_key}`

---

## 1. Initial Reconnaissance

We are provided `cipher.txt`, which contains a 342-character hexadecimal string (`171` bytes):

```text
3117521b170b06483d0d101b5c1e45041b540201421c5e1a0058524301110306540a45161a544e000c155009000f175f1a450100540a1642065e000c051a4540450f13580011071c500006075245010e071c1107164200421a060d1c4a0d1753106e0a17031556070b052d4506003d10430f06091b42063a0917481345061d11000a16525d0b0414171107114201581a110b1c564e0a0c524506004205581c00421c54161142065803004c
```

Notice the byte distribution: almost all bytes are in the range `0x00`–`0x5f`, which is a classic indicator of ASCII text XORed with an ASCII key.

---

## 2. Cryptanalysis (Crib Dragging & Repeating-Key XOR)

We have two strong known-plaintext cribs:
1. The flag format prefix: `rstcon{`
2. The organization name mentioned in the prompt: `SecurityShrimp`

### Method A: Crib-Dragging `rstcon{`
Sliding the 7-byte crib `rstcon{` across every position $i$ of the ciphertext and computing $C[i:i+7] \oplus \text{"rstcon\{"}$ reveals at **offset 86**:

```text
Offset 86: key = b'r1nebr1'
```

Notice that `r1nebr1` is periodic with period **5**. Since $86 \equiv 1 \pmod 5$, shifting the 5-byte repeating key to align with offset 0 yields:

$$\text{Key} = \texttt{br1ne}$$

### Method B: Crib-Dragging `SecurityShrimp` at Offset 0
XORing the first 14 bytes of the ciphertext with `SecurityShrimp` directly yields:

```text
b'br1nebr1nebr1n'
```

Confirming the 5-byte repeating XOR key is `br1ne` ("brackish" water = brine!).

---

## 3. Exploitation & Solution

Decrypting the entire ciphertext with the repeating key `br1ne`:

### Solver Script (`solve.py`)

```python
from itertools import cycle

with open("cipher.txt", "r") as f:
    ct = bytes.fromhex(f.read().strip())

# 1. Crib-drag 'rstcon{' to locate the repeating key
crib = b"rstcon{"
for offset in range(len(ct) - len(crib) + 1):
    candidate = bytes(a ^ b for a, b in zip(ct[offset : offset + len(crib)], crib))
    if candidate == b"r1nebr1":
        print(f"[+] Crib match at offset {offset}: {candidate.decode()}")

# 2. Decrypt using the 5-byte repeating key 'br1ne'
key = b"br1ne"
pt = bytes(c ^ k for c, k in zip(ct, cycle(key))).decode()
print(f"[+] Key: {key.decode()}")
print(f"[+] Plaintext: {pt}")
```

### Output

```text
[+] Crib match at offset 86: r1nebr1
[+] Key: br1ne
[+] Plaintext: SecurityShrimp field note: rotated the engagement creds tonight. maintenance token is rstcon{cr1b_dragging_the_brackish_key} do not leave it sitting on the wire next time.
```
