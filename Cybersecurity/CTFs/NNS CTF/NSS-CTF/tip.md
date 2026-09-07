# NSS CTF 2026 — `crypto_nss-ctf` — progress notes

## Files
- `crypto_nss-ctf/challenge.sage` — key-gen + signing (SageMath).
- `crypto_nss-ctf/output.py` — the data we get: `pk` (256 ints), `sigs` (10 × `(m_i, sig_i)`), `ct` (hex).
- Goal: decrypt `ct` (AES-128-ECB). Key = `sha256(bytes(f[i] % 256 for i in range(256)))`, so **we must recover the private polynomial `f` exactly** (its 256 centered integer coefficients).

## What the scheme is
A **pqNTRUSign / NTRU-lattice signature** in `R = Z[x]/(x^256+1)`, `q = 367`, `p = 3`.

Key-gen:
- `u = ternary(90, 91)`  (90 `+1`, 91 `-1`; a small secret shared by `f` and `g`)
- `f = u + 3·ternary(88)`   → coeffs in `[-4,4]`, `||f|| ≈ 42`
- `g = u + 3·ternary(60)`   → `||g|| ≈ 35`
- public `h = g / f mod q`  (this is `pk`)
- `f` is a unit in `R_q`; `u` is a unit in `R_3`.

Sign(m):  `y = center(u^-1 · m mod 3)`, `z = ternary(96)`, `w = y + 3z + e'` (e' a small mod-3 correction),
returns `sig = f · w mod q`.
So each transcript entry is **`sig_i = f · w_i mod q` with `w_i` small (`||w_i|| ≈ 44`, coeffs in `[-5,5]`).**
There is **no rejection sampling / no norm bound on `w`**, so the transcript leaks the key.

## The intended attack (lattice)

`f` is a unit, so `w_i = f^-1 · sig_i mod q` is uniquely determined and *small*.
Pick a pivot `sig_0` (unit) and set `R_t = sig_t · sig_0^{-1} mod q`.  Then for the true `w`'s:

```
w_t  ≡  R_t · w_0   (mod q)     for t = 1..K-1
```

Build the lattice (dimension `D = K·256`)

```
rows j=0..255 :  [ x^j | R_1·x^j mod q | R_2·x^j mod q | ... ]     (the "w_0 = x^j" generators)
q·I blocks    :  [  0  |     q·I       |      0        | ... ]  ...
```

The vector `(w_0, w_1, …, w_{K-1})` (and all 256 rotations `x^j·(…)`) is an unusually short
dense rank-256 sublattice.  Gap vs. Gaussian heuristic:

| K | dim | gap  | BKZ block needed (est.) |
|---|-----|------|--------------------------|
| 2 | 512 | ~1.8 | 40–55  (basically full NTRU) |
| 3 | 768 | ~4.5 | ~30 |
| 4 |1024 | ~7.4 | ~20 |
| 6 |1536 | ~12  | ~15 (but LLL is heavy) |

**Endgame once any short vector `v` is found:** `v`'s first 256 coords `= ± x^j · w_0`.
Compute `f_cand = v0^{-1} · sig_0 mod q` (ring inverse) → this is `± x^{-j} · f` (small, coeffs `[-4,4]`).
Then brute-force all `512` candidates `± x^t · f_cand`, derive the AES key, decrypt, and keep the
one whose plaintext starts `NNS{` and has valid PKCS#7 padding.  (Sanity filter: `g_cand = h·f_cand`
must also be small, and `f ≡ g (mod 3)`.)

### Alternative attack from `pk` alone (no signatures) — noted, not yet used
`h(1) = 1`, and `(h-1)·f = g-f = 3(rg-rf)` *exactly* (no mod-q wrap, since `|g-f| ≤ 6`).
- `(h-1)·u ≡ 0 (mod 3)` ⇒ `u ∈ ker(h-1)` in `R_3`.  `x^256+1` splits into 2 deg-128 irreducibles
  over GF(3), so that kernel is a 128-dim GF(3)-subspace; `||u|| ≈ 13.5 ≈ 1.26·GH`, so `u` is not
  cleanly isolable by SVP alone (needs the exact ternary weights 90/91 as extra constraints).
- With `H' = 3^{-1}(h-1) mod q`: `(f, rg-rf) ∈ L_{H'}`, norm ≈ 45, gap ≈ 2.33 in dim 512.
- If `u` is recovered: `rg ≡ h·rf + 3^{-1}(h-1)u (mod q)` ⇒ Kannan-embed BDD, dim 513, gap ≈ 4.4.

The K=3/K=4 signature lattice is the cleanest path.

## Environment / tooling status

