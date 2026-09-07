"""
Nguyen-Regev "Learning a Parallelepiped" attack on NTRUSign-251 (no perturbation).
Reference: Nguyen & Regev, "Learning a Parallelepiped: Cryptanalysis of GGH
and NTRU Signatures", Eurocrypt 2006 / J. Cryptology 2009.
https://cims.nyu.edu/~regev/papers/gghattack.pdf

Pipeline (Algorithm 1 + 2 from the paper, using NTRU's rotation symmetry
from Section 3 / Table 1 to turn 500 signatures into 500*N samples):
  1. From each (message, signature) pair, recover the missing companion
     coordinate t via the public key h (t == sig*h mod q, representative
     chosen closest to m, since (sig,t) is close to the target (0,m)).
  2. sample = (sig, t - m); this lies in the secret parallelepiped.
  3. Expand via the N block-rotations of NTRU lattices -> N samples/signature.
  4. Approximate the Gram matrix, Cholesky-whiten into a hypercube.
  5. Gradient descent on the empirical 4th moment (kurtosis) to find hypercube
     directions; map back through the whitening transform; round to integers.
  6. Identify which recovered row is (a rotation of) f, verify via AES-ECB
     decryption of ct with sha256(f) as key.
"""
import json
import sys
import time
from hashlib import shake_256, sha256

import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def cyc_conv_mat(a, b, N):
    """Vectorized cyclic convolution using FFT-free wrap (fast for many calls)."""
    conv = np.convolve(a, b)
    if len(conv) <= N:
        out = np.zeros(N, dtype=np.int64)
        out[: len(conv)] = conv
        return out
    head = conv[:N].copy()
    tail = conv[N:]
    k = len(tail)
    idx = np.arange(k) % N
    np.add.at(head, idx, tail)
    return head


def get_m(msg: bytes, N):
    digest = shake_256(msg).digest(N)
    return np.array([c & 127 for c in digest], dtype=np.int64)


