import sys, time, hashlib, pickle, os, subprocess
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pathlib import Path
import ast, json

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:8.1f}s]", *a, flush=True)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'crypto_nss-ctf/output.py'
ns = {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(OUT.read_text()).body}
pk = ns['pk']; sigs = ns['sigs']; ct = bytes.fromhex(ns['ct'])
n = 256; q = 367
h = [x % q for x in pk]
S_all = [[c % q for c in s] for (m, s) in sigs]

FPLLL = os.environ.get('FPLLL', '/tmp/fplll-5.5.0/fplll/fplll')
ENV = dict(os.environ, LD_LIBRARY_PATH="/tmp/fplll-5.5.0/fplll/.libs:/tmp/localroot/usr/lib/x86_64-linux-gnu")

def rmul(a, b):
    res = [0]*(2*n)
    for i in range(n):
        ai = a[i]
        if ai:
            for j in range(n): res[i+j] += ai*b[j]
    return [(res[i]-res[i+n]) % q for i in range(n)]
def shift(pc, j):
    out = [0]*n
    for k in range(n):
        s = k-j
        out[k] = pc[s] % q if s >= 0 else (-pc[s+n]) % q
    return out
def center(v, m=q): return [((x+m//2) % m)-m//2 for x in v]
def mat_of(pc):
    cols = [shift(pc, j) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]
def solve_mod(A, rhs):
    n_ = len(A); M = [r[:] for r in A]; R = [x[:] for x in rhs]; w = len(R[0])
    for col in range(n_):
        piv = next((r for r in range(col, n_) if M[r][col] % q), None)
        if piv is None: return None
        M[col], M[piv] = M[piv], M[col]; R[col], R[piv] = R[piv], R[col]
        inv = pow(M[col][col], q-2, q)
        M[col] = [(x*inv) % q for x in M[col]]; R[col] = [(x*inv) % q for x in R[col]]
        for r in range(n_):
            if r != col and M[r][col] % q:
                fn = M[r][col]
                M[r] = [(M[r][k]-fn*M[col][k]) % q for k in range(n_)]
                R[r] = [(R[r][k]-fn*R[col][k]) % q for k in range(w)]
    return M, R
def ring_inv(pc):
    def trim(a):
        while a and not a[-1]: a.pop()
        return a
    def submul(a, b, c):
        out = a[:] + [0]*max(0, len(b)+len(c)-1-len(a))
        for i, x in enumerate(b):
            for j, y in enumerate(c): out[i+j] = (out[i+j]-x*y)%q
        return trim(out)
    def divrem(a,b):
        a=a[:]; d=[0]*max(0,len(a)-len(b)+1); inv=pow(b[-1],-1,q)
        while len(a)>=len(b):
            j=len(a)-len(b); c=a[-1]*inv%q; d[j]=c
            for i,x in enumerate(b): a[i+j]=(a[i+j]-c*x)%q
            trim(a)
        return d,a
    a,b=[1]+[0]*(n-1)+[1],trim([x%q for x in pc])
    s,t=[],[1]
    while b:
        d,r=divrem(a,b); a,b=b,r; s,t=t,submul(s,d,t)
    if len(a)!=1: return None
    s=[x*pow(a[0],-1,q)%q for x in s]
    return s+[0]*(n-len(s))

order = list(range(10))
pivot = next(i for i in order if ring_inv(S_all[i]) is not None)
order.remove(pivot); order = [pivot]+order
K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
BLOCKS = [int(x) for x in sys.argv[2].split(",") if x] if len(sys.argv) > 2 else [20, 24, 28, 32]
use = order[:K]; D = K*n
CACHE = str(ROOT / f'basis_K{K}.pkl')
log(f"K={K} dim={D} sigs={use} blocks={BLOCKS}")

S0 = S_all[use[0]]; S0inv = ring_inv(S0)
Rl = [None] + [rmul(S_all[use[t]], S0inv) for t in range(1, K)]

fresh = not os.path.exists(CACHE)
if not fresh:
    B = pickle.load(open(CACHE, "rb")); log("loaded cache", CACHE)
else:
    B = [[0]*D for _ in range(D)]
    for j in range(n):
        B[j][j] = 1
        for t in range(1, K):
            cv = shift(Rl[t], j); c0 = t*n
            for i in range(n): B[j][c0+i] = cv[i]
    row = n
    for t in range(1, K):
        for j in range(n):
            B[row][t*n+j] = q; row += 1
    log("basis built fresh")

def to_fplll(B):
    return "[" + "\n".join("[" + " ".join(str(x) for x in r) + "]" for r in B) + "\n]\n"
def from_fplll(s):
    rows = []
    for line in s.replace("]", " ").split("["):
        line = line.strip()
        if not line: continue
        vals = line.split()
        if len(vals) == D:
            rows.append([int(v) for v in vals])
    return rows

def norm(v): return sum(x*x for x in v)**0.5
tgt = 44.0*(K**0.5)

def negshift_poly(pc, t):
    return [pc[k-t] if k-t >= 0 else -pc[k-t+n] for k in range(n)]
def endgame(found):
    for s in (1, -1):
        for t in range(n):
            ft = [s*x for x in negshift_poly(found, t)]
            key = hashlib.sha256(bytes(x % 256 for x in ft)).digest()
            pt = AES.new(key, AES.MODE_ECB).decrypt(ct)
            if pt.startswith(b"NNS{"):
                try: flag = unpad(pt,16).decode('utf-8')
                except (ValueError, UnicodeDecodeError): continue
                g = center(rmul(h,ft))
                u = center(ft,3)
                assert max(map(abs,ft))<=4 and max(map(abs,g))<=4
                assert center(g,3)==u
                assert u.count(1)==90 and u.count(-1)==91
                rf=[(a-b)//3 for a,b in zip(ft,u)]
                rg=[(a-b)//3 for a,b in zip(g,u)]
                assert rf.count(1)==rf.count(-1)==88
                assert rg.count(1)==rg.count(-1)==60
                fi=ring_inv(ft)
                ws=[center(rmul(fi,si)) for si in S_all]
                assert all(max(map(abs,w))<=5 for w in ws)
                (ROOT/'recovered.json').write_text(json.dumps(dict(flag=flag,f=ft,g=g,u=u,key=key.hex(),w=ws),indent=2))
                (ROOT/'flag.txt').write_text(flag+'\n')
                log("FLAG:", flag); print("\n>>> "+flag+"\n", flush=True); return True
    return False
def try_extract(B, tag):
    rows = sorted(B, key=norm)
    log(f"{tag}: min norms {['%.0f'%norm(r) for r in rows[:8]]}")
    for v in rows[:1000]:
        if norm(v) > 2*tgt: break
        for blk in range(K):
            v0 = [v[blk*n+j] % q for j in range(n)]
            if not any(v0): continue
            inv = ring_inv(v0)
            if inv is None: continue
            Sblk = S0 if blk == 0 else S_all[use[blk]]
            f_cand = center(rmul(inv, Sblk))
            if max(abs(x) for x in f_cand) <= 6:
                g_cand = center(rmul(h, [x % q for x in f_cand]))
                if max(abs(x) for x in g_cand) <= 8:
                    log(f"HIT blk {blk} f{(min(f_cand),max(f_cand))} g{(min(g_cand),max(g_cand))}")
                    if endgame(f_cand): return True
    return False

flatter = os.environ.get('FLATTER', '/tmp/nss-flatter/build/bin/flatter')
if fresh and os.path.isfile(flatter):
    log('Initial reduction with flatter')
    flat_env = dict(ENV, OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1')
    flat_env['LD_LIBRARY_PATH'] += ':/tmp/nss-flatter/build/lib'
    reduced = subprocess.run([flatter, '-rhf', '1.012'], input=to_fplll(B),
                             capture_output=True, text=True, env=flat_env, check=True)
    B = from_fplll(reduced.stdout)
    assert len(B)==D and all(len(row)==D for row in B)
    pickle.dump(B, open(CACHE,'wb'))
if try_extract(B, "start"): sys.exit(0)
cur = B
for b in BLOCKS:
    inp = to_fplll(cur)
    p = None
    for fargs in [["-f", "mpfr", "-p", "212"]]:
        log(f"fplll BKZ-{b} {fargs} ...")
        pp = subprocess.run([FPLLL, "-a", "bkz", "-b", str(b), "-bkzmaxloops", "4"] + fargs,
                            input=inp, capture_output=True, text=True, env=ENV)
        if (pp.returncode == 0 or 'loops limit exceeded' in pp.stderr or 'time limit exceeded' in pp.stderr) and "[[" in pp.stdout:
            p = pp; break
        log("  err:", (pp.stderr or "")[:200])
    if p is None:
        log("all float types failed for BKZ-%d" % b); continue
    cur = from_fplll(p.stdout)
    if len(cur) != D:
        log("parse fail, got", len(cur), "rows"); break
    pickle.dump(cur, open(CACHE, "wb"))
    if try_extract(cur, f"BKZ-{b}"): sys.exit(0)
log("exhausted")
