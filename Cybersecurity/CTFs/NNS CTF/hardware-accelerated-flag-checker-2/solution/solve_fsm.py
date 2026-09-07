"""Read the extracted netlist, model the combinational logic + 5 DFFs as an
FSM, and search for the character sequence that makes found_flag go high."""
import sys, ast
from collections import deque

NET = sys.argv[1]

gates = []            # (name, celltype, {pin: net})
for line in open(NET):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    name, cell, rest = line.split(None, 2)
    gates.append((name, cell, ast.literal_eval(rest)))

# ---- boolean function per sky130_fd_sc_hd cell (output pin -> lambda(inputs)) ----
def F(cell, p):
    g = lambda k: p.get(k)
    A, B, C, D = g('A'), g('B'), g('C'), g('D')
    if cell in ('inv',):                    return ('Y', ['A'], lambda v: 1 - v['A'])
    if cell.startswith('clkdlybuf') or cell.startswith('clkbuf') or cell in ('buf','dlygate4sd3'):
        return ('X', ['A'], lambda v: v['A'])
    if cell.startswith('clkinv'):           return ('Y', ['A'], lambda v: 1 - v['A'])
    T = {
      'and2'  : ('X', 'A B',        lambda v: v['A'] & v['B']),
      'and3'  : ('X', 'A B C',      lambda v: v['A'] & v['B'] & v['C']),
      'and4'  : ('X', 'A B C D',    lambda v: v['A'] & v['B'] & v['C'] & v['D']),
      'and2b' : ('X', 'A_N B',      lambda v: (1-v['A_N']) & v['B']),
      'and3b' : ('X', 'A_N B C',    lambda v: (1-v['A_N']) & v['B'] & v['C']),
      'and4b' : ('X', 'A_N B C D',  lambda v: (1-v['A_N']) & v['B'] & v['C'] & v['D']),
      'and4bb': ('X', 'A_N B_N C D',lambda v: (1-v['A_N']) & (1-v['B_N']) & v['C'] & v['D']),
      'nand2' : ('Y', 'A B',        lambda v: 1-(v['A'] & v['B'])),
      'nand3' : ('Y', 'A B C',      lambda v: 1-(v['A'] & v['B'] & v['C'])),
      'nand4' : ('Y', 'A B C D',    lambda v: 1-(v['A'] & v['B'] & v['C'] & v['D'])),
      'nand2b': ('Y', 'A_N B',      lambda v: 1-((1-v['A_N']) & v['B'])),
      'nand3b': ('Y', 'A_N B C',    lambda v: 1-((1-v['A_N']) & v['B'] & v['C'])),
      'nand4b': ('Y', 'A_N B C D',  lambda v: 1-((1-v['A_N']) & v['B'] & v['C'] & v['D'])),
      'or2'   : ('X', 'A B',        lambda v: v['A'] | v['B']),
      'or3'   : ('X', 'A B C',      lambda v: v['A'] | v['B'] | v['C']),
      'or4'   : ('X', 'A B C D',    lambda v: v['A'] | v['B'] | v['C'] | v['D']),
      'or3b'  : ('X', 'A B C_N',    lambda v: v['A'] | v['B'] | (1-v['C_N'])),
      'or4b'  : ('X', 'A B C D_N',  lambda v: v['A'] | v['B'] | v['C'] | (1-v['D_N'])),
      'or4bb' : ('X', 'A B C_N D_N',lambda v: v['A'] | v['B'] | (1-v['C_N']) | (1-v['D_N'])),
      'nor2'  : ('Y', 'A B',        lambda v: 1-(v['A'] | v['B'])),
      'nor3'  : ('Y', 'A B C',      lambda v: 1-(v['A'] | v['B'] | v['C'])),
      'nor4'  : ('Y', 'A B C D',    lambda v: 1-(v['A'] | v['B'] | v['C'] | v['D'])),
      'nor3b' : ('Y', 'A B C_N',    lambda v: 1-(v['A'] | v['B'] | (1-v['C_N']))),
      'nor4b' : ('Y', 'A B C D_N',  lambda v: 1-(v['A'] | v['B'] | v['C'] | (1-v['D_N']))),
      'xnor2' : ('Y', 'A B',        lambda v: 1-(v['A'] ^ v['B'])),
      'xor2'  : ('X', 'A B',        lambda v: v['A'] ^ v['B']),
      'a21oi' : ('Y', 'A1 A2 B1',        lambda v: 1-((v['A1'] & v['A2']) | v['B1'])),
      'a21o'  : ('X', 'A1 A2 B1',        lambda v: (v['A1'] & v['A2']) | v['B1']),
      'a21boi': ('Y', 'A1 A2 B1_N',      lambda v: 1-((v['A1'] & v['A2']) | (1-v['B1_N']))),
      'a211o' : ('X', 'A1 A2 B1 C1',     lambda v: (v['A1'] & v['A2']) | v['B1'] | v['C1']),
      'a211oi': ('Y', 'A1 A2 B1 C1',     lambda v: 1-((v['A1'] & v['A2']) | v['B1'] | v['C1'])),
      'a22o'  : ('X', 'A1 A2 B1 B2',     lambda v: (v['A1'] & v['A2']) | (v['B1'] & v['B2'])),
      'a2bb2oi':('Y', 'A1_N A2_N B1 B2', lambda v: 1-(((1-v['A1_N']) & (1-v['A2_N'])) | (v['B1'] & v['B2']))),
      'a31oi' : ('Y', 'A1 A2 A3 B1',     lambda v: 1-((v['A1'] & v['A2'] & v['A3']) | v['B1'])),
      'a311o' : ('X', 'A1 A2 A3 B1 C1',  lambda v: (v['A1'] & v['A2'] & v['A3']) | v['B1'] | v['C1']),
      'a32o'  : ('X', 'A1 A2 A3 B1 B2',  lambda v: (v['A1'] & v['A2'] & v['A3']) | (v['B1'] & v['B2'])),
      'o21a'  : ('X', 'A1 A2 B1',        lambda v: (v['A1'] | v['A2']) & v['B1']),
      'o21ai' : ('Y', 'A1 A2 B1',        lambda v: 1-((v['A1'] | v['A2']) & v['B1'])),
      'o21ba' : ('X', 'A1 A2 B1_N',      lambda v: (v['A1'] | v['A2']) & (1-v['B1_N'])),
      'o21bai': ('Y', 'A1 A2 B1_N',      lambda v: 1-((v['A1'] | v['A2']) & (1-v['B1_N']))),
      'o22a'  : ('X', 'A1 A2 B1 B2',     lambda v: (v['A1'] | v['A2']) & (v['B1'] | v['B2'])),
      'o2bb2a': ('X', 'A1_N A2_N B1 B2', lambda v: ((1-v['A1_N']) | (1-v['A2_N'])) & (v['B1'] | v['B2'])),
      'o31ai' : ('Y', 'A1 A2 A3 B1',     lambda v: 1-((v['A1'] | v['A2'] | v['A3']) & v['B1'])),
      'o32a'  : ('X', 'A1 A2 A3 B1 B2',  lambda v: (v['A1'] | v['A2'] | v['A3']) & (v['B1'] | v['B2'])),
      'o41a'  : ('X', 'A1 A2 A3 A4 B1',  lambda v: (v['A1'] | v['A2'] | v['A3'] | v['A4']) & v['B1']),
      'o2111a': ('X', 'A1 A2 B1 C1 D1',  lambda v: (v['A1'] | v['A2']) & v['B1'] & v['C1'] & v['D1']),
    }
    base = cell
    if base in T:
        o, ins, fn = T[base]
        return (o, ins.split(), fn)
    return None

