# ARC4 Reactor — CTF Challenge Writeup

## Challenge Information
- **Name:** ARC4 Reactor
- **Points:** 481
- **Author:** Veryyes
- **Description:** `I AM IRONMAN AND ALL HIS SECRETS`
- **Flag:** `rstcon{n3utronz_Go_BRRRR}`

---

## 1. Initial Reconnaissance

Inspecting the challenge directory (`ARC4 Reactor`), we find two files:
- `description.txt`: Contains the challenge metadata and description (`I AM IRONMAN AND ALL HIS SECRETS`).
- `reactor.zip`: A 5.96 MB ZIP archive.

Extracting `reactor.zip` reveals three files:
| File Name | Size (Bytes) | Description |
| :--- | :--- | :--- |
| `arc_reactor.png` | `2,313,994` | Original plaintext PNG image |
| `arc_reactor.png.enc` | `2,313,994` | Encrypted version of `arc_reactor.png` |
| `documents.zip.enc` | `1,343,907` | Encrypted ZIP archive containing the target secrets |

---

## 2. Vulnerability Analysis (RC4 Keystream Reuse / Two-Time Pad)

The challenge title **ARC4 Reactor** references the **ARC4 (Alleged RC4)** stream cipher. 

RC4 is a stream cipher that generates a pseudorandom keystream $K$ from a secret key and encrypts plaintext $P$ by XORing it byte-by-byte with $K$:

$$C = P \oplus K$$

Notice that:
1. Both `arc_reactor.png` ($P_1$) and its encrypted counterpart `arc_reactor.png.enc` ($C_1$) are provided and have the exact same size (`2,313,994` bytes).
2. `documents.zip.enc` ($C_2$) is `1,343,907` bytes, which is smaller than `arc_reactor.png`.

Because the same key (and therefore the exact same RC4 keystream $K$) was reused to encrypt both files without a unique nonce/IV, this results in a classic **Two-Time Pad (Keystream Reuse)** vulnerability:

$$K = P_1 \oplus C_1$$

$$P_2 = C_2 \oplus K = C_2 \oplus P_1 \oplus C_1$$

---

## 3. Exploitation & Solution

We can recover the plaintext `documents.zip` ($P_2$) by XORing `arc_reactor.png`, `arc_reactor.png.enc`, and `documents.zip.enc` over the length of `documents.zip.enc`.

### Solver Script (`solve.py`)

```python
import zipfile

with (
    open("arc_reactor.png", "rb") as f_p1,
    open("arc_reactor.png.enc", "rb") as f_c1,
    open("documents.zip.enc", "rb") as f_c2,
):
    p1 = f_p1.read()
    c1 = f_c1.read()
    c2 = f_c2.read()

# Recover documents.zip via XOR (P2 = P1 ^ C1 ^ C2)
p2 = bytes(a ^ b ^ c for a, b, c in zip(p1, c1, c2))

with open("documents.zip", "wb") as out:
    out.write(p2)

print(f"[+] Recovered documents.zip (Header: {p2[:4]})")

# Extract the recovered ZIP archive
with zipfile.ZipFile("documents.zip", "r") as z:
    print("[+] Contents of documents.zip:", z.namelist())
    z.extractall("extracted_docs")
```

### Verification & Flag Extraction

1. Running the XOR recovery yields a file starting with `PK\x03\x04` (`50 4B 03 04`), confirming a valid ZIP archive (`documents.zip`).
2. Extracting `documents.zip` produces a 7-page PDF presentation titled **`split funny atoms haha.pdf`** (*"Nuclear Power and the Energy Grid"*).
3. Inspecting **Page 7** of `split funny atoms haha.pdf` reveals the flag directly on the slide:

```text
rstcon{n3utronz_Go_BRRRR}
```
