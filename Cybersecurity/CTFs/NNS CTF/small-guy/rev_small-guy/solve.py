#!/usr/bin/env python3
"""
Solver for the "small-guy" reversing challenge.

The binary hides its flag check inside the DWARF CFI (.eh_frame) "unwind
program" of a self-recursive function. A 32-byte input (the content of
NNS{...}) is loaded into four 64-bit words (rbx, r12, r13, r14) and the
function recurses 256 times, throwing a C++ exception at the base case.
As the exception unwinds back out through all 256 stack frames, each
frame's CFI row applies one of 32 possible mixing operations (add, xor,
multiply, rotate-xor, swap, or a small LCG loop) to the four words. Which
operation fires at recursion depth `idx` is selected by a fixed byte table
XORed with the first two bytes of input; the operand used inside some of
those 32 operations ("rcx") is the round key belonging to level `idx+1`
(one level deeper), except at the very deepest level whose key is
explicitly zero. The final four words are compared against a fixed 32-byte
blob; equality is not achievable by brute force, but the whole chain is a
sequence of invertible operations, so it can be run backwards from the
target given the right first two bytes -- which are recovered by brute
forcing all 65536 possibilities and checking self-consistency.

See SOLUTION.md in this directory for the full write-up.

Usage: python3 solve.py [path-to-small-guy-binary]
"""
import struct
import sys

MASK = (1 << 64) - 1
GOLDEN_RATIO = 0x9e3779b97f4a7c15

BASE_VADDR = 0x400000
DIGIT_TABLE_VADDR = 0x4014d0   # 256 bytes
KEY_TABLE_VADDR = 0x4015d0     # 256 x 8-byte qwords
TARGET_VADDR = 0x401dd0        # 32 bytes, the value memcmp'd against


def load_tables(binary_path):
    data = open(binary_path, "rb").read()
    digit_off = DIGIT_TABLE_VADDR - BASE_VADDR
    key_off = KEY_TABLE_VADDR - BASE_VADDR
    target_off = TARGET_VADDR - BASE_VADDR
    digit_table = list(data[digit_off:digit_off + 256])
    key_table = list(struct.unpack_from("<256Q", data, key_off))
    target = data[target_off:target_off + 32]
    return digit_table, key_table, target


def rol(x, n):
    n &= 63
    if n == 0:
        return x & MASK
    return ((x << n) | (x >> (64 - n))) & MASK


def digit_for(idx, acc, digit_table):
    return (digit_table[idx] + ((acc >> (idx & 7)) & 0xFFFFFFFF)) & 0x1F


def rcx_for(idx, acc, key_table):
    # The round key used *inside* level idx's own formula belongs to level
    # idx+1 (one level deeper in the recursion), because it is recovered
    # from the stack slot that level idx+1 pushed before recursing further.
    # The deepest real level (255) has no such deeper push -- the base case
    # explicitly zeroes it.
    if idx + 1 > 255:
        return 0
    return key_table[idx + 1] ^ ((acc * GOLDEN_RATIO) & MASK)


def modinv(a):
    return pow(a, -1, 1 << 64)


MUL_CONST = {
    12: 6364136223846793005,
    13: 2862933555777941757,
    14: 3935559000370003845,
    15: 18397679294719823053,
}
INV_MUL_CONST = {k: modinv(v) for k, v in MUL_CONST.items()}


def forward_case(idx, rbx, r12, r13, r14, rcx):
    if idx == 0: rbx = (rbx + 11400714819323198485) & MASK
    elif idx == 1: r12 = (r12 + 13787848793156543929) & MASK
    elif idx == 2: r13 = (r13 + 10723151780598845931) & MASK
    elif idx == 3: r14 = (r14 + 2685821657736338717) & MASK
    elif idx == 4: rbx = (rbx + 15485907386658061715) & MASK
    elif idx == 5: r12 = (r12 + 11562461410679940143) & MASK
    elif idx == 6: r13 = (r13 + 16646288086500911323) & MASK
    elif idx == 7: r14 = (r14 + 10285213230658275043) & MASK
    elif idx == 8: rbx = rbx ^ rol(r12, 7)
    elif idx == 9: r12 = r12 ^ rol(r13, 17)
    elif idx == 10: r13 = r13 ^ rol(r14, 29)
    elif idx == 11: r14 = r14 ^ rol(rbx, 41)
    elif idx == 12: rbx = (rbx * MUL_CONST[12]) & MASK
    elif idx == 13: r12 = (r12 * MUL_CONST[13]) & MASK
    elif idx == 14: r13 = (r13 * MUL_CONST[14]) & MASK
    elif idx == 15: r14 = (r14 * MUL_CONST[15]) & MASK
    elif idx == 16: rbx = rbx ^ rcx
    elif idx == 17: r12 = r12 ^ rcx
    elif idx == 18: r13 = r13 ^ rcx
    elif idx == 19: r14 = r14 ^ rcx
    elif idx == 20: rbx = (rbx + rcx * 14029467366897019727) & MASK
    elif idx == 21: r12 = (r12 + rcx * 1609587929392839161) & MASK
    elif idx == 22: r13 = (r13 + rcx * 9650029242287828579) & MASK
    elif idx == 23: r14 = (r14 + rcx * 11400714785074694791) & MASK
    elif idx == 24: rbx = rbx ^ rol(r13, 11)
    elif idx == 25: r12 = r12 ^ rol(r14, 23)
    elif idx == 26: r13 = r13 ^ rol(rbx, 37)
    elif idx == 27: r14 = r14 ^ rol(r12, 53)
    elif idx == 28: rbx, r13 = r13, rbx
    elif idx == 29: r12, r14 = r14, r12
    elif idx == 30:
        x = rbx
        count = (rcx & 3) + 1
        for _ in range(count):
            x = (x * 1812433253 + 2567483615) & MASK
        rbx = x
    elif idx == 31:
        x = r13
        count = (rcx & 3) + 1
        for _ in range(count):
            x = (x * 1103515245 + 12345) & MASK
        r13 = x
    return rbx & MASK, r12 & MASK, r13 & MASK, r14 & MASK