# ---- build evaluable gate list ----
drivers = {}          # net -> (gatename, outpin)
comb = []             # (outnet, [innets], fn)   evaluated combinationally
dff = []              # (qnet, dnet)
import re
def strip_drv(c):
    return re.sub(r'_\d+$', '', c)      # drop drive-strength suffix (nand2_2 -> nand2)

for name, cell, conns in gates:
    fam = strip_drv(cell)
    if fam == 'dfxtp':
        dff.append((conns['Q'], conns['D']))
        continue
    spec = F(fam, conns)
    if spec is None:
        print("!! unknown cell", fam, name, file=sys.stderr)
        continue
    opin, ins, fn = spec
    onet = conns[opin]
    innets = [conns[i] for i in ins]
    comb.append((onet, innets, fn, ins))
    drivers[onet] = name

# primary inputs
PI_char = {b: None for b in range(7)}
for name, cell, conns in gates:
    if name.startswith('input') and conns.get('A','').startswith('character['):
        b = int(conns['A'][10:-1]); PI_char[b] = conns['A']
RST = None
for name, cell, conns in gates:
    if conns.get('A') == 'reset_n':
        RST = 'reset_n'

qnets = [q for q, d in dff]
dnets = [d for q, d in dff]

# topological order for comb
from collections import defaultdict
outof = {o: (o, ins, fn) for (o, ins, fn, pn) in comb}
memo_order = []
visiting = set(); done = set()
def visit(n):
    if n in done or n not in outof:
        done.add(n); return
    if n in visiting:
        return   # loop guard (shouldn't happen in comb)
    visiting.add(n)
    for i in outof[n][1]:
        visit(i)
    visiting.discard(n); done.add(n); memo_order.append(n)
