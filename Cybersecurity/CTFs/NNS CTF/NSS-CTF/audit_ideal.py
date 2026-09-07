"""Verify every observed difference belongs to the recovered integer ideal."""
import pickle
from flint import fmpz_mat
import agent_alt_pubkey as base

basis=pickle.loads((base.ROOT/'basis_ideal_hnf.pkl').read_bytes())
det=abs(int(fmpz_mat(basis).det()))
print('Ideal determinant bits:',det.bit_length(),flush=True)
for i,(_,s) in enumerate(base.DATA['sigs']):
    t=base.multiply(base.H,s)
    d=base.center([(x-y)*pow(3,-1,base.Q)%base.Q for x,y in zip(t,s)])
    rows=[[d[k-j] if k>=j else -d[k-j+base.N] for k in range(base.N)] for j in range(base.N)]
    h=fmpz_mat(basis+rows).hnf()
    reduced=[[int(h[k,j]) for j in range(base.N)] for k in range(h.nrows()) if any(h[k,j] for j in range(base.N))]
    assert reduced==basis, f'Signature {i} changes the integer ideal'
    print(f'Signature {i}: same integer ideal',flush=True)
