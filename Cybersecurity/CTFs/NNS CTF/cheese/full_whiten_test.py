"""Assess the unprojected (true parallelepiped) whitening for downhill."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from fast_validate import FastMoment, slow


def full_whitener(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = samples.mean(axis=0)
    centered = samples - mean
    gram = 3.0 * (centered.T @ centered) / len(samples)
    values, vectors = np.linalg.eigh(gram)
    if values[0] <= 0:
        raise RuntimeError(f"non-positive covariance eigenvalue {values[0]}")
    inv_sqrt = vectors @ np.diag(1.0 / np.sqrt(values)) @ vectors.T
    return inv_sqrt, mean, values


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "local_data_500.json")
    data = json.loads(path.read_text())
    samples, N, _q, _h = slow.build_samples(data)
    L, mean, values = full_whitener(samples)
    print(f"eigenvalue range {values[0]:.3e}..{values[-1]:.3e}; cond={values[-1]/values[0]:.3e}")
    C = (samples - mean) @ L
    identity_error = np.max(np.abs(3.0 * (C.T @ C) / len(C) - np.eye(2 * N)))
    print(f"whitening max covariance error {identity_error:.3e}")

    base = samples[: len(data["sigs"])].copy()
    fast = FastMoment(base, np.eye(2 * N), L, mean)
    rng = np.random.default_rng(3)
    for trial in range(2):
        w = rng.normal(size=2 * N)
        w /= np.linalg.norm(w)
        dense = C @ w
        fft = fast.dots(w).T.reshape(-1)
        dm, dg = slow.mom4(C, w), slow.grad_mom4(C, w, len(C))
        fm, fg = fast.moment_gradient(w)
        print(f"random {trial}: dots {np.max(abs(dense-fft)):.3e}; mom {abs(dm-fm):.3e}; grad {np.max(abs(dg-fg)):.3e}")

    if "true_F" in data:
        row = np.array(data["true_F"] + data["true_G"], dtype=float)
        w = row @ L
        w /= np.linalg.norm(w)
        print(f"true F/G direction mom4={fast.moment_gradient(w)[0]:.6f}")
        row = np.array(data["true_f"] + data["true_g"], dtype=float)
        w = row @ L
        w /= np.linalg.norm(w)
        print(f"true f/g direction mom4={fast.moment_gradient(w)[0]:.6f}")


if __name__ == "__main__":
    main()
