# Evilgram — Solve Writeup

**Flag:** `K17{y0u_Th0ug5t_W3_w3Re_Ev1l_bUt_re4llY_we_are_JuSt_m4ss1ve_cH1cken_l0vers_w1th_a_huge_Hung3r_anD_n0th1ng_cAn_sT4nD_1n_OuR_way!!}`

## Challenge

> Evilgram is home to some of the most devious villains and evildoers. We've managed to hack
> into a suspects account, but we can't seem to find any proof of wrongdoing. They've sent some
> weird changing messages to known criminals but we haven't had any luck deciphering them. Can
> you help us crack the case?

The handout (`handout.zip`) contains a single static page, [`handout/evilgram/evilgram.html`](handout/evilgram/evilgram.html) — a mock chat app ("Evilgram") with a sidebar of contacts (Anton Chigurh, John Wick, The Boys, LIVECon Group Chat, Customer Support) and their message history baked into the HTML.

## Recon

Most threads are flavour text, but two things in the **John Wick** chat stand out:

1. John Wick pastes the *actual Python source* of an "encryption" tool he wrote for the group (a `uv run --script` one-file script using `numpy` + `plotly`), in response to Michael Myers asking for "the encryption code" (with "the validation part removed for security").
2. Right before that, "Me" sends an embedded **animated 3D Plotly voxel plot** titled `"message"` — a `Mesh3d` animation with 128 frames rendered inline in the page (`Plotly.newPlot(...)` + `Plotly.addFrames(...)` on two very long lines).

So the flag isn't hidden in HTML/JS obfuscation — it's encoded *by the algorithm in the pasted script*, and the only ciphertext we have is the rendered voxel animation. We have to reverse the whole pipeline.

## Understanding the encoder script

The pasted script does, in order:

1. **`encode_msg_to_ruleset(msg)`** — treats the message bytes as one big-endian integer `msg_num`, converts it to a [factorial number system](https://en.wikipedia.org/wiki/Factorial_number_system) (factoradic) representation with 256 digits, then uses that factoradic (as a [Lehmer code](https://en.wikipedia.org/wiki/Lehmer_code)) to deterministically build a **permutation of `0..255`** called `ruleset`. This is a bijection: message ⟷ permutation.
2. **`generateHist(ruleset, historySize=128, mapSize=4, seed=None)`** — seeds a random 4×4×4 binary grid, then runs a **reversible 3D cellular automaton** for 128 steps. Each step partitions the toroidal 4×4×4 grid into eight 2×2×2 blocks (a "Margolus neighbourhood", with the partition offset rotating every step based on `step & 1`, `step & 2`, `step & 4` — the standard trick for making a block-CA isotropic/reversible), reads each block's 8 cells as an 8-bit "block state" (0–255), and replaces it with `ruleset[state]`. Because `ruleset` is a permutation, this update is exactly invertible.
3. **`gen_plotly(...)`** — renders each of the 128 saved grid states (`hist`) as a voxel `Mesh3d` animation frame (one cube mesh per active cell) and writes it out as the HTML we're given.

The crucial comment left in the script: `# Make sure your message is reversible before sending.` — i.e. the sender has to double check the animation alone is enough to reconstruct everything, which tells us the intended solve path is: **recover `ruleset` purely from the rendered animation, then invert step 1.**

Since the CA's block update is just "look up `ruleset[state]`", and a permutation is fully determined once you've observed all 256 `(state → next_state)` pairs, we don't need to know the random seed at all — we only need enough (before, after) block-state observations across the 127 frame-to-frame transitions (8 blocks × 127 transitions ≈ 1016 samples) to see all 256 states at least once.

## Extracting the data

Plotly's `Mesh3d` frames store voxels as flat `x`/`y`/`z` vertex arrays, 8 vertices per cube (`build_voxel_mesh`/`pad_vertices` in the script). All frames are padded to the same length (`max_voxels * 8` vertices), so short frames have trailing filler.

**Gotcha:** `pad_vertices` fills unused rows with **plain `(0,0,0)`**, not the real cube shape (`cube_vertices`) offset to `(0,0,0)`. So:
- A **real** voxel at the origin still has 7 non-zero vertices (only the very first vertex is `(0,0,0)`).
- A **padding** "cube" has all 8 vertices identically `(0,0,0)`.

That distinction (not "is the coordinate `(0,0,0)`?" but "are *all 8* vertices exactly zero?") is what lets you tell real origin-voxels apart from padding. Missing this originally produced ~130 conflicting `(state → next_state)` observations; fixing it dropped conflicts to **zero** with all 256 states observed.

## Solve scripts

Three scripts in [`solve/`](solve/), run in order:

1. [`solve/extract_json.py`](solve/extract_json.py) — finds the `Plotly.newPlot(...)` / `Plotly.addFrames(...)` calls in the HTML and pulls out the embedded JSON (`data` + all 128 `frames`) via simple string-aware bracket matching (no JS engine needed).
2. [`solve/solve.py`](solve/solve.py) — reconstructs the 128 binary 4×4×4 grids from the voxel vertices (correctly separating real voxels from padding, as above), replays the CA's exact `calcBlockState` logic (copied from the pasted encoder) over every consecutive frame pair to collect `(before_state → after_state)` pairs, and assembles the full 256-entry `ruleset` permutation.
3. [`solve/decode_message.py`](solve/decode_message.py) — inverts the Lehmer-code construction: for each `ruleset[j]`, finds its index in the shrinking list `l = [0..255]` (that index is the original factoradic digit), reverses to undo the encoder's `.reverse()`, sums `digit[i] * i!` to rebuild `msg_num`, then converts back to bytes and UTF-8 decodes.

```bash
cd solve
python extract_json.py     # -> data/initial_data.json, data/frames.json
python solve.py             # -> data/mapping.json (the recovered 256-entry ruleset)
python decode_message.py    # -> prints the recovered plaintext message
```

## Result

The recovered plaintext (the message "John Wick" actually sent):

```
please i NEED the kfc recipe ASAP my local kfc closed down and I NEED MY CHICKEN K17{y0u_Th0ug5t_W3_w3Re_Ev1l_bUt_re4llY_we_are_JuSt_m4ss1ve_cH1cken_l0vers_w1th_a_huge_Hung3r_anD_n0th1ng_cAn_sT4nD_1n_OuR_way!!}
```

**Flag:** `K17{y0u_Th0ug5t_W3_w3Re_Ev1l_bUt_re4llY_we_are_JuSt_m4ss1ve_cH1cken_l0vers_w1th_a_huge_Hung3r_anD_n0th1ng_cAn_sT4nD_1n_OuR_way!!}`
