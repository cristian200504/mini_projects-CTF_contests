import re, json, sys

N = 251
N_SIGS = 500
names = [f"friend{i}" for i in range(N_SIGS)]

with open("remote_raw.txt") as f:
    text = f.read()

m = re.search(r"pk = (\[[^\]]*\])", text)
pk = json.loads(m.group(1))
if len(pk) < N:
    pk = pk + [0] * (N - len(pk))

m = re.search(r"ct = ([0-9a-f]+)", text)
ct = m.group(1)

sig_lines = re.findall(r"(\[-?\d+(?:,\s*-?\d+)*\])", text)
sigs_raw = [json.loads(s) for s in sig_lines]
if sigs_raw and sigs_raw[0] == pk:
    sigs_raw = sigs_raw[1:]
elif sigs_raw and len(sigs_raw[0]) < N and sigs_raw[0] == pk[:len(sigs_raw[0])]:
    sigs_raw = sigs_raw[1:]

sigs = []
for i in range(min(len(sigs_raw), N_SIGS)):
    s = sigs_raw[i]
    if len(s) < N:
        s = s + [0] * (N - len(s))
    sigs.append({"msg": names[i].encode().hex(), "sig": s})

print("num sigs:", len(sigs), file=sys.stderr)
out = {"N": N, "q": 128, "pk_h": pk, "ct": ct, "sigs": sigs}
with open("remote_data.json", "w") as f:
    json.dump(out, f)
print("wrote remote_data.json", file=sys.stderr)
