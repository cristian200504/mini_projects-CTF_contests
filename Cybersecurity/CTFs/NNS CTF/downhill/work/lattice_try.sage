"""Quick direct NTRU lattice-reduction experiment for downhill.

The public relation g = h*f mod q puts (g,f) in the 2N-dimensional lattice
with basis rows (qI,0) and (H,I).  This script is primarily a diagnostic: it
checks whether straightforward LLL/BKZ is already strong enough for the
challenge parameters before spending time on the signature attack.
"""
import json
import sys
import time

from fpylll import BKZ, IntegerMatrix, LLL


path = sys.argv[1] if len(sys.argv) > 1 else "local_data_500.json"
block_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
with open(path) as source:
    data = json.load(source)

N, q = data["N"], data["q"]
h = data["pk_h"]

# A row vector f multiplied by H is the cyclic product f*h.
H = [[h[(column - row) % N] for column in range(N)] for row in range(N)]
rows = []
for i in range(N):
    rows.append([q if i == j else 0 for j in range(N)] + [0] * N)
for i in range(N):
    rows.append(H[i] + [1 if i == j else 0 for j in range(N)])

B = IntegerMatrix.from_matrix(rows)
print(f"reducing {2*N}D NTRU lattice with BKZ-{block_size}", flush=True)
t0 = time.time()
LLL.reduction(B, delta=0.99)
print(f"LLL done in {time.time()-t0:.1f}s; first norm²={sum(int(B[0,j])**2 for j in range(2*N))}", flush=True)

if block_size > 2:
    params = BKZ.Param(block_size=block_size, max_loops=2)
    BKZ.reduction(B, params)
    print(f"BKZ done in {time.time()-t0:.1f}s; first norm²={sum(int(B[0,j])**2 for j in range(2*N))}", flush=True)

def check_pair(g, f):
    return set(g) <= {0, 1} and set(f) <= {0, 1} and sum(g) == 71 and sum(f) == 73

for row in range(2*N):
    vector = [int(B[row, col]) for col in range(2*N)]
    for sign in (1, -1):
        g = [sign * value for value in vector[:N]]
        f = [sign * value for value in vector[N:]]
        if check_pair(g, f):
            print(f"FOUND sparse pair in basis row {row}: f weight={sum(f)}, g weight={sum(g)}")
            if "true_f" in data:
                print("matches true f up to rotation:", any(f == data["true_f"][r:] + data["true_f"][:r] for r in range(N)))
            sys.exit(0)

print("no direct sparse secret row found")
for row in range(min(10, 2*N)):
    vector = [int(B[row, col]) for col in range(2*N)]
    print(row, sum(value*value for value in vector), min(vector), max(vector))