def recover_t(sig, h, m, q, N):
    r = cyc_conv_mat(sig, h, N) % q  # residue in [0, q)
    # pick the representative of r (mod q) closest to m (since t approx m)
    t = m + (((r - m) + q // 2) % q - q // 2)
    return t


def build_samples(data):
    N, q = data["N"], data["q"]
    h = np.array(data["pk_h"], dtype=np.int64)
    n_sigs = len(data["sigs"])

    sig_mat = np.zeros((n_sigs, N), dtype=np.int64)
    dev_mat = np.zeros((n_sigs, N), dtype=np.int64)  # t - m

    for i, entry in enumerate(data["sigs"]):
        sig = np.array(entry["sig"], dtype=np.int64)
        msg = bytes.fromhex(entry["msg"])
        m = get_m(msg, N)
        t = recover_t(sig, h, m, q, N)
        sig_mat[i] = sig
        dev_mat[i] = t - m

    # base samples: (sig, t-m), shape (n_sigs, 2N)
    base = np.concatenate([sig_mat, dev_mat], axis=1).astype(np.float64)

    # expand via the N block-rotations (Section 3 / Whyte's observation):
    # sigma(x1..xN,y1..yN) = (xN,x1..x_{N-1}, yN,y1..y_{N-1}) == roll each half by 1
    samples = np.empty((n_sigs * N, 2 * N), dtype=np.float64)
    xs = base[:, :N]
    ys = base[:, N:]
    for r in range(N):
        rx = np.roll(xs, r, axis=1)
        ry = np.roll(ys, r, axis=1)
        samples[r * n_sigs:(r + 1) * n_sigs, :N] = rx
        samples[r * n_sigs:(r + 1) * n_sigs, N:] = ry

    return samples, N, q, h


def dc_complement_basis(N):
    """
    Orthonormal (N, N-1) basis spanning the orthogonal complement of the
    all-ones vector in R^N (via QR).
    """
    ones = np.ones((N, 1)) / np.sqrt(N)
    M = np.concatenate([ones, np.eye(N)], axis=1)
    Q, _ = np.linalg.qr(M)
    return Q[:, 1:N]  # (N, N-1), orthogonal to ones, orthonormal columns


def build_dc_projection(N):
    """Block-diagonal (2N, 2(N-1)) matrix projecting out the rotation-invariant
    'DC' direction of each half (x^N-1 = (x-1)*Phi_N(x) for prime N splits the
    ring into a 1-dim constant part + an (N-1)-dim cyclotomic part; the DC part
    has anomalously large, cryptographically-uninteresting variance that
    otherwise dominates and corrupts the covariance/whitening)."""
    Bn = dc_complement_basis(N)
    B = np.zeros((2 * N, 2 * (N - 1)))
    B[:N, : N - 1] = Bn
    B[N:, N - 1:] = Bn
    return B


def whiten(samples, B):
    # Project out the DC/rotation-invariant direction of each half (see
    # build_dc_projection), then empirically center (standard ICA/HPP
    # preprocessing; Lemma 1 assumes E[v]=0, but the real transcript has a
    # nonzero mean from the rounding convention).
    proj = samples @ B  # (n_samp, 2(N-1))
    mean = proj.mean(axis=0)
    centered = proj - mean
    n_samp, dim = centered.shape
    G = 3.0 * (centered.T @ centered) / n_samp  # Lemma 1
    Ginv = np.linalg.inv(G)
    # Cholesky of G^{-1} = L L^T (numpy gives lower-triangular L)
    L = np.linalg.cholesky(Ginv)
    C = centered @ L  # samples of the (approx) hypercube
    return C, L, mean


def deflate(samples, B, L, w_bad_list, N):
    """Project the N-dim rotation-closure of one or more spurious converged
    directions out of the raw samples entirely, then rebuild the DC
    projection + whitening on the residual. Some real-world landscapes here
    have a small number of very strong non-secret-row attractors that
    capture nearly all random restarts (confirmed empirically: they fail
    the scale-search validation, i.e. they aren't genuine integer lattice
    rows) -- removing them lets subsequent descents reach other basins,
    including hopefully the true secret rows, instead of just re-finding
    the same decoys every time."""
    Linv = np.linalg.inv(L)
    cols = []
    for w_bad in w_bad_list:
        v_full = (w_bad @ Linv) @ B.T  # (2N,) approx row in original space
        first, second = v_full[:N], v_full[N:]
        for r in range(N):
            cols.append(np.concatenate([np.roll(first, r), np.roll(second, r)]))
    Q, _ = np.linalg.qr(np.array(cols).T)  # (2N, <= N*len(w_bad_list)) orthonormal
    residual = samples - (samples @ Q) @ Q.T

    proj = residual @ B
    mean = proj.mean(axis=0)
    centered = proj - mean
    n_samp = centered.shape[0]
    G = 3.0 * (centered.T @ centered) / n_samp
    vals, vecs = np.linalg.eigh(G)
    keep = vals > 1e-6 * vals.max()
    vals_k, vecs_k = vals[keep], vecs[:, keep]
    Linv_half = vecs_k @ np.diag(1 / np.sqrt(vals_k))
    C = centered @ Linv_half
    return C, Linv_half, mean, Q


def mom4(C, w):
    proj = C @ w
    return np.mean(proj ** 4)


def grad_mom4(C, w, n_samp):
    proj = C @ w
    return 4.0 * (C.T @ (proj ** 3)) / n_samp


DELTAS = np.array([1.0, 0.5, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001])


def one_descent(C, max_steps=300, patience=25, rng=None):
    """Run gradient steps with a per-step line search over DELTAS (a fixed
    delta=0.7 as in the paper turns out to badly overshoot for this
    empirically-whitened, only-approximately-orthogonal C -- confirmed
    directly: at the true minimum itself, delta=0.7 pushes mom4 from 0.226
    up to 1.27, while delta=0.1 improves it. A fixed small delta is instead
    too slow to reach the (narrow) true-row basin from a random start, so we
    line-search each step: try several deltas at once (vectorized), keep
    whichever improves most. Track and return the best point seen; stop
    early only after `patience` consecutive non-improving steps."""
    n_samp, dim = C.shape
    rng = rng or np.random.default_rng()
    w = rng.standard_normal(dim)
    w /= np.linalg.norm(w)
    best_w, best_val = w, mom4(C, w)
    cur_w, cur_val = w, best_val
    stale = 0
    for _ in range(max_steps):
        g = grad_mom4(C, cur_w, n_samp)
        # all deltas' candidates at once: (dim, n_deltas)
        cands = cur_w[:, None] - DELTAS[None, :] * g[:, None]
        cands /= np.linalg.norm(cands, axis=0, keepdims=True)
        proj = C @ cands  # (n_samp, n_deltas)
        vals = np.mean(proj ** 4, axis=0)  # (n_deltas,)
        i = np.argmin(vals)
        if vals[i] >= cur_val:
            break
        cur_w, cur_val = cands[:, i], vals[i]
        if cur_val < best_val - 1e-9:
            best_w, best_val = cur_w, cur_val
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    return best_w, best_val


def try_fg_pattern(w_approx, L, B, N, q, ct):
    """w_approx: approx unit vector in the (DC-projected) hypercube space.
    Map back through L^-1 and B^T, then search a small integer shift per half
    (the DC component we project out) for an exact 0/1 sparse row matching
    the f/g pattern directly. (Kept as a fallback; in practice f,g doesn't
    whiten cleanly at reachable sample sizes -- see build_candidate below.)"""
    v_reduced = w_approx @ np.linalg.inv(L)  # (2(N-1),)
    v_full = v_reduced @ B.T  # (2N,), zero mean per half by construction

    first = v_full[:N]
    second = v_full[N:]

    for half in (first, -first, second, -second):
        for shift in range(-3, 4):
            cand = np.round(half + shift).astype(np.int64)
            ones = np.sum(cand == 1)
            zeros = np.sum(cand == 0)
            if ones + zeros == N and 60 <= ones <= 85:
                for r in range(N):
                    rot = np.roll(cand, r)
                    key = sha256(bytes(int(c) for c in rot)).digest()
                    try:
                        pt = AES.new(key, AES.MODE_ECB).decrypt(ct)
                        flag = unpad(pt, 16)
                        return flag
                    except Exception:
                        continue
    return None


def _refine_scale(d_half, s0, iters=60):
    """Given a fixed direction d_half and an initial scale guess s0, refine
    s so that s*d_half lands as close as possible to SOME integer vector,
    up to an unknown additive constant (the DC component B projects out has
    a real, generally non-integer value -- row.mean() need not be an
    integer since N=251 doesn't divide the row's coefficient sum -- so we
    fit against INTEGER DIFFERENCES from position 0, which are exact
    regardless of that constant, rather than trying to round the raw
    values or their mean directly)."""
    s = s0
    for _ in range(iters):
        raw = s * d_half
        rel = np.round(raw - raw[0])
        target = rel - rel.mean()
        centered = d_half - d_half.mean()
        denom = np.dot(centered, centered)
        if denom == 0:
            break
        s_new = np.dot(centered, target) / denom
        if abs(s_new - s) < 1e-13:
            s = s_new
            break
        s = s_new
    return s


def _coarse_scale_search(d_half, lo=0.3, hi=8.0, step=0.002, threshold=0.15):
    """Find the smallest scale s in [lo,hi) making s*d_half look
    integer-lattice-like (up to a constant), via circular variance of the
    fractional part -- scanned low-to-high since integer multiples of the
    true scale are aliases that also look integer-like. Returns None if no
    scale in range gets even roughly close (this direction is very likely
    not a genuine lattice row at all -- e.g. a spurious local minimum of
    the noisy landscape rather than the true secret row). The threshold is
    deliberately lenient: an imperfectly-converged descent can still be
    useful, and the expensive exact algebraic derivation downstream is the
    real, unforgiving arbiter of correctness -- this is just a cheap filter
    to avoid feeding it obvious garbage."""
    for s in np.arange(lo, hi, step):
        v = s * d_half
        ang = 2 * np.pi * v
        cvar = 1 - np.abs(np.mean(np.exp(1j * ang)))
        if cvar < threshold:
            return s
    return None


def build_FG_candidate(w_approx, L, B, N):
    """Map a hypercube-space unit vector back to TWO (N,) integer
    *difference* vectors (rel_F, rel_G), each exact up to one unknown
    additive integer constant per half (recovered separately, e.g. via
    brute force in derive_and_verify.sage) -- see _refine_scale's docstring
    for why the constant can't be pinned down here. Returns (None, None) if
    either half's scale search fails to lock onto an integer lattice at
    all -- this descent converged to a spurious point in the (empirically
    noisy) 4th-moment landscape, not a genuine secret-row direction, and
    forcing a "candidate" out of it just produces near-zero garbage."""
    v_reduced = w_approx @ np.linalg.inv(L)
    d = v_reduced @ B.T
    d1, d2 = d[:N], d[N:]

    s1_0 = _coarse_scale_search(d1)
    s2_0 = _coarse_scale_search(d2)
    if s1_0 is None or s2_0 is None:
        return None, None

    s1 = _refine_scale(d1, s1_0)
    s2 = _refine_scale(d2, s2_0)

    first_i = np.round(s1 * d1 - s1 * d1[0]).astype(np.int64)
    second_i = np.round(s2 * d2 - s2 * d2[0]).astype(np.int64)
    return first_i, second_i


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "local_data.json"
    time_budget = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    out_path = sys.argv[3] if len(sys.argv) > 3 else "fg_candidates.json"

    with open(path) as f:
        data = json.load(f)

    # append mode: reload any candidates already found by a previous call
    # (this script is meant to be invoked repeatedly with a short
    # time_budget each time, so a single call always fits comfortably
    # inside one foreground tool-call timeout).
    candidates = []
    try:
        with open(out_path) as fp:
            candidates = json.load(fp).get("candidates", [])
    except FileNotFoundError:
        pass

    t0 = time.time()
    samples, N, q, h = build_samples(data)
    print(f"built {samples.shape[0]} samples x {samples.shape[1]} dim in {time.time()-t0:.1f}s", flush=True)

    B = build_dc_projection(N)
    t0 = time.time()
    C, L, mean = whiten(samples, B)
    print(f"whitened in {time.time()-t0:.1f}s", flush=True)

    ct = bytes.fromhex(data["ct"])
    rng = np.random.default_rng()  # fresh randomness each call, not a fixed seed

    i = 0
    t0 = time.time()
    while time.time() - t0 < time_budget:
        i += 1
        w, val = one_descent(C, rng=rng)
        # cheap direct fallback check (won't normally hit, see writeup)
        flag = try_fg_pattern(w, L, B, N, q, ct)
        if flag is not None:
            print(f"[{i}] DIRECT SUCCESS after {time.time()-t0:.1f}s: {flag}")
            return

        first_i, second_i = build_FG_candidate(w, L, B, N)
        # only keep candidates whose scale search actually locked onto an
        # integer lattice AND whose resulting range looks plausible
        # (F,G had range roughly -10..10 in our local tests)
        kept = (first_i is not None
                and np.max(np.abs(first_i)) <= 40 and np.max(np.abs(second_i)) <= 40
                and np.max(first_i) > np.min(first_i)  # reject degenerate all-equal (e.g. all-zero)
                and np.max(second_i) > np.min(second_i))
        if kept:
            candidates.append({"F": first_i.tolist(), "G": second_i.tolist(), "mom4": float(val)})

        elapsed = time.time() - t0
        print(f"[{i}] mom4={val:.4f} kept={kept} total_kept_all_time={len(candidates)} "
              f"({elapsed:.1f}s / {time_budget:.0f}s budget)", flush=True)

        with open(out_path, "w") as fp:
            json.dump({"N": N, "q": q, "ct": data["ct"], "candidates": candidates}, fp)
    print(f"time budget exhausted after {i} descents this call; {len(candidates)} candidates total in {out_path}")
    print(f"wrote {len(candidates)} candidates to {out_path}")


if __name__ == "__main__":
    main()
