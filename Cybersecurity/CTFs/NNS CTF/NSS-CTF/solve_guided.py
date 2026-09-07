"""Use confident estimated coefficients to shorten the exact correction lattice."""
from pathlib import Path
import pickle
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
chars=ns['characters']; count=len(chars); mult=10000
for k in (96,128,160,192,208):
    for scale in (1.,.975,1.025,.95,1.05,.9,1.1):
        current=estimate*scale
        rounded=np.clip(np.rint(current),-2,2).astype(int).tolist()
        confidence=[]
        for i,x in enumerate(current):
            alternatives=[a for a in range(-2,3) if a!=rounded[i]]
            confidence.append(min(abs(a-x) for a in alternatives)-abs(rounded[i]-x))
        positions=sorted(range(n),key=lambda i:confidence[i])[:k]
        dim=k+count+1
        rows=[[0]*dim for _ in range(dim)]
        for j,i in enumerate(positions):
            rows[j][j]=1
            for c,(char,mod) in enumerate(chars): rows[j][k+c]=char[i]*mult
        for c,(char,mod) in enumerate(chars): rows[k+c][k+c]=mod*mult
        for c,value in enumerate(ns['syndrome'](rounded)): rows[-1][k+c]=value*mult
        rows[-1][-1]=1
        base.log('Guided correction LLL:',k,'unknown coefficients, scale',scale)
        reduced=fmpz_mat(rows).lll(delta=.99,eta=.501)
        reduced=[[int(x) for x in row] for row in reduced.tolist()]
        for row in sorted(reduced,key=lambda r:sum(x*x for x in r)):
            if abs(row[-1])!=1 or any(row[k:-1]): continue
            candidate=rounded[:]
            for j,i in enumerate(positions): candidate[i]+=row[-1]*row[j]
            if max(map(abs,candidate))>2: continue
            assert ns['syndrome'](candidate)==ns['zero']
            if ns['ns']['inspect']([candidate],'guided correction'):
                raise SystemExit(0)
base.log('No key found in guided corrections')
