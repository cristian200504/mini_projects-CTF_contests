"""Reduce the supplied matching checkpoint, then run verified extraction."""
import os, pickle, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
b=pickle.load(open('/tmp/lll_K4.pkl','rb'))
source='['+'\n'.join('['+' '.join(map(str,r))+']' for r in b)+'\n]\n'
env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH='/tmp/nss-flatter/build/lib:/tmp/fplll-5.5.0/fplll/.libs:/tmp/localroot/usr/lib/x86_64-linux-gnu')
print('Reducing checkpoint with flatter',flush=True)
p=subprocess.run(['/tmp/nss-flatter/build/bin/flatter','-rhf','1.012'],input=source,text=True,capture_output=True,env=env)
print(p.stderr,flush=True)
if p.returncode: raise SystemExit(p.returncode)
b=[[int(x) for x in r.split()] for r in p.stdout.replace(']','').split('[') if r.strip()]
assert len(b)==1024 and all(len(r)==1024 for r in b)
pickle.dump(b,open(root/'basis_K4.pkl','wb'))
print('Minimum norm:',min(sum(x*x for x in r)**0.5 for r in b),flush=True)
subprocess.run([sys.executable,str(root/'solve.py'),'4',''],check=True)
