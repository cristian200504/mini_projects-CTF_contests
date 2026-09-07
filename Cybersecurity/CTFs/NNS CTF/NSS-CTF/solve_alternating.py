"""Refine a statistical phase estimate with exact integer signing vectors."""
from pathlib import Path
import pickle
import numpy as np

ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'solve_statistical.py')}
exec((ROOT/'solve_statistical.py').read_text().split('rng=np.random.default_rng')[0],ns)
base=ns['base']; n=base.N
twist=ns['twist']; spectra=ns['spectra']; amplitude=ns['amplitude']
fit=pickle.loads((ROOT/'phase_fit.pkl').read_bytes())
phase=np.concatenate((fit['theta'],-fit['theta'][::-1]))
estimate=(np.fft.ifft(amplitude*np.exp(-1j*phase))/twist).real
estimate*=np.sqrt(296)/np.linalg.norm(estimate)
best=1e99
for start_scale in (1.,.975,1.025,.95,1.05,.9,1.1):
    d=estimate*start_scale
    for iteration in range(200):
        ds=np.fft.fft(d*twist)
        w=(np.fft.ifft(spectra/ds,axis=1)/twist).real
        wi=np.clip(np.rint(w),-5,5)
        ws=np.fft.fft(wi*twist,axis=1)
        new_ds=np.sum(np.conj(ws)*spectra,axis=0)/np.sum(np.abs(ws)**2,axis=0)
        new_d=(np.fft.ifft(new_ds)/twist).real
        new_d=np.clip(new_d,-2,2)
        residual=float(np.mean(np.abs(spectra-ws*new_ds)**2)/n)
        rounded=np.rint(new_d).astype(int).tolist()
        if residual<best:
            best=residual
            if iteration%10==0: base.log('Alternation',start_scale,iteration,'residual',residual,'integer error',np.linalg.norm(new_d-np.rint(new_d)))
            (ROOT/'divisor_estimate.pkl').write_bytes(pickle.dumps(new_d))
        if ns['syndrome'](rounded)==ns['zero']:
            if ns['ns']['inspect']([rounded],'alternating integer recovery'):
                raise SystemExit(0)
        change=np.linalg.norm(new_d-d)
        d=new_d
        if change<1e-9: break
    base.log('Alternation ended',start_scale,'iteration',iteration,'residual',residual)
    candidate=ns['repair'](d,160)
    if candidate is not None and ns['ns']['inspect']([candidate],'alternating corrected recovery'):
        raise SystemExit(0)
base.log('No key found by alternation')
