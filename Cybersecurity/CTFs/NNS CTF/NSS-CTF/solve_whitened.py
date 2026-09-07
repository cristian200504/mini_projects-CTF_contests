"""Whiten the exact-product ideal using the ten observed spectral powers."""
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
from flint import fmpz_mat

ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'solve_ideal.py')}
exec((ROOT/'solve_ideal.py').read_text().split('inv3 = pow(3, -1, Q)')[0],ns)
base=ns['base']
n=base.N
diffs=[]
for _,s in base.DATA['sigs']:
    t=base.multiply(base.H,s)
    diffs.append(base.center([(x-y)*pow(3,-1,base.Q)%base.Q for x,y in zip(t,s)]))
ns['differences']=diffs

# Twisting a real coefficient vector evaluates it at the odd 512th roots
# rather than the 256th roots used by an ordinary FFT.
twist=np.exp(-1j*np.pi*np.arange(n)/n)
spectra=np.fft.fft(np.asarray(diffs)*twist,axis=1)
weights=1/np.sqrt(np.mean(np.abs(spectra)**2,axis=0))
weights/=np.exp(np.mean(np.log(weights)))
assert np.allclose(weights,weights[::-1])

source=ROOT/'basis_ideal.pkl'
rows=pickle.loads(source.read_bytes())
B=fmpz_mat(rows)
transformed=np.fft.ifft(np.fft.fft(np.asarray(rows,dtype=float)*twist,axis=1)*weights,axis=1)/twist
assert np.max(np.abs(transformed.imag))<1e-7
scale=2**40
M=fmpz_mat([[int(round(x*scale)) for x in row] for row in transformed.real])
base.log('Spectral whitening:',float(min(weights)),float(max(weights)),'basis condition',float(np.linalg.cond(np.asarray(rows,dtype=float))))
base.log('Reducing whitened integer basis with FLINT')
L,U=M.lll(transform=True,delta=.99,eta=.501)
assert U*M==L
original=U*B
reduced=[[int(x) for x in row] for row in original.tolist()]
(ROOT/'basis_ideal_whitened.pkl').write_bytes(pickle.dumps(reduced))
base.log('Whitened minimum norm',min(sum(int(x)**2 for x in row)**.5 for row in L.tolist())/scale)
if ns['inspect'](reduced,'whitened LLL'):
    sys.exit(0)
for block in (20,24,28,32,36,40,44,48):
    base.log('Whitened BKZ',block)
    encoded=base.encode([[int(x) for x in row] for row in L.tolist()])
    proc=subprocess.run([base.FPLLL,'-a','bkz','-b',str(block),'-bkzmaxloops','4','-f','mpfr','-p','160','-of','u'],
                        input=encoded,text=True,capture_output=True,env=base.ENV)
    if proc.returncode and 'loops limit exceeded' not in proc.stderr:
        base.log('BKZ failed',proc.stderr[:500]); continue
    T=fmpz_mat(ns['decode'](proc.stdout))
    L=T*L
    original=T*original
    reduced=[[int(x) for x in row] for row in original.tolist()]
    (ROOT/'basis_ideal_whitened.pkl').write_bytes(pickle.dumps(reduced))
    if ns['inspect'](reduced,'whitened BKZ-'+str(block)):
        sys.exit(0)
base.log('No key found in whitened reduction')