def inverse_case(idx, rbx, r12, r13, r14, rcx):
    if idx == 0: rbx = (rbx - 11400714819323198485) & MASK
    elif idx == 1: r12 = (r12 - 13787848793156543929) & MASK
    elif idx == 2: r13 = (r13 - 10723151780598845931) & MASK
    elif idx == 3: r14 = (r14 - 2685821657736338717) & MASK
    elif idx == 4: rbx = (rbx - 15485907386658061715) & MASK
    elif idx == 5: r12 = (r12 - 11562461410679940143) & MASK
    elif idx == 6: r13 = (r13 - 16646288086500911323) & MASK
    elif idx == 7: r14 = (r14 - 10285213230658275043) & MASK
    elif idx == 8: rbx = rbx ^ rol(r12, 7)
    elif idx == 9: r12 = r12 ^ rol(r13, 17)
    elif idx == 10: r13 = r13 ^ rol(r14, 29)
    elif idx == 11: r14 = r14 ^ rol(rbx, 41)
    elif idx == 12: rbx = (rbx * INV_MUL_CONST[12]) & MASK
    elif idx == 13: r12 = (r12 * INV_MUL_CONST[13]) & MASK
    elif idx == 14: r13 = (r13 * INV_MUL_CONST[14]) & MASK
    elif idx == 15: r14 = (r14 * INV_MUL_CONST[15]) & MASK
    elif idx == 16: rbx = rbx ^ rcx
    elif idx == 17: r12 = r12 ^ rcx
    elif idx == 18: r13 = r13 ^ rcx
    elif idx == 19: r14 = r14 ^ rcx
    elif idx == 20: rbx = (rbx - rcx * 14029467366897019727) & MASK
    elif idx == 21: r12 = (r12 - rcx * 1609587929392839161) & MASK
    elif idx == 22: r13 = (r13 - rcx * 9650029242287828579) & MASK
    elif idx == 23: r14 = (r14 - rcx * 11400714785074694791) & MASK
    elif idx == 24: rbx = rbx ^ rol(r13, 11)
    elif idx == 25: r12 = r12 ^ rol(r14, 23)
    elif idx == 26: r13 = r13 ^ rol(rbx, 37)
    elif idx == 27: r14 = r14 ^ rol(r12, 53)
    elif idx == 28: rbx, r13 = r13, rbx
    elif idx == 29: r12, r14 = r14, r12
    elif idx == 30:
        x = rbx
        count = (rcx & 3) + 1
        for _ in range(count):
            x = ((x - 2567483615) * INV_MUL_CONST_MT) & MASK
        rbx = x
    elif idx == 31:
        x = r13
        count = (rcx & 3) + 1
        for _ in range(count):
            x = ((x - 12345) * INV_MUL_CONST_LCG) & MASK
        r13 = x
    return rbx & MASK, r12 & MASK, r13 & MASK, r14 & MASK


INV_MUL_CONST_MT = modinv(1812433253)
INV_MUL_CONST_LCG = modinv(1103515245)


def forward_hash(content32, digit_table, key_table):
    """Reference implementation: what the real binary computes for a given
    32-byte input. Used only to double check candidates."""
    acc = content32[0] | (content32[1] << 8)
    rbx, r12, r13, r14 = struct.unpack("<QQQQ", content32)
    for idx in range(255, -1, -1):
        digit = digit_for(idx, acc, digit_table)
        rcx = rcx_for(idx, acc, key_table)
        rbx, r12, r13, r14 = forward_case(digit, rbx, r12, r13, r14, rcx)
    return struct.pack("<QQQQ", rbx, r12, r13, r14)


def invert_for_acc(target32, acc, digit_table, key_table):
    rbx, r12, r13, r14 = struct.unpack("<QQQQ", target32)
    for idx in range(0, 256):
        digit = digit_for(idx, acc, digit_table)
        rcx = rcx_for(idx, acc, key_table)
        rbx, r12, r13, r14 = inverse_case(digit, rbx, r12, r13, r14, rcx)
    return struct.pack("<QQQQ", rbx, r12, r13, r14)


def main():
    binary_path = sys.argv[1] if len(sys.argv) > 1 else "small-guy"
    digit_table, key_table, target = load_tables(binary_path)

    candidates = []
    for acc in range(0x10000):
        content = invert_for_acc(target, acc, digit_table, key_table)
        if (content[0] | (content[1] << 8)) != acc:
            continue
        if all(0x20 <= b < 0x7f for b in content):
            candidates.append(content)

    if not candidates:
        print("No printable self-consistent preimage found.")
        return

    for content in candidates:
        assert forward_hash(content, digit_table, key_table) == target
        flag = "NNS{" + content.decode() + "}"
        print(flag)


if __name__ == "__main__":
    main()
