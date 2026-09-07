import json
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\santey\Desktop\NNS CTF\downhill\work")
from attack import cyc_conv_mat


data = json.load(open("remote_data.json"))
rows = np.array(json.load(open("corrected_remote_linesearch.json"))["rows"])
h = np.array(data["pk_h"])
N, q = 251, 128

for number, row in enumerate(rows):
    print(
        number,
        "ranges",
        (row[:N].min(), row[:N].max()),
        (row[N:].min(), row[N:].max()),
        "norm",
        np.linalg.norm(row),
    )
    rankings = []
    for sign in (1, -1):
        for scale in np.arange(0.05, 10.0, 0.002):
            F = np.rint(sign * scale * row[:N]).astype(int)
            G = np.rint(sign * scale * row[N:]).astype(int)
            remainder = (cyc_conv_mat(F, h, N) - G) % q
            centered = np.minimum(remainder, q - remainder)
            rankings.append((int(centered.sum()), int(centered.max()), float(scale), sign))
    print("  relation best", sorted(rankings)[:10])
