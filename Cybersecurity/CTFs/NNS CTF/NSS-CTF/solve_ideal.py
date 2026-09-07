"""Recover the shared short divisor of nearly unwrapped signature differences.

With d=(g-f)/3, the centered D_i=(h*s_i-s_i)/3 modulo q usually
equals the exact negacyclic integer product d*w_i.  Their joint integer
ideal therefore gives a 256-dimensional lattice containing d.
"""
import json
import pickle
import subprocess
import sys
from pathlib import Path

from flint import fmpz_mat
import agent_alt_pubkey as base

ROOT = Path(__file__).resolve().parent
N, Q = base.N, base.Q
ns = {'__file__': str(ROOT / 'solve.py')}
exec((ROOT / 'solve.py').read_text().split('order = list(range(10))')[0], ns)


def signed_shift(poly, amount):
    return [poly[k-amount] if k >= amount else -poly[k-amount+N] for k in range(N)]


def multiplication_rows(poly):
    return [signed_shift(poly, j) for j in range(N)]


def exact_ideal_hnf(rows):
    reduced = fmpz_mat(rows).hnf()
    result = [[int(reduced[i, j]) for j in range(N)] for i in range(reduced.nrows())]
    result = [row for row in result if any(row)]
    assert len(result) == N
    return result


def decode(raw):
    rows = [[int(x) for x in chunk.split()] for chunk in raw.replace(']', '').split('[') if chunk.strip()]
    assert len(rows) == N and all(len(row) == N for row in rows)
    return rows


hm1 = [(x-(i == 0)) % Q for i, x in enumerate(base.H)]
inv = ns['ring_inv'](hm1)
assert inv is not None
f_from_d = [(3*x) % Q for x in inv]


def inspect(basis, label):
    ordered = sorted(basis, key=lambda row: sum(x*x for x in row))
    base.log(label, 'norms', [round(sum(x*x for x in row)**.5, 2) for row in ordered[:8]])
    for d in ordered:
        if sum(x*x for x in d) > 100**2:
            break
        candidate = base.center(base.multiply(d, f_from_d))
        if max(map(abs, candidate)) > 4:
            continue
        result = base.validate(candidate)
        if not result:
            continue
        f, g, u, key, plaintext = result
        fi = ns['ring_inv'](f)
        ws = [base.center(base.multiply(fi, s)) for m, s in base.DATA['sigs']]
        exact_count = 0
        actual_d = [(y-x)//3 for x, y in zip(f, g)]
        for D, w in zip(differences, ws):
            prod = [0]*N
            for i, di in enumerate(actual_d):
                for j, wj in enumerate(w):
                    k = i+j
                    prod[k % N] += di*wj if k < N else -di*wj
            exact_count += prod == D
        record = dict(f=f, g=g, u=u, key=key.hex(), flag=plaintext.decode(), w=ws,
                      exact_difference_products=exact_count)
        (ROOT/'recovered.json').write_text(json.dumps(record, indent=2))
        (ROOT/'flag.txt').write_text(plaintext.decode()+'\n')
        base.log('RECOVERED', plaintext.decode(), 'exact products', exact_count)
        subprocess.run([sys.executable, str(ROOT/'verify.py')], check=True)
        return True
    return False


inv3 = pow(3, -1, Q)
differences = []
for i, (m, s) in enumerate(base.DATA['sigs']):
    t = base.multiply(base.H, s)
    D = base.center([(y-x)*inv3 % Q for x, y in zip(s, t)])
    differences.append(D)
    base.log('D', i, 'max', max(map(abs, D)), 'sum parity', sum(D) % 2)

cache = ROOT/'basis_ideal.pkl'
if cache.exists():
    basis = pickle.loads(cache.read_bytes())
    base.log('Loaded reduced ideal basis')
else:
    # Three independent generators usually remove all extraneous factors.
    base.log('Computing HNF from the first two exact-product candidates')
    basis = exact_ideal_hnf(multiplication_rows(differences[0])+multiplication_rows(differences[1]))
    base.log('HNF completed, determinant bits', abs(int(fmpz_mat(basis).det())).bit_length())
    for i in (2, 3):
        updated = exact_ideal_hnf(basis + multiplication_rows(differences[i]))
        unchanged = updated == basis
        basis = updated
        base.log('HNF added', i, 'unchanged', unchanged, 'determinant bits', abs(int(fmpz_mat(basis).det())).bit_length())
        if unchanged:
            break
    (ROOT/'basis_ideal_hnf.pkl').write_bytes(pickle.dumps(basis))
    base.log('Reducing ideal lattice with flatter')
    proc = subprocess.run([base.FLATTER, '-rhf', '1.012'], input=base.encode(basis),
                          text=True, capture_output=True, env=base.ENV)
    if proc.returncode:
        raise RuntimeError(proc.stderr[:1000])
    basis = decode(proc.stdout)
    cache.write_bytes(pickle.dumps(basis))

if inspect(basis, 'flatter'):
    sys.exit(0)
for block in [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '20,24,28,32,36,40,44,48').split(',') if x]:
    base.log('Ideal lattice BKZ', block)
    proc = subprocess.run([base.FPLLL, '-a', 'bkz', '-b', str(block), '-bkzmaxloops', '4',
                           '-f', 'mpfr', '-p', '160'], input=base.encode(basis),
                          text=True, capture_output=True, env=base.ENV)
    if proc.returncode and '[[' not in proc.stdout:
        base.log('BKZ failed', proc.stderr[:500])
        continue
    basis = decode(proc.stdout)
    cache.write_bytes(pickle.dumps(basis))
    if inspect(basis, 'BKZ-'+str(block)):
        sys.exit(0)
base.log('No key in this reduction')
