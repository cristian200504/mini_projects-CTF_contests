"""Extract the stable 5x7 character cells from the left-scrolling matrix."""

from pathlib import Path
from collections import defaultdict

from PIL import Image, ImageDraw

from render_frames import read_map, render


def source_frames():
    result = []
    for line in Path("i2c_packets.txt").read_text().splitlines():
        v = [int(x, 16) for x in line.split()[2:]]
        if len(v) == 134 and v[:2] == [0x60, 0x18]:
            result.append(v[2:])
    anodes, cathodes = read_map()
    return [[row[::-1] for row in render(frame, anodes, cathodes)[::-1]] for frame in result]


def glyph(grid, begin):
    return tuple(row[begin : begin + 5] for row in grid)


def main():
    grids = source_frames()
    # At frame 5, character #1 is at x=5 and character #2 at x=11.  Every
    # six frame updates advances exactly one 5-pixel glyph plus its spacer.
    cells = []
    for n in range(5, len(grids), 6):
        cells.append((n, glyph(grids[n], 5), glyph(grids[n], 11)))

    print("cells", len(cells))
    for n, left, right in cells:
        print(f"FRAME {n} X5")
        print("\n".join(left))
        print(f"FRAME {n} X11")
        print("\n".join(right))

    # Contact sheets in manageable chunks put the stream in reading order.
    scale, label, cols, chunk_size = 20, 22, 10, 30
    cw, ch = 5 * scale, 7 * scale + label
    for first in range(0, len(cells), chunk_size):
        chunk = cells[first : first + chunk_size]
        rows = (len(chunk) + cols - 1) // cols
        image = Image.new("RGB", (cw * cols, ch * rows), "#202020")
        draw = ImageDraw.Draw(image)
        for local, (frame, _, cell) in enumerate(chunk):
            i = first + local
            x, y = (local % cols) * cw, (local // cols) * ch
            draw.text((x + 1, y), str(i + 2), fill="white")
            for yy, line in enumerate(cell):
                for xx, value in enumerate(line):
                    if value == "#":
                        draw.rectangle((x + xx * scale, y + label + yy * scale, x + (xx + 1) * scale - 1, y + label + (yy + 1) * scale - 1), fill="white")
        image.save(f"glyph_chunk_{first // chunk_size}.png")


if __name__ == "__main__":
    main()
