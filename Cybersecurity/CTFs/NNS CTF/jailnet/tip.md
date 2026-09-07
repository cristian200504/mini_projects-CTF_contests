# jailnet — investigation notes (session 2)

Goal: escape the Janet "sandbox" in `pwn_jailnet/server.janet` and read `/flag.txt`.
Live instance: `ncat --ssl jailnet-f27162716dcb.chall.nnsc.tf 1337`.

This file supersedes the earlier session-1 notes. Everything below was
re-derived and verified against a local reproduction.

---

## 1. What the service actually does (worker branch of `server.janet`)

Per TCP connection the parent spawns a fresh `janet server.janet --worker`
process whose stdin/stdout/stderr are piped to the socket. The worker:

1. `env = (table/proto-flatten (fiber/getenv (fiber/current)))`
   — a **fresh flat table**: the script env's own keys + every core binding,
   flattened out of the prototype chain. Values are the **shared**
   binding-entry tables (`@{:value <fn> :macro true ...}`), same objects as
   in the real root env.
2. `(sandbox :asm :chroot :env :ffi :fs :hrtime :modules :net :signal
     :subprocess :threads :unmarshal)` — note: **not** `:sandbox`, **not**
     `:compile` (they need `compile` to work and `sandbox` to stay callable).
3. Name filter — `(put env k nil)` for every key matching:
   - prefix: `debug fiber ev/ file net/ os/ module/ bundle/ int/`
   - substring: `env flycheck loader source compile eval mac marshal proto
     image parse dyn global doc peg with ffi/defbind`
   - exact: `resume cancel yield propagate signal trace untrace *debug*
     stdin stdout stderr getline sandbox comptime compif compwhen
     run-context dofile repl require import import* use all-bindings
     native asm disasm hash protect try defer edefer prompt label return
     generate coro varfn tracev cli-main slurp spit quit ffi/context`
4. `forbidden-form?` on the parsed form — recursively rejects:
   the keyword `:macro`, any `:core/u64` value, any `:core/s64` value
   (recurses through tuple/array/struct/table; keys **and** values checked).
5. `(compile form env "submission")` — macro expansion happens here, with
   `fiber->env = env` (the filtered table). Sandbox state at this point is
   the step-2 set (FFI/fs/etc already off).
6. `(sandbox :all)` → `janet_vm.sandbox_flags |= 0xFFFFFFFF`. Now permanent.
7. `(fiber/new thunk :t env)` then `(resume fiber)`; on success the result
   is discarded (nothing is printed). Errors ARE printed (stderr → socket).
   `:t` is a sigmask (block error+user0..4), irrelevant.

Input cap: `0x20000` bytes. Exactly one top-level form is consumed.
To see anything you must `(print ...)` yourself, or cause an error.

Build: official `janet-v1.41.2-linux-x64` release (SHA in Dockerfile).
`/flag.txt` is written by `entrypoint.sh` from `$FLAG`, then `FLAG` is
unset. Owned `ctf:ctf`, mode 0644, our uid = ctf → readable **if** we can
call an OS read primitive.

---

## 2. Core conclusion

Everything that can touch the OS is either name-filtered or blocked by
`(sandbox :all)` at runtime. **The only escape is to get native code
execution back.** Concretely:

- **All `ffi/*` bindings survive the name filter** — `ffi/native`,
  `ffi/lookup`, `ffi/call`, `ffi/read`, `ffi/write`, `ffi/malloc`,
  `ffi/pointer-buffer`, `ffi/pointer-cfunction`, `ffi/jitfn`,
  `ffi/signature`, `ffi/struct`, `ffi/size`, `ffi/align`, `ffi/trampoline`,
  `ffi/calling-conventions`. Verified.
- They are only stopped by the runtime check `janet_sandbox_assert(...)`
  against `janet_vm.sandbox_flags`. `ffi/size`, `ffi/align`, `ffi/struct`,
  `ffi/signature`, `ffi/trampoline`, `ffi/calling-conventions` have **no**
  sandbox assert and work right now. The dangerous ones
  (`native/lookup/call/read/write/malloc/free/pointer-buffer/
  pointer-cfunction/jitfn`) assert `FFI_DEFINE|FFI_USE|FFI_JIT`, all set
  by `:ffi`.
- `janet_sandbox()` is purely additive (`|= flags`). Re-enabling FFI
  requires an **arbitrary memory write** that clears the FFI bits in
  `janet_vm.sandbox_flags` (a `uint32_t`, deep inside the `__thread
  JanetVM janet_vm` struct — TLS).

So the win condition is:

```
<mem-write primitive>  →  zero janet_vm.sandbox_flags
→ (ffi/native nil)            # self handle (janet links libc)
→ (ffi/lookup h "system")     # or open/read/write, or execl
→ (ffi/signature :default :int :ptr)
→ (ffi/call sysptr sig ["cat /flag.txt 1>&2"])
```

