"""Find the AS1130 memory-to-board mapping that matches the supplied photo."""

from pathlib import Path


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


def rows(text):
    return [[int(x) for x in line.split()] for line in text.splitlines() if line.strip()]


def load():
    left, right = PINOUT.read_text().split("Cathodes are lines CSn where n are")
    anodes = rows(left.split("Anodes are lines CSn where n are", 1)[1])
    cathodes = rows(right)
    frames = []
    for line in Path("i2c_packets.txt").read_text().splitlines():
        x = [int(v, 16) for v in line.split()[2:]]
        if len(x) == 134 and x[:2] == [0x60, 0x18]:
            frames.append(x[2:])
    return anodes, cathodes, frames


def main():
    anodes, cathodes, frames = load()
    formulas = {
        "c*11+a": lambda a, c: c * 11 + a,
        "c*11+a-skip": lambda a, c: c * 11 + a - (a > c),
        "a*11+c": lambda a, c: a * 11 + c,
        "a*11+c-skip": lambda a, c: a * 11 + c - (c > a),
        "a*12+c": lambda a, c: a * 12 + c,
        "c*10+a": lambda a, c: c * 10 + a,
        "a*10+c": lambda a, c: a * 10 + c,
    }
    transforms = {
        "normal": lambda g: g,
        "flip-x": lambda g: [r[::-1] for r in g],
        "flip-y": lambda g: g[::-1],
        "rotate-180": lambda g: [r[::-1] for r in g[::-1]],
    }
    for name, func in formulas.items():
        results = []
        for fnum, frame in enumerate(frames):
            grid = []
            valid = True
            for r in range(7):
                row = ""
                for col in range(17):
                    idx = func(anodes[r][col], cathodes[r][col])
                    if not 0 <= idx < len(frame):
                        valid = False
                        break
                    row += "#" if frame[idx] else "."
                if not valid:
                    break
                grid.append(row)
            if valid:
                for transform_name, transform in transforms.items():
                    oriented = transform(grid)
                    error = sum(a != b for row, target_row in zip(oriented, TARGET) for a, b in zip(row, target_row))
                    results.append((error, fnum, transform_name))
        print(name, sorted(results)[:12])


if __name__ == "__main__":
    main()
