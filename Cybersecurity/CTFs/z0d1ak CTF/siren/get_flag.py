import socket
import ssl
import json
import hashlib
import os
import subprocess
from ecdsa import SECP256k1

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

conn = socket.create_connection(('siren-162ef798f77b.chals.z0d1ak.org', 1337))
sock = context.wrap_socket(conn, server_hostname='siren-162ef798f77b.chals.z0d1ak.org')

def recv_line():
    line = b""
    while not line.endswith(b"\n"):
        c = sock.recv(1)
        if not c:
            break
        line += c
    return json.loads(line.decode())

def send_req(req):
    sock.send((json.dumps(req) + "\n").encode())
    return recv_line()

print("Banner:", recv_line())

pubkey = send_req({"cmd": "pubkey"})
print("Pubkey:", pubkey)

song_id = pubkey["song_id"]
N = int(pubkey["n"], 16)
PITCH_BITS = pubkey["pitch_bits"]
Qx = int(pubkey["Qx"], 16)
Qy = int(pubkey["Qy"], 16)
PRIV_MSG = pubkey["priv_msg"]

def public_pitch(msg):
    material = (song_id + ":" + msg).encode()
    h = int.from_bytes(hashlib.sha256(material).digest(), "big")
    return h >> (256 - PITCH_BITS)

def msg_hash(msg):
    h = int.from_bytes(hashlib.sha256(msg.encode()).digest(), "big")
    return h % N

print("Collecting sigs...")
sigs = []
for i in range(45):
    msg = f"pwn_me_{i}"
    res = send_req({"cmd": "sign", "msg": msg})
    r = int(res["r"], 16)
    s = int(res["s"], 16)
    z = msg_hash(msg)
    K0 = public_pitch(msg) << (256 - PITCH_BITS)
    sigs.append((r, s, z, K0))

with open("sigs_live.json", "w") as f:
    json.dump({"N": N, "sigs": sigs}, f)

print("Running LLL in WSL...")
proc = subprocess.run(["wsl", "python3", "solve_live_fpylll.py"], capture_output=True, text=True)
print("WSL output:")
print(proc.stdout)
if proc.stderr:
    print("WSL err:")
    print(proc.stderr)

D = None
for line in proc.stdout.split("\n"):
    if "Found D: " in line:
        D = int(line.split("Found D: ")[1])
        break

if not D:
    print("Failed to find D")
    exit(1)

G = SECP256k1.generator
Q_calc = D * G
assert Q_calc.x() == Qx, "Public key mismatch!"
print("D found and verified!")

print("Forging signature for", PRIV_MSG)
z_priv = msg_hash(PRIV_MSG)
k = 1337
R = k * G
r = R.x() % N
s = (pow(k, -1, N) * (z_priv + r * D)) % N

res = send_req({"cmd": "unlock", "r": hex(r), "s": hex(s)})
print("Flag:", res)
