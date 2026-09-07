"""Render AS1130 PWM register writes from the decoded I2C trace."""
from pathlib import Path
import sys

root = Path(r"C:\Users\santey\Desktop\NNS CTF")
trace = Path(sys.argv[1] if len(sys.argv)>1 else r"C:\Users\santey\Desktop\NNS CTF\cheese\dotmatrix_raw.i2c.txt")

anodes = [[int(x) for x in line.split()] for line in """8 1 0 1 1 9 2 2 5 2 6 5 9 6 5 1 5
1 0 0 0 9 1 6 6 2 6 7 6 7 9 0 6 6
0 0 9 1 8 1 2 3 2 2 3 3 3 9 0 2 3
4 4 5 8 3 1 6 4 2 3 9 4 3 3 0 3 8
8 6 8 8 0 8 7 3 8 1 9 9 2 8 5 8 4
5 5 9 0 4 5 6 3 4 4 1 5 5 4 2 4 4
5 8 9 7 0 7 7 7 7 7 1 6 7 2 7 7 4""".splitlines()]
cathodes = [[int(x) for x in line.split()] for line in """11 11 0 2 1 2 10 11 2 6 11 0 6 10 1 6 3
0 11 1 6 0 7 6 7 7 2 11 3 10 7 7 0 1
2 10 1 10 1 3 1 6 2 3 11 7 10 3 3 0 8
11 6 4 4 1 4 4 7 4 2 4 10 3 4 4 0 9
8 9 6 0 9 7 9 9 3 9 9 10 9 2 9 5 9
11 10 5 5 0 7 5 5 3 1 5 6 5 2 5 5 4
8 10 8 0 8 7 8 5 3 1 8 8 6 8 2 4 8""".splitlines()]

def led_index(anode, cathode):
    # AS1130's first LED coordinate selects the active (grounded) current
    # segment, i.e. the cathode; its second coordinate walks source CS lines.
    if anode == cathode:
        # The supplied 17x7 panel map includes ten unconnected slots; a
        # cross-plexed LED cannot use one CS line for both terminals.
        return None
    return cathode * 11 + anode - (anode > cathode)

def render(pwm, flip=False):
    rows=[]
    for ars, crs in zip(anodes,cathodes):
        vals=[pwm[k] if (k:=led_index(a,c)) is not None else 0 for a,c in zip(ars,crs)]
        rows.append(''.join('#' if x else '.' for x in vals))
    if flip:
        rows=[r[::-1] for r in rows[::-1]]
    return rows

frames=[]
for line in trace.read_text().splitlines():
    try:
        n, begin, end, reason, h, ack = line.split('\t')
    except ValueError:
        continue
    data=[int(x,16) for x in h.split()]
    if len(data)==134 and data[:2]==[0x60,0x18]:
        frames.append((int(n),int(begin),data[2:]))

print('frames',len(frames))
for selected in [0,1,2,3,4,5,10,-10,-5,-1]:
    n,t,pwm=frames[selected]
    print('\nFRAME',selected,n,f'{t/50_000_000:.6f}')
    print('\n'.join(render(pwm)))

out=trace.with_name('dotmatrix_frames.txt')
with out.open('w') as f:
    for j,(n,t,pwm) in enumerate(frames):
        f.write(f'FRAME {j} transaction {n} {t/50_000_000:.6f}\n')
        f.write('\n'.join(render(pwm))+'\n\n')
print(out)
