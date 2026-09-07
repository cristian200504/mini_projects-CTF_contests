#!/usr/bin/env python3
"""
NNS CTF - "littlefs"  (misc / hardware, beginner, 77 pts)

Recovers the flag from a Saleae Logic 1.x `.logicdata` capture of the SPI bus
between an nRF5340 and an mx25r64 NOR flash.  Firmware = Zephyr + littlefs; it
mounts the flash filesystem and reads /lfs1/flag.txt, so the file's 80 bytes
travel over the SPI data line.

The intended solve is: open the capture in Saleae Logic 2, add the SPI analyser
(Clock = ch2, Enable = ch1 active-low, MOSI = ch0, MISO = ch3, CPOL 0 / CPHA 0,
MSB first) and read the flag out of the decoded byte column.

This script does the same thing without the GUI: it parses the undocumented
`.logicdata` container directly (see SOLUTION.md), rebuilds the four waveforms,
and decodes the SPI transfers.

Usage:  python solve.py littlefs.logicdata
"""
import sys
import struct
import bisect


# ---------------------------------------------------------------- container --
def load(path):
    data = open(path, "rb").read()
    n = len(data)
    u64 = lambda o: struct.unpack_from("<Q", data, o)[0]

    # 4 "structured sections": 8x0xFF, u64==3, then 32-byte records
    #   (ts:u64, f1:u64, f2:u64, f3:u64)
    # f3==1 records are timing checkpoints:  f1 = cumulative edge count,
    #                                        ts = absolute sample time of edge f1.
    ffs, i = [], 0
    while True:
        j = data.find(b"\xff" * 8, i)
        if j < 0:
            break
        ffs.append(j)
        i = j + 1
    starts = [j for j in ffs if u64(j + 8) == 3][:4]

    structs, ends = [], []
    for st in starts:
        o, recs = st + 16, []
        while o + 32 <= n:
            ts, f1, f2, f3 = u64(o), u64(o + 8), u64(o + 16), u64(o + 24)
            if ts > 0x7FFFFFFF or (recs and ts + 8 < recs[-1][0]):
                break
            if f3 > 32 or f1 > 1e7 or f2 > 1e7:
                break
            recs.append((ts, f1, f2, f3))
            o += 32
        structs.append(recs)
        ends.append(o)

    # the compact edge stream ("block1") sits just before each structured
    # section, bracketed by a 3x-repeated  <01|02> <varint> 00  marker.
    # one byte per edge:  delta = b & 0x7f   (samples since previous edge)
    #                     level = b >> 7     (line level after the edge)
    def block1(idx):
        lo = 0x180 if idx == 0 else ends[idx - 1]
        seg = data[lo:starts[idx]]
        spans, k = [], 0
        while k < len(seg) - 6:
            hit = False
            if seg[k] in (1, 2):
                for vlen in (1, 2, 3):
                    ul = 1 + vlen + 1
                    u = seg[k:k + ul]
                    if len(u) == ul and u[-1] == 0 and seg[k:k + 3 * ul - 1] == u + u + u[:-1]:
                        spans.append((k, k + 3 * ul - 1))
                        k += 3 * ul - 1
                        hit = True
                        break
            if not hit:
                k += 1
        return seg[spans[0][1]:spans[1][0]]

    return structs, block1


def timeline(b1, recs):
    """block1 stream + f3==1 checkpoints  ->  sorted [(sample_time, level)]."""
    m = len(b1)
    delta = [x & 0x7F for x in b1]
    level = [x >> 7 for x in b1]
    cum = [0]
    for d in delta:
        cum.append(cum[-1] + d)

    cps = sorted({(f1, ts) for ts, f1, f2, f3 in recs if f3 == 1 and 0 <= f1 <= m})
    mono = []
    for f1, ts in cps:
        if mono and (f1 <= mono[-1][0] or ts < mono[-1][1]):
            continue
        mono.append((f1, ts))
    cps = mono

    abst = [None] * m
    for a in range(len(cps)):
        f_a, ts_a = cps[a]
        f_b = cps[a + 1][0] if a + 1 < len(cps) else m
        base = cum[f_a]
        for k in range(f_a, min(f_b, m)):
            abst[k] = ts_a + (cum[k + 1] - base)
        if 0 <= f_a - 1 < m:
            abst[f_a - 1] = ts_a
    last = cps[0][1] if cps else 0
    for k in range(m):
        if abst[k] is None:
            abst[k] = last
        else:
            last = abst[k]
    return sorted(zip(abst, level))


