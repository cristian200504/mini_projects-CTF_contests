"""Calibrate scale recovery on the local downhill key with ground truth."""
import json
import sys

import numpy as np

from corrected_attack import prepare


path = r"C:\Users\santey\Desktop\NNS CTF\downhill\work\local_data_500.json"
data = json.load(open(path))
engine, Linv = prepare(data)
row = np.array(data["true_F"] + data["true_G"], dtype=float)
w = row @ engine.L
norm = np.linalg.norm(w)
w /= norm
approx = 2 * (w @ Linv)
actual_scale = norm / 2
print("secret whitening norm", norm, "exact scale", actual_scale)
print("max exact reconstruction error", np.max(np.abs(np.rint(actual_scale * approx) - row)))

ranked = []
for scale in np.arange(.05, 15, .001):
    v = scale * approx
    cvar = 1 - abs(np.mean(np.exp(2j * np.pi * v)))
    err = np.std(v - np.rint(v))
    ranked.append((cvar, err, scale))
print("circular minima", sorted(ranked)[:15])
print("nearest true scale", min(ranked, key=lambda item: abs(item[2] - actual_scale)))