for o in list(outof):
    visit(o)

def evaluate(state, char_bits, reset_n):
    v = {}
    v['VPWR'] = 1; v['VGND'] = 0
    for i, q in enumerate(qnets):
        v[q] = state[i]
    for b in range(7):
        if PI_char[b] is not None:
            v[PI_char[b]] = char_bits[b]
    if RST is not None:
        v[RST] = reset_n
    for o in memo_order:
        _, ins, fn = outof[o]
        try:
            v[o] = fn({k: v.get(nn, 0) for k, nn in zip(_pinnames(o), ins)})
        except Exception as e:
            v[o] = 0
    return v

# need pin-name mapping per comb gate
pinmap = {}
for (o, ins, fn, pn) in comb:
    pinmap[o] = pn
def _pinnames(o):
    return pinmap[o]

FOUND = None
for name, cell, conns in gates:
    if conns.get('X') == 'found_flag' or conns.get('Y') == 'found_flag':
        FOUND = 'found_flag'
# found_flag net drives output port; the driving gate output net:
found_net = None
for (o, ins, fn, pn) in comb:
    if o == 'found_flag':
        found_net = 'found_flag'
if found_net is None:
    # output buffer: output9 A=n138 X=found_flag ; n138 is the real accept net
    for name, cell, conns in gates:
        if conns.get('X') == 'found_flag':
            found_net = conns['found_flag'] if False else conns.get('A')
print("accept net:", found_net, " state Qs:", qnets, " Ds:", dnets, file=sys.stderr)

def step(state, char_bits, reset_n):
    v = {}
    v['VPWR'] = 1; v['VGND'] = 0
    for i, q in enumerate(qnets):
        v[q] = state[i]
    for b in range(7):
        v[PI_char[b]] = char_bits[b]
    v[RST] = reset_n
    for o in memo_order:
        _, ins, fn = outof[o]
        v[o] = fn({k: v.get(nn, 0) for k, nn in zip(pinmap[o], ins)})
    nxt = tuple(v.get(d, 0) for d in dnets)
    acc = v.get(found_net, 0)
    return nxt, acc

# ---- find reset state ----
s = tuple([0]*len(qnets))
for _ in range(10):
    s, _a = step(s, [0]*7, 0)
reset_state = s
print("reset state:", reset_state, file=sys.stderr)

# ---- BFS over characters (printable ASCII 0x20..0x7e) ----
start = reset_state
# transition: from state, on char c -> next state
from functools import lru_cache
def trans(state, c):
    bits = [(c >> b) & 1 for b in range(7)]
    return step(state, bits, 1)

# BFS shortest accepting run
seen = {start: []}
q = deque([start])
answer = None
while q:
    st = q.popleft()
    path = seen[st]
    for c in range(0x20, 0x7f):
        ns, acc = trans(st, c)
        if acc:
            # `acc` is found_flag evaluated from the state *before* this cycle,
            # so the char used to observe it is a don't-care -> the flag is `path`
            answer = path
            print("FLAG:", ''.join(map(chr, answer)))
            q.clear(); break
        if ns not in seen and len(path) < 80:
            seen[ns] = path + [c]
            q.append(ns)
    if answer: break

if not answer:
    print("no accepting sequence found; states reached:", len(seen), file=sys.stderr)
