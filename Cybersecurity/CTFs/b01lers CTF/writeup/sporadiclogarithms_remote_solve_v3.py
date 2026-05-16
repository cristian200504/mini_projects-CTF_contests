#!/usr/bin/env python3
"""
Correct BSGS for the holomorph DLP.

The holomorph element is (matrix, c^k). Multiplication:
  (a, c^i) * (b, c^j) = (a * c^i * b * c^{-i}, c^{i+j})

hol_pow((g, c), x) = (g * phi(g) * phi^2(g) * ... * phi^{x-1}(g), c^x)
where phi(a) = c*a*c^{-1}

Let S(x) = first component = g * phi(g) * ... * phi^{x-1}(g)

Key recurrence:
  S(0) = I (identity)
  S(x+1) = S(x) * phi^x(g)

For BSGS, write x = i*m + j (0 <= j < m):
  S(i*m + j) = S(i*m) * phi^{i*m}(S(j))

So: h = S(i*m) * phi^{i*m}(S(j))
=> S(i*m)^{-1} * h = phi^{i*m}(S(j))
=> phi^{-i*m}(S(i*m)^{-1} * h) = S(j)

Since phi has period k (order of c), phi^{i*m} = phi^{(i*m) mod k}

Strategy:
- Baby steps: compute S(j) for j = 0..m-1
- Giant steps: compute phi^{-i*m}(S(i*m)^{-1} * h) for i = 0,1,...
  and check if it equals any S(j)

But applying phi^{-i*m} to a value costs queries. Instead, let's rearrange:

h = S(i*m) * phi^{i*m}(S(j))

Let T(i) = S(i*m)^{-1} * h
Then T(i) = phi^{i*m}(S(j))

Since phi has period k, phi^{i*m} = phi^{(i*m) mod k}

So for each i, we need to check if T(i) equals phi^r(S(j)) for r = (i*m) mod k.

Better approach: precompute phi^r(S(j)) for all j and r = 0..k-1.
Then for each giant step i, compute T(i) and check against the table for r = (i*m) mod k.

This costs:
- Baby steps: m multiplications
- Phi applications: m * k phi calls (to get phi^r(S(j)) for all r)
- Giant steps: bound/m multiplications + inv calls

With m = 512, k <= 8: 512 + 512*8 + 512 + 512 = ~5600 queries. Should be fine!
"""

import socket
import ssl
import sys
import re


class RemoteConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.ssl_sock = None
        
    def connect(self):
        print(f"[*] Connecting to {self.host}:{self.port}...", file=sys.stderr)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.ssl_sock = context.wrap_socket(self.sock, server_hostname=self.host)
        self.ssl_sock.connect((self.host, self.port))
        print("[+] Connected!", file=sys.stderr)
        
    def send(self, data):
        self.ssl_sock.sendall(data.encode() + b'\n')
        
    def recv_line(self):
        line = b''
        while True:
            try:
                char = self.ssl_sock.recv(1)
                if not char:
                    return line.decode(errors='ignore') if line else None
                line += char
                if char == b'\n':
                    return line[:-1].decode(errors='ignore')
                if line.endswith(b'bb> '):
                    return line.decode(errors='ignore')
            except Exception as e:
                return line.decode(errors='ignore') if line else None
    
    def recv_until_prompt(self):
        lines = []
        while True:
            line = self.recv_line()
            if not line:
                break
            if 'bb>' in line:
                before = line.split('bb>')[0].strip()
                if before:
                    lines.append(before)
                break
            lines.append(line)
        return lines
            
    def close(self):
        if self.ssl_sock:
            self.ssl_sock.close()


class BB:
    def __init__(self, conn):
        self.conn = conn
        self.queries = 0
        
    def _cmd(self, cmd):
        self.conn.send(cmd)
        lines = self.conn.recv_until_prompt()
        for line in reversed(lines):
            if line.strip():
                return line.strip()
        return ""
    
    def mul(self, a, b):
        self.queries += 1
        return int(self._cmd(f"mul {a} {b}"))
    
    def inv(self, a):
        self.queries += 1
        return int(self._cmd(f"inv {a}"))
    
    def phi(self, a):
        self.queries += 1
        return int(self._cmd(f"phi {a}"))
    
    def eq(self, a, b):
        self.queries += 1
        return self._cmd(f"eq {a} {b}") == "1"
    
    def submit(self, x):
        resp = self._cmd(f"submit {x}")
        return resp


