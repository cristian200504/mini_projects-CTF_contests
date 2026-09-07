"""
Models the ECDSA nonce k = bytes_to_long(str(uuid.uuid4())[:32].encode())
as a PartialInteger: which byte positions are exactly known, and which are
"7 unknown low bits + 1 known zero high bit" (every ASCII hex digit / '-' is
< 0x80, so the top bit of every byte in this string is always 0).

Byte string layout (index 0 = first char = most-significant byte of k):
  0-7   : 8 hex chars   (free)
  8     : '-'           (KNOWN = 0x2D)
  9-12  : 4 hex chars   (free)
  13    : '-'           (KNOWN = 0x2D)
  14    : '4'           (KNOWN = 0x34, uuid4 version nibble)
  15-17 : 3 hex chars   (free)
  18    : '-'           (KNOWN = 0x2D)
  19    : variant char, one of '8','9','a','b' (treated as free/7-bit here)
  20-22 : 3 hex chars   (free)
  23    : '-'           (KNOWN = 0x2D)
  24-31 : 8 hex chars   (free; the tail 4 chars of the real UUID are dropped
                          by the [:32] truncation)
"""
import sys

FIXED_POSITIONS = {8: 0x2D, 13: 0x2D, 14: 0x34, 18: 0x2D, 23: 0x2D}


def classify():
    """Returns (fixed_positions_dict, free_positions_list) for indices 0..31."""
    free = [i for i in range(32) if i not in FIXED_POSITIONS]
    return FIXED_POSITIONS, free


def build_partial_integer(PartialInteger):
    """
    Builds a PartialInteger representing k, generic over any single UUID's
    randomness (i.e. this is the *shape*, used once and shared for every
    signature since the fixed/free positions never change).
    Must add components LSB-of-k first (index 31) up to MSB-of-k last (index 0);
    within a free byte, add the unknown 7 bits first, then the known top bit (0).
    """
    p = PartialInteger()
    for i in range(31, -1, -1):
        if i in FIXED_POSITIONS:
            p.add_known(FIXED_POSITIONS[i], 8)
        else:
            p.add_unknown(7)
            p.add_known(0, 1)
    return p


def k_from_string(s32):
    """Reference: exact integer value of k given the 32-char truncated uuid string."""
    b = s32.encode()
    assert len(b) == 32
    v = 0
    for byte in b:
        v = (v << 8) | byte
    return v


if __name__ == "__main__":
    # Pure-Python self-check of the bit layout WITHOUT needing PartialInteger/sage:
    # verify byte(i) < 128 always, and the fixed positions are truly fixed, using
    # real uuid4 samples.
    import uuid

    fixed, free = classify()
    print("fixed positions:", fixed)
    print("num free positions:", len(free), free)

    bad = 0
    for _ in range(500000):
        s = str(uuid.uuid4())[:32]
        b = s.encode()
        for i, byte in enumerate(b):
            if i in fixed:
                if byte != fixed[i]:
                    print("MISMATCH fixed pos", i, hex(byte))
                    bad += 1
            else:
                if byte >= 128:
                    print("MISMATCH free pos top bit", i, hex(byte))
                    bad += 1
    print("bad =", bad, "(expect 0)")
