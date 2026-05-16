from math import floor
from os import urandom
MAX_SIGMA = 1.8205
INV_2SIGMA2 = 1 / (2 * (MAX_SIGMA ** 2))
RCDT_PREC = 72
LN2 = 0.69314718056
ILN2 = 1.44269504089
RCDT = [
    3024686241123004913666,
    1564742784480091954050,
    636254429462080897535,
    199560484645026482916,
    47667343854657281903,
    8595902006365044063,
    1163297957344668388,
    117656387352093658,
    8867391802663976,
    496969357462633,
    20680885154299,
    638331848991,
    14602316184,
    247426747,
    3104126,
    28824,
    198,
    1]
C = [
    0x00000004741183A3,
    0x00000036548CFC06,
    0x0000024FDCBF140A,
    0x0000171D939DE045,
    0x0000D00CF58F6F84,
    0x000680681CF796E3,
    0x002D82D8305B0FEA,
    0x011111110E066FD0,
    0x0555555555070F00,
    0x155555555581FF00,
    0x400000000002B400,
    0x7FFFFFFFFFFF4800,
    0x8000000000000000]


def basesampler(randombytes=urandom):
    u = int.from_bytes(randombytes(RCDT_PREC >> 3), "little")
    z0 = 0
    for elt in RCDT:
        z0 += int(u < elt)
    return z0


def approxexp(x, ccs):
    y = C[0]
    z = int(x * (1 << 63))
    for elt in C[1:]:
        y = elt - ((z * y) >> 63)
    z = int(ccs * (1 << 63)) << 1
    y = (z * y) >> 63
    return y


def berexp(x, ccs, randombytes=urandom):
    s = int(x * ILN2)
    r = x - s * LN2
    s = min(s, 63)
    z = (approxexp(r, ccs) - 1) >> s
    for i in range(56, -8, -8):
        p = int.from_bytes(randombytes(1), "little")
        w = p - ((z >> i) & 0xFF)
        if w:
            break
    return (w < 0)


def samplerz(mu, sigma, sigmin, randombytes=urandom):
    s = int(floor(mu))
    r = mu - s
    dss = 1 / (2 * sigma * sigma)
    ccs = sigmin / sigma

    while(1):
        z0 = basesampler(randombytes=randombytes)
        b = int.from_bytes(randombytes(1), "little")
        b &= 1
        z = b + (2 * b - 1) * z0
        x = ((z - r) ** 2) * dss
        x -= (z0 ** 2) * INV_2SIGMA2
        if berexp(x, ccs, randombytes=randombytes):
            return z + s
