"""Recover d*conjugate(d) in the 128-dimensional real subfield."""
import pickle
import subprocess
from pathlib import Path
import numpy as np
from flint import fmpz_mat

ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'solve_statistical.py')}
exec((ROOT/'solve_statistical.py').read_text().split('rng=np.random.default_rng')[0],ns)
base=ns['base']; n=base.N; r=n//2

def mul(a,b):
    out=np.convolve(np.asarray(a,dtype=np.int64),np.asarray(b,dtype=np.int64))
    out=np.pad(out,(0,1))
    return [int(x) for x in out[:n]-out[n:]]
def bar(a): return [a[0]]+[-a[n-j] for j in range(1,n)]
def shift(a,j): return [a[k-j] if k>=j else -a[k-j+n] for k in range(n)]
def real_rows(a):
    result=[a[:r]]
    for j in range(1,r):
        v=[x-y for x,y in zip(shift(a,j),shift(a,n-j))]
        assert v==bar(v)
        result.append(v[:r])
    return result
def hnf(rows):
    h=fmpz_mat(rows).hnf()
    out=[[int(x) for x in row] for row in h.tolist() if any(row)]
    assert len(out)==r
    return out

norms=[mul(d,bar(d)) for d in ns['diffs']]
cache=ROOT/'basis_real_hnf.pkl'
if cache.exists(): basis=pickle.loads(cache.read_bytes())
else:
    base.log('Building real ideal from exact squared magnitudes')
    basis=hnf(real_rows(norms[0])+real_rows(norms[1]))
    for i in (2,3):
        updated=hnf(basis+real_rows(norms[i]))
        base.log('Real ideal added sample',i,'unchanged',updated==basis)
        if updated==basis: break
        basis=updated
    cache.write_bytes(pickle.dumps(basis))
det=abs(int(fmpz_mat(basis).det()))
base.log('Real ideal determinant bits',det.bit_length())
basis=[[int(x) for x in row] for row in fmpz_mat(basis).lll().tolist()]
(ROOT/'basis_real.pkl').write_bytes(pickle.dumps(basis))

def inspect(rows,target,label):
    ordered=sorted(rows,key=lambda v:sum(x*x for x in v))
    base.log(label,'minimum',sum(x*x for x in ordered[0])**.5)
    for row in ordered:
        if row[-1] not in (-20,20): continue
        sign=row[-1]//20
        c=[x-sign*y for x,y in zip(target,row[:-1])]
        if not 200<c[0]<450 or max(map(abs,c[1:]))>100: continue
        full=c+[0]+[-x for x in c[:0:-1]]
        spectral=(np.fft.fft(np.asarray(full)*ns['twist'])).real
        if min(spectral)<=0: continue
        candidate_det=abs(int(fmpz_mat(real_rows(full)).det()))
        if candidate_det!=det: continue
        base.log('Recovered positive norm candidate, trace coefficient',c[0])
        (ROOT/'recovered_norm.pkl').write_bytes(pickle.dumps(full))
        return True
    return False

mean=np.mean(np.asarray(norms,dtype=float),axis=0)
for variance in (7.8,8.0,7.6,8.2):
    target=np.rint(mean[:r]/(n*variance)).astype(int).tolist()
    rows=[row+[0] for row in basis]+[target+[20]]
    base.log('Norm BDD LLL, variance',variance)
    rows=[[int(x) for x in row] for row in fmpz_mat(rows).lll().tolist()]
    if inspect(rows,target,'norm LLL'): raise SystemExit(0)
    for block in (20,28,36):
        base.log('Norm BDD BKZ',block)
        proc=subprocess.run([base.FPLLL,'-a','bkz','-b',str(block),'-bkzmaxloops','4','-f','mpfr','-p','160'],
                            input=base.encode(rows),text=True,capture_output=True,env=base.ENV)
        if proc.returncode and 'loops limit exceeded' not in proc.stderr:
            base.log('Failure',proc.stderr[:300]); continue
        rows=[[int(x) for x in part.split()] for part in proc.stdout.replace(']','').split('[') if part.strip()]
        assert len(rows)==r+1
        if inspect(rows,target,'norm BKZ-'+str(block)): raise SystemExit(0)
base.log('No norm recovered')
