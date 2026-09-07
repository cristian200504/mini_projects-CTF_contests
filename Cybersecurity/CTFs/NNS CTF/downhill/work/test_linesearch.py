import json, time
import numpy as np
import attack as A

data = json.load(open("local_data_500.json"))
samples, N, q, h = A.build_samples(data)
B = A.build_dc_projection(N)
C, L, mean = A.whiten(samples, B)

true_F = np.array(data["true_F"], dtype=np.float64)
true_G = np.array(data["true_G"], dtype=np.float64)
row = np.concatenate([true_F, true_G])
c_true = (row @ B) @ L
w_true = c_true / np.linalg.norm(c_true)
print("true mom4:", A.mom4(C, w_true), flush=True)

rng = np.random.default_rng(1)
t0 = time.time()
for i in range(10):
    w, val = A.one_descent(C, max_steps=300, patience=25, rng=rng)
    print(f"descent {i}: final mom4={val:.5f}  ({time.time()-t0:.1f}s elapsed)", flush=True)