# ------------------------------------------------------------------- decode --
def decode(structs, block1, drop_spurious, flip_marker, sample_at):
    """Reconstruct the SPI byte stream from the data line.

    drop_spurious : remove the phantom first clock the timeline emits per burst
    flip_marker   : flip the burst's first data edge (a resync marker that
                    carries the pre-gap level, not the real one)
    sample_at     : 0 -> sample the data line AT each rising clock edge
                   -1 -> sample at the preceding (falling) edge
    """
    counts = {i: len(block1(i)) for i in range(4)}
    sck_i = max(counts, key=counts.get)                    # clock: most edges
    data_i = sorted(counts, key=counts.get)[2]             # data line: 2nd most

    sck = timeline(block1(sck_i), structs[sck_i])
    st = [t for t, l in sck]
    sl = [l for t, l in sck]

    rising = [k for k in range(len(sck)) if sl[k] == 1]
    bursts, cur = [], [rising[0]]
    for a, b in zip(rising, rising[1:]):
        if st[b] - st[a] > 30:
            bursts.append(cur)
            cur = [b]
        else:
            cur.append(b)
    bursts.append(cur)
    if drop_spurious:
        for seg in bursts:
            if len(seg) > 2 and st[seg[1]] - st[seg[0]] < 5:
                del seg[0]

    snap = {}
    for t, l in timeline(block1(data_i), structs[data_i]):
        p = bisect.bisect_left(st, t)
        cand = [x for x in (p - 2, p - 1, p, p + 1, p + 2) if 0 <= x < len(st)]
        snap[min(cand, key=lambda x: abs(st[x] - t))] = l
    snap = sorted(snap.items())

    IDLE = 1
    out = bytearray()
    for seg in bursts:
        i0 = bisect.bisect_left([e for e, l in snap], seg[0] - 2)
        i1 = bisect.bisect_right([e for e, l in snap], seg[-1] + 2)
        loc = [list(x) for x in snap[i0:i1]]
        if flip_marker and loc and loc[0][1] == IDLE:
            loc[0][1] = 1 - IDLE
        le = [x[0] for x in loc]
        bits = []
        for ei in seg:
            p = bisect.bisect_right(le, ei + sample_at)
            bits.append((loc[p - 1][1] if p else IDLE) ^ 1)   # data line is inverted
        for j in range(0, len(bits) // 8 * 8, 8):
            v = 0
            for x in bits[j:j + 8]:
                v = (v << 1) | x
            out.append(v)
    return bytes(out)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    structs, block1 = load(sys.argv[1])

    # Pass A: straight decode. Every 64-bit-aligned byte is correct EXCEPT
    #         byte 0 of each read burst (clock-gap resync artefact).
    body = decode(structs, block1, drop_spurious=False, flip_marker=False, sample_at=0)
    # Pass B: drop the phantom burst-start clock + fix the resync marker; this
    #         recovers byte 0 of each burst (but shifts the tail by one clock).
    head = decode(structs, block1, drop_spurious=True, flip_marker=True, sample_at=-1)

    a = body.find(b"NS{") - 1                     # start of read chunk 1
    b = body.find(b"mb3dded") - 1                 # start of read chunk 2
    chunk1 = bytes([head[head.find(b"NS{") - 1]]) + body[a + 1:a + 64]
    chunk2 = bytes([head[head.find(b"mb3dded") - 1]]) + body[b + 1:b + 16]
    print((chunk1 + chunk2).decode("latin1"))


if __name__ == "__main__":
    main()