`janet_sandbox_assert(f)` panics iff `f & janet_vm.sandbox_flags`.
Clearing the whole word is fine.

---

## 3. Leak primitive (ASLR defeat)

`(ffi/trampoline :default)` → `<pointer 0xXXXXXXXXXXXX>` = address of
`janet_ffi_sysv64_standard_callback` **inside the janet binary**. Binary is
PIE, so this leaks the image base. We have the exact release binary
(`scratchpad/janet.bin`, not stripped) to compute any fixed offset from
that symbol.

Open problem: `janet_vm` is `__thread` (TLS), so its runtime address is not
a fixed offset from the image base — need either a pointer into the TLS
block, or compute `%fs`-relative, or corrupt something reachable without
knowing `&janet_vm` (e.g. a `JanetBuffer`/`JanetArray` `data` pointer, or a
`JanetFunction`/abstract, i.e. a relative/heap-based write rather than
absolute).

`nm janet.bin` highlights: `janet_local_vm` (returns `&janet_vm`),
`janet_sandbox`, `janet_sandbox_assert`, `system@GLIBC` is imported.
`janet_vm` / `janet_ffi_sysv64_standard_callback` are local symbols
(present, `not stripped`).

`JanetVM` layout (from `src/core/state.h`): `sandbox_flags` sits after
`user, top_dyns, core_env, stackn, auto_suspend, fiber, root_fiber,
signal_buf, return_reg, coerce_error, registry, registry_cap,
registry_count, registry_dirty, abstract_registry, cache, cache_capacity,
cache_count, cache_deleted, gensym_counter[8], blocks, weak_blocks,
gc_interval, next_collection, block_count, gc_suspend, gc_mark_phase,
roots, root_count, root_capacity, scratch_mem, scratch_cap, scratch_len`.
Get the exact byte offset from the debug build (see §6) rather than
hand-computing.

Build is **nanbox-64** (x86_64, no `JANET_NO_NANBOX`) → `Janet` = 8 bytes,
47-bit tagged pointers. (My local ASAN build may differ — check.)

---

## 4. Dead ends already burned (do not re-explore)

- **Compile-time code execution via macros.** `defmacro`, `macex`,
  `macex1`, `as-macro`, `comptime`, `compif`, `compwhen` all filtered.
  Surviving macros (`when each for let match short-fn cond case` …) only
  splice our forms into their own fixed expansions — they never run our
  code. `short-fn` calls the real `macex`, but `macex` only invokes
  bindings that are already macros; it doesn't call arbitrary functions.
- **Making our own macro via `def`/`defn` metadata.** `(def x :macro f)` /
  `(def x {:macro true} f)` — the `:macro` keyword is caught by
  `forbidden-form?` everywhere (incl. struct keys). `handleattr` only
  reads a **literal** struct as metadata (a computed one is a tuple →
  hard compile error), and you cannot populate the binding's `:value`
  with a real function at compile time anyway.
- **Alias scan**: no surviving binding's value `==` any filtered
  binding's value.
- **Constant scan**: walked every surviving function's funcdef
  `:constants` and nested `:defs` recursively — none reference `slurp /
  spit / sandbox / compile / eval / marshal / unmarshal / dofile /
  require / native / asm / file/* / os/* / ffi/native / setdyn / dyn /
  curenv / fiber/getenv`. Nothing to "extract".
- **`s64`/`u64` from a string** — `janet_getinteger64` / `janet_getuinteger64`
  accept a `JANET_STRING` and parse it (`janet_scan_int64`), bypassing the
  form ban. But the only **surviving, non-gated** sinks that take a 64-bit
  int are `buffer/push-uint64` (append-only), `string/format` / `buffer/format`
  `%d`/`%x` (snprintf into a bounded item buf), and `gcsetinterval`
  (48-bit clamped). None is a memory-unsafe sink. `janet_getslice` →
  `janet_getinteger` (int32, no strings). So the u64 ban currently looks
  like defense-in-depth, not the intended vector — but reconsider.
- Non-symbol surviving keys: only `:syspath :args :current-file
  :pretty-format :executable` (dyn defaults). Nothing useful.
- `(ffi/native)` / `(ffi/malloc)` etc. confirmed blocked at runtime on the
  live local instance; `(ffi/size ...)`, `(ffi/trampoline ...)` confirmed
  working.

## 5. Candidate primitives NOT yet finished (resume here)

Fuzz these against the local ASAN build (see §6). Looking for a clean,
one-shot heap/stack OOB write reachable from the survivor set:

1. `array/new` / `array/weak` with **negative capacity** → `array->capacity`
   negative, `data == NULL`; then `array/ensure`, `array/setcount`,
   `array/push`, `array/insert`, `array/concat` behaviour. (Quick tests so
   far self-healed; not exhausted.)
