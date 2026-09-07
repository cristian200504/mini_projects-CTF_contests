# small-guy — Solution

**Flag:** `NNS{unw1nd_m3_1f_y0u_c4n_sm4ll_guy!!}`

## 1. Setup

`rev_small-guy.tar.gz` extracts to a `Dockerfile` and a small (19 KB), stripped,
dynamically-linked x86-64 ELF, `small-guy`. The Dockerfile just copies the
binary into a `debian:trixie-slim` image and runs it — no extra context.

Basic probing:

```
$ ./small-guy
usage: ./small-guy NNS{...}

$ ./small-guy 'NNS{aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}'
the small guy only understands 32 characters
```

So the program wants a single argument shaped `NNS{...}`, where `...` is
**exactly 32 characters**. That makes the full flag 37 characters long
(`NNS{` + 32 + `}`).

## 2. First look at `main`

Disassembling (radare2 / objdump) shows `main` doing something very
ordinary:

1. Checks `argc == 2`.
2. `strlen(argv[1])`.
3. Checks the string starts with `NNS{` and ends with `}` (compared as a
   4-byte and 1-byte literal), and that the content between them is exactly
   32 bytes.
4. Copies those 32 bytes into a small **custom ELF section called `.vmin`**
   at a fixed writable address (`0x4d0000`, 40 bytes reserved — the 32
   content bytes plus a padded copy of the first two).
5. Calls a tiny helper `fcn_00400600`, which just does:
   ```c
   sub rsp, 8
   edi = 0
   call fcn_00400618
   add rsp, 8
   ret
   ```
6. After that call returns, it does
   `memcmp(0x404080, 0x401dd0, 0x20)` and prints `"Correct!"` or `"Wrong."`
   based on the result.

`0x401dd0` is a fixed 32-byte blob baked into `.rodata` — the target hash.
`0x404080` is in `.bss` and is *written* by an exception landing pad we'll
get to shortly. The `.vmin` section name is the big tell: this binary
implements a small **virtual machine**, and `0x4d0000` is its input tape.

## 3. `fcn_00400618`: a recursive function that always throws

`fcn_00400618(long n)`:

```c
if (n == 256) { throw 1; }          // base case, always throws
digit  = compute_digit(n);           // 0..31, depends only on n and 2 input bytes
key    = compute_roundkey(n);        // 64-bit, ditto
push key; push key;                  // stack padding / a place for key to live
switch (digit) {                     // 32 cases, ALL of them:
  case 0..31: fcn_00400618(n + 1); break;
}
```

Every one of the 32 `switch` cases does the exact same two things: call
`fcn_00400618` again with `n+1`, then return. Statically, this looks like
pure control-flow-flattening noise — 32 code paths that are all
observably identical. Following it with a debugger confirms recursion
depth always reaches exactly 256 before throwing, and the registers
`rbx/r12/r13/r14` (the eventual comparison operands) are **never touched by
any real instruction** in this function. And yet, after the exception
propagates and is caught, those four registers hold values that clearly
depend on the input. Something invisible to normal disassembly is
mutating them.

## 4. The real payload lives in `.eh_frame`

The answer is in the C++ exception-unwinding metadata. `readelf
--debug-dump=frames` on this binary shows something no normal compiler
ever emits: dozens of `DW_CFA_val_expression` entries — full **DWARF stack
expressions** (`DW_OP_breg`, `DW_OP_mul`, `DW_OP_xor`, `DW_OP_shl/shr`,
even a mini loop via `DW_OP_bra`) attached to `rbx`, `r12`, `r13`, `r14`,
scattered across the 32 call sites inside `fcn_00400618`.

This metadata is normally just bookkeeping so a debugger/unwinder can
figure out how to restore a caller's registers while walking the stack.
Here, it's been turned into a private, Turing-complete-ish computation
that only runs when a real exception unwinds through the function — i.e.
when the recursion's base case throws and libgcc's `_Unwind_RaiseException`
walks back out through all 256 stack frames, applying each frame's CFI
rule to update a *virtual* register file as it goes.

`fcn_00400600`'s own frame is the only one with an actual `try`/`catch`
(confirmed via `.gcc_except_table`); `fcn_00400618`'s call sites are *not*
individually protected, so a throw from depth 256 unwinds cleanly through
**all** 256 recursive frames before it's finally caught back in
`fcn_00400600`. At that point the CFI-computed `rbx/r12/r13/r14` are
installed as real CPU registers, the catch handler copies them to
`0x404080`, and *that* is what gets `memcmp`'d against the target.

## 5. Reconstructing the VM

Digging through the raw CFI opcodes (not the human-readable interpretation,
the actual `DW_CFA_val_expression` byte streams) revealed the structure:

- **State**: four 64-bit words, initially the raw 32 bytes of the flag
  content (`rbx = bytes[0:8]`, `r12 = bytes[8:16]`, `r13 = bytes[16:24]`,
  `r14 = bytes[24:32]`), loaded fresh from `.vmin` at the base case
  (`n == 256`).
