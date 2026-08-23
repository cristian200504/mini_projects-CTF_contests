import json
from fpylll import IntegerMatrix, LLL

with open("sigs_live.json") as f:
    data = json.load(f)

N = data["N"]
sigs = data["sigs"]

m = len(sigs)
A = []
B = []

def inverse_mod(a, m):
    return pow(a, -1, m)

for (r, s, z, K0) in sigs:
    s_inv = inverse_mod(s, N)
    a = (s_inv * r) % N
    b = (s_inv * z - K0) % N
    A.append(a)
    B.append(b)

X = 2**246
W = 2**10

M = IntegerMatrix(m + 2, m + 2)
for i in range(m):
    M[i, i] = N * W

for i in range(m):
    M[m, i] = A[i] * W
M[m, m] = 1

for i in range(m):
    M[m+1, i] = B[i] * W
M[m+1, m+1] = X

LLL.reduction(M)

for i in range(M.nrows):
    row = [M[i, j] for j in range(M.ncols)]
    if row[-1] == X:
        D = row[-2]
        print(f"Found D: {D}")
        break
    elif row[-1] == -X:
        D = -row[-2]
        print(f"Found D: {D}")
        break
else:
    print("Failed")
