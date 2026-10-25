# Life Savings — CTF Challenge Writeup

## Challenge Information
- **Name:** Life Savings
- **Points:** 10
- **Author:** Veryyes
- **Description:** `Dude, my casino voucher photo got all corrupted and glitchy after I took it. It won't open on my phone or computer. Can you fix it fr fr??`
- **Flag:** `rstcon{ka$h_m3_outs1de-howbout_that}`

---

## 1. Initial Reconnaissance

We are given `corrupted.png` (`2,182,646` bytes). Inspecting the first 64 bytes of the file in hex reveals the nature of the corruption:

```text
89504e470d0a1a0a  -> Valid PNG 8-byte signature
0000000d 49484452 -> IHDR chunk (length 13)
00000000          -> Width:  0 (Zeroed out!)
00000000          -> Height: 0 (Zeroed out!)
08 06 00 00 00    -> Bit depth = 8, Color type = 6 (RGBA, 4 bytes/pixel), Compression = 0, Filter = 0, Interlace = 0
00000000          -> IHDR CRC32: 0 (Zeroed out!)
```

Scanning all `270` chunks in `corrupted.png` (`IHDR`, `sBIT`, `267` `IDAT` chunks, and `IEND`) reveals two issues preventing image viewers from opening the file:
1. Both **Width** and **Height** in the `IHDR` chunk were zeroed out (`0x00000000`).
2. Every single chunk's **CRC32 checksum** was zeroed out (`0x00000000`).

---

## 2. Recovering Image Dimensions from Decompressed `IDAT` Data

Even without the `IHDR` dimensions or CRCs, we can concatenate all `267` `IDAT` chunk payloads and decompress the raw pixel stream using `zlib`:
- **Decompressed `IDAT` size:** `6,292,992` bytes.
- Because `IHDR` specifies **Bit Depth = 8** and **Color Type = 6 (RGBA)**, each pixel takes $4\text{ bytes}$, and each horizontal scanline of width $W$ is preceded by a 1-byte PNG filter type (`0`–`4`).
- Therefore, for an image of width $W$ and height $H$:

$$\text{Decompressed Size} = H \times (1 + 4W) = 6,292,992$$

Factoring `6,292,992` for valid dimensions $(W, H)$ where every scanline starts with a valid PNG filter byte $\in \{0, 1, 2, 3, 4\}$ yields a **unique** solution:

$$W = 1024, \quad H = 1536 \quad (1536 \times (1 + 4 \times 1024) = 1536 \times 4097 = 6,292,992)$$

---

## 3. Repairing the PNG & Extracting the Flag

We repair `corrupted.png` by:
1. Writing $W = 1024$ (`0x00000400`) and $H = 1536$ (`0x00000600`) into the `IHDR` chunk.
2. Recomputing and writing the valid `zlib.crc32(chunk_type + chunk_data)` checksum for every chunk in the file.

### Solver Script (`solve.py`)

```python
import struct
import zlib

with open("corrupted.png", "rb") as f:
    data = f.read()

# Step 1: Concatenate IDAT chunks and determine (Width, Height)
offset = 8
idat_stream = bytearray()
while offset < len(data):
    length = struct.unpack(">I", data[offset : offset + 4])[0]
    ctype = data[offset + 4 : offset + 8]
    cdata = data[offset + 8 : offset + 8 + length]
    if ctype == b"IDAT":
        idat_stream.extend(cdata)
    offset += 12 + length

raw_scanlines = zlib.decompress(bytes(idat_stream))
width, height = None, None
for w in range(100, 5000):
    stride = 1 + 4 * w
    if len(raw_scanlines) % stride == 0:
        h = len(raw_scanlines) // stride
        if set(raw_scanlines[0::stride]).issubset({0, 1, 2, 3, 4}):
            width, height = w, h
            break

print(f"[+] Recovered dimensions: {width}x{height}")

# Step 2: Patch IHDR dimensions and recalculate CRC32 for all chunks
repaired = bytearray(data[:8])
offset = 8
while offset < len(data):
    length = struct.unpack(">I", data[offset : offset + 4])[0]
    ctype = data[offset + 4 : offset + 8]
    cdata = bytearray(data[offset + 8 : offset + 8 + length])

    if ctype == b"IHDR":
        cdata[0:4] = struct.pack(">I", width)
        cdata[4:8] = struct.pack(">I", height)

    crc = zlib.crc32(ctype + cdata) & 0xFFFFFFFF
    repaired.extend(struct.pack(">I", length))
    repaired.extend(ctype)
    repaired.extend(cdata)
    repaired.extend(struct.pack(">I", crc))
    offset += 12 + length

with open("fixed.png", "wb") as f:
    f.write(repaired)

print("[+] Saved repaired image to fixed.png")
```

Opening the repaired `fixed.png` reveals a photo of a **Grand Sovereign Casino Resort** \$1,000,000.00 cashable receipt, with the flag printed directly under the `VALIDATION` barcode:

```text
rstcon{ka$h_m3_outs1de-howbout_that}
```
