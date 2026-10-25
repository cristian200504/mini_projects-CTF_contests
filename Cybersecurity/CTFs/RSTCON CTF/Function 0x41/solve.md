# Function 0x41 — Solve Writeup

**Category:** ICS / Industrial Protocol  
**Points:** 10  
**Flag:** `rstcon{user_defined_fc_reversed}`

---

## Challenge Description

> This field device speaks a vendor extension on top of Modbus/TCP, function code 0x41. The integrator who documented it is long gone and the manual went with them.

A live Modbus/TCP server is provided along with its Python source (`server.py`). The server implements the standard FC 0x03 (Read Holding Registers) plus a custom **vendor-extension function code 0x41**.

- Mirror 1: `18.215.143.250:1502`
- Mirror 2: `18.145.136.91:1502`

---

## Analysis

Reading `server.py` reveals everything needed.

### Custom FC 0x41 Handler

```python
CUSTOM_FC = 0x41

def transform(seed: int) -> int:
    return (((seed ^ 0x1F3D) * 0x0101) + 0x2027) & 0xFFFF

def handle_pdu(pdu: bytes) -> bytes:
    ...
    if fc == CUSTOM_FC:
        if len(pdu) < 5:
            return exception(fc, 0x03)
        seed, guess = struct.unpack(">HH", pdu[1:5])
        if guess == transform(seed):
            return struct.pack(">BB", CUSTOM_FC, 0x00) + FLAG
        return struct.pack(">BB", CUSTOM_FC, 0x01)
```

The request PDU for FC 0x41 carries two 16-bit big-endian fields:
- `seed`  — a value we choose freely
- `guess` — must equal `transform(seed)`

The transform is a simple deterministic function:

```
guess = (((seed XOR 0x1F3D) * 0x0101) + 0x2027) & 0xFFFF
```

If the guess is correct, the server responds with FC 0x41, status `0x00`, followed by the raw flag bytes. If wrong, it returns status `0x01`.

### Packet Structure

The server uses standard Modbus/TCP framing (MBAP header + PDU):

```
MBAP Header (7 bytes):
  Transaction ID : 2 bytes
  Protocol ID    : 2 bytes (always 0x0000)
  Length         : 2 bytes  (= remaining bytes including Unit ID)
  Unit ID        : 1 byte   (= 0x01)

PDU (5 bytes for FC 0x41):
  Function Code  : 0x41
  Seed           : 2 bytes big-endian
  Guess          : 2 bytes big-endian
```

---

## Solution

Pick any seed, compute the transform, send the packet.

```python
import socket
import struct

HOST = '18.215.143.250'
PORT = 1502

def transform(seed: int) -> int:
    return (((seed ^ 0x1F3D) * 0x0101) + 0x2027) & 0xFFFF

seed  = 0x1234
guess = transform(seed)          # 0x3630

unit = 0x01
pdu  = struct.pack('>BHH', 0x41, seed, guess)
mbap = struct.pack('>HHH', 1, 0, len(pdu) + 1)
packet = mbap + bytes([unit]) + pdu

s = socket.socket()
s.settimeout(5)
s.connect((HOST, PORT))
s.sendall(packet)
resp = s.recv(1024)
s.close()

# Response: MBAP(6) + unit(1) + fc(1) + status(1) + flag bytes
flag = resp[9:].decode()
print(flag)
```

### Output

```
rstcon{user_defined_fc_reversed}
```

---

## Key Takeaways

1. **Source code was provided** — the server's entire logic was readable. Real-world vendor extensions are usually undocumented, so having the source made this a pure reverse-engineering-from-code exercise.

2. **The transform is invertible** but inversion isn't even necessary — since you control the seed, you just evaluate the forward function and send the result.

3. **FC 0x41 = 65 decimal** — Modbus only standardises FCs 1–43 and 43–44. Anything from 65–72 and 100–110 is in the "user-defined" range, exactly where vendor extensions live. The challenge name literally spells this out.

4. **No authentication, no replay protection** — a single crafted packet is enough to dump the flag. Classic ICS security antipattern.
