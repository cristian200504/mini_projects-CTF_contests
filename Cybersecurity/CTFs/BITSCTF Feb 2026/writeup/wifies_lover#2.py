import re
import struct
from pathlib import Path

OUT = Path("output.txt").read_text()

# ---------------- Parse ----------------
rounds = int(re.search(r"rounds\s*=\s*(\d+)", OUT).group(1))
tweak = int(re.search(r"tweak\s*=\s*0x([0-9a-fA-F]+)", OUT).group(1), 16)
rk0 = int(re.search(r"leaked_k0\s*=\s*0x([0-9a-fA-F]+)", OUT).group(1), 16)
rk3 = int(re.search(r"leaked_k3\s*=\s*0x([0-9a-fA-F]+)", OUT).group(1), 16)

pairs = []
for m in re.finditer(r"\(\s*0x([0-9a-fA-F]+)\s*,\s*0x([0-9a-fA-F]+)\s*\)", OUT):
    pairs.append((int(m.group(1), 16), int(m.group(2), 16)))

m = re.search(r"encrypted_flag\s*=\s*\[(.*?)\]", OUT, flags=re.S)
enc_flag = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]+)", m.group(1))]

print(f"[+] rounds={rounds} tweak=0x{tweak:032x}")
print(f"[+] rk0(leaked_k0)=0x{rk0:08x} rk3(leaked_k3)=0x{rk3:08x}")
print(f"[+] pairs={len(pairs)} flag_blocks={len(enc_flag)}")

# ---------------- Cipher primitives (from cipher.py) ----------------
S = [0, 4, 2, 11, 10, 12, 9, 8, 5, 15, 13, 3, 7, 1, 6, 14]
I = [0, 13, 2, 11, 1, 8, 14, 12, 7, 6, 4, 3, 5, 10, 15, 9]

def a32(s: int) -> int:
    r = 0
    for i in range(8):
        r |= S[(s >> (i * 4)) & 0xF] << (i * 4)
    return r

def b32(s: int) -> int:
    r = 0
    for i in range(8):
        r |= I[(s >> (i * 4)) & 0xF] << (i * 4)
    return r

def c32(s: int) -> int:
    return (s & 0xF0F0F0F0) | ((s & 0x0F0F0000) >> 16) | ((s & 0x00000F0F) << 16)

def d(x: int) -> int:
    return (0xF) & ((x << 1) ^ (((x >> 3) & 1) * 0x3))

def e(x: int, y: int) -> int:
    r = 0
    if y & 1: r ^= x
    if y & 2: r ^= d(x)
    if y & 4: r ^= d(d(x))
    if y & 8: r ^= d(d(d(x)))
    return r & 0xF

def f32(s: int) -> int:
    c0, c1, c2, c3 = (s >> 28) & 0xF, (s >> 24) & 0xF, (s >> 20) & 0xF, (s >> 16) & 0xF
    c4, c5, c6, c7 = (s >> 12) & 0xF, (s >> 8) & 0xF, (s >> 4) & 0xF, s & 0xF
    return ((e(c0, 0x2) ^ e(c1, 0x1) ^ e(c2, 0x1) ^ e(c3, 0x9)) << 28 |
            (e(c0, 0x1) ^ e(c1, 0x4) ^ e(c2, 0xF) ^ e(c3, 0x1)) << 24 |
            (e(c0, 0xD) ^ e(c1, 0x9) ^ e(c2, 0x4) ^ e(c3, 0x1)) << 20 |
            (e(c0, 0x1) ^ e(c1, 0xD) ^ e(c2, 0x1) ^ e(c3, 0x2)) << 16 |
            (e(c4, 0x2) ^ e(c5, 0x1) ^ e(c6, 0x1) ^ e(c7, 0x9)) << 12 |
            (e(c4, 0x1) ^ e(c5, 0x4) ^ e(c6, 0xF) ^ e(c7, 0x1)) << 8 |
            (e(c4, 0xD) ^ e(c5, 0x9) ^ e(c6, 0x4) ^ e(c7, 0x1)) << 4 |
            (e(c4, 0x1) ^ e(c5, 0xD) ^ e(c6, 0x1) ^ e(c7, 0x2)))

# f is an involution here (f(f(x))==x), c is also its own inverse.

def round_full(s: int, rk: int) -> int:
    s ^= rk
    s = a32(s)
    s = c32(s)
    s = f32(s)
    return s & 0xFFFFFFFF

def encrypt_with_rks(pt: int, rk0: int, rk1: int, rk2: int, rk3: int, rk4: int) -> int:
    s = pt
    s = round_full(s, rk0)
    s = round_full(s, rk1)
    s = round_full(s, rk2)
    s ^= rk3
    s = a32(s)
    s = c32(s)
    s ^= rk4
    return s & 0xFFFFFFFF

