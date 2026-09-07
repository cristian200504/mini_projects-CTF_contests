"""Score approximate secret rows against the public NTRU relation."""
import json
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\santey\Desktop\NNS CTF\downhill\work")
from attack import cyc_conv_mat


row_file = sys.argv[1] if len(sys.argv) > 1 else "new_instance_results.json"
data_file = sys.argv[2] if len(sys.argv) > 2 else "remote_data.json"
data = json.load(open(data_file))
rows = np.array(json.load(open(row_file))["rows"])
h = np.array(data["pk_h"])
N, q = data["N"], data["q"]


def score(first, second):
    residue = (cyc_conv_mat(first, h, N) - second) % q
    centered = np.minimum(residue, q - residue)
    return int(centered.sum()), int(np.count_nonzero(centered)), int(centered.max())


for number, row in enumerate(rows):
    rankings = []
    for sign in (1, -1):
        for scale in np.arange(0.05, 5.0, 0.001):
            first = np.rint(sign * scale * row[:N]).astype(np.int64)
            second = np.rint(sign * scale * row[N:]).astype(np.int64)
            if max(np.max(np.abs(first)), np.max(np.abs(second))) < 3:
                continue
            rankings.append((*score(first, second), float(scale), sign))
    print(number, "range", (row[:N].min(), row[:N].max()), (row[N:].min(), row[N:].max()))
    for item in sorted(rankings)[:12]:
        print(" ", item)
