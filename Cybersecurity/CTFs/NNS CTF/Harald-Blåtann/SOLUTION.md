# Harald-Blåtann - In-Depth Reverse Engineering Solution

## 1. Challenge Summary
- **Category:** Reverse Engineering / Embedded Firmware / Bluetooth Low Energy (BLE)
- **Target File:** `harald-blatann.hex` (Intel HEX format)
- **Architecture:** ARM Cortex-M33 (ARMv8-M Thumb2)
- **Platform:** Zephyr RTOS v4.4.0 with BLE Host & Controller stack and PSA Crypto (`mbedtls`).
- **Decoy Flag in Firmware:** `NNS{th15_is_n0t_th3_fl4g}`
- **Actual Flag:** `NNS{w1r3lessly_s3nt_4nd_ch3ck3d_by_th3_p0w3r_0f_k1ng_bl4t4nn}`

---

## 2. Firmware Architecture & Memory Mapping

Parsing the Intel HEX file revealed the code and read-only data layout:
- **Base Address:** `0x1000000` (Flash space for Nordic nRF5340 / nRF52 family series).
- **Firmware Size:** `0x28B6B` bytes (range `0x1000000` - `0x1028B6B`).
- **RAM Base:** `0x21000000`.

A preliminary scan revealed standard Bluetooth SIG profiles (GAP `0x1800`, GATT `0x1801`, Device Information `0x180A`, Battery `0x180F`, Current Time `0x1805`, Heart Rate `0x180D`, Immediate Alert `0x1802`).

In addition to standard profiles, a custom vendor GATT service was registered at `0x1026DCC` with 128-bit UUIDs based on prefix `debc...345678`:
- `0x1026DF4`: Read/Write characteristic mapped to buffer `0x21000689`.
- `0x1026E30`: Read/Write characteristic mapped to buffer `0x21000674`.
- `0x1026E58`: Read/Write characteristic mapped to buffer `0x21000614` — which statically contains the decoy string `NNS{th15_is_n0t_th3_fl4g}`.
- `0x1026E94`: Write characteristic mapped to buffer `0x2100065F`.
- `0x1026ED0`: Notification characteristic for flag validation outcome.
- `0x1026F0C`: Notification characteristic for cryptographic status.

---

## 3. Cryptographic Verification Analysis (`0x1011B14`)

Tracing calls to the notification triggers led directly to the central flag validation handler at `0x1011B14`:

```armasm
0x1011b14: push    {r4, r5, r6, lr}
0x1011b16: sub     sp, #0x80
0x1011b18: mov     r4, r3                  ; input length
0x1011b1a: add     r3, sp, #0x14
0x1011b1c: str     r3, [sp, #8]
0x1011b1e: movs    r3, #0x60               ; ciphertext length (96 bytes)
0x1011b20: ldr     r0, =0x210029f8         ; pointer to key handle
0x1011b22: add     r6, sp, #0x20           ; destination plaintext buffer
0x1011b24: str     r3, [sp, #4]
0x1011b26: str     r6, [sp]
0x1011b28: ldr     r1, =0x04404000         ; PSA algorithm identifier (AES-CBC)
0x1011b2a: mov     r5, r2                  ; input buffer pointer
0x1011b2c: ldr     r0, [r0]                ; key handle
0x1011b2e: ldr     r2, =0x1028103          ; ciphertext address in flash
0x1011b30: bl      psa_cipher_decrypt      ; (0x101e188)
0x1011b3e: cmp     r4, #0x3c               ; checks that input length > 60 bytes
0x1011b40: bhi     0x1011b54
...
0x1011b64: bl      memcmp                  ; compares input buffer against decrypted plaintext
0x1011b68: clz     r0, r0
0x1011b6c: lsrs    r0, r0, #5
0x1011b6e: str     r0, [sp, #0x1c]
0x1011b70: b       0x1011b46               ; notifies characteristic 0x1026ED0 with result
```

### Key Import & Configuration (`0x1011B80`)
Inspecting how the key handle at `0x210029F8` was initialized:
- **Key Type:** `0x00002400` (AES)
- **Key Size:** 256 bits (32 bytes)
- **Algorithm:** `0x04404000` (AES-CBC)
- **Key Material Flash Location:** `0x1028163` (32 bytes)

---

## 4. Flash Payload Extraction & Decryption

The firmware contains the encrypted flag and key hardcoded in flash:
1. **AES-256 Key (32 bytes at `0x1028163`):**
   `2fe96d47402f3ea712adb224b1be475185e524848646c58897be4893f67abf76`
2. **Ciphertext Blob (96 bytes at `0x1028103`):**
   `43a70bc8e54e61cfff8d0a6d7d09fe20dde4bdfff3b45d91a80b420fdca73a90af6d2d7655f11d6646b85959d4caa9bc395864fbbc039cd14f1eb6fab295bd2dc267e789262d9b333cc23aef59583b31e2d1016f63c132366525561708f76f0f`

Under the PSA Crypto / Zephyr cipher storage representation:
- **IV (first 16 bytes):** `43a70bc8e54e61cfff8d0a6d7d09fe20`
- **Ciphertext (remaining 80 bytes):** `dde4bdfff3b45d91a80b420fdca73a90af6d2d7655f11d6646b85959d4caa9bc395864fbbc039cd14f1eb6fab295bd2dc267e789262d9b333cc23aef59583b31e2d1016f63c132366525561708f76f0f`

Decrypting this block using AES-256 in CBC mode yields:
```
NNS{w1r3lessly_s3nt_4nd_ch3ck3d_by_th3_p0w3r_0f_k1ng_bl4t4nn}\x00\x00\x00\x10\x10\x10...
```

---

## 5. Automated Solve Script

The included script [`solve.py`](solve.py) parses `rev_harald/harald-blatann.hex`, extracts the key and ciphertext directly from flash offsets, and prints the recovered flag:

```bash
python solve.py
```

Output:
```
[+] Flag recovered: NNS{w1r3lessly_s3nt_4nd_ch3ck3d_by_th3_p0w3r_0f_k1ng_bl4t4nn}
```

