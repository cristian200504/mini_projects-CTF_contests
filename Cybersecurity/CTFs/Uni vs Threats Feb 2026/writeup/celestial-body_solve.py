#!/usr/bin/env python3
"""Solve the 'celestial-body' CTF without brute forcing any large space.

This challenge (see encrypt.py) does:
- publish epoch_hash = sha256("HH:MM:SS").hexdigest()[:16] for an unknown time
- derive LCG parameters a,b from Halley’s comet heliocentric position at that UTC time
- run an LCG mod a 512-bit prime p and broadcast 5 truncated (top-192-bit) snapshots
- step once more, derive an AES key from the final state, and encrypt the flag

We solve it by:
1) Enumerating the only 86,400 possible "HH:MM:SS" inputs to match epoch_hash.
2) Recomputing (a,b) exactly like encrypt.py using Skyfield + MPC comet elements + de421.
3) Recovering the hidden low 320 bits of the LCG state via a small lattice/CVP attack
   (LLL + Babai). No brute force over 2^320.
4) Recomputing the final state and decrypting.

Dependencies (Windows):
    py -m pip install pycryptodome sympy skyfield numpy pandas

Run:
    py solve.py --input output.txt

If MPC download is blocked, manually download:
    https://minorplanetcenter.net/iau/Ephemerides/Comets/Soft00Cmt.txt
and save it as CometEls.txt next to solve.py.

If Skyfield cannot download de421.bsp (offline), place de421.bsp next to solve.py.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Tuple

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import unpad
from Crypto.Util.number import long_to_bytes

from sympy import Matrix, Rational, ceiling, floor

# Challenge parameters
PRIME_BITS = 512
TRUNCATE_BITS = 192
UNKNOWN_BITS = PRIME_BITS - TRUNCATE_BITS  # 320
X = 1 << UNKNOWN_BITS  # 2^320


@dataclass
class ParsedTransmission:
    date_str: str
    epoch_hash: str
    p: int
    t_by_step: Dict[int, int]
    iv: bytes
    ciphertext: bytes


def _must_match(pattern: str, text: str, flags: int = 0) -> re.Match:
    m = re.search(pattern, text, flags)
    if not m:
        raise ValueError(f"Failed to parse pattern: {pattern}")
    return m


def parse_output_file(path: str) -> ParsedTransmission:
    raw = open(path, "r", encoding="utf-8").read()

    date_str = _must_match(r"Transmission Date\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", raw).group(1)
    epoch_hash = _must_match(r"epoch_hash\s*=\s*([0-9a-fA-F]{16})", raw).group(1).lower()
    p = int(_must_match(r"\bp\s*=\s*([0-9]+)", raw).group(1))

    t_by_step: Dict[int, int] = {}
    for step in (0, 4, 10, 18, 28):
        t_by_step[step] = int(_must_match(rf"t_{step}\s*=\s*([0-9]+)", raw).group(1))

    iv = bytes.fromhex(_must_match(r"iv\s*=\s*([0-9a-fA-F]+)", raw).group(1))
    ciphertext = bytes.fromhex(_must_match(r"ciphertext\s*=\s*([0-9a-fA-F]+)", raw).group(1))

    return ParsedTransmission(date_str, epoch_hash, p, t_by_step, iv, ciphertext)


def recover_time_from_epoch_hash(epoch_hash16: str) -> Tuple[int, int, int, str]:
    """Recover HH:MM:SS from sha256(time_str).hexdigest()[:16]."""
    target = epoch_hash16.lower()
    for h in range(24):
        for m in range(60):
            for s in range(60):
                t = f"{h:02d}:{m:02d}:{s:02d}"
                if hashlib.sha256(t.encode()).hexdigest()[:16] == target:
                    return h, m, s, t
    raise ValueError("No matching time found (unexpected)")


def _download(url: str, dst: str) -> None:
    print(f"[+] Downloading {url} -> {dst}")
    urllib.request.urlretrieve(url, dst)


def ensure_comet_elements(path: str = "CometEls.txt") -> str:
    """Ensure CometEls.txt exists. Tries a few MPC URLs."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    urls = [
        "https://minorplanetcenter.net/iau/Ephemerides/Comets/Soft00Cmt.txt",
        "https://www.minorplanetcenter.net/iau/Ephemerides/Comets/Soft00Cmt.txt",
        "https://minorplanetcenter.org/iau/Ephemerides/Comets/Soft00Cmt.txt",
    ]

    last_err: Exception | None = None
    for u in urls:
        try:
            _download(u, path)
            if os.path.getsize(path) > 0:
                return path
        except Exception as e:  # noqa: BLE001
            last_err = e

    raise RuntimeError(
        "Could not download CometEls.txt from MPC. "
        "Download it manually and place it next to solve.py. "
        f"Last error: {last_err}"
    )


