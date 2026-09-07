"""Turn a low-moment recovery row into an exact public-key-consistent F,G."""
import json
import sys
import numpy as np

sys.path.insert(0, r"C:\Users\santey\Desktop\NNS CTF\downhill\work")
from attack import cyc_conv_mat

rows = json.load(open(sys.argv[1]))["rows"]
data = json.load(open(sys.argv[2]))
index = int(sys.argv[3])
scale = float(sys.argv[4])
N, q = data["N"], data["q"]
row = np.asarray(rows[index])
F = np.rint(scale * row[:N]).astype(int)
# Once F is correctly rounded, this is the exact G modulo q.  Its small,
# centered representative is the short NTRU basis polynomial.
raw_G = cyc_conv_mat(F, np.asarray(data["pk_h"]), N) % q
G = np.where(raw_G > q // 2, raw_G - q, raw_G).astype(int)
json.dump({"F": F.tolist(), "G": G.tolist()}, open(sys.argv[5], "w"))
print("F range", F.min(), F.max(), "G range", G.min(), G.max())
