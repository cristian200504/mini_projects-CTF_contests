"""Recover the key using the shared ternary component in f and g.

For d=(g-f)/3 and a=f+2*d, both a and d are unusually short.
The public equation is d = (h-1)/(1+2*h) * a modulo q.
"""
import os
import pickle
import subprocess
import sys
from pathlib import Path
import agent_alt_pubkey as base

ROOT = Path(__file__).resolve().parent
ns = {'__file__': str(ROOT / 'solve.py')}
exec((ROOT / 'solve.py').read_text().split('order = list(range(10))')[0], ns)
SCALE = 2
N, Q = base.N, base.Q

def build_basis():
    den = [(2*x + (i == 0)) % Q for i,x in enumerate(base.H)]
    inv = ns['ring_inv'](den)
    assert inv is not None
    hp = base.multiply([(x-(i==0))%Q for i,x in enumerate(base.H)], inv)
    basis = [[0]*(2*N) for _ in range(2*N)]
    for j in range(N):
        basis[j][j] = 1
        basis[j][N:] = [SCALE*x for x in base.shift(hp,j)]
        basis[N+j][N+j] = SCALE*Q
    return basis

def inspect(basis, label):
    rows=sorted(basis,key=lambda r:sum(x*x for x in r))
    base.log(label, 'norms', [round(sum(x*x for x in r)**.5,2) for r in rows[:8]])
    for row in rows:
        if sum(x*x for x in row)>120**2: break
        assert all(x%SCALE==0 for x in row[N:])
        d=[x//SCALE for x in row[N:]]
        f=[a-2*b for a,b in zip(row[:N],d)]
        if max(map(abs,f))>4: continue
        result=base.validate(f)
        if result:
            import json
            f,g,u,key,plaintext=result
            fi=ns['ring_inv'](f)
            ws=[base.center(base.multiply(fi,s)) for m,s in base.DATA['sigs']]
            record=dict(f=f,g=g,u=u,key=key.hex(),flag=plaintext.decode(),w=ws)
            (ROOT/'recovered.json').write_text(json.dumps(record,indent=2))
            (ROOT/'flag.txt').write_text(plaintext.decode()+'\n')
            base.log('RECOVERED',plaintext.decode())
            subprocess.run([sys.executable,str(ROOT/'verify.py')],check=True)
            return True
    return False

cache=ROOT/'basis_balanced.pkl'
if cache.exists():
    b=pickle.loads(cache.read_bytes())
else:
    b=build_basis()
    base.log('Balanced lattice: flatter, dimension',len(b))
    proc=subprocess.run([base.FLATTER,'-rhf','1.012'],input=base.encode(b),text=True,capture_output=True,env=base.ENV,check=True)
    b=base.decode(proc.stdout)
    assert len(b)==2*N
    cache.write_bytes(pickle.dumps(b))
if inspect(b,'flatter'): sys.exit()
for block in [int(x) for x in (sys.argv[1] if len(sys.argv)>1 else '20,24,28,32,36,40').split(',')]:
    base.log('Balanced lattice: BKZ',block)
    proc=subprocess.run([base.FPLLL,'-a','bkz','-b',str(block),'-bkzmaxloops','4','-f','mpfr','-p','160'],input=base.encode(b),text=True,capture_output=True,env=base.ENV)
    if proc.returncode and 'loops limit exceeded' not in proc.stderr and 'time limit exceeded' not in proc.stderr:
        base.log('Reduction failed',proc.stderr[:500]); continue
    b=base.decode(proc.stdout)
    assert len(b)==2*N
    cache.write_bytes(pickle.dumps(b))
    if inspect(b,'BKZ-'+str(block)): sys.exit()
base.log('No key in this reduction')