- **256 rounds**, one per recursion level `idx = 0..255`, applied in
  **descending** order (`idx = 255` first, `idx = 0` last) — because
  unwinding proceeds from the deepest frame (256) outward to the
  shallowest (0).
- At each level, a **digit** `0..31` selects one of 32 fixed mixing
  operations (add/xor/multiply/rotate-xor/swap a pair of words/a tiny
  LCG loop iterated 1–4 times), and a **round key** feeds the operations
  that need one:
  ```
  digit(idx) = (digit_table[idx] + ((acc >> (idx & 7)) & 0xffffffff)) & 0x1f
  rcx(idx)   = key_table[idx+1] XOR (acc * 0x9e3779b97f4a7c15)     # note: idx+1
  ```
  where `acc` is the first two bytes of the flag content, and
  `digit_table`/`key_table` are two fixed lookup tables sitting in
  `.rodata` (`0x4014d0`, 256 bytes; `0x4015d0`, 256 × 8 bytes).
- The `idx+1` in the round-key formula is the single most counter-intuitive
  part of the whole binary: the key value used *inside* level `idx`'s own
  operation is not the one it itself pushed on the stack, but the one
  pushed by the **next deeper** frame (`idx+1`). At the very deepest level
  (`idx == 255`) there is no such frame — the base case never pushes a
  key — so its CFI rule explicitly hard-codes the key to zero instead of
  reading the stack.
- All 32 possible operations are individually invertible: additions invert
  to subtraction, multiplications use odd constants (invertible mod
  2^64 via `pow(c, -1, 2**64)`), XORs (including the rotate-xor ones) are
  involutions given the untouched operand, register swaps invert to
  themselves, and the two small LCG loops invert by running the same
  fixed iteration count backwards.

Getting to this exact model took a lot of careful differential testing —
patching the recursion's exit threshold in gdb to isolate individual
rounds, and cross-checking against `frame N` / `print $reg` inside gdb to
nail down exactly which CFI row governs which transition and which
round-key is really in scope. The `solve.py` in this directory is the
final, validated model, and it reproduces the real binary's output bit
for bit at every tested recursion depth, including the true depth of 256.

## 6. Inverting it

Crucially, the **32-bit digit and the round keys only depend on the first
two bytes of the input** (`acc`), not on the rest of the content. That
means: for a *guessed* 2-byte prefix, the entire 256-step sequence of
(operation, key) pairs is fully determined and can be run **backwards**
from the known target hash, all the way back to a candidate 32-byte
preimage — independent of whether the guess is right.

So the attack is:

1. For each of the 65536 possible first-two-bytes (`acc = 0..0xffff`):
   - Derive the digit/round-key sequence for all 256 levels.
   - Starting from the target hash bytes, apply the **inverse** of each of
     the 256 operations, in the order that undoes them (`idx = 0` first,
     up to `idx = 255` last — the reverse of how they were applied
     forward).
   - This yields a candidate 32-byte preimage.
2. Keep only candidates whose own first two bytes match the `acc` we
   guessed with (self-consistency check) and whose bytes are all
   printable ASCII.
3. Exactly one candidate survives out of 65536:
   ```
   unw1nd_m3_1f_y0u_c4n_sm4ll_guy!!
   ```

Wrapped back into the expected format:

```
NNS{unw1nd_m3_1f_y0u_c4n_sm4ll_guy!!}
```

Running it against the real binary confirms it:

```
$ ./small-guy 'NNS{unw1nd_m3_1f_y0u_c4n_sm4ll_guy!!}'
Correct!
```

The flag itself is the punchline: *"unwind me if you can"* — a direct nod
to the DWARF stack-unwinding trick the whole challenge is built on, and
the description's "a small guy once told me something special" is simply
the challenge (and binary) introducing itself.

## 7. Files in this directory

- `description.txt` — original challenge description.
- `rev_small-guy.tar.gz` — original challenge archive, untouched.
- `rev_small-guy/Dockerfile`, `rev_small-guy/small-guy` — original challenge
  files from the archive.
- `rev_small-guy/solve.py` — standalone solver. Needs only the `small-guy`
  binary next to it (or passed as an argument); extracts the two lookup
  tables and the target hash directly from the binary's `.rodata`, runs
  the 65536-way brute force described above, and prints the flag. Takes
  about 20 seconds on a typical machine, no debugger/emulation required.

```
python3 solve.py small-guy
```

## 8. Key takeaway / how this obfuscation works in general

This is a real (if unusual) anti-reversing technique: hiding computation
inside `.eh_frame` `DW_CFA_val_expression`/`DW_CFA_expression` opcodes,
which are part of the ABI-mandated unwind metadata every C++ binary
already ships, and triggering their evaluation by deliberately throwing
an exception through a deep, uniform recursion. Static disassembly of the
*code* section shows nothing but a pointless-looking, deeply recursive
function; the actual logic only "runs" inside libgcc's unwinder during
the throw, and is invisible to `objdump -d`/Ghidra/IDA's default view
unless you specifically inspect the exception tables. The way to spot and
defeat it is exactly what this write-up did: notice registers changing
value with no instructions that write them, then go dump
`.eh_frame`/`.gcc_except_table` instead of trusting the disassembly.
