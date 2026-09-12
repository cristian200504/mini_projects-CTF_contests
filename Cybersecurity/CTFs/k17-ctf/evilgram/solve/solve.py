"""
Step 2: reconstruct the 128 4x4x4 cellular-automaton frames from the extracted
voxel vertex data, then replay the CA's block-update logic (copied straight
from the encoder script John Wick pasted in-chat) on every consecutive frame
pair to recover the full 256-entry `ruleset` permutation with zero ambiguity.

Key gotcha: `pad_vertices` pads unused cube slots with plain (0,0,0,...,0) for
all 8 vertices of the "cube" -- NOT the real cube_vertices shape offset by
(0,0,0). So padding is a degenerate (all-8-vertices-identical) group, while a
*real* voxel at the origin still has 7 distinct non-zero vertices. Checking
for "all 8 vertices exactly zero" is what correctly tells padding apart from
a genuine voxel sitting at (0,0,0).

Usage: run from this directory after extract_json.py -> writes ./data/mapping.json
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

MAP_SIZE = 4

with open(os.path.join(DATA_DIR, "frames.json")) as f:
    frames = json.load(f)
frames.sort(key=lambda fr: int(fr["name"]))


def frame_to_map(frame):
    d = frame["data"][0]
    xs, ys, zs = d["x"], d["y"], d["z"]
    assert len(xs) % 8 == 0
    active = set()
    for c in range(len(xs) // 8):
        base = c * 8
        gx, gy, gz = xs[base:base + 8], ys[base:base + 8], zs[base:base + 8]
        if all(v == 0 for v in gx) and all(v == 0 for v in gy) and all(v == 0 for v in gz):
            continue  # padding cube
        active.add((int(gx[0]), int(gy[0]), int(gz[0])))  # first vertex = min corner
    m = np.zeros((MAP_SIZE, MAP_SIZE, MAP_SIZE), dtype=np.int64)
    for (x, y, z) in active:
        m[z][y][x] = 1
    return m


hist = [frame_to_map(fr) for fr in frames]
print("frames reconstructed:", len(hist))
print("voxel counts (first 10):", [int(h.sum()) for h in hist[:10]])


# --- copied verbatim (logic-wise) from the encoder script's calcBlockState ---
def calcBlockState(m, x, y, z):
    zSize, ySize, xSize = m.shape
    return (m[z % zSize][y % ySize][x % xSize] +
            m[z % zSize][y % ySize][(x + 1) % xSize] * 2 +
            m[z % zSize][(y + 1) % ySize][x % xSize] * 4 +
            m[z % zSize][(y + 1) % ySize][(x + 1) % xSize] * 8 +
            m[(z + 1) % zSize][y % ySize][x % xSize] * 16 +
            m[(z + 1) % zSize][y % ySize][(x + 1) % xSize] * 32 +
            m[(z + 1) % zSize][(y + 1) % ySize][x % xSize] * 64 +
            m[(z + 1) % zSize][(y + 1) % ySize][(x + 1) % xSize] * 128)


mapping = {}
conflicts = 0
for k in range(len(hist) - 1):
    step = k + 1  # step_forwards(map, ruleset, step) -- 1-indexed in the original loop
    before, after = hist[k], hist[k + 1]
    for zz in range(MAP_SIZE >> 1):
        for yy in range(MAP_SIZE >> 1):
            for xx in range(MAP_SIZE >> 1):
                X = xx * 2 + (step & 1)
                Y = yy * 2 + (1 if (step & 2) != 0 else 0)
                Z = zz * 2 + (1 if (step & 4) != 0 else 0)
                b = int(calcBlockState(before, X, Y, Z))
                a = int(calcBlockState(after, X, Y, Z))
                if b in mapping and mapping[b] != a:
                    conflicts += 1
                mapping[b] = a

print("distinct domain states recovered:", len(mapping), "/ 256")
print("conflicts:", conflicts)
missing_domain = sorted(set(range(256)) - set(mapping.keys()))
missing_range = sorted(set(range(256)) - set(mapping.values()))
print("missing domain states:", missing_domain)
print("missing range states:", missing_range)

with open(os.path.join(DATA_DIR, "mapping.json"), "w") as f:
    json.dump({str(k): v for k, v in mapping.items()}, f)
print("wrote", os.path.join(DATA_DIR, "mapping.json"))