def derive_lcg_params_from_halley(date_str: str, hour: int, minute: int, second: int) -> Tuple[int, int]:
    """Reproduce encrypt.py's load_comet_and_derive() to get (a,b)."""
    try:
        from skyfield.api import load
        from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
        from skyfield.data import mpc
    except ModuleNotFoundError as e:
        missing = getattr(e, "name", "") or "(unknown)"
        raise RuntimeError(
            "Missing dependency. Install with:\n"
            "  py -m pip install skyfield numpy pandas\n"
            f"(Python reported missing module: {missing})"
        ) from e

    y, mo, d = map(int, date_str.split("-"))

    comet_path = ensure_comet_elements("CometEls.txt")

    ts = load.timescale()
    t = ts.utc(y, mo, d, hour, minute, second)

    with load.open(comet_path) as f:
        comets = mpc.load_comets_dataframe(f)

    # IMPORTANT: encrypt.py sets the index before selecting.
    comets = comets.set_index("designation", drop=False)
    row = comets.loc["1P/Halley"]

    eph = load("de421.bsp")
    sun = eph["sun"]
    halley = sun + mpc.comet_orbit(row, ts, GM_SUN)

    astrometric = sun.at(t).observe(halley)
    x, y_, z = astrometric.position.au

    # MUST match encrypt.py exactly: underscore separators and 10 decimals.
    coord_string = f"{x:.10f}_{y_:.10f}_{z:.10f}"

    a = int.from_bytes(hashlib.sha512((coord_string + "_A").encode()).digest(), "big")
    b = int.from_bytes(hashlib.sha512((coord_string + "_B").encode()).digest(), "big")
    return a, b


def lcg_affine_jump(A: int, B: int, p: int, d: int) -> Tuple[int, int]:
    """Return (mul, add) s.t. after d steps: s' = mul*s + add (mod p)."""
    mul = pow(A, d, p)
    if A % p == 1:
        add = (B * d) % p
    else:
        inv = pow((A - 1) % p, -1, p)
        add = (B * (mul - 1) * inv) % p
    return mul, add


def _nearest_integer(q: Rational) -> int:
    if q >= 0:
        return int(floor(q + Rational(1, 2)))
    return int(ceiling(q - Rational(1, 2)))


def babai_closest_vector(B_cols: Matrix, target: Matrix) -> Tuple[Matrix, List[int]]:
    """Babai nearest-plane CVP on a full-rank lattice basis (columns)."""
    n = B_cols.cols

    # Gram–Schmidt
    Bstar: List[Matrix] = [None] * n  # type: ignore[assignment]
    mu: List[List[Rational]] = [[Rational(0) for _ in range(n)] for __ in range(n)]

    for i in range(n):
        v = B_cols.col(i)
        for j in range(i):
            mu[i][j] = (v.dot(Bstar[j])) / (Bstar[j].dot(Bstar[j]))
            v = v - mu[i][j] * Bstar[j]
        Bstar[i] = v

    y = Matrix(target)
    coeffs: List[int] = [0] * n
    for i in reversed(range(n)):
        c = (y.dot(Bstar[i])) / (Bstar[i].dot(Bstar[i]))
        ci = _nearest_integer(c)
        coeffs[i] = ci
        y = y - ci * B_cols.col(i)

    v = Matrix([0] * B_cols.rows)
    for i in range(n):
        v += coeffs[i] * B_cols.col(i)
    return v, coeffs