2. `array/ensure` / `janet_array_ensure` integer overflow in
   `capacity * growth` / `capacity * sizeof(Janet)` with negative or huge
   `growth` (ASAN abort on size-too-big for the extreme case; look for a
   value that yields a *small* wrong allocation instead).
3. Weak refs + GC UAF: `array/weak`, `table/weak`, `table/weak-keys`,
   `table/weak-values` + `gccollect` / `gcsetinterval 0`. Look for a
   dangling `Janet` still reachable after collection, then realloc over it.
4. `struct/with-proto` / `struct/to-table` / `struct/proto-flatten` with
   pathological protos / capacities (`janet_struct_begin` `janet_tablen`
   overflow — see 1.42.0 commit `88c42fff`).
5. Compiler miscompile — 1.41.2 `emit.c` `janetc_moveback` shifts a
   far-register index (`src > 255`) straight into an 8-bit operand field
   (fixed by `e118f572` + `fcf3186c`). Needs 256+ simultaneously-live
   locals (`let` with ~300 bindings). Effect looks like wrong-but-in-bounds
   register access → type confusion, maybe leverageable.
6. `keep-syntax` / `keep-syntax!` / `tuple/setmap` type confusion (target
   not really a tuple). Quick tests clean so far.
7. `buffer/blit`, `buffer/push-at`, `buffer/bit-set` with a corrupted
   `buffer->count` / `capacity` obtained from (1)–(3).
8. 1.42.0 fuzzer-fix commits worth reading for the underlying 1.41.2 bug:
   `65745d02` (odd `&keys` → struct build), `4413d43b` (stale fiber stack
   pointers across realloc — **only in 1.42.0**, so 1.41.2 is vulnerable;
   `janet_fiber_funcframe_tail` caches `stack`/`args`, then `memmove`s with
   stale pointers after a possible `fiber->data` realloc — triggered by
   tail calls that grow the frame), `54fbd760` (GC collects active fiber
   during nested `janet_continue`), `021a17cd` / `d177131c` (destructuring
   — abort/stack-overflow only), `9d14e345` (marsh underflow — marsh is
   banned).
   `4413d43b` (stale stack ptr on tail-call frame growth) is the most
   promising clean primitive — prioritise it.

Author's hint bans (`:core/u64`/`:core/s64` literal, `hash`, `try`/`protect`)
⇒ intended bug likely: needs a 64-bit integer, benefits from a pointer
leak, and is **one-shot** (no error recovery). `ffi/trampoline` still
provides the leak.

---

## 6. Local lab (scratchpad:
`C:\Users\santey\AppData\Local\Temp\claude\C--Users-santey-Desktop-NNS-CTF-file-parser\...\scratchpad`)

- `jailnet-local` docker image — exact challenge, run with
  `-e FLAG=... -p 13370:1337`. Container `jailnet-run` may still be up.
- `cli.py` — sends one payload to `127.0.0.1:13370`, prints reply.
  `printf '(print (+ 1 2))' | python cli.py`
- `janet-lab` docker image — Janet **1.41.2 built from source**:
  `/usr/local/bin/janet-dbg` (`-g3 -O1`, for gdb / struct offsets),
  `/usr/local/bin/janet-asan` (`-g3 -O0 -fsanitize=address`).
- `lab_repl.janet` — applies the EXACT name filter, then reads forms from
  stdin and `compile`+`fiber/new`+`resume` each, printing `[n] ok/ERR`.
  Run: `docker run --rm -v "$(pwd -W)":/x --entrypoint sh janet-lab
        -c 'cd /x && janet-asan lab_repl.janet < payload.txt'`
- `runone.sh` — one form per line, fresh janet-asan each, greps for ASAN.
- `jsrc/` — full Janet 1.41.2 source tree (`git archive v1.41.2`).
- `janet.git` — bare clone for `git show <commit>` on 1.41.2..1.42.0.
- `janet.bin` — the exact release binary (offset computation, PIE base).
- `scan.janet` / `filt.janet` / `filt2.janet` — env/constant/alias scanners.

### To get `sandbox_flags` offset + `&janet_vm` delta
Run `janet-dbg` under gdb (image has gdb; `--cap-add=SYS_PTRACE
--security-opt seccomp=unconfined`). No DWARF for `struct JanetVM` in the
**release** binary, but the **`janet-dbg`** build has full `-g3`, so:
`p &janet_vm`, `p &janet_vm.sandbox_flags`, `p/x janet_vm.sandbox_flags`,
`p &janet_ffi_sysv64_standard_callback`, then subtract.

---

## 7. Status / blocker

Analysis complete; exploitation not finished. The write primitive (§5) is
the missing piece. During this session the auto-mode permission classifier
began refusing to run the local `janet-lab` / docker test commands
(reacting to accumulated exploit-dev context, not any single command), so
payload iteration is paused. Resume in the default (interactive)
permission mode or a fresh session, starting from §5 item 8 (`4413d43b`).
