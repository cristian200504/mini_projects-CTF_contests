"""Recover downhill's NTRUSign key with corrected lifts and FFT descent."""
import json, sys, time, os
from pathlib import Path
from hashlib import sha256
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from unwrap_test import unwrap
from fast_validate import FastMoment

def prepare(data):
    base=unwrap(data)
    M,D=base.shape; N=D//2
    # Orbit covariance consists of four circulant blocks; compute it with
    # FFT correlations instead of allocating all 125,500 orbit samples.
    blocks=base.reshape(M,2,N)
    mean=np.repeat(blocks.mean(axis=(0,2)),N)
    blocks=blocks-mean.reshape(1,2,N)
    bf=np.fft.fft(blocks,axis=2)
    cov=np.empty((D,D))
    for a in range(2):
        for b in range(2):
            corr=np.fft.ifft(np.mean(np.conj(bf[:,a])*bf[:,b],axis=0)).real/N
            cov[a*N:(a+1)*N,b*N:(b+1)*N]=corr[(np.arange(N)[None,:]-np.arange(N)[:,None])%N]
    vals,vec=np.linalg.eigh(3*cov)
    print('cov eig',vals[0],vals[-1],flush=True)
    L=(vec*(1/np.sqrt(vals)))@vec.T
    Linv=(vec*np.sqrt(vals))@vec.T
    return FastMoment(base,np.eye(D),L,mean),Linv

def check(w,Linv,data):
    N=data['N']; d=2*(w@Linv)
    # A recovered row can have sign, cyclic shift and small empirical
    # scaling/mean errors. The true f has precisely 73 one coefficients.
    for h in [d[:N],-d[:N],d[N:],-d[N:]]:
        ranks=np.argsort(h); f=np.zeros(N,dtype=int); f[ranks[-73:]]=1
        fit=np.std(h-f)
        if fit>0.22:continue
        for r in range(N):
            rot=np.roll(f,r)
            key=sha256(bytes(rot.tolist())).digest()
            pt=AES.new(key,AES.MODE_ECB).decrypt(bytes.fromhex(data['ct']))
            if pt.startswith(b'NNS{'):
                try:flag=unpad(pt,16).decode()
                except (ValueError,UnicodeError):continue
                if flag.endswith('}'):
                    return flag,rot
    return None,None

def line_step(engine,w,val,grad):
    u=engine.dots(w); v=engine.dots(grad)
    moments=np.array([val,np.mean(u*u*u*v),np.mean(u*u*v*v),np.mean(u*v*v*v),np.mean(v*v*v*v)])
    delta=np.array([.03,.1,.3,.5,.6,.65,.68,.7,.71,.72,.73,.735,.74,.7425,.745,.7475,.75,.755,.76,.78,.8,1.,2.,5.])
    numerator=moments[0]-4*delta*moments[1]+6*delta**2*moments[2]-4*delta**3*moments[3]+delta**4*moments[4]
    normsq=1-2*delta*np.dot(w,grad)+delta**2*np.dot(grad,grad)
    vals=numerator/normsq**2
    best=int(np.argmin(vals))
    new=w-delta[best]*grad
    return new/np.linalg.norm(new)

def run(path,seconds=180,output='corrected_results.json',seed=None):
    data=json.loads(Path(path).read_text())
    engine,Linv=prepare(data); D=engine.L.shape[0]
    rng=np.random.default_rng(seed); start=time.time(); count=0
    rows=[]
    while time.time()-start<seconds:
        count+=1; w=rng.normal(size=D); w/=np.linalg.norm(w)
        best=1.; stale=0
        for step in range(200):
            val,grad=engine.moment_gradient(w)
            if val<best-1e-8:best=val; bw=w.copy(); stale=0
            else:stale+=1
            if step>12 and (stale>4 or val<.205):
                flag,f=check(bw,Linv,data)
                if flag:
                    print('FLAG:',flag,flush=True)
                    Path(output).write_text(json.dumps({'flag':flag,'f':f.tolist(),'attempt':count,'steps':step}))
                    return
            if stale>8:break
            new=line_step(engine,w,val,grad)
            if np.linalg.norm(new-w)<1e-7:break
            w=new
        flag,f=check(bw,Linv,data)
        print(f'[{count}] mom4={best:.6f} steps={step} sec={time.time()-start:.1f}',flush=True)
        if flag:
            print('FLAG:',flag,flush=True)
            Path(output).write_text(json.dumps({'flag':flag,'f':f.tolist()}));return
        rows.append((2*(bw@Linv)).tolist())
        Path(output).write_text(json.dumps({'ct':data['ct'],'N':data['N'],'q':data['q'],'rows':rows}))
    print('finished',count,'descents',flush=True)

if __name__=='__main__':
    run(sys.argv[1],float(sys.argv[2]) if len(sys.argv)>2 else 180,
        sys.argv[3] if len(sys.argv)>3 else 'corrected_results.json',
        int(sys.argv[4]) if len(sys.argv)>4 else None)
