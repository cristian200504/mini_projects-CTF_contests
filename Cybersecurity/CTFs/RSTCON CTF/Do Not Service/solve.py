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
