# Purgatory - Reverse Engineering Writeup & In-Depth Solution

## Overview
- summary: The challenge hinges on Erlang BEAM virtual machine hot code reloading semantics.
- Category: Reverse Engineering
- Platform: Erlang / BEAM VM (OTP 28)
- Remote Instance: `welcome ncat --ssl purgatory-da8b8ebf1fbc.chall.nnsc.tf 1337`
- Flag: `NNS{soft_pur63_w0Uld_h4ve_real1y_s4ved_y0u_th3R3}`

---

## 1. Background & Vulnerability Analysis

In `purgatory_runner.erl`:
```erlang
run([OldPath, NewPath]) ->
    load(OldPath),
    Worker = purgatory:boot(),
    load(NewPath),
    io:put_chars("purgatory validator\n"),
    prompt(Worker);
```

1. `load(OldPath)` loads `old.beam` into the BEAM runtime as module `purgatory`.
2. `purgatory:boot()` spawns a resident actor process running `purgatory:loop/0`.
3. `load(NewPath)` hot-reloads `new.beam` as module `purgatory`.

According to Erlang's code reloading rules:
- Local calls (e.g. `validate(Input)`) execute inside the code version the process was created with (`old.beam`) unless explicitly qualified as external (`?MODULE:loop()`).
- External calls (e.g. `purgatory:second_half(Input, Fun)`) always resolve to the latest loaded version (`new.beam`).

---

## 2. BEAMDisassembly Details

Disassembling old.beam and new.beam reveals:
1. `validate/1` (old version):
   - Checks byte size is exactly 25.
   - Makes a local call to `first_half/1` (from `old.beam`).
   - Creates a fun object (function closure) for `mask/2` (from `old.beam`).
   - Makes an external call `{extfunc, purgatory, second_half, 2}` which executes in `new.beam`!

2. `the fun passed`:
   - Because the fun was created in `old.beam`, it uses `old.mask` table.

3. `new.beam`'s second_half/2` calls `PlaceholderFun(Idx, Byte)` for indices 13..24 and checks the masked value with new affine coefficients.

---

## 3. Recovering the Passphrase

** First Half (indices 0..12) **: old.beam affine congruences map to:
  `0ld_c0d3_w1n5_`

** Second Half (indices 13..24) **: new.beam affine congruences mapped with old.beam XOR mask table map to:
  `1n_th3_3nd!`

** Combined Passphrase **:
  `0ld_c0d3_w1n5_1n_th3_3nd!`

---

## 4. Running the Solution

Simply run: `python solve.py`
` NNS{soft_pur63_w0Uld_h4ve_real1y_s4ved_y0u_th3R3}`
