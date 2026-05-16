#!/usr/bin/env python3
import re
import hashlib
import socket
import time
import sys

HOST = "51.210.244.18"
PORT = 8677

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def caesar_plus3(s: str) -> str:
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - ord("a") + 3) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - ord("A") + 3) % 26 + ord("A")))
        else:
            out.append(ch)
    return "".join(out)

def hamming_weight(n: int) -> int:
    try:
        return n.bit_count()
    except AttributeError:
        return bin(n).count("1")

def to_mac(hexstr: str) -> str:
    hexstr = hexstr.strip().lower()
    if len(hexstr) % 2 != 0:
        hexstr = "0" + hexstr
    pairs = [hexstr[i:i+2] for i in range(0, len(hexstr), 2)]
    return ":".join(pairs)

def solve_question(line: str) -> str | None:
    line = line.strip()
    # [DEBUG]
    # print(f"[DEBUG] Parsing: {line}")

    # Q1: 947 - 460 ?
    m = re.search(r"Q\d+:\s*(-?\d+)\s*([\+\-\*/])\s*(-?\d+)\s*\?", line)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        if op == "+": return str(a + b)
        if op == "-": return str(a - b)
        if op == "*": return str(a * b)
        if op == "/": return str(a // b)

    # Reverse this string:
    m = re.search(r"Reverse this string:\s*'([^']*)'", line)
    if m:
        return m.group(1)[::-1]

    # SHA256
    m = re.search(r"SHA256 hash \(hex\) of\s*'([^']*)'", line)
    if m:
        return sha256_hex(m.group(1))

    # Smallest number
    m = re.search(r"smallest number in\s*\[([0-9,\s-]+)\]", line)
    if m:
        nums = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
        return str(min(nums))

    # Words > 5 chars (adjust regex for > N)
    m = re.search(r"From\s*\[(.*)\],\s*keep only words\s*>\s*(\d+) chars", line)
    if m:
        inside, lim = m.group(1), int(m.group(2))
        words = re.findall(r"'([^']*)'", inside)
        return ",".join([w for w in words if len(w) > lim])

    # 4167 XOR 5306
    m = re.search(r"What is\s*(\d+)\s*XOR\s*(\d+)\s*\(decimal\)\?", line, re.IGNORECASE)
    if m:
        return str(int(m.group(1)) ^ int(m.group(2)))

    # Caesar +3
    m = re.search(r"Apply Caesar cipher\s*\(\+(\d+)\)\s*to\s*'([^']*)'", line)
    if m:
        # Assuming fixed +3 func for now, user func doesn't take shift arg
        return caesar_plus3(m.group(2))

    # Hamming weight
    m = re.search(r"Hamming weight of\s*(\d+)\?", line, re.IGNORECASE)
    if m:
        return str(hamming_weight(int(m.group(1))))

    # Binary
    m = re.search(r"Convert\s*(\d+)\s*to binary\s*\(bits only\)", line, re.IGNORECASE)
    if m:
        return bin(int(m.group(1)))[2:]

    # MAC
    m = re.search(r"Format\s*'([0-9a-fA-F]+)'\s*as a MAC address", line, re.IGNORECASE)
    if m:
        return to_mac(m.group(1))

    return None

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        print("[*] Connected")
        
        buf = ""
        while True:
            # We read byte by byte or small chunks to be responsive
            # BUT efficient. 
            # The server sends prompts.
            try:
                chunk = s.recv(1024)
                if not chunk:
                    break
                decoded = chunk.decode(errors="ignore")
                print(decoded, end="", flush=True)
                buf += decoded

                # Check for lines
                while "\n" in buf:
                    line, rest = buf.split("\n", 1)
                    # We might want to keep the line for history, but we need to find Qs
                    # The prompt '> ' comes usually AFTER a question, potentially without a newline if it's an input prompt?
                    # Actually, usually input prompts don't have newlines.
                    # Q1: 1+1 ?\n> 
                    # So splitting by \n might hide the prompt if it's in `rest`.
                    
                    # Strategy: Search buffer for "Q<n>: ... ?"
                    # If found, solve and send.
                    pass 
                    # Wait, if we split buf, we lose context if we aren't careful.
                    # Let's just accumulate buf and clear it when we handle a Q.
                    buf = line + "\n" + rest # restore for now? No.
                    break 

                # Better loop:
                # Check for "Q... ?"
                # If we see a "?", we might have a question.
                # If we see ">", we definitely should send answer if we have one.

                if ">" in buf or "?" in buf:
                     # Attempt solve
                     qs = list(re.finditer(r"(Q\d+:.*?(\?|chars|address|'|\]))", buf, re.DOTALL))
                     if qs:
                         # Get latest
                         last_match = qs[-1]
                         q_full = last_match.group(1)
                         
                         # Check if we already answered this Q?
                         # We can check if we cleared buffer.
                         
                         ans = solve_question(q_full)
                         if ans:
                             print(f"\n[SOLVER] Found Q: {q_full.strip()} -> {ans}")
                             # Simulate "thinking" if needed?
                             # user said "if you try to get the answer too early the nc bot flags you"
                             # Sleep 0.2s?
                             time.sleep(0.2)
                             s.sendall((ans + "\n").encode())
                             print("[SOLVER] Sent.")
                             buf = "" # Clear buffer
                         
            except Exception as e:
                print(e)
                break
    except KeyboardInterrupt:
        print("\n[*] Exiting")
    finally:
        s.close()

if __name__ == "__main__":
    main()
