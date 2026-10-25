# Setpoint — CTF Challenge Writeup

## Challenge Information
- **Name:** Setpoint
- **Points:** 10
- **Author:** f8al
- **Description:** `After a maintenance window, a tank controller's alarm config block was rewritten in a single burst. Recover what was pushed into the config registers from the capture. Files: setpoint.pcap`
- **Flag:** `rstcon{high_alarm_disabled_silently}` (Raw payload: `high_alarm_disabled_silently`)

---

## 1. Initial Reconnaissance

We are provided `setpoint.pcap` (`350` packets), which captures **Modbus/TCP** traffic (`TCP/502`) between an HMI/engineering workstation (`192.168.95.40`) and a tank controller PLC (`192.168.95.10`).

The challenge prompt states that the controller's alarm configuration block was *"rewritten in a single burst"*, pointing to a **Modbus Function Code `16` (`0x10` — Write Multiple Holding Registers)** command.

---

## 2. Protocol & Traffic Analysis (Modbus/TCP)

Scanning all Modbus/TCP requests sent to `192.168.95.10:502` shows three function codes:
- **FC `0x04` (Read Input Registers):** `80` requests — periodic polling of sensor input registers.
- **FC `0x03` (Read Holding Registers):** `5` requests — reading `2` holding registers starting at address `0x0190` (`400`), the alarm configuration block.
- **FC `0x10` / `16` (Write Multiple Holding Registers):** `1` request (Transaction ID `46`).

Inspecting the single **FC `0x10` (Write Multiple Holding Registers)** request in Transaction ID `46`:

```text
MBAP Header: 002e 0000 0023 01
  - Transaction ID: 0x002e (46)
  - Protocol ID:    0x0000 (Modbus)
  - Length:         0x0023 (35 bytes)
  - Unit ID:        0x01   (1)

PDU (Function Code 0x10):
  - Function Code:    0x10   (16 - Write Multiple Holding Registers)
  - Starting Address: 0x0190 (Register 400)
  - Register Count:   0x000e (14 registers)
  - Byte Count:       0x1c   (28 bytes)
  - Register Payload: 686967685f616c61726d5f64697361626c65645f73696c656e746c79
```

Decoding the 28-byte register payload as ASCII characters yields:

```text
high_alarm_disabled_silently
```

---

## 3. Solver Script (`solve.py`)

```python
import struct

with open("setpoint.pcap", "rb") as f:
    data = f.read()

offset = 24  # Skip 24-byte global PCAP header

while offset < len(data):
    ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", data[offset : offset + 16])
    offset += 16
    pkt = data[offset : offset + incl_len]
    offset += incl_len

    if len(pkt) > 54:
        dst_port = struct.unpack(">H", pkt[36:38])[0]
        payload = pkt[54:]
        if dst_port == 502 and len(payload) >= 13:
            tid, pid, length, uid, fc = struct.unpack(">HHHBB", payload[:8])
            # Function Code 16 (0x10) = Write Multiple Holding Registers
            if fc == 16:
                start_addr, reg_count, byte_count = struct.unpack(">HHB", payload[8:13])
                reg_bytes = payload[13 : 13 + byte_count]
                secret = reg_bytes.decode()
                print(f"[+] Transaction ID: {tid}")
                print(f"[+] Target Register Block: {start_addr} ({reg_count} registers, {byte_count} bytes)")
                print(f"[+] Extracted Payload: {secret}")
                print(f"[+] Flag: rstcon{{{secret}}}")
```

### Output

```text
[+] Transaction ID: 46
[+] Target Register Block: 400 (14 registers, 28 bytes)
[+] Extracted Payload: high_alarm_disabled_silently
[+] Flag: rstcon{high_alarm_disabled_silently}
```
