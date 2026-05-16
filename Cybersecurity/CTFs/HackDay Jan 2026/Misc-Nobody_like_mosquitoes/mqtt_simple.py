import socket
import struct

def mqtt_connect(client_id):
    # MQTT Connect Packet
    # Fixed Label: 0x10 (Connect)
    # Remaining Length: calculated below
    
    # Variable Header:
    # Protocol Name length: 00 04
    # Protocol Name: MQTT
    # Level: 04 (3.1.1)
    # Connect Flags: 02 (Clean Session)
    # Keep Alive: 00 3c (60s)
    
    var_header = b'\x00\x04MQTT\x04\x02\x00\x3c'
    
    # Payload:
    # Client ID length
    # Client ID
    payload = struct.pack("!H", len(client_id)) + client_id.encode()
    
    rem_len = len(var_header) + len(payload)
    fixed_header = b'\x10' + bytes([rem_len]) # assuming rem_len < 127
    
    return fixed_header + var_header + payload

def mqtt_subscribe(topic):
    # MQTT Subscribe Packet
    # Fixed Label: 0x82
    # Packet ID: 00 01
    # Topic length
    # Topic
    # Requested QoS: 00
    
    var_header = b'\x00\x01'
    payload = struct.pack("!H", len(topic)) + topic.encode() + b'\x00'
    
    rem_len = len(var_header) + len(payload)
    fixed_header = b'\x82' + bytes([rem_len])
    
    return fixed_header + var_header + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    
    s = socket.create_connection((server, port), timeout=10)
    print("[*] Connected to socket")
    
    s.sendall(mqtt_connect("ctf-client"))
    print("[*] Sent Connect")
    
    connack = s.recv(4)
    print(f"[*] Connack: {connack.hex()}")
    
    s.sendall(mqtt_subscribe("#"))
    print("[*] Sent Subscribe #")
    
    suback = s.recv(5)
    print(f"[*] Suback: {suback.hex()}")
    
    try:
        while True:
            data = s.recv(1024)
            if not data:
                break
            # Parsing minimal publish
            # 0x30 is Publish
            print(f"[*] Received: {data.hex()}")
            # Print as text to spot flag
            try:
                print(f"[*] Text: {data.decode(errors='ignore')}")
            except:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
