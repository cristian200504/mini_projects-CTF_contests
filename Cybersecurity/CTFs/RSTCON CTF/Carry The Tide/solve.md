# Carry The Tide - Solve & Writeup

## Challenge Information
- **Category:** Reverse Engineering
- **Points:** 70
- **Author:** f8al
- **Files Provided:** `carry` (ELF 32-bit Hitachi SH executable)
- **Description:** 
  > A sluice controller will only align if you give it the right control key.
  > 
  > Provided: carry

---

## 1. Initial Analysis & Architecture Identification

Inspecting the ELF header of the provided binary `carry`:

```bash
$ file carry
carry: ELF 32-bit LSB executable, Renesas SH, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=..., not stripped
```

The binary targets the **Hitachi SuperH (SH-4)** architecture (32-bit, little-endian).

Key symbols extracted from the symbol table (`.symtab`):
- `main` at `0x400804` (size 220 bytes)
- `check` at `0x400730` (size 212 bytes)

---

## 2. Disassembly & Reverse Engineering

### `main` (`0x400804`)
1. Prints the banner: `"Carry the tide. Enter control key: "`.
2. Reads user input via `fgets(buf, 40, stdin)`.
3. Strips trailing newline using `strcspn(buf, "\r\n")`.
4. Passes the buffer into `check(buf)`.
5. If `check` returns `1`:
   - Prints `"Sluice aligned."`
6. Otherwise:
   - Prints `"Out of phase."`

### `check` (`0x400730`)
Disassembling `check` with Capstone (`CS_ARCH_SH`, `CS_MODE_SH4A`):

```sh4
0x40073c: mov.l   r4, @(48, r1)     ; Save input pointer
0x400742: mov.l   @(48, r1), r4
0x400744: mov.l   0x4007fc, r1      ; strlen
0x400746: jsr     @r1
0x400748: nop     
0x400750: mov.l   r1, @(60, r2)     ; Save strlen(input)
0x400752: mov     #38, r1           ; Expected length = 38
0x40075a: cmp/eq  r1, r2
0x40075c: bt      0x400764
0x40075e: mov     #0, r1
0x400760: bra     0x4007ee          ; Return 0 if len != 38
0x400764: mov     #90, r2           ; Initial previous value = 90 (0x5A, 'Z')
0x40076a: mov.b   r0, @(6, r1)      ; Store prev = 90
0x400772: mov.l   r2, @(56, r1)     ; i = 0
0x400774: bra     0x4007dc          ; Jump to loop check

; Loop body:
0x400786: mov.b   @r1, r1           ; r1 = input[i]
0x40078e: mov.b   @(6, r2), r0      ; r0 = prev
0x400792: add     r3, r2            ; r2 = (prev + input[i])
0x400796: mov.b   r0, @(7, r1)      ; temp = (prev + input[i]) & 0xFF
0x400798: mov.l   0x400800, r2      ; Pointer to target array in .rodata (0x40095c)
0x4007a2: mov.b   @r1, r1           ; r1 = target[i]
0x4007ae: cmp/eq  r1, r2            ; Verify: target[i] == ((prev + input[i]) & 0xFF)
0x4007b0: bt      0x4007b8
0x4007b2: mov     #0, r1
0x4007b4: bra     0x4007ee          ; Return 0 if mismatch
0x4007b8: mov.b   @r1, r2           ; r2 = input[i]
0x4007cc: mov.b   r0, @(6, r1)      ; prev = input[i]
0x4007d8: add     #1, r2            ; i++
0x4007dc: cmp/ge  r1, r2            ; Loop while i < 38
0x4007ea: bf      0x400778
0x4007ec: mov     #1, r1            ; Return 1 if all match
```

The algorithm performs a running sum over adjacent input bytes:
- Initial state: $\text{prev} = 90$
- For each $i \in [0, 37]$:
  $$\text{target}[i] = (\text{prev} + \text{input}[i]) \pmod{256}$$
  $$\text{prev} = \text{input}[i]$$

Target bytes in `.rodata` at `0x40095c` (38 bytes):
```python
[204, 229, 231, 215, 210, 221, 233, 237, 231, 227, 220, 215, 215, 213, 198, 210, 232, 226, 204, 212, 227, 229, 224, 215, 210, 215, 210, 200, 215, 205, 209, 215, 219, 219, 215, 229, 216, 226]
```

---

## 3. Solution / Inversion

To recover the input key, we simply reverse the addition:
$$\text{input}[i] = (\text{target}[i] - \text{prev}) \pmod{256}$$
$$\text{prev} = \text{input}[i]$$

### Solver Script (`solve.py`)

```python
#!/usr/bin/env python3

target = [
    204, 229, 231, 215, 210, 221, 233, 237, 231, 227, 220, 215,
    215, 213, 198, 210, 232, 226, 204, 212, 227, 229, 224, 215,
    210, 215, 210, 200, 215, 205, 209, 215, 219, 219, 215, 229,
    216, 226
]

prev = 90
flag = []

for val in target:
    c = (val - prev) % 256
    flag.append(c)
    prev = c

flag_str = bytes(flag).decode('utf-8')
print(f"Recovered Flag: {flag_str}")
```

---

## 4. Flag

```text
rstcon{running_sum_unwinds_in_reverse}
```
