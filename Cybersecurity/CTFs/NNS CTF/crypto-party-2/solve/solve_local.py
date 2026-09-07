"""
Run inside SageMath. Generates 6 real signatures from a local Party (with a
KNOWN secret_key, for verification), builds the PartialInteger model for the
nonce, runs the Extended HNP attack, and checks whether the true private key
is among the yielded candidates.

Run with:  sage -python solve_local.py
"""
import sys
import time
from hashlib import sha256

sys.path.insert(0, ".")

from Crypto.Util.number import bytes_to_long
from ecdsa import curves

from partial_integer import PartialInteger
from nonce_model import build_partial_integer, FIXED_POSITIONS
from extended_hnp import dsa_known_bits
from local_server import Party, n as N


def main():
    party = Party()
    print("TRUE secret_key =", party.secret_key)

    names = [f"friend_{i}" for i in range(6)]
    h_list = []
    r_list = []
    s_list = []
    for name in names:
        h = bytes_to_long(sha256(name.encode()).digest())
        r, s = party.invite(name)
        h_list.append(h)
        r_list.append(r)
        s_list.append(s)

    bit_length = N.bit_length()
    print("N.bit_length() =", bit_length)

    x_partial = PartialInteger.unknown(bit_length)
    k_partials = [build_partial_integer(PartialInteger) for _ in names]

    # sanity: each k_partial should have total bit_length == 256
    assert k_partials[0].bit_length == 256, k_partials[0].bit_length

    t0 = time.time()
    found = None
    count = 0
    for candidate in dsa_known_bits(N, h_list, r_list, s_list, x_partial, k_partials):
        count += 1
        if candidate == party.secret_key:
            found = candidate
            print(f"[{count}] MATCH! candidate == true secret_key")
            break
        else:
            print(f"[{count}] candidate != true key (mismatch)")
        if count > 5:
            break

    dt = time.time() - t0
    print(f"done in {dt:.1f}s, candidates checked = {count}, found = {found is not None}")


if __name__ == "__main__":
    main()
