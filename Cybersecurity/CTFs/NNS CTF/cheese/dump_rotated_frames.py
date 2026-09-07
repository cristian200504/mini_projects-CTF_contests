from pathlib import Path
import sys

from render_frames import read_map, render


def frames():
    result = []
    for line in Path("i2c_packets.txt").read_text().splitlines():
        values = [int(x, 16) for x in line.split()[2:]]
        if len(values) == 134 and values[:2] == [0x60, 0x18]:
            result.append(values[2:])
    return result


def rotate(grid):
    return [row[::-1] for row in grid[::-1]]


if __name__ == "__main__":
    source = frames()
    anodes, cathodes = read_map()
    wanted = [int(x) for x in sys.argv[1:]] or list(range(len(source)))
    for number in wanted:
        print(f"FRAME {number}")
        print("\n".join(rotate(render(source[number], anodes, cathodes))))
        print()