def solve_round(conn):
    # Read all setup text until prompt
    all_text = ""
    while True:
        line = conn.recv_line()
        if not line:
            return False
        print(line, file=sys.stderr)
        all_text += line + " "
        if "bb>" in line:
            break
    
    # Parse handles and bound
    one = int(re.search(r'one=(\d+)', all_text).group(1))
    g   = int(re.search(r'\bg=(\d+)', all_text).group(1))
    c   = int(re.search(r'\bc=(\d+)', all_text).group(1))
    h   = int(re.search(r'\bh=(\d+)', all_text).group(1))
    bound = int(re.search(r'\[0,\s*(\d+)\]', all_text).group(1))
    
    print(f"[*] one={one} g={g} c={c} h={h} bound={bound}", file=sys.stderr)
    
    bb = BB(conn)
    
    # Step 1: Find phi period k (order of c, at most 8)
    print("[*] Finding phi period...", file=sys.stderr)
    k = None
    cur = g
    for i in range(1, 20):
        cur = bb.phi(cur)
        if bb.eq(cur, g):
            k = i
            break
    print(f"[*] phi period k={k}", file=sys.stderr)
    
    # Step 2: Precompute phi^r(g) for r = 0..k-1
    phi_g = [g]
    cur = g
    for r in range(1, k):
        cur = bb.phi(cur)
        phi_g.append(cur)
    # phi_g[r] = phi^r(g)
    
    # Step 3: Baby steps - compute S(j) for j = 0..m-1
    # S(0) = one (identity)
    # S(j) = S(j-1) * phi^{j-1}(g)
    from math import isqrt
    m = isqrt(bound) + 1
    print(f"[*] Baby steps m={m}...", file=sys.stderr)
    
    S = [one]  # S[j] = handle for S(j)
    cur_s = one
    for j in range(1, m):
        r = (j - 1) % k
        cur_s = bb.mul(cur_s, phi_g[r])
        S.append(cur_s)
    
    print(f"[*] Baby steps done, queries={bb.queries}", file=sys.stderr)
    
    # Step 4: For each r in 0..k-1, build table: phi^r(S(j)) -> j
    # We need to check: T(i) = phi^{(i*m) mod k}(S(j))
    # So build tables[r][handle] = j for each r
    print("[*] Building phi-twisted baby step tables...", file=sys.stderr)
    tables = [{} for _ in range(k)]
    
    for j in range(m):
        sj = S[j]
        # phi^0(S(j)) = S(j)
        tables[0][sj] = j
        cur_phi_sj = sj
        for r in range(1, k):
            cur_phi_sj = bb.phi(cur_phi_sj)
            tables[r][cur_phi_sj] = j
    
    print(f"[*] Tables built, queries={bb.queries}", file=sys.stderr)
    
    # Step 5: Giant steps
    # T(i) = S(i*m)^{-1} * h
    # We check T(i) against tables[(i*m) mod k]
    # 
    # Recurrence for S(i*m):
    # S((i+1)*m) = S(i*m) * phi^{i*m}(S(m))
    # But phi^{i*m} = phi^{(i*m) mod k}
    # 
    # So we need phi^r(S(m)) for r = 0..k-1
    
    # Compute S(m)
    s_m = S[-1]  # S[m-1]
    r = (m - 1) % k
    s_m = bb.mul(s_m, phi_g[r])
    
    # Compute phi^r(S(m)) for r = 0..k-1
    phi_sm = [s_m]
    cur = s_m
    for r in range(1, k):
        cur = bb.phi(cur)
        phi_sm.append(cur)
    
    print(f"[*] Giant steps starting, queries={bb.queries}", file=sys.stderr)
    
    # T(0) = S(0)^{-1} * h = one^{-1} * h = h
    # T(i+1) = S((i+1)*m)^{-1} * h
    # S((i+1)*m) = S(i*m) * phi^{(i*m) mod k}(S(m))
    # T(i+1) = (S(i*m) * phi^{(i*m) mod k}(S(m)))^{-1} * h
    #         = phi^{(i*m) mod k}(S(m))^{-1} * S(i*m)^{-1} * h
    #         = phi^{(i*m) mod k}(S(m))^{-1} * T(i)
    
    # Precompute inv of phi^r(S(m))
    phi_sm_inv = []
    for r in range(k):
        phi_sm_inv.append(bb.inv(phi_sm[r]))
    
    max_i = (bound // m) + 2
    T = h  # T(0) = h
    
    for i in range(max_i):
        r_check = (i * m) % k
        
        if T in tables[r_check]:
            j = tables[r_check][T]
            x = i * m + j
            if 0 <= x <= bound:
                print(f"[*] Found x={x} at i={i}, j={j}, queries={bb.queries}", file=sys.stderr)
                resp = bb.submit(x)
                print(f"[*] Server response: {resp}", file=sys.stderr)
                return "correct" in resp
        
        # T(i+1) = phi^{(i*m) mod k}(S(m))^{-1} * T(i)
        r_mul = (i * m) % k
        T = bb.mul(phi_sm_inv[r_mul], T)
        
        if i % 50 == 0:
            print(f"[*] Giant step {i}/{max_i}, queries={bb.queries}", file=sys.stderr)
        
        if bb.queries > 9500:
            print("[!] Query limit approaching!", file=sys.stderr)
            break
    
    print("[!] Failed to find x", file=sys.stderr)
    return False


def main():
    host = "sporadiclogarithms.opus4-7.b01le.rs"
    port = 8443
    
    conn = RemoteConnection(host, port)
    conn.connect()
    
    try:
        # Read initial banner
        while True:
            line = conn.recv_line()
            if not line:
                break
            print(line, file=sys.stderr)
            if "Round 1/" in line:
                break
        
        for round_num in range(1, 6):
            print(f"\n[*] ===== Round {round_num}/5 =====", file=sys.stderr)
            if not solve_round(conn):
                print(f"[!] Failed round {round_num}", file=sys.stderr)
                return 1
            print(f"[+] Passed round {round_num}!", file=sys.stderr)
        
        # Read flag
        while True:
            line = conn.recv_line()
            if not line:
                break
            print(line, file=sys.stderr)
            if "flag{" in line.lower() or "bctf{" in line.lower() or "b01l" in line.lower():
                print(f"\n*** FLAG: {line} ***")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
