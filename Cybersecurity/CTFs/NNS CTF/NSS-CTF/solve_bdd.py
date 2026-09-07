"""Decode a rounded divisor estimate in the exact integer ideal."""
from pathlib import Path
import pickle
import subprocess
import numpy as np
from flint import fmpz_mat

ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'solve_statistical.py')}
exec((ROOT/'solve_statistical.py').read_text().split('rng=np.random.default_rng')[0],ns)
base=ns['base']; n=base.N
fit=pickle.loads((ROOT/'phase_fit.pkl').read_bytes())
phase=np.concatenate((fit['theta'],-fit['theta'][::-1]))
estimate=(np.fft.ifft(ns['amplitude']*np.exp(-1j*phase))/ns['twist']).real
estimate*=np.sqrt(296)/np.linalg.norm(estimate)
target=np.clip(np.rint(estimate),-2,2).astype(int).tolist()
basis=pickle.loads((ROOT/'basis_ideal.pkl').read_bytes())
rows=[row+[0] for row in basis]+[target+[1]]
base.log('Reducing BDD embedding')
rows=[[int(x) for x in row] for row in fmpz_mat(rows).lll().tolist()]

def inspect(rows,label):
    ordered=sorted(rows,key=lambda r:sum(x*x for x in r))
    base.log(label,'minimum',sum(x*x for x in ordered[0])**.5)
    for row in ordered:
        if abs(row[-1])!=1: continue
        d=[x-row[-1]*y for x,y in zip(target,row[:-1])]
        if max(map(abs,d))<=2 and ns['ns']['inspect']([d],label): return True
    return False

if inspect(rows,'BDD LLL'): raise SystemExit(0)
for block in (20,24,28,32,36,40):
    base.log('BDD BKZ',block)
    proc=subprocess.run([base.FPLLL,'-a','bkz','-b',str(block),'-bkzmaxloops','4','-f','mpfr','-p','160'],
                        input=base.encode(rows),text=True,capture_output=True,env=base.ENV)
    if proc.returncode and 'loops limit exceeded' not in proc.stderr:
        base.log('Failed',proc.stderr[:500]);continue
    rows=[[int(x) for x in part.split()] for part in proc.stdout.replace(']','').split('[') if part.strip()]
    assert len(rows)==n+1
    (ROOT/'basis_bdd.pkl').write_bytes(pickle.dumps(rows))
    if inspect(rows,'BDD BKZ-'+str(block)): raise SystemExit(0)
