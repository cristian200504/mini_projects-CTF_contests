from __future__ import annotations

from as1130_decode_research import as_bytes, decode

ANODES = [
    [8,1,0,1,1,9,2,2,5,2,6,5,9,6,5,1,5],
    [1,0,0,0,9,1,6,6,2,6,7,6,7,9,0,6,6],
    [0,0,9,1,8,1,2,3,2,2,3,3,3,9,0,2,3],
    [4,4,5,8,3,1,6,4,2,3,9,4,3,3,0,3,8],
    [8,6,8,8,0,8,7,3,8,1,9,9,2,8,5,8,4],
    [5,5,9,0,4,5,6,3,4,4,1,5,5,4,2,4,4],
    [5,8,9,7,0,7,7,7,7,7,1,6,7,2,7,7,4],
]
CATHODES = [
    [11,11,0,2,1,2,10,11,2,6,11,0,6,10,1,6,3],
    [0,11,1,6,0,7,6,7,7,2,11,3,10,7,7,0,1],
    [2,10,1,10,1,3,1,6,2,3,11,7,10,3,3,0,8],
    [11,6,4,4,1,4,4,7,4,2,4,10,3,4,4,0,9],
    [8,9,6,0,9,7,9,9,3,9,9,10,9,2,9,5,9],
    [11,10,5,5,0,7,5,5,3,1,5,6,5,2,5,5,4],
    [8,10,8,0,8,7,8,5,3,1,8,8,6,8,2,4,8],
]
PHOTO = [
    "#...#.#...#..###.",
    "#...#.#...#.#...#",
    "##..#.##..#.#....",
    "#.#.#.#.#.#..###.",
    "#..##.#..##.....#",
    "#...#.#...#.#...#",
    "#...#.#...#..###.",
]


def main() -> None:
    txs = [(s, as_bytes(bits)[0]) for s, bits in decode()]
    frames = [d[2:134] for _, d in txs if len(d) >= 134 and d[:2] == [0x60, 0x18]]
    results = []
    for layout in ("cathode11anode", "anode12cathode"):
        for invert_anode in (False, True):
            for invert_cathode in (False, True):
                for flipx in (False, True):
                    for flipy in (False, True):
                        for inverted_brightness in (False, True):
                            best = 120
                            best_frame = 0
                            for n, d in enumerate(frames):
                                difference = 0
                                for py in range(7):
                                    for px in range(17):
                                        x = 16 - px if flipx else px
                                        y = 6 - py if flipy else py
                                        a = ANODES[y][x]
                                        c = CATHODES[y][x]
                                        if invert_anode:
                                            a = 10 - a
                                        if invert_cathode:
                                            c = 11 - c
                                        i = c * 11 + a if layout == "cathode11anode" else a * 12 + c
                                        on = d[i] != 0
                                        if inverted_brightness:
                                            on = not on
                                        if on != (PHOTO[py][px] == "#"):
                                            difference += 1
                                if difference < best:
                                    best, best_frame = difference, n
                            results.append((best, best_frame, layout, invert_anode, invert_cathode, flipx, flipy, inverted_brightness))
    for result in sorted(results)[:40]:
        print(result)


if __name__ == "__main__":
    main()
