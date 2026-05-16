#!/usr/bin/env python3
"""
Remote solver for sporadiclogarithms CTF challenge.
Connects to the server and solves all rounds.
"""

import socket
import ssl
import sys
from math import isqrt


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


class BBClient:
    """Client for interacting with the black box oracle."""
    
    def __init__(self, conn):
        self.conn = conn
        self.one = None
        self.g = None
        self.c = None
        self.h = None
        self.bound = None
        self.query_count = 0
        
    def send_command(self, cmd):
        """Send a command and get the response."""
        self.conn.send(cmd)
        # Read all lines until we get the prompt back
        lines = self.conn.recv_until_prompt()
        # The response should be the last non-empty line
        for line in reversed(lines):
            if line.strip():
                return line.strip()
        return ""
    
    def mul(self, a, b):
        """Multiply two elements."""
        self.query_count += 1
        resp = self.send_command(f"mul {a} {b}")
        return int(resp)
    
    def inv(self, a):
        """Invert an element."""
        self.query_count += 1
        resp = self.send_command(f"inv {a}")
        return int(resp)
    
    def phi(self, a):
        """Apply conjugation phi(a) = c*a*c^-1."""
        self.query_count += 1
        resp = self.send_command(f"phi {a}")
        try:
            return int(resp)
        except ValueError:
            print(f"[!] Failed to parse phi response: '{resp}'", file=sys.stderr)
            raise
    
    def eq(self, a, b):
        """Check if two elements are equal."""
        self.query_count += 1
        resp = self.send_command(f"eq {a} {b}")
        return resp == "1"
    
    def submit(self, x):
        """Submit the answer."""
        self.send_command(f"submit {x}")


def find_phi_period(bb):
    """Find the period of phi (order of c)."""
    print("[*] Finding phi period...", file=sys.stderr)
    test_elem = bb.g  # This is handle 2
    phi_powers = [test_elem]
    
    for i in range(1, 20):  # c order is at most 8
        test_elem = bb.phi(test_elem)  # Apply phi to get new handle
        if bb.eq(test_elem, bb.g):
            print(f"[*] Phi period = {i}", file=sys.stderr)
            return i
        phi_powers.append(test_elem)
    
    print("[!] Could not find phi period in 20 iterations", file=sys.stderr)
    return None


def solve_with_bsgs(bb, phi_period):
    """
    Baby-step giant-step optimized for the holomorph structure.
    We want to find x such that h = s(x).
    Write x = i*m + j where 0 <= j < m.
    Then h = s(i*m + j) = s(i*m) * s(j) (approximately, ignoring the c^x part for now)
    So h * s(i*m)^{-1} = s(j)
    """
    bound = bb.bound
    m = min(isqrt(bound) + 1, 600)  # Reduce m to save queries
    
    print(f"[*] BSGS with m={m}, bound={bound}", file=sys.stderr)
    
    # Precompute phi^i(g) for i = 0 to phi_period-1
    print("[*] Precomputing phi powers of g...", file=sys.stderr)
    phi_g_powers = [bb.g]
    current = bb.g
    for i in range(1, phi_period):
        current = bb.phi(current)
        phi_g_powers.append(current)
    
    # Baby steps: compute s(j) for j = 0, 1, ..., m-1 and store in table
    print("[*] Computing baby steps...", file=sys.stderr)
    baby_steps = [bb.one]  # s(0) = identity
    
    current_s = bb.one
    for j in range(1, m):
        # s(j) = s(j-1) * phi^(j-1)(g)
        phi_idx = (j - 1) % phi_period
        current_s = bb.mul(current_s, phi_g_powers[phi_idx])
        baby_steps.append(current_s)
        
        if j % 200 == 0:
            print(f"[*] Baby step {j}/{m}, queries={bb.query_count}", file=sys.stderr)
    
    # Compute s(m)
    print("[*] Computing s(m)...", file=sys.stderr)
    s_m = baby_steps[-1]  # s(m-1)
    phi_idx = (m - 1) % phi_period
    s_m = bb.mul(s_m, phi_g_powers[phi_idx])
    
    s_m_inv = bb.inv(s_m)
    
    # Giant steps: compute h * s(i*m)^{-1} and check against baby steps
    print("[*] Computing giant steps...", file=sys.stderr)
    current = bb.h
    
    max_giant_steps = (bound // m) + 2
    for i in range(max_giant_steps):
        if i % 20 == 0:
            print(f"[*] Giant step {i}/{max_giant_steps}, queries={bb.query_count}", file=sys.stderr)
        
        # Check if current matches any baby step
        for j, baby_handle in enumerate(baby_steps):
            if bb.eq(current, baby_handle):
                x = i * m + j
                if x <= bound:
                    print(f"[*] Found x = {x} (queries used: {bb.query_count})", file=sys.stderr)
                    return x
                    
        # current = current * s_m_inv = h * s(i*m)^{-1} * s(m)^{-1} = h * s((i+1)*m)^{-1}
        current = bb.mul(current, s_m_inv)
        
        if bb.query_count > 9500:
            print("[!] Approaching query limit!", file=sys.stderr)
            break
    
    print("[!] Failed to find x", file=sys.stderr)
    return None


def solve_round(conn):
    """Solve one round of the challenge."""
    bb = BBClient(conn)
    
    # Read the setup information and buffer all lines
    all_text = ""
    while True:
        line = conn.recv_line()
        if not line:
            return False
        
        print(line, file=sys.stderr)
        all_text += line + " "
        
        if "bb>" in line:
            break
    
    # Parse from the buffered text
    import re
    one_match = re.search(r'one=(\d+)', all_text)
    g_match = re.search(r'\bg=(\d+)', all_text)
    c_match = re.search(r'\bc=(\d+)', all_text)
    h_match = re.search(r'\bh=(\d+)', all_text)
    bound_match = re.search(r'\[0,\s*(\d+)\]', all_text)
    
    if one_match:
        bb.one = int(one_match.group(1))
    if g_match:
        bb.g = int(g_match.group(1))
    if c_match:
        bb.c = int(c_match.group(1))
    if h_match:
        bb.h = int(h_match.group(1))
    if bound_match:
        bb.bound = int(bound_match.group(1))
    
    print(f"[*] Parsed: one={bb.one}, g={bb.g}, c={bb.c}, h={bb.h}, bound={bb.bound}", file=sys.stderr)
    
    # Validate we got all values
    if None in [bb.one, bb.g, bb.c, bb.h, bb.bound]:
        print("[!] Failed to parse all required values", file=sys.stderr)
        return False
    
    # Find phi period
    phi_period = find_phi_period(bb)
    if phi_period is None:
        print("[!] Could not find phi period", file=sys.stderr)
        return False
    
    # Solve using baby-step giant-step
    x = solve_with_bsgs(bb, phi_period)
    
    if x is not None:
        bb.submit(x)
        # Read response
        response = conn.recv_line()
        print(response, file=sys.stderr)
        return "correct" in response
    
    return False


def main():
    """Main function to solve all rounds."""
    host = "sporadiclogarithms.opus4-7.b01le.rs"
    port = 8443
    
    conn = RemoteConnection(host, port)
    
    try:
        conn.connect()
        
        # Read initial messages
        while True:
            line = conn.recv_line()
            if not line:
                break
            print(line, file=sys.stderr)
            
            if "Round 1/" in line:
                break
        
        # Solve each round
        for round_num in range(1, 6):
            print(f"\n[*] ===== Solving round {round_num} =====", file=sys.stderr)
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
            if "flag{" in line or "FLAG{" in line:
                print(f"\n[+] FLAG CAPTURED: {line}", file=sys.stderr)
        
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
