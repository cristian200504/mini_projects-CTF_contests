# Coil Toss — CTF Challenge Writeup

## Challenge Information
- **Name:** Coil Toss
- **Points:** 10
- **Author:** f8al
- **Description:** `We mirrored the link between an HMI and a PLC on a water plant skid for a few minutes. The operator swears they only "read some gauges," but a register on the PLC kept getting poked. Figure out what the workstation actually wrote. Files: coil-toss.pcap`
- **Flag:** `rstcon{fc06_writes_dont_lie}` (Raw payload: `fc06_writes_dont_lie`)

---

## 1. Initial Reconnaissance

We are provided `coil-toss.pcap` (`398` packets), which captures TCP traffic between an HMI workstation (`192.168.95.40`) and a PLC (`192.168.95.10`) over TCP port `502` (**Modbus/TCP**).

The challenge description notes:
> *"The operator swears they only 'read some gauges,' but a register on the PLC kept getting poked. Figure out what the workstation actually wrote."*

---

## 2. Protocol & Traffic Analysis (Modbus/TCP)

In Modbus/TCP, each payload begins with a 7-byte MBAP (Modbus Application Protocol) header followed by a 1-byte **Function Code (FC)** and data:
- **FC `0x03` (Read Holding Registers):** `72` requests — background polling of registers `1`–`4` ("reading gauges").
- **FC `0x05` (Write Single Coil):** `6` requests — toggling coils `5` and `6` (a decoy referenced by the challenge title *Coil Toss*).
- **FC `0x06` (Write Single Holding Register):** `20` requests — writing 16-bit values to holding register `100` (`0x0064`).

Inspecting the 20 **Function Code `0x06` (Write Single Register)** requests sent from `192.168.95.40` to `192.168.95.10:502`:

| Transaction ID | Register | Hex Value | ASCII Character |
| :---: | :---: | :---: | :---: |
| `5` | `0x0064` (100) | `0x0066` | `f` |
| `8` | `0x0064` (100) | `0x0063` | `c` |
| `11` | `0x0064` (100) | `0x0030` | `0` |
| `15` | `0x0064` (100) | `0x0036` | `6` |
| `20` | `0x0064` (100) | `0x005f` | `_` |
| `26` | `0x0064` (100) | `0x0077` | `w` |
| `32` | `0x0064` (100) | `0x0072` | `r` |
| `37` | `0x0064` (100) | `0x0069` | `i` |
| `41` | `0x0064` (100) | `0x0074` | `t` |
| `46` | `0x0064` (100) | `0x0065` | `e` |
| `52` | `0x0064` (100) | `0x0073` | `s` |
| `55` | `0x0064` (100) | `0x005f` | `_` |
| `59` | `0x0064` (100) | `0x0064` | `d` |
| `65` | `0x0064` (100) | `0x006f` | `o` |
| `70` | `0x0064` (100) | `0x006e` | `n` |
| `75` | `0x0064` (100) | `0x0074` | `t` |
| `79` | `0x0064` (100) | `0x005f` | `_` |
| `83` | `0x0064` (100) | `0x006c` | `l` |
| `87` | `0x0064` (100) | `0x0069` | `i` |
| `90` | `0x0064` (100) | `0x0065` | `e` |

Concatenating the written values in transaction order yields:
```text
fc06_writes_dont_lie
```

---

## 3. Solver Script (`solve.py`)

```python
import struct

with open("coil-toss.pcap", "rb") as f:
    data = f.read()

offset = 24  # Skip 24-byte global PCAP header
written_chars = []

while offset < len(data):
    ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", data[offset : offset + 16])
    offset += 16
    pkt = data[offset : offset + incl_len]
    offset += incl_len

    # Check TCP packets with a Modbus/TCP payload destined for port 502
    if len(pkt) > 54:
        dst_port = struct.unpack(">H", pkt[36:38])[0]
        payload = pkt[54:]
        if dst_port == 502 and len(payload) >= 12:
            tid, pid, length, uid, fc = struct.unpack(">HHHBB", payload[:8])
            # Function Code 6 = Write Single Holding Register
            if fc == 6:
                reg, val = struct.unpack(">HH", payload[8:12])
                written_chars.append(chr(val))

secret = "".join(written_chars)
print(f"[+] Extracted FC06 register writes: {secret}")
print(f"[+] Flag: rstcon{{{secret}}}")
```

### Output

```text
[+] Extracted FC06 register writes: fc06_writes_dont_lie
[+] Flag: rstcon{fc06_writes_dont_lie}
```