- Host is Windows; **WSL2 "Kali"** has `python3.13`, `numpy`, `pycryptodome`, `g++`, `make` (no sudo).
- `pip install --user --break-system-packages fpylll cysignals` → installs, **but is flaky**:
  - `LLL.reduction(A, method="fast"/default, float_type="double")` → SIGSEGV via cysignals.
  - `method="proved", float_type="ld"` works on dim 512 (~4.6 min) but on dim ≥ 768 throws
    `ReductionError: infinite loop in babai` (needs `float_type="mpfr", precision≥160`).
  - Running **multiple fpylll jobs in parallel reliably crashes them** (mem/signal). Run ONE at a time.
  - `BKZ.DEFAULT_STRATEGY` → `RuntimeError: Cannot open strategies file` (wheel ships no strategies json).
    Use `BKZ.Param(block_size=b, flags=BKZ.AUTO_ABORT|BKZ.MAX_LOOPS)` with **no** `strategies=`.
- **Built the `fplll` CLI from source** (robust, no cysignals):  `/tmp/fplll-5.5.0/fplll/fplll`
  - libs at `/tmp/fplll-5.5.0/fplll/.libs/` ; MPFR headers/libs extracted locally to `/tmp/localroot`.
  - run as e.g. `LD_LIBRARY_PATH=/tmp/fplll-5.5.0/fplll/.libs:/tmp/localroot/usr/lib/x86_64-linux-gnu \
    /tmp/fplll-5.5.0/fplll/fplll -a bkz -b 25 -f mpfr -p 200 < basis.txt`
    (matrix format: `[[a b c]\n[d e f]\n]`).

## Scripts (in the session scratchpad)
`…/scratchpad/solve.py`  — full pipeline: parse → ring math (negacyclic mul, mod-q Gauss inverse) →
build K-block lattice → LLL/BKZ (fpylll) → extract `f` → brute 512 rotations → decrypt.
Params: `python3 solve.py <K> <float_type> <method>`. Caches the reduced basis to `/tmp/lll_K<K>.pkl`
after every stage so a crashed BKZ can resume.

## Where I stopped
- K=2 (dim 512): LLL done, min norm still 367; needs deep BKZ — abandoned (gap too small).
- **K=4 (dim 1024): wrapper-LLL completed OK (~11.5 min), cached.** Then died at `BKZ.Param`
  because of the missing-strategies-file bug. **Next:** re-run the BKZ stage (from the K=4 cache)
  with `BKZ.Param(block_size=b, flags=AUTO_ABORT|MAX_LOOPS)` (no strategies), or feed the cached
  basis to the `fplll` CLI with `-a bkz -b 20..30 -f mpfr -p 200`.
- Expectation: K=4 has gap ≈ 7.4, so BKZ ≈ 20 should surface the short vector; then the 512-way
  brute-force decrypt yields the flag `NNS{…}`.

## Continuation notes

The solver confirmed that the archive contents and the extracted challenge files match the data used by the cached K=4 lattice basis. This matters because a reduced basis from different signatures would produce meaningless candidate keys.

The solver reviewed the challenge source and corrected one detail in the earlier notes: SHA-256 produces a 32-byte key, so the ciphertext is encrypted with AES-256 in ECB mode rather than AES-128. The block size is still 16 bytes.

The original recovery script was copied into the challenge directory as `solve.py` and made self-contained. It now reads `crypto_nss-ctf/output.py` relative to the challenge directory, parses its literal assignments without executing the file, and uses a polynomial extended-Euclidean inverse instead of a full 256-by-256 modular Gaussian elimination for every candidate. The new inversion routine was checked by multiplying a signature polynomial by its computed inverse and obtaining one in the quotient ring.

The solver strengthened the candidate validation. A recovered private polynomial is accepted only if all of the following hold:

- its coefficients and the derived public companion polynomial have the expected small ranges;
- both polynomials reduce to the same ternary polynomial modulo 3;
- that shared polynomial contains exactly 90 coefficients equal to 1 and 91 equal to -1;
- the two independent ternary additions have exactly the key-generation weights 88 and 60;
- the private polynomial reconstructs every one of the ten supplied signatures from the recovered short signing vectors;
- AES decryption has valid PKCS#7 padding and starts with the expected `NNS{` prefix.

An independent `verify.py` was added. After recovery, it checks the public-key equation, exact key-generation weights, all ten signature equations, the AES padding, and an encrypt-after-decrypt round trip. Successful recovery will write the plaintext to `flag.txt` and the private data and signing vectors to `recovered.json` so the result is reproducible rather than based only on a recognizable-looking plaintext.

The cached 1024-dimensional K=4 basis was inspected. Its first 768 rows still included many trivial vectors of norm 367, while the remaining rows were much longer, showing that the previous LLL stage had not yet exposed the hidden short rank-256 sublattice. The existing BKZ-20 reduction was therefore left running.

The solver also built the `flatter` lattice reducer locally and launched it on a copy of the same checkpoint. This gives a faster independent reduction path while preserving the long-running fplll BKZ job. The resulting basis is saved as `basis_K4.pkl` in the challenge directory and is passed through the same strict extraction and verification pipeline.

At the time of this update, the recovery and verification code is complete, but no candidate private polynomial or flag has yet passed the checks. The active work is the computational lattice-reduction stage. Additional parallel work is testing higher-sample signature lattices and algebraic alternatives in case they reach the short signing-vector sublattice faster.
