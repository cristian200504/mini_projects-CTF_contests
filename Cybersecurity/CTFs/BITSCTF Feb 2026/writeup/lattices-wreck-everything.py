#!/usr/bin/env python3
"""
Leakithium / "Lattices Wreck Everything" — working solve

Recovers the missing Falcon secret coefficients f from leaked hints via a
Kannan-embedding lattice attack, then decrypts:

    key = SHA256(f.tobytes())
    flag = ciphertext XOR key

Deps:
  pip install numpy fpylll cysignals

Run:
  python solve_working.py challenge_data.json challenge_flag.enc
"""

import sys
import json
import hashlib
import random

import numpy as np
from fpylll import IntegerMatrix, LLL, BKZ


def centerlift_mod_q(v: np.ndarray, q: int) -> np.ndarray:
    v = np.mod(v, q)
    v = np.where(v > q // 2, v - q, v)
    return v


def decrypt_with_f(f: np.ndarray, enc_hex: str) -> bytes:
    # IMPORTANT: challenge used np.array(list_of_ints) => int64 on 64-bit machines
    f = np.asarray(f, dtype=np.int64)
    key = hashlib.sha256(f.tobytes()).digest()
    ct = bytes.fromhex(enc_hex.strip())
    return bytes([c ^ key[i % len(key)] for i, c in enumerate(ct)])


def build_reduced_instance(A: np.ndarray, q: int, hints: list, n: int):
    """
    Original relation (b==0):
        f*A + (-g) == 0 (mod q)

    Split f = f_known + f_unknown (unknown only on leaked-missing indices U):

        f_unknown*A + e = -f_known*A (mod q),  where e = -g is small.

    This is an LWE instance:
        A_lwe * s + e = b_lwe  (mod q)
    with s = unknown coefficients of f.
    """
    hint_map = {int(i): int(v) for i, v in hints}

    f_known = np.zeros(n, dtype=np.int64)
    unknown_idx = []
    for i in range(n):
        if i in hint_map:
            f_known[i] = hint_map[i]
        else:
            unknown_idx.append(i)

    b_lwe = (- (f_known @ A)) % q
    b_lwe = b_lwe.astype(np.int64)

    # A_lwe[j, k] = A[unknown_idx[k], j]
    A_lwe = (A[unknown_idx, :].T % q).astype(np.int64)

    return A_lwe, b_lwe, unknown_idx, f_known


def build_embedding_basis(A_sub: np.ndarray, b_sub: np.ndarray, q: int, M: int = 1) -> IntegerMatrix:
    """
    Kannan embedding (row basis) for CVP->SVP.

    Dimension: d = m + nsec + 1

    Short vector with last coordinate ±M gives the solution.
    """
    m, nsec = A_sub.shape
    d = m + nsec + 1
    B = IntegerMatrix(d, d)

    # q * I_m
    for i in range(m):
        B[i, i] = q

    # (A_sub | I)
    for j in range(nsec):
        row = m + j
        for i in range(m):
            B[row, i] = int(A_sub[i, j])
        B[row, m + j] = 1

    # target row (b | M)
    last = d - 1
    for i in range(m):
        B[last, i] = int(b_sub[i])
    B[last, last] = int(M)

    return B


def solve_once(
    A_lwe: np.ndarray,
    b_lwe: np.ndarray,
    A_full: np.ndarray,
    q: int,
    unknown_idx: list,
    f_known: np.ndarray,
    enc_hex: str,
    seed: int = 0,
    m: int = 96,
    bkz_block: int = 26,
    bkz_loops: int = 2,
    max_s_abs: int = 40,
    max_g_abs: int = 60,
):
    """
    One fast solve attempt:
      - choose m equations using seed
      - LLL + small BKZ
      - extract vector with last coord ±1
      - verify by checking g = f*A is small after center-lift
      - decrypt
    """
    rng = random.Random(seed)
    n_eq = A_lwe.shape[0]
    nsec = A_lwe.shape[1]

    rows = sorted(rng.sample(range(n_eq), m))
    A_sub = A_lwe[rows, :]
    b_sub = b_lwe[rows]

    B = build_embedding_basis(A_sub, b_sub, q=q, M=1)

    LLL.reduction(B, delta=0.99)
    BKZ.reduction(B, BKZ.Param(block_size=bkz_block, max_loops=bkz_loops))

    d = B.nrows
    for r in range(d):
        vec = [int(B[r, c]) for c in range(d)]
        if abs(vec[-1]) != 1:
            continue
        if vec[-1] == -1:
            vec = [-x for x in vec]

        # vec ≈ (e, -s, 1) => s = -vec[m:m+nsec]
        s = np.array([-x for x in vec[m:m + nsec]], dtype=np.int64)
        if np.max(np.abs(s)) > max_s_abs:
            continue

        f = f_known.copy()
        for k, idx in enumerate(unknown_idx):
            f[idx] = int(s[k])

        # Falcon consistency check
        g_cent = centerlift_mod_q(((f @ A_full) % q).astype(np.int64), q)
        if np.max(np.abs(g_cent)) > max_g_abs:
            continue

        pt = decrypt_with_f(f, enc_hex)
        if b"BITSCTF{" in pt and b"}" in pt:
            return f, pt

    return None, None


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} challenge_data.json challenge_flag.enc")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = json.load(f)

    q = int(data["q"])
    n = int(data["n"])
    A = np.array(data["A"], dtype=np.int64)
    hints = data["hints"]

    with open(sys.argv[2], "r") as f:
        enc_hex = f.read().strip()

    A_lwe, b_lwe, unknown_idx, f_known = build_reduced_instance(A, q, hints, n)

    print(f"q={q}, n={n}")
    print(f"Known f coeffs: {n - len(unknown_idx)} / {n}")
    print(f"Unknown f coeffs: {len(unknown_idx)}")

    # These parameters solve the provided instance essentially immediately.
    # Fallback tries a few nearby values to be robust across environments.
    for m in [96, 104, 112]:
        for seed in range(0, 10):
            f_rec, pt = solve_once(
                A_lwe=A_lwe,
                b_lwe=b_lwe,
                A_full=A,
                q=q,
                unknown_idx=unknown_idx,
                f_known=f_known,
                enc_hex=enc_hex,
                seed=seed,
                m=m,
                bkz_block=26,
                bkz_loops=2,
            )
            if pt is not None:
                print("\n[+] FLAG:", pt.decode(errors="replace"))
                return

    print("[!] Not found with quick parameters. Try bkz_block=28/30 and seeds up to 100.")
    sys.exit(2)


if __name__ == "__main__":
    main()