"""
Run inside SageMath. Loads remote_data.json (ct + 6 real (r,s) invite codes
from the live instance), runs the Extended HNP attack to recover secret_key,
then AES-ECB-decrypts ct with it to get the flag.

Run with:  sage -python solve_remote.py
"""
import json
import time
from hashlib import sha256

from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from ecdsa import curves

from partial_integer import PartialInteger
from nonce_model import build_partial_integer
from extended_hnp import dsa_known_bits

N = curves.NIST256p.order


def try_decrypt(candidate_key, ct_int):
    try:
        key = long_to_bytes(candidate_key, 32)
        cipher = AES.new(key, AES.MODE_ECB)
        ct_bytes = long_to_bytes(ct_int)
        # ct_bytes might be missing leading zero bytes from bytes_to_long/int
        # round-tripping; pad to a multiple of 16 from the left with zeros.
        if len(ct_bytes) % 16 != 0:
            ct_bytes = b"\x00" * (16 - len(ct_bytes) % 16) + ct_bytes
        pt = cipher.decrypt(ct_bytes)
        return unpad(pt, 16)
    except Exception as e:
        return None


def main():
    with open("remote_data.json") as f:
        data = json.load(f)

    ct = data["ct"]
    invites = data["invites"]

    h_list = [bytes_to_long(sha256(inv["name"].encode()).digest()) for inv in invites]
    r_list = [inv["r"] for inv in invites]
    s_list = [inv["s"] for inv in invites]

    bit_length = N.bit_length()
    x_partial = PartialInteger.unknown(bit_length)
    k_partials = [build_partial_integer(PartialInteger) for _ in invites]

    t0 = time.time()
    found_flag = None
    count = 0
    for candidate in dsa_known_bits(N, h_list, r_list, s_list, x_partial, k_partials):
        count += 1
        print(f"[{count}] candidate secret_key = {candidate}")
        flag = try_decrypt(candidate, ct)
        if flag is not None:
            print(f"[{count}] DECRYPT SUCCESS: {flag}")
            found_flag = flag
            break
        else:
            print(f"[{count}] decrypt failed / bad padding, not the key")
        if count > 5:
            break

    dt = time.time() - t0
    print(f"done in {dt:.1f}s, candidates checked = {count}")
    if found_flag:
        print("FLAG:", found_flag.decode(errors="replace"))
    else:
        print("FAILED to recover flag")


if __name__ == "__main__":
    main()
