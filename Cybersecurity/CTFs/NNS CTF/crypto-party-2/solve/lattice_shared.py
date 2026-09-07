import logging

from sage.all import ZZ, QQ, matrix, lcm


def _lll_rational_safe(B):
    """
    Sage's Matrix_rational_dense.LLL() crashes (SIGILL inside _clear_denom)
    on matrices whose entries span an extreme dynamic range (as produced by
    extended_hnp, mixing ~2^256-scale integers with ~2^-300-scale deltas).
    Work around it by manually clearing denominators to a common scale,
    running LLL on the resulting exact-integer matrix, then rescaling back.
    """
    if B.base_ring() is ZZ:
        return B.LLL()

    denoms = [e.denominator() for e in B.list()]
    S = lcm(denoms) if denoms else ZZ(1)
    if S == 1:
        return B.change_ring(ZZ).LLL().change_ring(QQ)

    B_int = matrix(ZZ, B.nrows(), B.ncols(), [e * S for e in B.list()])
    B_reduced = B_int.LLL()
    return matrix(QQ, B_reduced.nrows(), B_reduced.ncols(), [e / S for e in B_reduced.list()])


def shortest_vectors(B):
    """
    Computes the shortest non-zero vectors in a lattice.
    :param B: the basis of the lattice
    :return: a generator generating the shortest non-zero vectors
    """
    logging.debug(f"Computing shortest vectors in {B.nrows()} x {B.ncols()} matrix...")
    B = _lll_rational_safe(B)

    for row in B.rows():
        if not row.is_zero():
            yield row


# Babai's Nearest Plane Algorithm from "Lecture 3: CVP Algorithm" by Oded Regev.
def _closest_vectors_babai(B, t):
    B = _lll_rational_safe(B)

    for G in B.gram_schmidt():
        b = t
        for j in reversed(range(B.nrows())):
            b -= round((b * G[j]) / (G[j] * G[j])) * B[j]

        yield t - b


def _closest_vectors_embedding(B, t):
    B_ = B.new_matrix(B.nrows() + 1, B.ncols() + 1)
    for row in range(B.nrows()):
        for col in range(B.ncols()):
            B_[row, col] = B[row, col]

    for col in range(B.ncols()):
        B_[B.nrows(), col] = t[col]

    B_[B.nrows(), B.ncols()] = 1
    yield from shortest_vectors(B_)


def closest_vectors(B, t, algorithm="embedding"):
    """
    Computes the closest vectors in a lattice to a target vector.
    :param B: the basis of the lattice
    :param t: the target vector
    :param algorithm: the algorithm to use, can be "babai" or "embedding" (default: "embedding")
    :return: a generator generating the shortest non-zero vectors
    """
    logging.debug(f"Computing closest vectors in {B.nrows()} x {B.ncols()} matrix...")
    if algorithm == "babai":
        yield from _closest_vectors_babai(B, t)
    elif algorithm == "embedding":
        yield from _closest_vectors_embedding(B, t)
