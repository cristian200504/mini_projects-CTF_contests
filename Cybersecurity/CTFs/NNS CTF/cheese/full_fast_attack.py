"""FFT-accelerated Nguyen--Regev descent for the downhill challenge.

This keeps all 502 coordinates when whitening.  Removing the two DC
coordinates turns the genuine parallelepiped into a zonotope and produces
spurious fourth-moment minima; the full, well-conditioned eigensystem avoids
that loss of structure.  Cyclic rotations are evaluated analytically with
FFTs, so one descent is much cheaper than the dense expanded-sample version.
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

from fast_validate import FastMoment, slow


DELTAS = np.array([1.0, 0.7, 0.5, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001])


def full_whitener(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = samples.mean(axis=0)
    centered = samples - mean
    gram = 3.0 * (centered.T @ centered) / len(samples)
    values, vectors = np.linalg.eigh(gram)
    if values[0] <= 0:
        raise RuntimeError(f"non-positive covariance eigenvalue {values[0]}")
    L = vectors @ np.diag(1.0 / np.sqrt(values)) @ vectors.T
    return L, mean, values


def moment_only(engine: FastMoment, w: np.ndarray) -> float:
    return float(np.mean(engine.dots(w) ** 4))


def one_descent(engine: FastMoment, rng: np.random.Generator, max_steps: int = 500) -> tuple[np.ndarray, float, int]:
    width = engine.L.shape[0]
    w = rng.standard_normal(width)
    w /= np.linalg.norm(w)
    value, gradient = engine.moment_gradient(w)
    best_w, best_value = w.copy(), value

    for step in range(1, max_steps + 1):
        candidates = w[None, :] - DELTAS[:, None] * gradient[None, :]
        candidates /= np.linalg.norm(candidates, axis=1, keepdims=True)
        values = np.array([moment_only(engine, candidate) for candidate in candidates])
        choice = int(np.argmin(values))
        if values[choice] >= value - 1e-12:
            return best_w, best_value, step
        w = candidates[choice]
        value, gradient = engine.moment_gradient(w)
        if value < best_value:
            best_w, best_value = w.copy(), value
    return best_w, best_value, max_steps


def build_candidate(w: np.ndarray, L_inv: np.ndarray, N: int) -> tuple[np.ndarray | None, np.ndarray | None]:
    d = w @ L_inv
    first, second = d[:N], d[N:]
    s_first = slow._coarse_scale_search(first)
    s_second = slow._coarse_scale_search(second)
    if s_first is None or s_second is None:
        return None, None
    s_first = slow._refine_scale(first, s_first)
    s_second = slow._refine_scale(second, s_second)
    F = np.round(s_first * first - s_first * first[0]).astype(np.int64)
    G = np.round(s_second * second - s_second * second[0]).astype(np.int64)
    return F, G


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "remote_data.json")
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    out = Path(sys.argv[3] if len(sys.argv) > 3 else "full_candidates.json")
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else None

    data = json.loads(path.read_text())
    samples, N, q, _h = slow.build_samples(data)
    base = samples[: len(data["sigs"])].copy()
    L, mean, values = full_whitener(samples)
    print(f"prepared full {2*N}D whitening; cond={values[-1]/values[0]:.2e}", flush=True)
    del samples
    gc.collect()

    engine = FastMoment(base, np.eye(2 * N), L, mean)
    L_inv = np.linalg.inv(L)
    rng = np.random.default_rng(seed)
    candidates: list[dict[str, object]] = []
    if out.exists():
        saved = json.loads(out.read_text())
        candidates = saved.get("candidates", [])

    started = time.time()
    attempt = 0
    best_seen = float("inf")
    while time.time() - started < seconds:
        attempt += 1
        w, value, steps = one_descent(engine, rng)
        best_seen = min(best_seen, value)
        F, G = build_candidate(w, L_inv, N)
        kept = (
            F is not None
            and G is not None
            and np.max(np.abs(F)) <= 50
            and np.max(np.abs(G)) <= 50
            and np.ptp(F) > 0
            and np.ptp(G) > 0
        )
        if kept:
            candidates.append({"F": F.tolist(), "G": G.tolist(), "mom4": float(value)})
            out.write_text(json.dumps({"N": N, "q": q, "ct": data["ct"], "candidates": candidates}))
        print(
            f"[{attempt}] mom4={value:.6f} steps={steps} kept={kept} "
            f"best={best_seen:.6f} elapsed={time.time()-started:.1f}s",
            flush=True,
        )

    out.write_text(json.dumps({"N": N, "q": q, "ct": data["ct"], "candidates": candidates}))
    print(f"finished {attempt} descents; {len(candidates)} candidates saved to {out}")


if __name__ == "__main__":
    main()
