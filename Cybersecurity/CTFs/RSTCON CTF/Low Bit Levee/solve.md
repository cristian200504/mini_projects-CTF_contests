# Low Bit Levee — CTF Challenge Writeup

## Challenge Information
- **Name:** Low Bit Levee
- **Points:** 10
- **Author:** f8al
- **Description:** `A levee monitoring station was caught exfiltrating data inside its own status imagery. Provided: levee.png.`
- **Flag:** `rstcon{least_significant_secret_bits}`

---

## 1. Initial Reconnaissance

We are given `levee.png` (`2,623` bytes), a $256 \times 192$ 8-bit RGB PNG image showing a smooth blue-to-purple gradient.

The title **Low Bit Levee** directly points to **Least Significant Bit (LSB) steganography**.

---

## 2. LSB Steganography Analysis

Extracting the least significant bit (`c & 1`) from each color channel (`R, G, B`) of each pixel in row-major order and packing every 8 bits (MSB-first) into bytes yields:

- **Bytes `0..1`:** `0x0025` (`37` in big-endian), which encodes the 16-bit payload length (`37` bytes).
- **Bytes `2..38`:** `rstcon{least_significant_secret_bits}`

---

## 3. Solver Script (`solve.py`)

```python
import struct
from PIL import Image

im = Image.open("levee.png")
raw_bytes = im.tobytes()

# Extract the LSB (bit 0) of each R, G, B channel byte and pack into 8-bit bytes
bits = [b & 1 for b in raw_bytes]
extracted = bytes(
    int("".join(map(str, bits[i : i + 8])), 2)
    for i in range(0, 400, 8)
)

# First 2 bytes store the 16-bit big-endian length of the hidden message
msg_len = struct.unpack(">H", extracted[:2])[0]
flag = extracted[2 : 2 + msg_len].decode()

print(f"[+] Payload length: {msg_len} bytes")
print(f"[+] Flag: {flag}")
```

### Output

```text
[+] Payload length: 37 bytes
[+] Flag: rstcon{least_significant_secret_bits}
```