def recover_x0_lowbits(p: int, steps: List[int], tvals: List[int], A: int, B: int) -> int:
    """Recover the unknown low 320 bits of state at step 0 (x0) using LLL + CVP."""

    # Build the induced recurrence on low bits across each irregular gap.
    m_list: List[int] = []
    k_list: List[int] = []

    for i in range(len(steps) - 1):
        d = steps[i + 1] - steps[i]
        m_i, c_i = lcg_affine_jump(A, B, p, d)
        m_list.append(m_i)

        # From: t_{i+1}*X + x_{i+1} ≡ m_i*(t_i*X + x_i) + c_i (mod p)
        # => x_{i+1} ≡ m_i*x_i + (m_i*t_i*X + c_i - t_{i+1}*X) (mod p)
        k_i = (m_i * tvals[i] * X + c_i - tvals[i + 1] * X) % p
        k_list.append(k_i)

    # Express each x_i as: x_i = alpha_i*x0 + beta_i (mod p)
    alpha = [1]
    beta = [0]
    for i in range(len(k_list)):
        alpha.append((m_list[i] * alpha[i]) % p)
        beta.append((m_list[i] * beta[i] + k_list[i]) % p)

    # Use the 4 constraints (i=1..4): steps 4,10,18,28.
    alphas = [alpha[1], alpha[2], alpha[3], alpha[4]]
    betas = [beta[1], beta[2], beta[3], beta[4]]

    # Lattice basis (rows). Any lattice vector is:
    # (q1*p + a1*x0, q2*p + a2*x0, q3*p + a3*x0, q4*p + a4*x0, x0)
    Br = Matrix(
        [
            [p, 0, 0, 0, 0],
            [0, p, 0, 0, 0],
            [0, 0, p, 0, 0],
            [0, 0, 0, p, 0],
            [alphas[0], alphas[1], alphas[2], alphas[3], 1],
        ]
    )

    Br_red = Br.lll()
    Bc_red = Br_red.T

    # Center the allowed interval [0, X) at X/2 to make it bounded-distance.
    half = X // 2
    target = Matrix(
        [
            -betas[0] + half,
            -betas[1] + half,
            -betas[2] + half,
            -betas[3] + half,
            half,
        ]
    )

    closest, _coeffs = babai_closest_vector(Bc_red, target)
    x0 = int(closest[4])

    if not (0 <= x0 < X):
        raise ValueError(f"Recovered x0 out of bounds: {x0}")

    # Sanity-check: all implied x_i must land in [0, X)
    for i in range(1, 5):
        xi = (alpha[i] * x0 + beta[i]) % p
        if not (0 <= xi < X):
            raise ValueError(
                "Sanity-check failed: some derived low bits not in [0,2^320). "
                "This almost always means you derived the wrong (a,b) (wrong UTC time / data files)."
            )

    return x0


def decrypt_flag(p: int, A: int, B: int, t_by_step: Dict[int, int], iv: bytes, ciphertext: bytes) -> bytes:
    steps = sorted(t_by_step.keys())
    tvals = [t_by_step[s] for s in steps]

    x0 = recover_x0_lowbits(p, steps, tvals, A, B)

    # Rebuild low bits along the sampled steps.
    m_list: List[int] = []
    k_list: List[int] = []
    for i in range(len(steps) - 1):
        d = steps[i + 1] - steps[i]
        m_i, c_i = lcg_affine_jump(A, B, p, d)
        m_list.append(m_i)
        k_i = (m_i * tvals[i] * X + c_i - tvals[i + 1] * X) % p
        k_list.append(k_i)

    low = [x0]
    for i in range(len(k_list)):
        low.append((m_list[i] * low[i] + k_list[i]) % p)

    # Full sampled states s_i = t_i*X + low_i
    states = [tvals[i] * X + low[i] for i in range(len(steps))]
    s28 = states[steps.index(28)]

    # encrypt.py takes one more step after the last snapshot
    final_state = (A * s28 + B) % p

    key = SHA256.new(long_to_bytes(final_state)).digest()
    pt_padded = AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext)
    return unpad(pt_padded, 16)


def main() -> None:
    ap = argparse.ArgumentParser(description="Solve the Halley-LCG CTF")
    ap.add_argument("--input", default="output.txt", help="Path to output.txt")
    args = ap.parse_args()

    tx = parse_output_file(args.input)
    hour, minute, second, time_str = recover_time_from_epoch_hash(tx.epoch_hash)

    print(f"[+] Transmission date : {tx.date_str}")
    print(f"[+] epoch_hash        : {tx.epoch_hash}")
    print(f"[+] Recovered UTC time: {time_str}")

    a, b = derive_lcg_params_from_halley(tx.date_str, hour, minute, second)
    A = a % tx.p
    B = b % tx.p
    print("[+] Derived a,b from Halley ephemeris")

    flag = decrypt_flag(tx.p, A, B, tx.t_by_step, tx.iv, tx.ciphertext)
    try:
        print(flag.decode())
    except Exception:
        print(flag)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)
