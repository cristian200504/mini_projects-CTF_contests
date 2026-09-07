"""Estimate the divisor's phase, then correct rounding in the exact ideal."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import pickle
import sys
from fractions import Fraction
from math import lcm
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'solve_ideal.py')}
exec((ROOT/'solve_ideal.py').read_text().split('inv3 = pow(3, -1, Q)')[0],ns)
base=ns['base']; n=base.N
diffs=[]
for _,s in base.DATA['sigs']:
    t=base.multiply(base.H,s)
    diffs.append(base.center([(x-y)*pow(3,-1,base.Q)%base.Q for x,y in zip(t,s)]))
ns['differences']=diffs
twist=np.exp(-1j*np.pi*np.arange(n)/n)
spectra=np.fft.fft(np.asarray(diffs)*twist,axis=1)
amplitude=np.sqrt(np.mean(np.abs(spectra)**2,axis=0))
X=spectra/amplitude*np.sqrt(n)

def objective(theta):
    phase=np.concatenate((theta,-theta[::-1]))
    Z=X*np.exp(1j*phase)
    Y=(np.fft.ifft(Z,axis=1)/twist).real
    score=np.mean(Y**4)
    G=np.fft.fft((4*Y**3/Y.size)*twist,axis=1)
    grad=-np.imag(np.sum(np.conj(G)*Z,axis=0))/n
    return score,grad[:n//2]-grad[n//2:][::-1]

# These exact characters describe membership in the integer ideal.
hnf=pickle.loads((ROOT/'basis_ideal_hnf.pkl').read_bytes())
characters=[]
for j in range(n):
    if hnf[j][j]==1: continue
    v=[Fraction(0) for _ in range(n)]
    for k in range(n-1,-1,-1):
        v[k]=(Fraction(int(k==j))-sum(hnf[k][i]*v[i] for i in range(k+1,n)))/hnf[k][k]
    denom=lcm(*(x.denominator for x in v))
    characters.append(([int(x*denom)%denom for x in v],denom))

def syndrome(v):
    return tuple(sum(int(x)*a for x,a in zip(v,c))%m for c,m in characters)

mods=[m for _,m in characters]
def plus(a,b): return tuple((x+y)%m for x,y,m in zip(a,b,mods))
def minus(a,b): return tuple((x-y)%m for x,y,m in zip(a,b,mods))
zero=tuple(0 for _ in mods)

def repair(estimate, width=80):
    rounded=np.clip(np.rint(estimate),-2,2).astype(int).tolist()
    target=minus(zero,syndrome(rounded))
    if target==zero: return rounded
    # Try alternative roundings at the most uncertain positions. Any solution
    # is checked against exact ideal membership, independent of the estimate.
    choices=[]
    for i,x in enumerate(estimate):
        for delta in (-1,1):
            if -2<=rounded[i]+delta<=2:
                cost=abs(rounded[i]+delta-x)-abs(rounded[i]-x)
                sv=tuple(delta*c[i]%m for c,m in characters)
                choices.append((cost,i,delta,sv))
    choices.sort(key=lambda z:z[0]); choices=choices[:width]
    table={zero:()}
    for a in range(len(choices)):
        table[choices[a][3]]=(a,)
        for b in range(a):
            if choices[a][1]!=choices[b][1]:
                table[plus(choices[a][3],choices[b][3])]=(a,b)
    for sv,indices in table.items():
        other=table.get(minus(target,sv))
        if other is None: continue
        all_indices=indices+other
        positions=[choices[a][1] for a in all_indices]
        if len(set(positions))!=len(positions): continue
        candidate=rounded[:]
        for a in all_indices:
            candidate[choices[a][1]]+=choices[a][2]
        assert syndrome(candidate)==zero
        return candidate
    return None

def repair_subset(estimate,width=32):
    rounded=np.clip(np.rint(estimate),-2,2).astype(int).tolist()
    target=minus(zero,syndrome(rounded))
    choices=[]
    for i,x in enumerate(estimate):
        options=[delta for delta in (-1,1) if -2<=rounded[i]+delta<=2]
        delta=min(options,key=lambda d:abs(rounded[i]+d-x))
        cost=abs(rounded[i]+delta-x)-abs(rounded[i]-x)
        choices.append((cost,i,delta,tuple(delta*c[i]%m for c,m in characters)))
    choices.sort(key=lambda c:c[0]); choices=choices[:width]
    cut=width//2
    left=[zero]
    for _,_,_,sv in choices[:cut]:
        left.extend(plus(x,sv) for x in left[:])
    lookup={sv:mask for mask,sv in enumerate(left)}
    right=[zero]
    for _,_,_,sv in choices[cut:]:
        right.extend(plus(x,sv) for x in right[:])
    for mask,sv in enumerate(right):
        partner=lookup.get(minus(target,sv))
        if partner is None: continue
        full=partner+(mask<<cut)
        candidate=rounded[:]
        for k,(_,i,delta,_) in enumerate(choices):
            if full>>k&1: candidate[i]+=delta
        assert syndrome(candidate)==zero
        return candidate
    return None

rng=np.random.default_rng(20260906)
trial=rng.normal(size=n//2)
value,gradient=objective(trial)
direction=rng.normal(size=n//2); eps=1e-6
numerical=(objective(trial+eps*direction)[0]-objective(trial-eps*direction)[0])/(2*eps)
assert abs(numerical-gradient@direction)<1e-6
base.log('Exact ideal characters built; phase gradient checked')
if len(sys.argv)>1 and sys.argv[1]=='refine':
    fit=pickle.loads((ROOT/'phase_fit.pkl').read_bytes())
    phase=np.concatenate((fit['theta'],-fit['theta'][::-1]))
    estimate=(np.fft.ifft(amplitude*np.exp(-1j*phase))/twist).real
    estimate*=np.sqrt(296)/np.linalg.norm(estimate)
    for width in (32,36,40):
        for scale in (1.,.975,1.025,.95,1.05,.925,1.075,.9,1.1):
            base.log('Subset correction',width,'scale',scale)
            candidate=repair_subset(estimate*scale,width)
            if candidate is not None:
                if ns['inspect']([candidate],'subset recovery'): raise SystemExit(0)
    raise SystemExit('No subset correction')
best=10
for restart in range(100):
    fit=minimize(objective,rng.uniform(-np.pi,np.pi,size=n//2),jac=True,method='L-BFGS-B',
                 options={'maxiter':1200,'ftol':1e-12,'gtol':1e-7,'maxls':40})
    if fit.fun<best:
        best=fit.fun
        base.log('Phase restart',restart,'kurtosis',fit.fun,'iterations',fit.nit)
        (ROOT/'phase_fit.pkl').write_bytes(pickle.dumps(dict(theta=fit.x,score=fit.fun)))
    if fit.fun>2.25: continue
    phase=np.concatenate((fit.x,-fit.x[::-1]))
    estimate=(np.fft.ifft(amplitude*np.exp(-1j*phase))/twist).real
    estimate*=np.sqrt(296)/np.linalg.norm(estimate)
    for scale in np.linspace(.85,1.15,13):
        candidate=repair(estimate*scale)
        if candidate is not None:
            base.log('Exact lattice candidate from phase estimate',restart,'scale',scale)
            if ns['inspect']([candidate],'statistical recovery'):
                raise SystemExit(0)
base.log('No recovered divisor after phase search')
