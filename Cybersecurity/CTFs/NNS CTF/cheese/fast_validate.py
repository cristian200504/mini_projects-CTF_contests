"""Validate FFT evaluation of the downhill fourth-moment objective.

`attack.py` expands every signature through all cyclic rotations.  The same
objective and gradient can be evaluated from the 500 unrotated samples with
two FFTs per sample, which makes large restart sweeps practical.  This file
first checks the formulas against the dense implementation exactly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


WORK = Path(r"C:\Users\santey\Desktop\NNS CTF\downhill\work")
sys.path.insert(0, str(WORK))
import attack as slow  # noqa: E402


class FastMoment:
    def __init__(self, base: np.ndarray, B: np.ndarray, L: np.ndarray, mean: np.ndarray):
        self.base = base
        self.B = B
        self.L = L
        self.mean = mean
        self.count, dimension = base.shape
        self.N = dimension // 2
        self.blocks = base.reshape(self.count, 2, self.N)
        self.blocks_fft = np.fft.fft(self.blocks, axis=2)
        self.W = B @ L

    def dots(self, w: np.ndarray) -> np.ndarray:
        """Return C@w in (message, rotation) order."""
        z = self.L @ w
        u = self.B @ z
        u_fft = np.fft.fft(u.reshape(2, self.N), axis=1)
        values = np.fft.ifft(
            np.sum(np.conj(self.blocks_fft) * u_fft[None, :, :], axis=1), axis=1
        ).real
        return values - self.mean @ z

    def moment_gradient(self, w: np.ndarray) -> tuple[float, np.ndarray]:
        z = self.L @ w
        dots = self.dots(w)
        powers = dots**3
        power_fft = np.fft.fft(powers, axis=1)
        # For a fixed base sample x, sum_r d[r]^3 * roll(x,r) is the
        # circular convolution d^3 * x.
        raw_gradient = np.fft.ifft(
            power_fft[:, None, :] * self.blocks_fft, axis=2
        ).real.sum(axis=0).reshape(-1) / (self.count * self.N)
        correction = self.B.T @ raw_gradient - self.mean * powers.mean()
        gradient = 4 * (self.L.T @ correction)
        return float(np.mean(dots**4)), gradient


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "remote_data.json")
    data = json.loads(path.read_text())
    samples, N, _q, _h = slow.build_samples(data)
    B = slow.build_dc_projection(N)
    C, L, mean = slow.whiten(samples, B)
    fast = FastMoment(samples[: len(data["sigs"])], B, L, mean)
    rng = np.random.default_rng(20260906)
    for trial in range(3):
        w = rng.standard_normal(C.shape[1])
        w /= np.linalg.norm(w)
        dense_dots = C @ w
        fft_dots = fast.dots(w).T.reshape(-1)
        dense_moment = slow.mom4(C, w)
        dense_gradient = slow.grad_mom4(C, w, C.shape[0])
        fast_moment, fast_gradient = fast.moment_gradient(w)
        print(
            f"trial {trial}: dot_max={np.max(np.abs(dense_dots-fft_dots)):.3e} "
            f"mom_delta={abs(dense_moment-fast_moment):.3e} "
            f"grad_max={np.max(np.abs(dense_gradient-fast_gradient)):.3e}"
        )


if __name__ == "__main__":
    main()
