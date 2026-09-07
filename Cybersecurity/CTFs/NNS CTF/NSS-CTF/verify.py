"""Independently check the recovered secret and decrypt the ciphertext."""
import ast, hashlib, json
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

root=Path(__file__).resolve().parent
data={node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse((root/'crypto_nss-ctf/output.py').read_text()).body}
secret=json.loads((root/'recovered.json').read_text())
n,q=256,367
def multiply_integer(a,b):
    result=[0]*n
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            k=i+j
            result[k%n]+=x*y*(1 if k<n else -1)
    return result
def multiply(a,b):
    return [x%q for x in multiply_integer(a,b)]
def centered(a,p): return [(x+p//2)%p-p//2 for x in a]
f,g,u=(secret[x] for x in ['f','g','u'])
assert all(len(v)==n for v in [f,g,u])
assert multiply(data['pk'],f)==[x%q for x in g]
assert centered(f,3)==centered(g,3)==u
assert u.count(1)==90 and u.count(-1)==91 and u.count(0)==75
for polynomial,weight in [(f,88),(g,60)]:
    r=[(a-b)//3 for a,b in zip(polynomial,u)]
    assert set(r)<={-1,0,1} and r.count(1)==r.count(-1)==weight
assert len(secret['w'])==len(data['sigs'])==10
for w,(_,s) in zip(secret['w'],data['sigs']):
    assert len(w)==n and max(map(abs,w))<=5
    assert multiply(f,w)==[x%q for x in s]
d=[(b-a)//3 for a,b in zip(f,g)]
exact_products=0
for w,(_,s) in zip(secret['w'],data['sigs']):
    t=multiply(data['pk'],s)
    observed=centered([(a-b)*pow(3,-1,q)%q for a,b in zip(t,s)],q)
    if multiply_integer(d,w)==observed:
        exact_products+=1
key=hashlib.sha256(bytes(x%256 for x in f)).digest()
ct=bytes.fromhex(data['ct'])
plaintext=unpad(AES.new(key,AES.MODE_ECB).decrypt(ct),16)
assert AES.new(key,AES.MODE_ECB).encrypt(pad(plaintext,16))==ct
assert plaintext.decode()==secret['flag']
print('Verified public key, exact key-generation weights, all 10 signatures, padding, and ciphertext round trip.')
print(f'Exact unwrapped difference products: {exact_products}/10.')
print(plaintext.decode())
