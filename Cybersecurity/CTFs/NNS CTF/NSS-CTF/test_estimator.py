"""Check the statistical estimator against a known synthetic divisor."""
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parent
ns={'__file__':str(root/'solve_statistical.py')}
exec((root/'solve_statistical.py').read_text().split('rng=np.random.default_rng')[0],ns)
n=ns['n']; twist=ns['twist']; rng=np.random.default_rng(781)
def ternary(a):
    v=np.zeros(n); v[rng.permutation(n)[:2*a]]=np.concatenate((np.ones(a),-np.ones(a)))
    return v
d=ternary(60)-ternary(88)
w=np.asarray([3*ternary(96)+rng.integers(-1,2,n)+rng.integers(-1,2,n) for i in range(10)])
Ds=np.fft.fft(w*twist,axis=1)*np.fft.fft(d*twist)
amp=np.sqrt(np.mean(np.abs(Ds)**2,axis=0))
ns['X']=Ds/amp*np.sqrt(n)
theta_true=-np.angle(np.fft.fft(d*twist))[:n//2]
print('True phase objective',ns['objective'](theta_true)[0],flush=True)
fit_true=ns['minimize'](ns['objective'],theta_true,jac=True,method='L-BFGS-B',options={'maxiter':1200,'ftol':1e-12})
print('True-start optimized objective',fit_true.fun,'phase motion',np.linalg.norm(fit_true.x-theta_true),flush=True)
for i in range(5):
    fit=ns['minimize'](ns['objective'],rng.uniform(-np.pi,np.pi,n//2),jac=True,method='L-BFGS-B',options={'maxiter':1200,'ftol':1e-12})
    phase=np.concatenate((fit.x,-fit.x[::-1]))
    est=(np.fft.ifft(amp*np.exp(-1j*phase))/twist).real
    est*=np.linalg.norm(d)/np.linalg.norm(est)
    candidates=[np.asarray([d[k-j] if k>=j else -d[k-j+n] for k in range(n)]) for j in range(n)]
    dots=[np.dot(est,c) for c in candidates]
    idx=np.argmax(np.abs(dots)); actual=candidates[idx]*np.sign(dots[idx])
    err=np.abs(est-actual)
    print('Score',fit.fun,'correlation',np.dot(est,actual)/np.dot(d,d),'RMSE',np.sqrt(np.mean(err**2)),'rounding errors',sum(np.rint(est)!=actual),flush=True)
