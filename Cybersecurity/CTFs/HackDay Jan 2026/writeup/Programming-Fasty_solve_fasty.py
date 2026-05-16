#!/usr/bin/env python3
import re
import hashlib
import socket

HOST = "51.210.244.18"
PORT = 8677

# ---------- helpers ----------
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
    # Python 3.8+: int.bit_count() exists on 3.8? Actually 3.8 lacks bit_count; 3.10+ has it.
    # We'll keep a compatible fallback.
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

# ---------- parsing / solving ----------
def solve_question(line: str) -> str | None:
    line = line.strip()

    # Q1: 947 - 460 ?
    m = re.search(r"Q\d+:\s*(-?\d+)\s*([\+\-\*/])\s*(-?\d+)\s*\?", line)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        if op == "+": return str(a + b)
        if op == "-": return str(a - b)
        if op == "*": return str(a * b)
        if op == "/": return str(a // b)  # in case they use integer division
        return None

    # Reverse this string: 'network141'
    m = re.search(r"Reverse this string:\s*'([^']*)'", line)
    if m:
        s = m.group(1)
        return s[::-1]

    # Give the SHA256 hash (hex) of 'password44'
    m = re.search(r"SHA256 hash \(hex\) of\s*'([^']*)'", line)
    if m:
        return sha256_hex(m.group(1))

    # Find the smallest number in [19, 61, 19, 33, 40]
    m = re.search(r"smallest number in\s*\[([0-9,\s-]+)\]", line)
    if m:
        nums = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
        return str(min(nums))

    # From ['red', ...], keep only words > 5 chars (comma-separated)
    m = re.search(r"From\s*\[(.*)\],\s*keep only words\s*>\s*5 chars", line)
    if m:
        inside = m.group(1)
        # extract quoted strings inside [...]
        words = re.findall(r"'([^']*)'", inside)
        kept = [w for w in words if len(w) > 5]
        return ",".join(kept)

    # What is 4167 XOR 5306 (decimal)?
    m = re.search(r"What is\s*(\d+)\s*XOR\s*(\d+)\s*\(decimal\)\?", line, re.IGNORECASE)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return str(a ^ b)

    # Apply Caesar cipher (+3) to 'hack'
    m = re.search(r"Apply Caesar cipher\s*\(\+3\)\s*to\s*'([^']*)'", line)
    if m:
        return caesar_plus3(m.group(1))

    # Hamming weight of 761659?
    m = re.search(r"Hamming weight of\s*(\d+)\?", line, re.IGNORECASE)
    if m:
        return str(hamming_weight(int(m.group(1))))

    # Convert 53 to binary (bits only)
    m = re.search(r"Convert\s*(\d+)\s*to binary\s*\(bits only\)", line, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return bin(n)[2:]

    # Format '315823c47561' as a MAC address
    m = re.search(r"Format\s*'([0-9a-fA-F]+)'\s*as a MAC address", line, re.IGNORECASE)
    if m:
        return to_mac(m.group(1))

    return None

# ---------- networking ----------
def recv_until(sock: socket.socket, marker: bytes = b"> ") -> bytes:
    data = b""
    sock.settimeout(3.0)
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data

def main():
    with socket.create_connection((HOST, PORT), timeout=5.0) as sock:
        # Read the intro until first prompt ("> ")
        buf = recv_until(sock, b"> ")
        text = buf.decode(errors="ignore")
        print(text, end="")

        while True:
            # Find the last line with a question (usually starts with Qn:)
            lines = text.splitlines()
            qline = None
            for ln in reversed(lines):
                if re.match(r"^\s*Q\d+:", ln):
                    qline = ln.strip()
                    break

            if qline:
                ans = solve_question(qline)
                if ans is None:
                    # If parsing failed, don't hang—send blank quickly.
                    ans = ""
                sock.sendall((ans + "\n").encode())
                # Receive until next prompt or until connection closes
                buf = recv_until(sock, b"> ")
                if not buf:
                    break
                text = buf.decode(errors="ignore")
                print(text, end="")

                # Stop if final score / flag / access result appears
                if "Final score" in text or "flag" in text.lower() or "Access denied" in text:
                    # There may still be more output; try a final read
                    try:
                        sock.settimeout(0.5)
                        rest = sock.recv(4096)
                        if rest:
                            print(rest.decode(errors="ignore"), end="")
                    except Exception:
                        pass
                    break
            else:
                # If we didn't see Qn: in what we read, just pull more
                try:
                    sock.settimeout(1.0)
                    more = sock.recv(4096)
                    if not more:
                        break
                    text = more.decode(errors="ignore")
                    print(text, end="")
                except Exception:
                    break

if __name__ == "__main__":
    main()

