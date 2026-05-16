#!/usr/bin/env python3
from pwn import remote, context
import re
import base64
import binascii
import hashlib
import string

context.log_level = "error"

HOST = "51.210.244.18"
PORT = 8688

# ---------- helpers ----------

def manhattan_snake(prompt: str) -> str:
    # Example: "Nokia Snake (0,0) moves: LEFT 10, RIGHT 8, LEFT 2..."
    moves = re.findall(r'\b(LEFT|RIGHT|UP|DOWN)\s+(\d+)\b', prompt, re.I)
    x = y = 0
    for d, n in moves:
        n = int(n)
        d = d.upper()
        if d == "LEFT":  x -= n
        if d == "RIGHT": x += n
        if d == "UP":    y += n
        if d == "DOWN":  y -= n
    return str(abs(x) + abs(y))

def maze_path(target: int) -> str:
    """
    Prompt: "Maze Target: 238 (A:x*2, B:(x-1)/3). Path?"
    Deterministic reverse walk to 1:
      if even -> reverse A: x/=2
      if odd  -> reverse B: x=3x+1
    Then reverse the operation list to output the forward path (from 1 to target).
    """
    x = target
    ops = []
    # These challenges are designed to finish quickly; cap just in case
    for _ in range(10000):
        if x == 1:
            break
        if x % 2 == 0:
            x //= 2
            ops.append("A")
        else:
            x = 3 * x + 1
            ops.append("B")
    if x != 1:
        # fallback: shouldn't happen in this CTF
        return ""
    return "".join(reversed(ops))

def ring_hops(prompt: str) -> str:
    # Example: "P2P-Ring: E->C->D->B->A->E. Start E, 5 hops?"
    seq = re.search(r'P2P-Ring:\s*([A-Z](?:->\s*[A-Z])+)', prompt)
    if not seq:
        return ""
    nodes = [x.strip() for x in seq.group(1).split("->")]
    # build mapping
    nxt = {}
    for a, b in zip(nodes, nodes[1:]):
        nxt[a] = b
    # if it's shown ending back to start, mapping is complete already
    m = re.search(r'Start\s*([A-Z])\s*,\s*(\d+)\s*hops', prompt, re.I)
    if not m:
        return ""
    cur = m.group(1).upper()
    hops = int(m.group(2))
    for _ in range(hops):
        cur = nxt[cur]
    return cur

def gb_cpu(prompt: str) -> str:
    # Example: "GB-CPU: X=3, Y=2 | ADD X Y, MUL X 2. Result?"
    regs = dict(re.findall(r'\b([A-Z])\s*=\s*(-?\d+)\b', prompt))
    regs = {k: int(v) for k, v in regs.items()}

    # instructions after "|"
    parts = prompt.split("|", 1)
    if len(parts) < 2:
        return ""
    instrs = parts[1]
    ops = re.findall(r'\b(ADD|MUL|SUB)\s+([A-Z])\s+([A-Z]|\-?\d+)\b', instrs, re.I)

    for op, r, arg in ops:
        op = op.upper()
        r = r.upper()
        val = regs[arg.upper()] if arg.upper() in regs else int(arg)
        if op == "ADD":
            regs[r] = regs.get(r, 0) + val
        elif op == "SUB":
            regs[r] = regs.get(r, 0) - val
        elif op == "MUL":
            regs[r] = regs.get(r, 0) * val

    # Usually asks for X
    return str(regs.get("X", 0))

def msn_decode(prompt: str) -> str:
    # Example: "MSN Encoding: Decode 'f0H4ier='"
    m = re.search(r"Decode\s*'([^']+)'", prompt)
    if not m:
        return ""
    b64 = m.group(1)
    raw = base64.b64decode(b64)
    # If printable -> return text; else return hex
    if all((chr(c) in string.printable and chr(c) not in "\r\n\t\x0b\x0c") for c in raw):
        return raw.decode(errors="ignore")
    return raw.hex()

def napster_zip(prompt: str) -> str:
    # Example: "Napster-Zip 'bbacbabbaaaa':"
    m = re.search(r"Napster-Zip\s*'([^']+)'", prompt)
    if not m:
        return ""
    s = m.group(1)

    # Simple RLE: count+char (no separators), e.g. "bbac" -> "2b1a1c"
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)

def winamp_checksum(prompt: str) -> str:
    # Example: "Winamp Playlist [DDCABACE]. Checksum?"
    m = re.search(r"\[([A-Z]+)\]", prompt)
    if not m:
        return ""
    seq = m.group(1)
    # checksum = sum(A=1..Z=26)
    total = sum((ord(ch) - ord("A") + 1) for ch in seq)
    return str(total)

def sha256_hex(prompt: str) -> str:
    # Example: "SHA256 hex of 'p4ss75'"
    m = re.search(r"SHA256 hex of\s*'([^']+)'", prompt, re.I)
    if not m:
        return ""
    data = m.group(1).encode()
    return hashlib.sha256(data).hexdigest()

# ---------- dispatcher ----------

def solve_question(line: str) -> str | None:
    if "Nokia Snake" in line:
        return manhattan_snake(line)

    if "Maze Target" in line:
        mt = re.search(r"Target:\s*(\d+)", line)
        if mt:
            return maze_path(int(mt.group(1)))

    if "P2P-Ring" in line:
        return ring_hops(line)

    if "GB-CPU" in line:
        return gb_cpu(line)

    if "MSN Encoding" in line:
        return msn_decode(line)

    if "Napster-Zip" in line:
        return napster_zip(line)

    if "Winamp Playlist" in line:
        return winamp_checksum(line)

    if "SHA256" in line:
        return sha256_hex(line)

    return None

def main():
    io = remote(HOST, PORT)

    # Print banner + keep reading lines.
    while True:
        line = io.recvline(timeout=10)
        if not line:
            break
        text = line.decode(errors="ignore")
        print(text, end="")

        # Questions come on a single line like: [Q1/10] ...
        if text.strip().startswith("[Q"):
            ans = solve_question(text)
            if ans is None or ans == "":
                print("\n[!] Could not parse question:\n", text)
                # If you want to take over manually:
                # io.interactive()
                # return
                ans = "0"
            io.sendline(ans.encode())
            # Optional: echo what we sent
            print(f"> {ans}")

if __name__ == "__main__":
    main()

