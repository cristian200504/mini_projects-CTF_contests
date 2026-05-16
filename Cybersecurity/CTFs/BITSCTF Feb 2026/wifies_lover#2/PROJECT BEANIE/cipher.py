R = [0x00000000000000000000000000000000, 0x000000000000000013198a2e03707344,
     0x0000000000000000a4093822299f31d0, 0x0000000000000000082efa98ec4e6c89,
     0x0000000000000000452821e638d01377, 0x0000000000000000be5466cf34e90c6c,
     0x00000000000000007ef84f78fd955cb1, 0x000000000000000085840851f1ac43aa,
     0x0000000000000000c882d32f25323c54, 0x000000000000000064a51195e0e3610d]
S = [0, 4, 2, 11, 10, 12, 9, 8, 5, 15, 13, 3, 7, 1, 6, 14]
I = [0, 13, 2, 11, 1, 8, 14, 12, 7, 6, 4, 3, 5, 10, 15, 9]

def a(s):
    r = 0
    for i in range(8): r |= S[(s >> (i * 4)) & 0xF] << (i * 4)
    return r

def b(s):
    r = 0
    for i in range(8): r |= I[(s >> (i * 4)) & 0xF] << (i * 4)
    return r

def c(s): return (s & 0xF0F0F0F0) | ((s & 0x0F0F0000) >> 16) | ((s & 0x00000F0F) << 16)

def d(x): return (0xF) & ((x << 1) ^ (((x >> 3) & 1) * 0x3))

def e(x, y):
    r = 0
    if y & 1: r ^= x
    if y & 2: r ^= d(x)
    if y & 4: r ^= d(d(x))
    if y & 8: r ^= d(d(d(x)))
    return r & 0xF

def f(s):
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

def g(s, k, r):
    if r == 0: return s
    for i in range(r - 1):
        s ^= k[i]; s = a(s); s = c(s); s = f(s)
    s ^= k[r - 1]; s = a(s); s = c(s); s ^= k[r]
    return s

def h(s, k, r):
    if r == 0: return s
    s ^= k[r]; s = c(s); s = b(s); s ^= k[r - 1]
    for i in range(r - 2, -1, -1):
        s = f(s); s = c(s); s = b(s); s ^= k[i]
    return s

def i(s):
    r = 0
    for j in range(32): r |= S[(s >> (j * 4)) & 0xF] << (j * 4)
    return r

def j(col):
    c0, c1, c2, c3 = (col >> 12) & 0xF, (col >> 8) & 0xF, (col >> 4) & 0xF, col & 0xF
    return (((c0 & 0b0111) ^ (c1 & 0b1011) ^ (c2 & 0b1101) ^ (c3 & 0b1110)) << 12 |
            ((c0 & 0b1011) ^ (c1 & 0b1101) ^ (c2 & 0b1110) ^ (c3 & 0b0111)) << 8 |
            ((c0 & 0b1101) ^ (c1 & 0b1110) ^ (c2 & 0b0111) ^ (c3 & 0b1011)) << 4 |
            ((c0 & 0b1110) ^ (c1 & 0b0111) ^ (c2 & 0b1011) ^ (c3 & 0b1101)))

def k(col):
    c0, c1, c2, c3 = (col >> 12) & 0xF, (col >> 8) & 0xF, (col >> 4) & 0xF, col & 0xF
    return (((c0 & 0b1011) ^ (c1 & 0b1101) ^ (c2 & 0b1110) ^ (c3 & 0b0111)) << 12 |
            ((c0 & 0b1101) ^ (c1 & 0b1110) ^ (c2 & 0b0111) ^ (c3 & 0b1011)) << 8 |
            ((c0 & 0b1110) ^ (c1 & 0b0111) ^ (c2 & 0b1011) ^ (c3 & 0b1101)) << 4 |
            ((c0 & 0b0111) ^ (c1 & 0b1011) ^ (c2 & 0b1101) ^ (c3 & 0b1110)))

def l(s):
    return (j((s >> 112) & 0xFFFF) << 112 | k((s >> 96) & 0xFFFF) << 96 |
            k((s >> 80) & 0xFFFF) << 80 | j((s >> 64) & 0xFFFF) << 64 |
            j((s >> 48) & 0xFFFF) << 48 | k((s >> 32) & 0xFFFF) << 32 |
            k((s >> 16) & 0xFFFF) << 16 | j(s & 0xFFFF))

def m(s):
    r = s & 0xF000F000F000F000F000F000F000F000
    r |= (s & 0x00000F000F000F0000000F000F000F00) << 16
    r |= (s & 0x0F000000000000000F00000000000000) >> 48
    r |= (s & 0x0000000000F000F00000000000F000F0) << 32
    r |= (s & 0x00F000F00000000000F000F000000000) >> 32
    r |= (s & 0x000000000000000F000000000000000F) << 48
    r |= (s & 0x000F000F000F0000000F000F000F0000) >> 16
    return r

def n(s):
    r = 0
    r |= (s ^ (s << 32)) & (0xFFFFFFFF << 96)
    r |= (s << 32) & (0xFFFFFFFF << 64)
    r |= (s ^ (s << 32)) & (0xFFFFFFFF << 32)
    r |= (s >> 96) & 0xFFFFFFFF
    return r

def o(s):
    r = s & 0xF000F000F000F000F000F000F000F000
    r |= ((s >> 64) & 0x000000000F000F00) << 96
    r |= ((s >> 0) & 0x0F000F0000000000) << 32
    r |= ((s >> 0) & 0x000000000F000F00) << 32
    r |= ((s >> 64) & 0x0F000F0000000000) >> 32
    r |= ((s >> 0) & 0x00F000F000F000F0) << 64
    r |= ((s >> 64) & 0x00F000F000F000F0)
    r |= ((s >> 64) & 0x000F000F00000000) << 32
    r |= ((s >> 0) & 0x00000000000F000F) << 96
    r |= ((s >> 0) & 0x000F000F00000000) >> 32
    r |= ((s >> 64) & 0x00000000000F000F) << 32
    return r

def p(key, tw, rnd):
    if rnd == 0: return tw
    for x in range(rnd):
        tw ^= key; tw ^= R[x]; tw = i(tw); tw = l(tw); tw = m(tw); tw = n(tw); tw = o(tw)
    tw ^= key; tw ^= R[rnd]
    return tw

def q(et, nr):
    rk = [0] * nr
    if nr > 0: rk[0] = (et >> 96) & 0xFFFFFFFF
    if nr > 1: rk[1] = (et >> 64) & 0xFFFFFFFF
    if nr > 2: rk[2] = (et >> 32) & 0xFFFFFFFF
    if nr > 3: rk[3] = et & 0xFFFFFFFF
    if nr > 4: rk[4] = rk[0] ^ rk[1]
    if nr > 5: rk[5] = rk[2] ^ rk[3]
    if nr > 6: rk[6] = rk[0] ^ rk[2]
    if nr > 7: rk[7] = rk[1] ^ rk[3]
    if nr > 8: rk[8] = rk[0] ^ rk[3]
    if nr > 9: rk[9] = rk[1] ^ rk[2]
    return rk

def encrypt(pt, mk, tw, rnd):
    et = p(mk, tw, rnd)
    rk = q(et, rnd + 1)
    return g(pt, rk, rnd)

def decrypt(ct, mk, tw, rnd):
    et = p(mk, tw, rnd)
    rk = q(et, rnd + 1)
    return h(ct, rk, rnd)