def decrypt_with_rks(ct: int, rk0: int, rk1: int, rk2: int, rk3: int, rk4: int) -> int:
    s = ct ^ rk4
    s = c32(s)
    s = b32(s)
    s ^= rk3
    for rk in (rk2, rk1, rk0):
        s = f32(s)      # inverse f
        s = c32(s)      # inverse c
        s = b32(s)      # inverse Sbox layer
        s ^= rk
    return s & 0xFFFFFFFF

# ---------------- Step 1: narrow rk4 nibble-wise using XOR balance over full 65536 set ----------------
cts = [ct for _, ct in pairs]

# c maps nibble positions: 0<->4, 2<->6, others fixed
mapping = {0: 4, 1: 1, 2: 6, 3: 3, 4: 0, 5: 5, 6: 2, 7: 7}

def xor_balance_for_key_nibble(pos_key: int, guess: int) -> int:
    """Compute XOR over all texts of invS( c(ct ^ (guess at this nibble)) ) at the affected nibble."""
    outpos = mapping[pos_key]
    shift = pos_key * 4
    mask = (guess & 0xF) << shift
    x = 0
    for ct in cts:
        u = c32(ct ^ mask)
        nib = (u >> (outpos * 4)) & 0xF
        x ^= I[nib]
    return x

nibble_cands = {}
for pos in range(8):
    good = []
    for g in range(16):
        if xor_balance_for_key_nibble(pos, g) == 0:
            good.append(g)
    nibble_cands[pos] = good

# build rk4 candidates
rk4_candidates = []
for n0 in nibble_cands[0]:
    for n1 in nibble_cands[1]:
        for n2 in nibble_cands[2]:
            for n3 in nibble_cands[3]:
                for n4 in nibble_cands[4]:
                    for n5 in nibble_cands[5]:
                        for n6 in nibble_cands[6]:
                            for n7 in nibble_cands[7]:
                                rk4 = (n0 |
                                       (n1 << 4) |
                                       (n2 << 8) |
                                       (n3 << 12) |
                                       (n4 << 16) |
                                       (n5 << 20) |
                                       (n6 << 24) |
                                       (n7 << 28))
                                rk4_candidates.append(rk4)

print(f"[+] rk4 candidates after integral filter: {len(rk4_candidates)}")

# ---------------- Step 2: for each rk4 candidate, derive rk1 and compute rk2 from ONE pair ----------------
(pt0, ct0) = pairs[0]

def two_rounds(pt: int, rk0: int, rk1: int) -> int:
    s = pt
    s = round_full(s, rk0)
    s = round_full(s, rk1)
    return s

def recover_rk2_from_pair(pt: int, ct: int, rk0: int, rk1: int, rk3: int, rk4: int) -> int:
    """Uses: ct -> undo last round -> state after round3; invert round3 layers to get (state_after_round2 ^ rk2)."""
    t2 = two_rounds(pt, rk0, rk1)

    s3 = ct ^ rk4
    s3 = c32(s3)
    s3 = b32(s3)
    s3 ^= rk3  # now s3 is output after round3

    x = f32(s3)      # inverse of f
    y = c32(x)       # inverse of c
    z = b32(y)       # inverse of Sbox layer
    rk2 = z ^ t2
    return rk2 & 0xFFFFFFFF

sol = None
for rk4 in rk4_candidates:
    rk1 = rk0 ^ rk4
    rk2 = recover_rk2_from_pair(pt0, ct0, rk0, rk1, rk3, rk4)

    # verify quickly on a chunk of pairs
    ok = True
    for pt, ct in pairs[:500]:
        if encrypt_with_rks(pt, rk0, rk1, rk2, rk3, rk4) != ct:
            ok = False
            break

    if ok:
        sol = (rk1, rk2, rk4)
        break

if not sol:
    raise SystemExit("[-] No solution found (unexpected).")

rk1, rk2, rk4 = sol
print(f"[+] Found round keys:")
print(f"    rk0=0x{rk0:08x}")
print(f"    rk1=0x{rk1:08x}")
print(f"    rk2=0x{rk2:08x}")
print(f"    rk3=0x{rk3:08x}")
print(f"    rk4=0x{rk4:08x}")

# ---------------- Step 3: decrypt flag blocks ----------------
blocks = [decrypt_with_rks(x, rk0, rk1, rk2, rk3, rk4) for x in enc_flag]
raw = b"".join(struct.pack(">I", b) for b in blocks).rstrip(b"\x00")

# The decrypted bytes are hex-ASCII of the actual flag
hex_str = raw.decode()
flag = bytes.fromhex(hex_str).decode()

print("[+] flag:", flag)