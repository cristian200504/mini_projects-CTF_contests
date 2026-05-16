from common import split, merge, q
from ntt_constants import roots_dict_Zq, inv_mod_q
i2 = 6145
sqr1 = roots_dict_Zq[2][0]


def split_ntt(f_ntt):
    n = len(f_ntt)
    w = roots_dict_Zq[n]
    f0_ntt = [0] * (n // 2)
    f1_ntt = [0] * (n // 2)
    for i in range(n // 2):
        f0_ntt[i] = (i2 * (f_ntt[2 * i] + f_ntt[2 * i + 1])) % q
        f1_ntt[i] = (i2 * (f_ntt[2 * i] - f_ntt[2 * i + 1]) * inv_mod_q[w[2 * i]]) % q
    return [f0_ntt, f1_ntt]


def merge_ntt(f_list_ntt):
    f0_ntt, f1_ntt = f_list_ntt
    n = 2 * len(f0_ntt)
    w = roots_dict_Zq[n]
    f_ntt = [0] * n
    for i in range(n // 2):
        f_ntt[2 * i + 0] = (f0_ntt[i] + w[2 * i] * f1_ntt[i]) % q
        f_ntt[2 * i + 1] = (f0_ntt[i] - w[2 * i] * f1_ntt[i]) % q
    return f_ntt


def ntt(f):
    n = len(f)
    if (n > 2):
        f0, f1 = split(f)
        f0_ntt = ntt(f0)
        f1_ntt = ntt(f1)
        f_ntt = merge_ntt([f0_ntt, f1_ntt])
    elif (n == 2):
        f_ntt = [0] * n
        f_ntt[0] = (f[0] + sqr1 * f[1]) % q
        f_ntt[1] = (f[0] - sqr1 * f[1]) % q
    return f_ntt


def intt(f_ntt):
    n = len(f_ntt)
    if (n > 2):
        f0_ntt, f1_ntt = split_ntt(f_ntt)
        f0 = intt(f0_ntt)
        f1 = intt(f1_ntt)
        f = merge([f0, f1])
    elif (n == 2):
        f = [0] * n
        f[0] = (i2 * (f_ntt[0] + f_ntt[1])) % q
        f[1] = (i2 * inv_mod_q[1479] * (f_ntt[0] - f_ntt[1])) % q
    return f


def add_zq(f, g):
    assert len(f) == len(g)
    deg = len(f)
    return [(f[i] + g[i]) % q for i in range(deg)]


def neg_zq(f):
    deg = len(f)
    return [(- f[i]) % q for i in range(deg)]


def sub_zq(f, g):
    return add_zq(f, neg_zq(g))


def mul_zq(f, g):
    return intt(mul_ntt(ntt(f), ntt(g)))


def div_zq(f, g):
    try:
        return intt(div_ntt(ntt(f), ntt(g)))
    except ZeroDivisionError:
        raise


def add_ntt(f_ntt, g_ntt):
    return add_zq(f_ntt, g_ntt)


def sub_ntt(f_ntt, g_ntt):
    return sub_zq(f_ntt, g_ntt)


def mul_ntt(f_ntt, g_ntt):
    assert len(f_ntt) == len(g_ntt)
    deg = len(f_ntt)
    return [(f_ntt[i] * g_ntt[i]) % q for i in range(deg)]


def div_ntt(f_ntt, g_ntt):
    assert len(f_ntt) == len(g_ntt)
    deg = len(f_ntt)
    if any(elt == 0 for elt in g_ntt):
        raise ZeroDivisionError
    return [(f_ntt[i] * inv_mod_q[g_ntt[i]]) % q for i in range(deg)]

ntt_ratio = 1
