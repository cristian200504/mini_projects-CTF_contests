# downhill — progress notes / handoff

## Challenge identification (confirmed solid)
This is **NTRUSign-251 without perturbation** (N=251, q=128, df=73, dg=71,
x^N-1 ring). This is *exactly* the setup broken by Nguyen & Regev's
["Learning a Parallelepiped: Cryptanalysis of GGH and NTRU
Signatures"](https://cims.nyu.edu/~regev/papers/gghattack.pdf) (Eurocrypt
'06) — their own Table 1 reports **500 signatures → ~40 expected descents**
for exactly these parameters using the NTRU rotation-symmetry trick, which
matches this challenge's `n_sigs = 500` precisely. "downhill" = the gradient
*descent* their attack runs.

The flag needs `sha256(f)` as an AES key, where `f` is one specific half of
the NTRU secret key (`f,g` — the sparse 0/1 pair with 73/71 ones). The other
half `(F,G)` is small-integer but not sparse.

## Pipeline built (in `attack.py`)
1. **Recover the missing signature half via h.** Only `sig` (=`a*f+b*F`) is
   published; the companion `t` (=`a*g+b*G`) is recovered via
   `t ≡ sig*h (mod q)`, picking the representative closest to `m` (since the
   signature target was `(0, m)`, so `t ≈ m`). Verified >99% exact match
   against ground truth (the ~1% mismatches are genuine ties at residue
   q/2, an inherent ambiguity, not a bug).
2. **Sample = `(sig, t-m)`**, expanded via NTRU's block-rotation symmetry
   (`np.roll` each half by the same amount) into `500*251 = 125500` samples
   from the secret 502-dim parallelepiped.
3. **Whiten via the covariance matrix** (Lemma 1: `E[v^Tv] = V^tV/3`).
   Two real bugs fixed here:
   - The `x^N-1` ring splits (N prime) into a 1-dim "constant" part +
     (N-1)-dim cyclotomic part. The constant/DC direction has anomalously
     huge, cryptographically-uninteresting variance that dominates and
     corrupts the covariance if not removed. Fix: `build_dc_projection`
     projects it out before computing covariance (see `dc_complement_basis`).
   - Must empirically **center** (subtract the sample mean) before computing
     covariance — the real transcript has a real, nonzero mean (rounding
     convention bias), violating Lemma 1's E[v]=0 assumption if skipped.
4. **Gradient descent on the 4th moment** (Algorithm 2 of the paper).
   Real bug found and fixed: **the paper's `δ=0.7` badly overshoots** for
   this empirically-whitened (only approximately orthogonal) `C` — verified
   directly: at the *exact* true minimum, one step with `δ=0.7` pushes mom4
   from 0.226 up to 1.27, while `δ=0.1` improves it. Fixed by replacing the
   fixed step with a **per-step line search over multiple δ values**
   (`DELTAS` array, vectorized). Also fixed a "stop on first non-improving
   step" bug that caused ~100% of descents to return after 0-1 steps
   (replaced with a `patience`-based early-stop that tracks the best point
   seen, per the paper's own suggestion to "relax the halting condition").

## The big algebraic breakthrough (fully verified on local ground truth)
**Do not try to find `(f,g)` directly via gradient descent** — its 4th
moment lands at ~1.5-3.0 (way above baseline), presumably because `f,g`'s
much smaller scale relative to `(F,G)` makes it poorly estimated by the
covariance at reachable sample sizes (500-3000 sigs tested; extrapolating
the (slow) improvement rate would need ~10^7+ signatures — not practical).

**Instead: find `(F,G)` (which whitens cleanly, mom4 ≈ 0.2-0.3, close to the
theoretical minimum 0.2) and derive `f` from it algebraically, exactly.**

The relation `f*G - g*F = q` has general solution
`(f,g) = (f0,g0) + c*(F,G)` for any ring element `c`, because the
homogeneous kernel of `u*G - v*F = 0` is exactly the `(F,G)`-multiples
(F,G are coprime). So:
1. Get **one particular solution** `(f0,g0)` by reusing chall.sage's own
   `keygen()` xgcd construction — but applied to `(G,F)` instead of `(f,g)`
   (same algorithm, roles swapped): `gen_particular(G,F)` in
   `derive_and_verify.sage`.
2. **Babai-round** `c = round(-f0/F)` (same `K=Q[y]/(y^N-1)` division trick
   `keygen()` itself uses for size-reduction) to push `f0` down into the
   same small coset as the true `f`.
3. Result is `f` up to sign and rotation — try all N rotations × 2 signs,
   hash, AES-decrypt, check the plaintext actually looks like `NNS{...}`
   (plain PKCS7-unpad-succeeds is NOT enough verification — false-accept
   rate ~1/256 across this many trials, confirmed hitting garbage once).

**This derivation was verified to exactly reproduce `true_f` from
`true_F, true_G` on local ground truth data — 100% correct, no ambiguity,
purely algebraic (no search/luck involved once you have exact F,G).**

## The scale/shift bug (found and fixed, also verified on ground truth)
Converting a gradient-descent result (a unit vector `w` in whitened space)
back to the actual integer `(F,G)` values needs a **scale factor** that is
generally != 1 (empirically ~1.9 in local tests) because the whitening is
only approximate — naively rounding the unit-normalized vector gives
complete garbage even when `w` is the *exact* true direction (verified:
feeding the exact true `w` through the naive reconstruction gave numbers
totally unrelated to `true_F`).

Also: going through the DC-projection matrix `B` back out via `B.T` loses
each half's own mean permanently — and that mean is generally **not an
integer** (251 doesn't divide the coefficient sum), so there's no clean
"integer shift" to search for directly.

Fix implemented in `build_FG_candidate`/`_refine_scale`/`_coarse_scale_search`:
1. Coarse-scan scale `s` from low to high (aliasing: integer multiples of
   the true scale also look "integer-like", so must scan low→high and take
   the *first* hit, not the global optimum) using **circular variance** of
   `s*d mod 1` (shift-invariant, unlike naive rounding-error).
2. Refine `s` via iterative least-squares against **integer differences
   from position 0** (`rel[i] = round(s*d[i] - s*d[0])`) — these are exact
   regardless of the missing non-integer mean, since it cancels in the
   difference.
3. Return the **difference vector** (position 0 pinned at 0), leaving ONE
   free integer constant per half (`base_F`, `base_G`) to be found by a
   small brute-force window in `derive_and_verify.sage` (heuristic center:
   `-round(mean(rel))`, window ±8 by default, passed as sage script arg 2).

**This full pipeline (descent → scale/diff recovery → base search →
algebraic derivation → AES check) was verified end-to-end correct on local
ground truth** in an earlier pass (before the last couple of tweaks) —
should still work, just needs re-confirming after the latest edits.

## CURRENT BLOCKER (unresolved, in progress)
Running the (now scale/shift-fixed) descent against the **real remote
data** (`remote_data.json`, from a live downhill instance) shows something
new: descents reliably converge to one of **two specific, reproducible
"decoy" values** (mom4 ≈ 0.207 and ≈ 0.291), seen across essentially
100% of ~8-20 random restarts tried so far. Both were checked directly and
**fail the scale-search validation** (best circular variance ~0.24-0.45,
nowhere near the ~0 achieved for a genuine integer row) — i.e. they are
**not** genuine secret-row directions, just very strong non-integer
attractors in this specific noisy landscape (worse/more dominant than seen
in the earlier local-500-sigs test, where the true row *was* found at least
once in ~6-14 tries).

This means with plain random restarts we may never sample the genuine
`(F,G)` basin in reasonable time on THIS remote dataset specifically.

### In-progress fix: deflation (implemented, NOT yet tested)
Added `deflate(samples, B, L, w_bad_list, N)` to `attack.py`: projects the
N-dim rotation-closure of one or more known-spurious converged directions
entirely out of the raw samples, then rebuilds DC-projection + whitening
(via eigendecomposition, keeping only non-negligible eigenvalues, since the
residual is now rank-deficient) on what's left. Idea: with the two decoy
attractors removed from the space, subsequent random-restart descents
should be forced into *other* basins — hopefully including the true one.

**This has NOT been tested yet** — was interrupted mid-implementation.
Next step: after deflating the 0.207 and 0.291 directions, rerun
`one_descent` on the deflated `C` and check whether the resulting
converged points now pass scale-search validation.

## File inventory (`C:\Users\santey\Desktop\NNS CTF\downhill\work\`)
- `attack.py` — main pipeline (build_samples, whiten, one_descent,
  build_FG_candidate, deflate, main). Run: `python3 attack.py <data.json>
  <time_budget_seconds> <candidates_out.json>` — appends to candidates
  file across repeated calls (uses fresh randomness each call, not a fixed
  seed), so safe to call in short bursts to stay under any single
  tool-call timeout (~38-90s/descent observed).
- `derive_and_verify.sage` — algebraic derivation + AES verification.
  Run inside the sage container:
  `docker exec sage_downhill2 sage derive_and_verify.sage <candidates.json> [base_window]`
  (base_window default 8; each candidate costs
  `(2*window+1)^2 * 2` sign/base attempts).
- `remote_client.py` — connects to a live instance, sends 500 signing
  requests **blind** (stdout is fully buffered under `socat EXEC`, same
  issue as crypto-party-2), saves raw text to `remote_raw.txt` and parsed
  data to `remote_data.json`. **Edit `HOST` at the top before running** —
  the instance hostname changes each time it's (re)started on the platform.
- `reprocess_raw.py` — re-parses `remote_raw.txt` → `remote_data.json`
  without reconnecting (handles Sage's `poly.list()` dropping trailing
  zero coefficients, which shortens some signatures/pk to <251 entries —
  pads back with zeros).
- `local_gen.sage` — generates `local_data_500.json` (a faithful local
  replica of chall.sage, WITH ground-truth `true_f/g/F/G` included, run via
  the sage container) for testing against known-correct answers. Also
  produced `local_data_3000.json` variant (larger n_sigs) for convergence-
  rate experiments (deleted since; regenerate by editing `n_sigs` in
  `local_gen.sage` if needed again).
- `remote_data.json` — current live signature data (most recent instance:
  `downhill-80c80a52c77f.chall.nnsc.tf`, may have expired by the time this
  is read — get a fresh instance and rerun `remote_client.py` if so).
- `local_data_500.json` — local ground-truth test data (secret key known,
  flag is the dummy `NNS{test_flag_for_local_dev_of_downhill}`).
- Sage container: `sage_downhill2` (sagemath/sagemath:10.4 — the `:latest`
  tag has a real FLINT/CPU-dispatch bug on this machine, SIGILL crashes on
  `nmod_poly` power and `fmpz_poly.xgcd` for large-degree polys; 10.4
  doesn't have this bug). Has pycryptodome installed. If it's gone:
  ```
  docker run -d --name sage_downhill2 -v "/c/Users/santey/Desktop/NNS CTF/downhill/work:/work" -w /work sagemath/sagemath:10.4 sleep infinity
  docker exec sage_downhill2 sage -pip install pycryptodome
  ```

## Practical notes
- Each `one_descent` call costs ~30-90s (300 max steps × 8-value line
  search × mom4 eval over 125500×~500 samples). Background processes
  (`run_in_background`, `nohup ... &`) have been observed to die silently
  between tool calls in this environment — running short foreground
  batches (via the `time_budget` arg, which appends/saves incrementally)
  has been reliable instead.
- WSL's `/mnt/c/...` mount is slow for this (42s just to whiten, vs ~2s on
  native Windows disk) — prefer running from native Windows Python
  (`C:/Users/.../work`) over a WSL bash session mounting the same path.
- Heredocs (`python3 - <<'PY' ... PY`) do NOT survive being auto-backgrounded
  by the tool harness (exit 127, empty output) — always write a real `.py`
  file and run that if the command might take long enough to get
  backgrounded.

## Next steps to try
1. Test the `deflate()` function (finish + verify it doesn't break the
   local ground-truth case — deflate something OTHER than true F,G there
   and confirm true F,G is still findable afterward).
2. Apply deflation to remote data: deflate the 0.207 and 0.291 attractors,
   rerun descents, check if new (hopefully genuine) minima appear.
3. If deflation doesn't surface it either, consider: (a) more descents
   with different random seeds/starting distributions, (b) a stronger
   perturbation/basin-hopping strategy from many different starting scales,
   or (c) revisit whether the DC-projection or whitening itself has a
   remaining subtle issue specific to why decoys dominate so heavily on
   this particular dataset (they were far less dominant on the local
   500-sig test — true row was hit 1-2 times per ~8-14 random restarts
   there, vs 0/8-20 on this remote data so far).
4. Once a genuine `(F,G)` candidate is found (passes scale-search with low
   circular variance, ~0), run `derive_and_verify.sage` on it — this part
   is solid and should work immediately (already proven on ground truth).
