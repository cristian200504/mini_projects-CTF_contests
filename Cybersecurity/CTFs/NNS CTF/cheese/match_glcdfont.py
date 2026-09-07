"""Try the recovered 5x7 glyph cells against the classic GLCD font."""
from __future__ import annotations

import re
from urllib.request import urlopen

import stitch_scroll


FONT_URL = "https://raw.githubusercontent.com/adafruit/Adafruit-GFX-Library/master/glcdfont.c"


def load_font() -> list[int]:
    source = urlopen(FONT_URL, timeout=20).read().decode("utf-8")
    payload = source.split("font[] PROGMEM = {", 1)[1].split("};", 1)[0]
    values = [int(token, 16) for token in re.findall(r"0x([0-9A-Fa-f]{2})", payload)]
    if len(values) != 1280:
        raise RuntimeError(f"expected 1280 font bytes, got {len(values)}")
    return values


def matrix(columns: list[int]) -> list[list[int]]:
    return [[(columns[x] >> y) & 1 for x in range(5)] for y in range(7)]


def transform(columns: list[int], flip_x: bool, flip_y: bool) -> list[int]:
    pixels = matrix(columns)
    if flip_y:
        pixels = pixels[::-1]
    if flip_x:
        pixels = [row[::-1] for row in pixels]
    return [sum(pixels[y][x] << y for y in range(7)) for x in range(5)]


def hamming(left: list[int], right: list[int]) -> int:
    return sum((a ^ b).bit_count() for a, b in zip(left, right))


def as_picture(columns: list[int]) -> str:
    return " / ".join("".join("#" if (columns[x] >> y) & 1 else "." for x in range(5)) for y in range(6, -1, -1))


def main() -> None:
    rows = stitch_scroll.ribbon(stitch_scroll.read_frames()[5::3])
    cells: list[list[int]] = []
    # The capture begins one pixel into the first N.  Cells are five pixels
    # wide with a one-pixel separator, so cell 0 begins at x=-1.
    for start in range(-1, len(rows[0]), 6):
        cells.append([
            sum((rows[y][start + x] if 0 <= start + x < len(rows[0]) else 0) << y for y in range(7))
            for x in range(5)
        ])

    font = load_font()
    printable = [(chr(code), font[code * 5 : code * 5 + 5]) for code in range(32, 127)]
    for flip_x in (False, True):
        for flip_y in (False, True):
            candidates = []
            errors = 0
            for cell in cells:
                ranked = sorted((hamming(cell, transform(pattern, flip_x, flip_y)), char) for char, pattern in printable)
                errors += ranked[0][0]
                candidates.append(ranked[0][1])
            print(f"flip_x={flip_x} flip_y={flip_y} total={errors}: {''.join(candidates)}")

    print("\nBest candidates using a vertical flip (cell, best five):")
    for number, cell in enumerate(cells):
        ranked = sorted((hamming(cell, transform(pattern, False, True)), char) for char, pattern in printable)[:5]
        print(f"{number:02d} {cell!s:28} {' '.join(f'{char}:{cost}' for cost, char in ranked):20} {as_picture(cell)}")


if __name__ == "__main__":
    main()
