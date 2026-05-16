#!/usr/bin/env python3
"""
Solution for sporadiclogarithms CTF challenge.

Key insight: Since c has small order, phi^k = identity for some small k.
This means the sequence g, phi(g), phi^2(g), ... is periodic.
We can use this structure to solve the DLP efficiently.
"""

import sys
from math import isqrt


class BBClient:
    """Client for interacting with the black box oracle."""
    
    def __init__(self):
        self.one = None
        self.g = None
        self.c = None
        self.h = None
        self.bound = None
        self.query_count = 0
        
    def send_command(self, cmd):
        """Send a command and get the response."""
        print(cmd, flush=True)
        response = sys.stdin.readline().strip()
        return response
    
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
        return int(resp)
    
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
    test_elem = bb.g
    phi_powers = [test_elem]
    
    for i in range(1, 20):  # c order is at most 8
        test_elem = bb.phi(test_elem)
        if bb.eq(test_elem, bb.g):
            print(f"[*] Phi period = {i}", file=sys.stderr)
            return i
        phi_powers.append(test_elem)
    
    return None


def solve_with_bsgs(bb, phi_period):
    """
    Baby-step giant-step optimized for the holomorph structure.
    """
    bound = bb.bound
    m = min(isqrt(bound) + 1, 1000)  # Limit baby steps to avoid too many queries
    
    print(f"[*] BSGS with m={m}, bound={bound}", file=sys.stderr)
    
    # Precompute phi^i(g) for i = 0 to phi_period-1
    print("[*] Precomputing phi powers of g...", file=sys.stderr)
    phi_g_powers = [bb.g]
    current = bb.g
    for i in range(1, phi_period):
        current = bb.phi(current)
        phi_g_powers.append(current)
    
    # Baby steps: compute s(j) for j = 0, 1, ..., m-1
    print("[*] Computing baby steps...", file=sys.stderr)
    baby_table = {}
    baby_table[bb.one] = 0
    
    current_s = bb.one
    for j in range(1, m):
        # s(j) = s(j-1) * phi^(j-1)(g)
        phi_idx = (j - 1) % phi_period
        current_s = bb.mul(current_s, phi_g_powers[phi_idx])
        baby_table[current_s] = j
        
        if j % 100 == 0:
            print(f"[*] Baby step {j}/{m}, queries={bb.query_count}", file=sys.stderr)
    
    # Compute s(m)
    print("[*] Computing s(m)...", file=sys.stderr)
    s_m = bb.one
    for j in range(m):
        phi_idx = j % phi_period
        s_m = bb.mul(s_m, phi_g_powers[phi_idx])
    
    s_m_inv = bb.inv(s_m)
    
    # Giant steps
    print("[*] Computing giant steps...", file=sys.stderr)
    current = bb.h
    
    max_giant_steps = (bound // m) + 2
    for i in range(max_giant_steps):
        if i % 10 == 0:
            print(f"[*] Giant step {i}/{max_giant_steps}, queries={bb.query_count}", file=sys.stderr)
        
        # Check if current is in baby_table
        if current in baby_table:
            j = baby_table[current]
            x = i * m + j
            if x <= bound:
                print(f"[*] Found x = {x} (queries used: {bb.query_count})", file=sys.stderr)
                return x
        
        # current = current * s_m_inv
        current = bb.mul(current, s_m_inv)
        
        if bb.query_count > 9000:
            print("[!] Approaching query limit!", file=sys.stderr)
            break
    
    print("[!] Failed to find x", file=sys.stderr)
    return None


def solve_round():
    """Solve one round of the challenge."""
    bb = BBClient()
    
    # Read the setup information
    while True:
        line = sys.stdin.readline()
        if not line:
            return False
        
        sys.stderr.write(line)
        sys.stderr.flush()
        
        if "group=GL" in line:
            # Parse: group=GL(3,65537) one=1 g=2 c=3 h=4
            parts = line.split()
            for part in parts:
                if part.startswith("one="):
                    bb.one = int(part.split("=")[1])
                elif part.startswith("g="):
                    bb.g = int(part.split("=")[1])
                elif part.startswith("c="):
                    bb.c = int(part.split("=")[1])
                elif part.startswith("h="):
                    bb.h = int(part.split("=")[1])
        
        if "Find any x in" in line:
            # Parse: Find any x in [0, 262144]
            bound_str = line.split("[0, ")[1].split("]")[0]
            bb.bound = int(bound_str)
            break
    
    # Wait for prompt
    while True:
        line = sys.stdin.readline()
        sys.stderr.write(line)
        sys.stderr.flush()
        if "bb>" in line:
            break
    
    print(f"[*] Parsed: one={bb.one}, g={bb.g}, c={bb.c}, h={bb.h}, bound={bb.bound}", file=sys.stderr)
    
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
        response = sys.stdin.readline()
        sys.stderr.write(response)
        sys.stderr.flush()
        return "correct" in response
    
    return False


def main():
    """Main function to solve all rounds."""
    # Read initial messages
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        sys.stderr.write(line)
        sys.stderr.flush()
        
        if "Round 1/" in line:
            break
    
    # Solve each round
    for round_num in range(1, 6):
        print(f"\n[*] ===== Solving round {round_num} =====", file=sys.stderr)
        if not solve_round():
            print(f"[!] Failed round {round_num}", file=sys.stderr)
            return 1
        print(f"[+] Passed round {round_num}!", file=sys.stderr)
    
    # Read flag
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        print(line, end="")
        sys.stderr.write(line)
        sys.stderr.flush()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
