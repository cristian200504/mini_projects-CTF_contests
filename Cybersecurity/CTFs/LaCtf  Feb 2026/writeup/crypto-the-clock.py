#!/usr/bin/env python3

import argparse
import hashlib
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


Point = Tuple[int, int]  # (x, y)


IDENTITY: Point = (0, 1)  # (Fp(0), Fp(1))


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0)
    g, x, y = egcd(b, a % b)
    return (g, y, x - (a // b) * y)


def invmod(a: int, m: int) -> int:
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f"no inverse for {a} mod {m} (gcd={g})")
    return x % m


def crt_pair(a1: int, m1: int, a2: int, m2: int) -> Tuple[int, int]:
    """Combine x≡a1 (mod m1), x≡a2 (mod m2) with gcd(m1,m2)=1."""
    g = math.gcd(m1, m2)
    if g != 1:
        raise ValueError(f"CRT requires coprime moduli, got gcd={g}")
    t = ((a2 - a1) % m2) * invmod(m1, m2) % m2
    x = a1 + m1 * t
    return x % (m1 * m2), m1 * m2


def crt(residues: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Return (x, M) where x satisfies all congruences, M=product(moduli)."""
    x, M = residues[0]
    for a, m in residues[1:]:
        x, M = crt_pair(x, M, a, m)
    return x, M


@dataclass
class ClockGroup:
    p: int

    def add(self, P: Point, Q: Point) -> Point:
        x1, y1 = P
        x2, y2 = Q
        x3 = (x1 * y2 + y1 * x2) % self.p
        y3 = (y1 * y2 - x1 * x2) % self.p
        return (x3, y3)

    def inv(self, P: Point) -> Point:
        # For norm-1 points, inverse is conjugate: (x,y) -> (-x, y)
        x, y = P
        return ((-x) % self.p, y % self.p)

    def sub(self, P: Point, Q: Point) -> Point:
        return self.add(P, self.inv(Q))

    def pow(self, P: Point, n: int) -> Point:
        if n < 0:
            return self.pow(self.inv(P), -n)
        R = IDENTITY
        B = P
        k = n
        while k:
            if k & 1:
                R = self.add(R, B)
            B = self.add(B, B)
            k >>= 1
        return R


def parse_output_txt(path: str) -> Dict[str, object]:
    s = open(path, "r", encoding="utf-8").read()

    def parse_point(label: str) -> Point:
        m = re.search(rf"{re.escape(label)}\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", s)
        if not m:
            raise ValueError(f"Could not find point for '{label}' in {path}")
        return (int(m.group(1)), int(m.group(2)))

    alice_pub = parse_point("Alice's public key:")
    bob_pub = parse_point("Bob's public key:")

    m = re.search(r"Encrypted flag:\s*([0-9a-fA-F]+)", s)
    if not m:
        raise ValueError(f"Could not find ciphertext in {path}")
    ct_hex = m.group(1).strip()
    return {"alice_pub": alice_pub, "bob_pub": bob_pub, "ct": bytes.fromhex(ct_hex)}


def parse_base_point_from_chall(path: str) -> Point:
    s = open(path, "r", encoding="utf-8").read()
    m = re.search(
        r"base_point\s*=\s*\(Fp\((\d+)\)\s*,\s*Fp\((\d+)\)\s*\)", s
    )
    if not m:
        raise ValueError(f"Could not parse base_point from {path}")
    return (int(m.group(1)), int(m.group(2)))


def recover_prime_p(points: List[Point]) -> int:
    # p divides (x^2 + y^2 - 1) for each norm-1 point
    g = 0
    for x, y in points:
        val = x * x + y * y - 1
        g = math.gcd(g, abs(val))
    if g == 0:
        raise ValueError("Failed to recover p (gcd became 0)")
    # strip small factors just in case
    for small in [2, 3, 5, 7, 11, 13]:
        while g % small == 0:
            # only strip if it still divides all; harmless in this challenge,
            # but keep it conservative: stop stripping once it's not plausible.
            g //= small
    return g


def trial_factor_small(n: int, bound: int = 100000) -> Dict[int, int]:
    """Trial divide by primes up to 'bound'. Works because this challenge is smooth."""
    factors: Dict[int, int] = {}
    x = n

    def add_factor(p: int):
        nonlocal x
        e = 0
        while x % p == 0:
            x //= p
            e += 1
        if e:
            factors[p] = factors.get(p, 0) + e

    add_factor(2)
    f = 3
    while f <= bound and f * f <= x:
        add_factor(f)
        f += 2

    if x != 1:
        # remaining cofactor (could be prime or >bound composite; in this task it’s small-prime product)
        factors[x] = factors.get(x, 0) + 1

    # If we ended with a composite "prime", try splitting once more with a slightly higher bound
    # (still cheap because challenge is designed to be smooth).
    changed = True
    while changed:
        changed = False
        for p in list(factors.keys()):
            if p > 1 and not is_probable_prime(p):
                # remove it and try factor it further
                exp = factors.pop(p)
                sub = _more_trial_factor(p, bound=500000)
                for sp, se in sub.items():
                    factors[sp] = factors.get(sp, 0) + se * exp
                changed = True
                break

    return factors


def _more_trial_factor(n: int, bound: int = 500000) -> Dict[int, int]:
    factors: Dict[int, int] = {}
    x = n
    for p in [2, 3, 5]:
        e = 0
        while x % p == 0:
            x //= p
            e += 1
        if e:
            factors[p] = e
    f = 7
    step = 4  # wheel-ish 6k±1
    while f <= bound and f * f <= x:
        e = 0
        while x % f == 0:
            x //= f
            e += 1
        if e:
            factors[f] = e
        f += step
        step = 6 - step
    if x != 1:
        factors[x] = factors.get(x, 0) + 1
    return factors


def is_probable_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for 64-bit-ish; here used as a sanity check, not critical."""
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    # write n-1 = d*2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    # bases good enough for our “sanity check” usage
    bases = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]
    for a in bases:
        a %= n
        if a == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def element_order(G: ClockGroup, g: Point, n: int, factorization: Dict[int, int]) -> int:
    """Compute the exact order of g given a multiple n and factorization of n."""
    ord_ = n
    for q, e in factorization.items():
        for _ in range(e):
            if ord_ % q != 0:
                break
            cand = ord_ // q
            if G.pow(g, cand) == IDENTITY:
                ord_ = cand
            else:
                break
    return ord_


def dlog_prime_power(G: ClockGroup, g: Point, h: Point, q: int, e: int, n: int) -> int:
    """
    Solve g^x = h in subgroup of order q^e using standard Pohlig–Hellman lifting.
    Assumes q is small enough to brute force order-q steps.
    """
    # Reduce to subgroup of order q^e
    g0 = G.pow(g, n // (q ** e))
    h0 = G.pow(h, n // (q ** e))

    x = 0
    qk = 1
    for k in range(e):
        # gk has order q
        gk = G.pow(g0, q ** (e - 1 - k))

        # hk = (h0 * g0^{-x})^{q^{e-1-k}}
        gx = G.pow(g0, x)
        hk = G.pow(G.sub(h0, gx), q ** (e - 1 - k))

        # brute force d in [0..q-1] such that gk^d == hk
        d = None
        cur = IDENTITY
        for j in range(q):
            if cur == hk:
                d = j
                break
            cur = G.add(cur, gk)
        if d is None:
            raise ValueError(f"Failed to find digit for q={q} at k={k}")

        x += d * qk
        qk *= q

    return x


def pohlig_hellman(G: ClockGroup, g: Point, h: Point, n: int, factors: Dict[int, int]) -> int:
    residues: List[Tuple[int, int]] = []
    for q, e in sorted(factors.items()):
        m = q ** e
        r = dlog_prime_power(G, g, h, q, e, n)
        residues.append((r % m, m))
    x, _ = crt(residues)
    return x % n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output.txt", help="path to output.txt")
    ap.add_argument("--chall", default="chall.py", help="path to chall.py")
    args = ap.parse_args()

    out = parse_output_txt(args.out)
    base = parse_base_point_from_chall(args.chall)
    alice_pub = out["alice_pub"]
    bob_pub = out["bob_pub"]
    ct = out["ct"]

    # 1) Recover p
    p = recover_prime_p([base, alice_pub, bob_pub])
    print(f"[+] recovered p = {p}")

    G = ClockGroup(p=p)

    # 2) Subgroup order divides p+1 for norm-1 elements
    n0 = p + 1
    print(f"[+] candidate group order (norm-1) n0 = p+1 = {n0}")

    # 3) Factor n0 (challenge is smooth)
    factors0 = trial_factor_small(n0, bound=100000)
    print("[+] factorization of n0 (may include composite cofactors if any):")
    for q in sorted(factors0):
        print(f"    {q}^{factors0[q]}")

    # 4) Compute exact order of base element (usually equals n0)
    ord_base = element_order(G, base, n0, factors0)
    print(f"[+] order(base) = {ord_base}")

    # Factor the exact order (refactor if reduced)
    factors = trial_factor_small(ord_base, bound=100000)
    print("[+] factorization of order(base):")
    for q in sorted(factors):
        print(f"    {q}^{factors[q]}")

    # 5) Discrete log to recover Alice secret a: base^a = alice_pub
    print("[*] solving discrete log for Alice secret with Pohlig–Hellman ...")
    a = pohlig_hellman(G, base, alice_pub, ord_base, factors)
    print(f"[+] recovered a = {a}")

    # 6) Shared secret = bob_pub^a
    shared = G.pow(bob_pub, a)
    sx, sy = shared
    print(f"[+] shared secret point = ({sx}, {sy})")

    # 7) AES key derivation & decrypt
    key = hashlib.md5(f"{sx},{sy}".encode()).digest()
    pt_padded = AES.new(key, AES.MODE_ECB).decrypt(ct)
    pt = unpad(pt_padded, 16)
    try:
        print("[+] decrypted:", pt.decode())
    except UnicodeDecodeError:
        print("[+] decrypted (raw bytes):", pt)


if __name__ == "__main__":
    main()
