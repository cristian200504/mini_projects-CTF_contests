"""De-interleave the three scrolling streams in the AS1130 capture.

The sender writes three closely interleaved PWM updates per displayed column.
For each residue class we retain its 17x7 image and append the incoming edge
of successive left-moving images, producing a single long text ribbon.
"""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image


ROOT = Path(r"C:\Users\santey\Desktop\NNS CTF\cheese")
SOURCE = ROOT / "dotmatrix_raw.csv"

ANODES = [[int(x) for x in row.split()] for row in """8 1 0 1 1 9 2 2 5 2 6 5 9 6 5 1 5
1 0 0 0 9 1 6 6 2 6 7 6 7 9 0 6 6
0 0 9 1 8 1 2 3 2 2 3 3 3 9 0 2 3
4 4 5 8 3 1 6 4 2 3 9 4 3 3 0 3 8
8 6 8 8 0 8 7 3 8 1 9 9 2 8 5 8 4
5 5 9 0 4 5 6 3 4 4 1 5 5 4 2 4 4
5 8 9 7 0 7 7 7 7 7 1 6 7 2 7 7 4""".splitlines()]
CATHODES = [[int(x) for x in row.split()] for row in """11 11 0 2 1 2 10 11 2 6 11 0 6 10 1 6 3
0 11 1 6 0 7 6 7 7 2 11 3 10 7 7 0 1
2 10 1 10 1 3 1 6 2 3 11 7 10 3 3 0 8
11 6 4 4 1 4 4 7 4 2 4 10 3 4 4 0 9
8 9 6 0 9 7 9 9 3 9 9 10 9 2 9 5 9
11 10 5 5 0 7 5 5 3 1 5 6 5 2 5 5 4
8 10 8 0 8 7 8 5 3 1 8 8 6 8 2 4 8""".splitlines()]


def read_frames() -> list[list[list[int]]]:
    scl = sda = 0
    active = False
    bits: list[int] = []
    messages: list[list[int]] = []

    with SOURCE.open(newline="") as source:
        rows = csv.reader(source)
        next(rows)
        for row in rows:
            _, next_scl, next_sda = map(int, row)
            if scl and next_scl and sda != next_sda:
                if sda and not next_sda:
                    active, bits = True, []
                elif active:
                    messages.append(bits)
                    active, bits = False, []
            if active and not scl and next_scl:
                bits.append(next_sda)
            scl, sda = next_scl, next_sda

    frames: list[list[list[int]]] = []
    for raw_bits in messages:
        data = [
            sum(bit << (7 - offset) for offset, bit in enumerate(raw_bits[i : i + 8]))
            for i in range(0, len(raw_bits) // 9 * 9, 9)
        ]
        if len(data) == 134 and data[:2] == [0x60, 0x18]:
            pwm = data[2:]
            # The photographed display is wired in the opposite horizontal
            # direction from AS1130's coordinate numbering.  Mirror each row
            # into its human-readable orientation before de-interleaving.
            frames.append([
                [int(bool(pwm[CATHODES[y][x] * 11 + ANODES[y][x]])) for x in range(16, -1, -1)]
                for y in range(7)
            ])
    return frames


def shift_error(old: list[list[int]], new: list[list[int]]) -> int:
    return sum(old[y][x + 1] != new[y][x] for y in range(7) for x in range(16))


def ribbon(stream: list[list[list[int]]]) -> list[list[int]]:
    # The content moves one display pixel left per stream entry.  Start with
    # the first 17 columns and append the incoming rightmost column.
    result = [row[:] for row in stream[0]]
    for frame in stream[1:]:
        for y in range(7):
            result[y].append(frame[y][-1])
    return result


def save_image(rows: list[list[int]], target: Path) -> None:
    scale = 5
    image = Image.new("RGB", (len(rows[0]) * scale, len(rows) * scale), (28, 28, 28))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, bit in enumerate(row):
            if bit:
                for dy in range(scale - 1):
                    for dx in range(scale - 1):
                        pixels[x * scale + dx, y * scale + dy] = (245, 245, 245)
    image.save(target)


def render_text(rows: list[list[int]]) -> str:
    return "\n".join("".join("#" if bit else "." for bit in row) for row in rows)


def main() -> None:
    frames = read_frames()
    print(f"Recovered {len(frames)} PWM images")
    # Frames 0--4 are display startup.  Frame 5 is the first fully written
    # screen, and its residue class thereafter is a lossless one-pixel scroll.
    starts = {0: 3, 1: 4, 2: 5}
    for phase in range(3):
        stream = frames[starts[phase]::3]
        errors = [shift_error(a, b) for a, b in zip(stream, stream[1:])]
        print(f"phase {phase}: {len(stream)} images; shift errors min={min(errors)} max={max(errors)} mean={sum(errors)/len(errors):.2f}")
        rows = ribbon(stream)
        (ROOT / f"scroll_phase_{phase}.txt").write_text(render_text(rows) + "\n")
        save_image(rows, ROOT / f"scroll_phase_{phase}.png")
        # All font rows are vertically symmetric enough to recognize either
        # orientation, but also write the 180-degree physical orientation.
        rotated = [row[::-1] for row in rows[::-1]]
        (ROOT / f"scroll_phase_{phase}_rotated.txt").write_text(render_text(rotated) + "\n")
        save_image(rotated, ROOT / f"scroll_phase_{phase}_rotated.png")

        if phase == 2:
            (ROOT / "scroll_flag.txt").write_text(render_text(rows) + "\n")
            save_image(rows, ROOT / "scroll_flag.png")


if __name__ == "__main__":
    main()
