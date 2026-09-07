"""Create quick contact sheets for candidate AS1130 address maps."""

from pathlib import Path
import sys
from PIL import Image, ImageDraw

from render_frames import read_map


MODE = sys.argv[1] if len(sys.argv) > 1 else "skip"


def get_frames():
    f = []
    for line in Path("i2c_packets.txt").read_text().splitlines():
        data = [int(x, 16) for x in line.split()[2:]]
        if len(data) == 134 and data[:2] == [0x60, 0x18]:
            f.append(data[2:])
    return f


def index(a, c):
    if MODE == "skip":
        return c * 11 + a - (a > c)
    if MODE == "swap_skip":
        return a * 11 + c - (c > a)
    if MODE == "swap":
        return a * 11 + c
    if MODE == "direct":
        return c * 11 + a
    raise ValueError(MODE)


def main():
    anodes, cathodes = read_map()
    grids = []
    for frame in get_frames():
        grid = []
        for r in range(7):
            grid.append("".join("#" if frame[index(anodes[r][x], cathodes[r][x])] else "." for x in range(17)))
        grids.append([row[::-1] for row in grid[::-1]])
    scale, label, cols = 6, 14, 20
    cw, ch = 17 * scale, 7 * scale + label
    rows = (len(grids) + cols - 1) // cols
    output = Image.new("RGB", (cols*cw, rows*ch), "#202020")
    draw = ImageDraw.Draw(output)
    for i, grid in enumerate(grids):
        x0,y0 = i%cols*cw, i//cols*ch
        draw.text((x0+1,y0),str(i),fill='white')
        for y,row in enumerate(grid):
            for x,v in enumerate(row):
                if v=='#': draw.rectangle((x0+x*scale,y0+label+y*scale,x0+(x+1)*scale-1,y0+label+(y+1)*scale-1),fill='white')
    output.save(f"variant_{MODE}.png")


if __name__ == '__main__':
    main()
