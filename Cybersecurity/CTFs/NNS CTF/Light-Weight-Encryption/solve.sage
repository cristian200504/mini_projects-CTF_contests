import ast
from sage.all import *
from Crypto.Util.number import long_to_bytes

# Load data
with open('output.py') as f:
    code = f.read()

local_dict = {}
exec(code, {}, local_dict)
pk = local_dict['pk']
ct = local_dict['ct']

A_flat = pk[0]
B = pk[1]
u = ct[0]
v = ct[1]

m = 112
n = 16
w = 130
q = 2**768
W = 2**424

A = [A_flat[i*n : (i+1)*n] for i in range(m)]

print("1. Constructing Primary Lattice to find sk and errors...")
# We use m_sub = 85 to ensure the target vector is uniquely the shortest
m_sub = 85
M = matrix(ZZ, m_sub + n + 1, m_sub + 1)
for i in range(m_sub):
    M[i, i] = q
for i in range(n):
    for j in range(m_sub):
        M[m_sub + i, j] = A[j][i]
for j in range(m_sub):
    M[m_sub + n, j] = B[j]
M[m_sub + n, m_sub] = W

print("Running primary LLL...")
L = M.LLL()

sk = None
pe = None
for row in L:
    if row[-1] != 0 and row[-1] % W == 0:
        tmp_sk = abs(row[-1] // W)
        if 2**120 < tmp_sk < 2**135:
            sk = tmp_sk
            pe = list(row[:-1])
            if row[-1] < 0:
                pe = [-x for x in pe]
            break

print("Found sk:", sk)

print("2. Recovering s' and full error vector Z...")
R_q = Zmod(q)
A_sub = A[:m_sub]
B_sub = B[:m_sub]

# Find an invertible 16x16 submatrix to solve for s' = s * sk mod q
for i in range(100):
    indices = sample(range(m_sub), n)
    sub_A = matrix(R_q, [A_sub[idx] for idx in indices])
    if sub_A.is_invertible():
        sub_V = vector(R_q, [(B_sub[idx]*sk - pe[idx]) for idx in indices])
        s_prime = sub_A.solve_right(sub_V)
        break

Z = []
for i in range(m):
    As = sum(A[i][j] * s_prime[j] * inverse_mod(sk, q) for j in range(n)) % q
    E_i = (B[i] - As) % q
    Z_i = (E_i * sk) % q
    if Z_i > q // 2:
        Z_i = Z_i - q
    Z.append(Z_i)

print("3. Constructing Subset Sum Lattice to recover p and sum(e_i)...")
K = 10000
M2 = matrix(ZZ, m + 1, m + n + 1)
for i in range(m):
    M2[i, i] = 1
    for j in range(n):
        M2[i, m + j] = K * A[i][j]
    M2[i, m + n] = K

for j in range(n):
    M2[m, m + j] = K * u[j]
M2[m, m + n] = K * w

print("Running subset sum LLL...")
L2 = M2.LLL()

x_base = None
x_null = []
for row in L2:
    if all(row[i] == 0 for i in range(m, m+n+1)):
        x_cand = list(row[:m])
        s = sum(x_cand)
        if s == -130:
            x_base = [-x for x in x_cand]
        elif s == 130:
            x_base = x_cand
        elif s == 0 and any(x != 0 for x in x_cand):
            x_null.append(x_cand)

print("4. Calculating p from null space differences...")
p = abs(sum(x_null[0][i] * Z[i] for i in range(m)))
for null_vec in x_null[1:]:
    p = gcd(p, abs(sum(null_vec[i] * Z[i] for i in range(m))))

print("Calculated p:", p)

print("5. Decrypting Flag...")
Y = (v * sk + sum(u[i] * s_prime[i] for i in range(n))) % q
pt_sk = (Y + sum(x_base[i] * Z[i] for i in range(m))) % q
pt = (pt_sk % p) * inverse_mod(sk, p) % p

print("Flag:", long_to_bytes(int(pt)).decode())
