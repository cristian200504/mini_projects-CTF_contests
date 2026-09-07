import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,r'C:\Users\santey\Desktop\NNS CTF\downhill\work')
import attack as A

def unwrap(d, verbose=True):
    N,q=d['N'],d['q']
    s=np.array([e['sig'] for e in d['sigs']],dtype=float)
    m=np.array([A.get_m(bytes.fromhex(e['msg']),N) for e in d['sigs']])
    h=np.array(d['pk_h'])
    residue=np.array([(A.cyc_conv_mat(a.astype('int64'),h,N)-b)%q for a,b in zip(s,m)])
    prediction=s.mean(axis=1)[:,None]*71/73
    t=residue+q*np.round((prediction-residue)/q)
    sf=np.fft.fft(s-s.mean(axis=1)[:,None],axis=1)
    true=np.array([e['true_t'] for e in d['sigs']])-m if 'true_t' in d['sigs'][0] else None
    for i in range(10):
        tf=np.fft.fft(t-t.mean(axis=1)[:,None],axis=1)
        beta=np.sum(tf*np.conj(sf),axis=0)/(np.sum(abs(sf)**2,axis=0)+1e-9)
        predicted=np.fft.ifft(sf*beta,axis=1).real+prediction
        new=residue+q*np.round((predicted-residue)/q)
        if verbose:
            print(i,'changes',np.sum(t!=new),'residual std',np.std(t-predicted),
                  'wrong',np.sum(t!=true) if true is not None else '-',flush=True)
        if np.array_equal(t,new):break
        t=new
    return np.concatenate([s,t],axis=1)

if __name__=='__main__':
    d=json.loads(Path(sys.argv[1]).read_text())
    unwrap(d)
