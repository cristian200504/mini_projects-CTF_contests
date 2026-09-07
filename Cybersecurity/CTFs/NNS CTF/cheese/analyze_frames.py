"""Analyze and visualize reconstructed 17x7 AS1130 screen states."""

from pathlib import Path
from collections import Counter

from PIL import Image, ImageDraw

from render_frames import read_map, render


def get_frames():
    result = []
    for line in Path("i2c_packets.txt").read_text(encoding="ascii").splitlines():
        values = [int(x, 16) for x in line.split()[2:]]
        if len(values) == 134 and values[:2] == [0x60, 0x18]:
            result.append(values[2:])
    return result


def bits(grid):
    return "".join(grid)


def hamming(left, right):
    return sum(a != b for one, two in zip(left, right) for a, b in zip(one, two))


def main():
    frames = get_frames()
    anodes, cathodes = read_map()
    # The supplied board photo establishes the left-right physical orientation.
    # The AS1130 CS order is electrically mirrored relative to that view.
    grids = [list(reversed([row[::-1] for row in render(frame, anodes, cathodes)])) for frame in frames]
    flat = [bits(grid) for grid in grids]
    changes = [sum(a != b for a, b in zip(left, right)) for left, right in zip(flat, flat[1:])]
    print("count", len(frames))
    print("lit first 80", [x.count("#") for x in flat[:80]])
    print("change distribution", Counter(changes).most_common())
    print("most static transitions", [(i + 1, d) for i, d in enumerate(changes) if d <= 1][:100])
    for n in range(3, 15):
        before, after = grids[n], grids[n + 1]
        candidates = {
            "left": [row[1:] + "." for row in before],
            "same": before,
            "right": ["." + row[:-1] for row in before],
        }
        scores = {name: sum(x != y for a, b in zip(candidate, after) for x, y in zip(a, b)) for name, candidate in candidates.items()}
        print(n, scores)
    for n in range(3, 10):
        before, after = grids[n], grids[n + 1]
        choices = []
        for dy in range(-2, 3):
            for dx in range(-3, 4):
                shifted = []
                for y in range(7):
                    row = ""
                    for x in range(17):
                        sy, sx = y - dy, x - dx
                        row += before[sy][sx] if 0 <= sy < 7 and 0 <= sx < 17 else "."
                    shifted.append(row)
                choices.append((hamming(shifted, after), dx, dy))
        print("2D", n, min(choices))

    scale, label, cols = 6, 14, 20
    cell_w, cell_h = 17 * scale, 7 * scale + label
    rows = (len(grids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "#202020")
    draw = ImageDraw.Draw(sheet)
    for i, grid in enumerate(grids):
        x0, y0 = (i % cols) * cell_w, (i // cols) * cell_h
        draw.text((x0 + 1, y0), str(i), fill="white")
        for y, row in enumerate(grid):
            for x, p in enumerate(row):
                if p == "#":
                    draw.rectangle((x0 + x * scale, y0 + label + y * scale, x0 + (x + 1) * scale - 1, y0 + label + (y + 1) * scale - 1), fill="white")
    sheet.save("frame_sheet_rotated.png")


if __name__ == "__main__":
    main()
