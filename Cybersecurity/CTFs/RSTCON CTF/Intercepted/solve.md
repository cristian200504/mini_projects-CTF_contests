# Intercepted — CTF Challenge Writeup

## Challenge Information
- **Name:** Intercepted
- **Points:** 10
- **Author:** f8al
- **Description:** `We grabbed a transmission off the wire. It has been through the encoder a few too many times. Peel it back. Provided: transmission.txt.`
- **Flag:** `rstcon{p33l_the_3ncoding_0ni0n}`

---

## 1. Initial Reconnaissance

We are given `transmission.txt`, which contains a 152-character hexadecimal string:

```text
5054303950543039565642505245315452316843527a6379576a525856564a4e55444e5a4e4664614e45784752444a4a57464253546c5261545546594e56704f55444e5a53566861536b383d
```

The prompt instructs us to "peel it back", indicating multiple nested encoding layers.

---

## 2. Step-by-Step Decoding

### Layer 1: Hexadecimal Decode
Decoding the hex string into ASCII produces a Base64-encoded string ending with `=`:

```text
PT09PT09VVBPRE1TR1hCRzcyWjRXVVJNUDNZNFdaNExGRDJJWFBSTlRaTUFYNVpOUDNZSVhaSk8=
```

### Layer 2: Base64 Decode
Decoding the Base64 string yields:

```text
======UPODMSGXBG72Z4WURMP3Y4WZ4LFD2IXPRNTZMAX5ZNP3YIXZJO
```

### Layer 3: String Reversal
Notice the `======` padding at the beginning of the string and the uppercase alphanumeric character set (`A-Z`, `2-7`), which is a reversed Base32 string. Reversing the string restores valid Base32:

```text
OJZXIY3PNZ5XAMZTNRPXI2DFL4ZW4Y3PMRUW4Z27GBXGSMDOPU======
```

### Layer 4: Base32 Decode
Decoding the Base32 string reveals the flag:

```text
rstcon{p33l_the_3ncoding_0ni0n}
```

---

## 3. Solver Script (`solve.py`)

```python
import base64

with open("transmission.txt", "r") as f:
    data = f.read().strip()

# Layer 1: Hex decode
step1 = bytes.fromhex(data).decode()
print(f"[1] Hex decoded:    {step1}")

# Layer 2: Base64 decode
step2 = base64.b64decode(step1).decode()
print(f"[2] Base64 decoded: {step2}")

# Layer 3: Reverse string
step3 = step2[::-1]
print(f"[3] Reversed:       {step3}")

# Layer 4: Base32 decode
flag = base64.b32decode(step3).decode()
print(f"[4] Flag:           {flag}")
```

### Output

```text
[1] Hex decoded:    PT09PT09VVBPRE1TR1hCRzcyWjRXVVJNUDNZNFdaNExGRDJJWFBSTlRaTUFYNVpOUDNZSVhaSk8=
[2] Base64 decoded: ======UPODMSGXBG72Z4WURMP3Y4WZ4LFD2IXPRNTZMAX5ZNP3YIXZJO
[3] Reversed:       OJZXIY3PNZ5XAMZTNRPXI2DFL4ZW4Y3PMRUW4Z27GBXGSMDOPU======
[4] Flag:           rstcon{p33l_the_3ncoding_0ni0n}
```
