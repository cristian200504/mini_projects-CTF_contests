"""Decode the Saleae row-per-change CSV as I2C (Channel 1=SCL, Channel 2=SDA)."""
from pathlib import Path
import csv
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\santey\Desktop\NNS CTF\cheese\dotmatrix_raw.csv")

events = []
with path.open(newline="") as f:
    rd = csv.reader(f)
    next(rd)
    for row in rd:
        events.append((int(row[0]), int(row[1].strip()), int(row[2].strip())))

transactions = []
active = False
bits = []
start = 0
prev_scl, prev_sda = events[0][1:]
for ts, scl, sda in events[1:]:
    # start/repeated-start: SDA falls while SCL is high
    if prev_sda == 1 and sda == 0 and scl == 1:
        if active and bits:
            # incomplete packet, preserve for diagnosis
            transactions.append((start, ts, bits, "restart"))
        active = True
        bits = []
        start = ts
    # stop: SDA rises while SCL high
    elif prev_sda == 0 and sda == 1 and scl == 1:
        if active:
            transactions.append((start, ts, bits, "stop"))
        active = False
        bits = []
    # sample on SCL rising edge
    if active and prev_scl == 0 and scl == 1:
        bits.append(sda)
    prev_scl, prev_sda = scl, sda

def bytes_from_bits(bits):
    vals=[]
    for i in range(0, len(bits) // 9 * 9, 9):
        b = 0
        for x in bits[i:i+8]:
            b = (b << 1) | x
        vals.append((b,bits[i+8]))
    return vals, len(bits)%9

valid=[]
for start,end,bits,why in transactions:
    # Saleae's row-per-change export can contain the SCL edge at a simultaneous
    # stop/restart as a separate row, leaving one non-data trailing sample.
    if len(bits) % 9 == 1:
        bits = bits[:-1]
    vals,rem=bytes_from_bits(bits)
    if vals and rem == 0:
        valid.append((start,end,[x for x,a in vals],[a for x,a in vals],why))

print(f"events={len(events)} transactions={len(transactions)} complete={len(valid)}")
print("bit lengths", [(len(x[2]), x[3]) for x in transactions[:30]])
for x in transactions[:5]:
    print("raw", x[0], x[1], ''.join(map(str, x[2])))
for i,(s,e,data,acks,why) in enumerate(valid[:100]):
    print(i, s,e, why, " ".join(f'{x:02x}' for x in data), "acks",''.join(map(str,acks)))

out=path.with_suffix('.i2c.txt')
with out.open('w') as f:
    for i,(s,e,data,acks,why) in enumerate(valid):
        f.write(f"{i}\t{s}\t{e}\t{why}\t"+' '.join(f'{x:02x}' for x in data)+f"\tacks={''.join(map(str,acks))}\n")
print(out)

# Compact summary for reverse engineering (all are writes to 7-bit 0x30).
from collections import Counter
print("length distribution", Counter(len(d) for _,_,d,_,_ in valid))
for i,(s,e,data,acks,why) in enumerate(valid):
    if len(data) > 10:
        print("long", i, len(data), f"{s/50_000_000:.6f}s", ' '.join(f'{x:02x}' for x in data[:20]), '...', ' '.join(f'{x:02x}' for x in data[-10:]))
