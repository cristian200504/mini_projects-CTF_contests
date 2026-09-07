"""Gate-level netlist extraction from flag_checker.gds using gdstk booleans.

Flatten the design, merge geometry per routing layer, bridge layers through
vias, then label every merged region by the cell pins whose li1 label point
falls inside it.
"""
import sys, gdstk
from collections import defaultdict

GDS = sys.argv[1]
lib = gdstk.read_gds(GDS)
cells = {c.name: c for c in lib.cells}
top = cells['flag_checker']

LI, M1, M2, M3, M4, M5 = (67,20),(68,20),(69,20),(70,20),(71,20),(72,20)
MCON, VIA1, VIA2, VIA3, VIA4 = (67,44),(68,44),(69,44),(70,44),(71,44)
ROUTE = [LI, M1, M2, M3, M4, M5]
VIAS = {MCON:(LI,M1), VIA1:(M1,M2), VIA2:(M2,M3), VIA3:(M3,M4), VIA4:(M4,M5)}

# ---- cell pin label points (relative, um) ----
cell_pin_pts = {}
for cn, c in cells.items():
    d = defaultdict(list)
    for lb in c.labels:
        if (lb.layer, lb.texttype) == (67, 5):
            d[lb.text].append(tuple(lb.origin))
    cell_pin_pts[cn] = d

# ---- instances (name via GDS property 61) ----
def inst_name(ref):
    for pr in ref.properties:
        if pr[0] == 'S_GDS_PROPERTY' and pr[1] == 61:
            return pr[2].rstrip(b'\x00').decode()
    return None

def xf(pt, ref):
    x, y = pt
    if ref.x_reflection:
        y = -y
    r = ref.rotation
    if abs(r) > 1e-9:
        import math
        ca, sa = math.cos(r), math.sin(r)
        x, y = x*ca - y*sa, x*sa + y*ca
    return (x + ref.origin[0], y + ref.origin[1])

insts = []            # (instname, cellname, {pin: [abs pt]})
for ref in top.references:
    fam = ref.cell.name.split('__')[1]
    if fam.startswith(('decap', 'fill', 'tap')):
        continue
    nm = inst_name(ref)
    pins = {p: [xf(pt, ref) for pt in pts]
            for p, pts in cell_pin_pts[ref.cell.name].items()}
    insts.append((nm, ref.cell.name, pins))
sys.stderr.write(f'{len(insts)} logic instances\n')

# ---- flatten & collect geometry per layer ----
flat = top.copy('flat').flatten()
bylayer = defaultdict(list)
for p in flat.polygons:
    ld = (p.layer, p.datatype)
    if ld in ROUTE or ld in VIAS:
        bylayer[ld].append(p)

merged = {}
for ld in ROUTE:
    m = gdstk.boolean(bylayer.get(ld, []), [], 'or')
    # heal hairline gaps between same-net shards
    m = gdstk.boolean(gdstk.offset(m, 0.012, join='miter'), [], 'or')
    merged[ld] = gdstk.offset(m, -0.012, join='miter')
sys.stderr.write('merged: ' + ', '.join(f'{k}:{len(v)}' for k, v in merged.items()) + '\n')

# node = (layer, index in merged[layer]);  union-find
nodes = []
idx_of = {}
for ld in ROUTE:
    for i, poly in enumerate(merged[ld]):
        idx_of[(ld, i)] = len(nodes)
        (bx0,by0),(bx1,by1) = poly.bounding_box()
        nodes.append((ld, i, poly, (bx0,by0,bx1,by1)))

parent = list(range(len(nodes)))
def find(x):
    r = x
    while parent[r] != r: r = parent[r]
    while parent[x] != r: parent[x], x = r, parent[x]
    return r
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: parent[ra] = rb

def bbov(a, b):
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]

# bridge layers through vias.  Grow the via a hair so an edge-only landing
# still registers as an intersection, then require a real (non-empty) overlap.
for vl, (lo, hi) in VIAS.items():
    for v in bylayer.get(vl, []):
        vg = gdstk.offset([v], 0.04, join='bevel')
        (a0,b0),(a1,b1) = v.bounding_box()
        vb = (a0-0.02, b0-0.02, a1+0.02, b1+0.02)
        touch = {}
        for lay in (lo, hi):
            for i, poly in enumerate(merged[lay]):
                if not bbov(vb, nodes[idx_of[(lay, i)]][3]):
                    continue
                if gdstk.boolean(vg, [poly], 'and'):
                    touch[lay] = idx_of[(lay, i)]
                    break
        if lo in touch and hi in touch:
            union(touch[lo], touch[hi])

# ---- name nets from top-level port labels ----
named = {}
for lb in top.labels:
    if (lb.layer, lb.texttype) != (69, 5):     # met2 signal port labels
        continue
    pt = tuple(lb.origin)
    for i, poly in enumerate(merged[M2]):
        if gdstk.inside([pt], poly)[0]:
            named[find(idx_of[(M2, i)])] = lb.text
            break

auto = {}
def netname(root):
    if root in named: return named[root]
    if root not in auto: auto[root] = 'n%d' % len(auto)
    return auto[root]

# ---- resolve each instance pin: li1 label point -> merged li1 poly -> net ----
li_bb = []
for i in range(len(merged[LI])):
    (a0,b0),(a1,b1) = merged[LI][i].bounding_box()
    li_bb.append((i,(a0,b0,a1,b1)))
def pin_net(pt):
    for i, bb in li_bb:
        if bb[0]-0.05 <= pt[0] <= bb[2]+0.05 and bb[1]-0.05 <= pt[1] <= bb[3]+0.05:
            if gdstk.inside([pt], merged[LI][i])[0]:
                return netname(find(idx_of[(LI, i)]))
    return None

# resolve pins: a pin may hit several merged li regions (one real net + stray
# fragments).  Pick the candidate that the rest of the netlist uses the most.
raw = []          # (nm, fam, {pin: set(candidate nets)})
for nm, cn, pins in insts:
    cand = {}
    for pin, pts in pins.items():
        ns = {pin_net(pt) for pt in pts}
        ns.discard(None)
        cand[pin] = ns
    raw.append((nm, cn.split('__')[1], cand))

pop = defaultdict(int)
for _, _, cand in raw:
    for ns in cand.values():
        for n in ns:
            pop[n] += 1

print("# name cell {pin: net}")
for nm, fam, cand in sorted(raw, key=lambda t: t[0] or ''):
    conns = {}
    for pin, ns in cand.items():
        if not ns:
            conns[pin] = '?'
        else:
            conns[pin] = max(ns, key=lambda n: (n in named, pop[n], n))
    print(nm, fam, conns)
