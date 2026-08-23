import socket
import ssl
import json
import hashlib
import os

host = 'cyclotomic-echo-859551231341.chals.z0d1ak.org'
port = 1337

N = 128

def poly_mul(a, b):
    c = [0] * (2*N)
    for i in range(N):
        for j in range(N):
            c[i+j] += a[i] * b[j]
    return [c[i] - c[i+N] for i in range(N)]

def poly_add(a, b): return [x + y for x, y in zip(a, b)]
def poly_sub(a, b): return [x - y for x, y in zip(a, b)]
def poly_scale(a, c): return [x * c for x in a]
def poly_round(a): return [round(x) for x in a]

with open('crypto_cyclotomic-echo/dist/recovery.json') as file:
    d = json.load(file)

f = d['f']
g = d['g']
F = d['F']
G = d['G']

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

print(f"Connecting to {host}:{port}...")
with socket.create_connection((host, port)) as sock:
    with context.wrap_socket(sock, server_hostname=host) as ssock:
        
        # Read the instance sent by the server
        # The server sends a single line of JSON
        f_in = ssock.makefile('r', encoding='utf-8')
        line = f_in.readline()
        print("Received from server:", line)
        instance = json.loads(line.strip())
        
        instance_id = instance['instance_id']
        target_hex = instance['target_hex']
        target = bytes.fromhex(target_hex)
        
        while True:
            salt = os.urandom(16)
            D = bytes.fromhex("6379636c6f746f6d69632d6563686f2f7369676e2f7632")
            m = target
            d_hash = hashlib.shake_256(D + bytes.fromhex(instance_id) + len(m).to_bytes(4, "little") + m + salt).digest(N // 4)
            hash_bits = [(d_hash[i >> 3] >> (i & 7)) & 1 for i in range(2 * N)]
            x = hash_bits[:N]
            y = hash_bits[N:]

            t1 = poly_add(poly_mul(x, g), poly_mul(y, G))
            t2 = poly_add(poly_mul(poly_scale(x, -1), f), poly_mul(poly_scale(y, -1), F))
            t1 = [v / 2.0 for v in t1]
            t2 = [v / 2.0 for v in t2]

            z1 = poly_round(t1)
            z2 = poly_round(t2)

            u = poly_add(poly_mul(z1, f), poly_mul(z2, g))
            v = poly_add(poly_mul(poly_scale(z1, -1), F), poly_mul(poly_scale(z2, -1), G))

            e2 = poly_sub(y, poly_scale(u, 2))
            
            def S(e2):
                for val in e2:
                    if val != 0: return val > 0
                return False
            
            if S(e2):
                break

        forgery = {
            "salt_hex": salt.hex(),
            "s1": u
        }
        
        print("Sending forgery...")
        forgery_json = json.dumps(forgery)
        print(forgery_json)
        ssock.sendall((forgery_json + "\n").encode())
        
        # Read the flag or response
        while True:
            resp = f_in.readline()
            if not resp:
                break
            print("Server response:", resp.strip())
