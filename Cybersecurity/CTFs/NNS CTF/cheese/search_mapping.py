"""Score plausible AS1130 cross-plex addressing permutations."""

from pathlib import Path
from statistics import mean


PINOUT = Path(r"C:\Users\santey\Desktop\NNS CTF\dot-matrix\misc_dot-matrix\pinout.txt")
TARGET = [
    "#...#.#...#..###.",
    "#...#.#...#.#...#",
    "##..#.##..#.#....",
    "#.#.#.#.#.#..###.",
    "#..##.#..##.....#",
    "#...#.#...#.#...#",
    "#...#.#...#..###.",
]


def read_rows(text):
    return [[int(x) for x in line.split()] for line in text.splitlines() if line.strip()]


def load():
    left, right = PINOUT.read_text().split("Cathodes are lines CSn where n are")
    anodes = read_rows(left.split("Anodes are lines CSn where n are", 1)[1])
    cathodes = read_rows(right)
    frames = []
    for line in Path("i2c_packets.txt").read_text().splitlines():
        v = [int(x, 16) for x in line.split()[2:]]
        if len(v) == 134 and v[:2] == [0x60, 0x18]:
            frames.append(v[2:])
    return anodes, cathodes, frames


def grid(frame, anodes, cathodes, formula):
    return [
        "".join("#" if frame[formula(anodes[r][c], cathodes[r][c])] else "." for c in range(17))
        for r in range(7)
    ]


def hamming(one, two):
    return sum(x != y for a, b in zip(one, two) for x, y in zip(a, b))


def main():
    anodes, cathodes, frames = load()
    candidates = []
    # Let the first register digit be either supplied map coordinate, and
    # enumerate cyclic interpretations of the other 11-slot coordinate.
    for segment_name, segment in (("c", lambda a, c: c), ("a", lambda a, c: a)):
        for operation in ("plain", "plus", "minus"):
            for k in range(11):
                def make(segment=segment, operation=operation, k=k):
                    def formula(a, c):
                        s = segment(a, c)
                        other = a if segment_name == "c" else c
                        if operation == "plain":
                            j = other
                        elif operation == "plus":
                            j = (other + s + k) % 11
                        else:
                            j = (other - s + k) % 11
                        return s * 11 + j
                    return formula
                formula = make()
                try:
                    grids = [grid(f, anodes, cathodes, formula) for f in frames]
                except IndexError:
                    continue
                # An actual one-pixel scroll should resemble some horizontal
                # translated predecessor more than an unrelated bitmap.
                motion = []
                for left, right in zip(grids, grids[1:]):
                    shifted_left = [row[1:] + "." for row in left]
                    shifted_right = ["." + row[:-1] for row in left]
                    motion.append(min(hamming(left, right), hamming(shifted_left, right), hamming(shifted_right, right)))
                transforms = [
                    lambda g: g,
                    lambda g: [r[::-1] for r in g],
                    lambda g: g[::-1],
                    lambda g: [r[::-1] for r in g[::-1]],
                ]
                target_score = min(hamming(t(g), TARGET) for g in grids for t in transforms)
                candidates.append((round(mean(motion), 3), target_score, segment_name, operation, k))
    for row in sorted(candidates)[:30]:
        print(row)


if __name__ == "__main__":
    main()
