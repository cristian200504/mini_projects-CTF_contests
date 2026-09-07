"""Independent public-key attack for the local NSS CTF challenge.

Use the unusually short relation H*f = d (mod q), where
H = (h-1)/3 and d = (g-f)/3.  The second lattice block is scaled
to balance the coefficient variances of f and d.
"""
import ast
import hashlib
import json
import math
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

ROOT = Path(__file__).resolve().parent
N, Q = 256, 367
SCALE = int(os.environ.get("AGENT_ALT_SCALE", "2"))
FPLLL = os.environ.get("FPLLL", "/tmp/fplll-5.5.0/fplll/fplll")
FLATTER = os.environ.get("FLATTER", "/tmp/nss-flatter/build/bin/flatter")
ENV = dict(os.environ)
ENV["LD_LIBRARY_PATH"] = (
    "/tmp/nss-flatter/build/lib:/tmp/fplll-5.5.0/fplll/.libs:"
    "/tmp/localroot/usr/lib/x86_64-linux-gnu"
)
ENV["OMP_NUM_THREADS"] = os.environ.get("OMP_NUM_THREADS", "2")
ENV["OPENBLAS_NUM_THREADS"] = "1"

tree = ast.parse((ROOT / "crypto_nss-ctf" / "output.py").read_text())
DATA = {
    node.targets[0].id: ast.literal_eval(node.value)
    for node in tree.body
    if isinstance(node, ast.Assign)
}
H = [x % Q for x in DATA["pk"]]
CT = bytes.fromhex(DATA["ct"])


def log(*items):
    print(time.strftime("%H:%M:%S"), *items, flush=True)


def center(values, modulus=Q):
    return [((int(x) + modulus // 2) % modulus) - modulus // 2 for x in values]


def shift(poly, amount):
    """Coefficients of x**amount * poly in Z_q[x]/(x**N+1)."""
    out = [0] * N
    for k in range(N):
        source = k - amount
        out[k] = poly[source] % Q if source >= 0 else (-poly[source + N]) % Q
    return out


def multiply(a, b):
    out = [0] * N
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                k = i + j
                out[k % N] += ai * bj if k < N else -ai * bj
    return [x % Q for x in out]


def build_basis():
    inv3 = pow(3, -1, Q)
    hp = [((H[i] - (i == 0)) * inv3) % Q for i in range(N)]
    dim = 2 * N
    basis = [[0] * dim for _ in range(dim)]
    for j in range(N):
        basis[j][j] = 1
        column = shift(hp, j)
        for i in range(N):
            basis[j][N + i] = SCALE * column[i]
        basis[N + j][N + j] = SCALE * Q
    return basis


def encode(basis):
    return "[" + "\n".join("[" + " ".join(map(str, row)) + "]" for row in basis) + "\n]\n"


def decode(raw):
    rows = []
    for part in raw.replace("]", "").split("["):
        if part.strip():
            row = [int(x) for x in part.split()]
            if len(row) == 2 * N:
                rows.append(row)
    return rows


def negacyclic_shift(poly, amount):
    return [poly[k - amount] if k >= amount else -poly[k - amount + N] for k in range(N)]


def validate(candidate):
    """Try all signed rotations, returning the exact secret on success."""
    for sign in (1, -1):
        for amount in range(N):
            f = [sign * x for x in negacyclic_shift(candidate, amount)]
            if max(map(abs, f)) > 4:
                continue
            u = center(f, 3)
            if (u.count(1), u.count(-1), u.count(0)) != (90, 91, 75):
                continue
            rf = [(a - b) // 3 for a, b in zip(f, u)]
            if set(rf) - {-1, 0, 1} or rf.count(1) != 88 or rf.count(-1) != 88:
                continue
            g = center(multiply(H, f))
            if max(map(abs, g)) > 4 or center(g, 3) != u:
                continue
            rg = [(a - b) // 3 for a, b in zip(g, u)]
            if set(rg) - {-1, 0, 1} or rg.count(1) != 60 or rg.count(-1) != 60:
                continue
            key = hashlib.sha256(bytes(x % 256 for x in f)).digest()
            try:
                plaintext = unpad(AES.new(key, AES.MODE_ECB).decrypt(CT), 16)
            except ValueError:
                continue
            if not plaintext.startswith(b"NNS{"):
                continue
            return f, g, u, key, plaintext
    return None


def inspect(basis, label):
    ordered = sorted(basis, key=lambda row: sum(x * x for x in row))
    norms = [math.isqrt(sum(x * x for x in row)) for row in ordered[:8]]
    log(label, "minimum norms", norms)
    for row in ordered:
        norm2 = sum(x * x for x in row)
        if norm2 > 140 * 140:
            break
        for sgn in (1, -1):
            f0 = [sgn * x for x in row[:N]]
            d_scaled = [sgn * x for x in row[N:]]
            if any(x % SCALE for x in d_scaled):
                continue
            d = [x // SCALE for x in d_scaled]
            if max(map(abs, f0)) <= 8 and max(map(abs, d)) <= 5:
                # Relation and key-generation ranges are cheap strong filters.
                g0 = [a + 3 * b for a, b in zip(f0, d)]
                if max(map(abs, g0)) <= 8:
                    result = validate(f0)
                    if result:
                        f, g, u, key, plaintext = result
                        record = {
                            "f": f,
                            "g": g,
                            "u": u,
                            "key": key.hex(),
                            "flag": plaintext.decode(),
                        }
                        (ROOT / "agent_alt_recovered.json").write_text(json.dumps(record, indent=2))
                        log("RECOVERED", plaintext.decode())
                        print("f =", f, flush=True)
                        return True
    return False


def main():
    blocks = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [24, 28, 32, 36, 40]
    cache = ROOT / f"agent_alt_basis_s{SCALE}.pkl"
    if cache.exists():
        basis = pickle.loads(cache.read_bytes())
        log("loaded", cache, len(basis))
    else:
        basis = build_basis()
        log("running flatter on dimension", len(basis), "scale", SCALE)
        proc = subprocess.run(
            [FLATTER, "-rhf", "1.012"], input=encode(basis), text=True,
            capture_output=True, env=ENV, check=True,
        )
        basis = decode(proc.stdout)
        if len(basis) != 2 * N:
            raise RuntimeError(f"flatter parse returned {len(basis)} rows")
        cache.write_bytes(pickle.dumps(basis))
    if inspect(basis, "flatter"):
        return
    for block in blocks:
        log("running BKZ", block)
        proc = subprocess.run(
            [FPLLL, "-a", "bkz", "-b", str(block), "-bkzmaxloops", "4", "-f", "mpfr", "-p", "160"],
            input=encode(basis), text=True, capture_output=True, env=ENV,
        )
        if proc.returncode and 'loops limit exceeded' not in proc.stderr and 'time limit exceeded' not in proc.stderr:
            log("BKZ failed", proc.stderr[:500])
            continue
        reduced = decode(proc.stdout)
        if len(reduced) != 2 * N:
            log("BKZ parse failed", len(reduced))
            continue
        basis = reduced
        cache.write_bytes(pickle.dumps(basis))
        if inspect(basis, f"BKZ-{block}"):
            return
    log("no key found")


if __name__ == "__main__":
    main()
