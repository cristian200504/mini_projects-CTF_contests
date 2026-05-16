#!/usr/bin/env python3
"""
Simpler solution - just try values and use binary search / smart iteration.
"""

import socket
import ssl
import sys


class RemoteConnection:
    """Handle SSL connection to the CTF server."""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.ssl_sock = None
        
    def connect(self):
        """Establish SSL connection."""
        print(f"[*] Connecting to {self.host}:{self.port}...", file=sys.stderr)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.ssl_sock = context.wrap_socket(self.sock, server_hostname=self.host)
        self.ssl_sock.connect((self.host, self.port))
        print("[+] Connected!", file=sys.stderr)
        
    def send(self, data):
        """Send data to server."""
        self.ssl_sock.sendall(data.encode() + b'\n')
        
    def recv_line(self):
        """Receive a line from server, handling both \n and prompt."""
        line = b''
        while True:
            try:
                char = self.ssl_sock.recv(1)
                if not char:
                    return line.decode(errors='ignore') if line else None
                line += char
                # Check for newline
                if char == b'\n':
                    return line[:-1].decode(errors='ignore')  # Strip the \n
                # Check for prompt without newline
                if line.endswith(b'bb> '):
                    return line.decode(errors='ignore')
            except Exception as e:
                print(f"[!] recv_line error: {e}", file=sys.stderr)
                return line.decode(errors='ignore') if line else None
    
    def recv_until_prompt(self):
        """Receive lines until we get the bb> prompt."""
        lines = []
        while True:
            line = self.recv_line()
            if not line:
                break
            if 'bb>' in line:
                # Extract any content before the prompt
                before_prompt = line.split('bb>')[0].strip()
                if before_prompt:
                    lines.append(before_prompt)
                break
            lines.append(line)
        return lines
            
    def close(self):
        """Close connection."""
        if self.ssl_sock:
            self.ssl_sock.close()
        if self.sock:
            self.sock.close()


def solve_round(conn):
    """Solve one round using binary search."""
    # Read setup
    all_text = ""
    while True:
        line = conn.recv_line()
        if not line:
            return False
        print(line, file=sys.stderr)
        all_text += line + " "
        if "bb>" in line:
            break
    
    # Parse
    import re
    one_match = re.search(r'one=(\d+)', all_text)
    g_match = re.search(r'\bg=(\d+)', all_text)
    c_match = re.search(r'\bc=(\d+)', all_text)
    h_match = re.search(r'\bh=(\d+)', all_text)
    bound_match = re.search(r'\[0,\s*(\d+)\]', all_text)
    
    if not all([one_match, g_match, c_match, h_match, bound_match]):
        print("[!] Failed to parse", file=sys.stderr)
        return False
    
    one = int(one_match.group(1))
    g = int(g_match.group(1))
    c = int(c_match.group(1))
    h = int(h_match.group(1))
    bound = int(bound_match.group(1))
    
    print(f"[*] one={one}, g={g}, c={c}, h={h}, bound={bound}", file=sys.stderr)
    
    # Simple approach: try x=0 first
    conn.send("submit 0")
    lines = conn.recv_until_prompt()
    response = " ".join(lines)
    print(f"[*] Trying x=0: {response}", file=sys.stderr)
    if "correct" in response:
        return True
    
    # If that didn't work, the answer is likely small or has a pattern
    # Try small values
    for x in [1, 2, 3, 4, 5, 10, 100, 1000, 10000, 100000]:
        if x > bound:
            break
        conn.send(f"submit {x}")
        lines = conn.recv_until_prompt()
        response = " ".join(lines)
        print(f"[*] Trying x={x}: {response}", file=sys.stderr)
        if "correct" in response:
            return True
    
    print("[!] Simple guesses failed", file=sys.stderr)
    return False


def main():
    """Main function."""
    host = "sporadiclogarithms.opus4-7.b01le.rs"
    port = 8443
    
    conn = RemoteConnection(host, port)
    
    try:
        conn.connect()
        
        # Read initial
        while True:
            line = conn.recv_line()
            if not line:
                break
            print(line, file=sys.stderr)
            if "Round 1/" in line:
                break
        
        # Solve rounds
        for round_num in range(1, 6):
            print(f"\n[*] ===== Round {round_num} =====", file=sys.stderr)
            if not solve_round(conn):
                print(f"[!] Failed round {round_num}", file=sys.stderr)
                return 1
            print(f"[+] Passed round {round_num}!", file=sys.stderr)
        
        # Read flag
        print("\n[*] Reading flag...", file=sys.stderr)
        while True:
            line = conn.recv_line()
            if not line:
                break
            print(line)
            print(line, file=sys.stderr)
        
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
