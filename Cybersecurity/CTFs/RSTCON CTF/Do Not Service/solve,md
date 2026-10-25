# Do Not Service - Solve & Writeup

## Challenge Information
- **Category:** Network Forensics / Packet Analysis
- **Points:** 70
- **Author:** Veryyes
- **Files Provided:** `odd_transmission.pcapng.gz`
- **Description:** 
  > The new IT guy said not to use this computer, I used it anyways.

---

## 1. Challenge Overview & Clue Analysis

- **Challenge Title:** `Do Not Service`
  - Play on acronym **DNS** (**D**o **N**ot **S**ervice / Domain Name Service).
- **Description:** *"The new IT guy said not to use this computer, I used it anyways."*
  - Suggests the computer was contaminated or running malicious / covert software in the background.
- **Capture File:** `odd_transmission.pcapng.gz` (~46.7 MB compressed, ~51.2 MB uncompressed).
  - Most of the capture consists of regular browser activity (Firefox on Pop!_OS visiting StackOverflow, Amazon, YouTube, LinkedIn, X, etc.) serving as background noise.

---

## 2. Forensic Investigation & Anomaly Discovery

Inspecting all protocols and flows in the capture:
- Almost all traffic is typical HTTP/HTTPS web traffic (`10.200.11.146` to external CDNs and web servers).
- Standard DNS resolution is directed to the local resolver `10.200.0.1:53`.

However, examining non-standard and broadcast/multicast traffic reveals an anomaly:
- Port **5353** is normally reserved for Multicast DNS (**mDNS** / `224.0.0.251` or `ff02::fb`).
- In this capture, `10.200.11.146` sends **unicast** UDP packets to an external public IP on AWS:
  $$\text{10.200.11.146:49058} \longrightarrow \text{3.143.112.103:5353}$$
- There are exactly **30 queries** and **30 responses** sent to this external address.

Inspecting the payloads of these unicast UDP 5353 packets shows they are DNS query packets with domain names formatted as:
```text
www.<base64-string>.<tld>
```

Decoding these base64 labels reveals a sequence of exfiltrated records:
```text
Item  0: AA1NYXR0aGV3IFlvdW5n                     -> \x00\rMatthew Young
Item  1: ABNDaHJpc3RvcGhlciBNaXJhbmRh             -> \x00\x13Christopher Miranda
Item  2: ABBTdGVwaGFuaWUgT2JyaWVu                 -> \x00\x10Stephanie Obrien
...
Item 22: AAlKYW1lcyBMZWU=                         -> \x00\tJames Lee
Item 23: AB1yc3Rjb257ZDBtYWluX25AbTNfRVhQYW5zaTBufQ== -> \x00\x1drstcon{d0main_n@m3_EXPansi0n}
Item 24: AAxUaW5hIEJvbmlsbGE=                     -> \x00\x0cTina Bonilla
...
```

Packet #31,567 at offset `23130036` contains the flag in record #23:
- Base64 string: `AB1yc3Rjb257ZDBtYWluX25AbTNfRVhQYW5zaTBufQ==`
- Base64 decoded: `\x00\x1drstcon{d0main_n@m3_EXPansi0n}`
  (where `\x1d` is 29, the length of the flag string).

---

## 3. Solution Script (`solve.py`)

```python
#!/usr/bin/env python3
"""
Do Not Service - RSTCON CTF
Solver script that extracts DNS exfiltration queries on port 5353.
"""

import os
import gzip
import struct
import base64

def find_flag():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pcapng_path = os.path.join(script_dir, "odd_transmission.pcapng")
    gz_path = os.path.join(script_dir, "odd_transmission.pcapng.gz")

    if os.path.exists(pcapng_path):
        print(f"[*] Reading {pcapng_path}...")
        with open(pcapng_path, "rb") as f:
            data = f.read()
    elif os.path.exists(gz_path):
        print(f"[*] Decompressing {gz_path} in memory...")
        with gzip.open(gz_path, "rb") as f:
            data = f.read()
    else:
        raise FileNotFoundError("Could not find odd_transmission.pcapng or odd_transmission.pcapng.gz")

    pos = 0
    total_len = len(data)
    exfil_data = []

    while pos < total_len:
        block_type, block_len = struct.unpack_from("<II", data, pos)
        if block_len == 0:
            break
        if block_type == 6:  # Enhanced Packet Block
            cap_len = struct.unpack_from("<I", data, pos + 20)[0]
            pkt = data[pos + 28 : pos + 28 + cap_len]
            # Ethernet (14 bytes) -> IPv4 (0x0800)
            if len(pkt) > 34 and pkt[12:14] == b"\x08\x00":
                ip_hdr = pkt[14:]
                proto = ip_hdr[9]
                ihl = (ip_hdr[0] & 0x0F) * 4
                if proto == 17:  # UDP
                    sp, dp = struct.unpack(">HH", ip_hdr[ihl : ihl + 4])
                    # Anomaly: Unicast DNS query on mDNS port (5353) to external IP
                    if dp == 5353:
                        dst_ip = ".".join(map(str, ip_hdr[16:20]))
                        if not dst_ip.startswith("224."):
                            payload = ip_hdr[ihl + 8 :]
                            # Search for base64 encoded label www.<base64>.<tld>
                            www_idx = payload.find(b"www")
                            if www_idx != -1 and www_idx + 3 < len(payload):
                                label_len = payload[www_idx + 3]
                                b64_bytes = payload[www_idx + 4 : www_idx + 4 + label_len]
                                try:
                                    decoded = base64.b64decode(b64_bytes)
                                    exfil_data.append(decoded)
                                except Exception:
                                    pass
        pos += block_len

    print(f"[*] Extracted {len(exfil_data)} exfiltration records from unicast port 5353 traffic.")
    for item in exfil_data:
        if b"rstcon{" in item:
            start = item.find(b"rstcon{")
            end = item.find(b"}", start) + 1
            flag = item[start:end].decode("utf-8")
            print(f"[+] Flag found: {flag}")
            return flag

if __name__ == "__main__":
    find_flag()
```

---

## 4. Flag

```text
rstcon{d0main_n@m3_EXPansi0n}
```
