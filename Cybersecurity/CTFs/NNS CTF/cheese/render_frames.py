"""Rebuild dot-matrix frames from the exported AS1130 I2C traffic."""

from pathlib import Path


PINOUT = Path(r"C:\Users\santey\Desktop\NNS CTF\dot-matrix\misc_dot-matrix\pinout.txt")


def map_lines(text: str) -> list[list[int]]:
    return [[int(x) for x in line.split()] for line in text.splitlines() if line.strip()]


def read_map():
    before, cathode_text = PINOUT.read_text().split("Cathodes are lines CSn where n are")
    anode_text = before.split("Anodes are lines CSn where n are", 1)[1]
    return map_lines(anode_text), map_lines(cathode_text)


def index(cathode: int, anode: int) -> int:
    # AS1130 has 12 scan lines; within each line, the other 11 CS lines are
    # stored consecutively.  The self-pair is omitted.
    return cathode * 11 + anode


def render(values: list[int], anodes, cathodes, reversed_pair=False) -> list[str]:
    return [
        "".join(
            "#" if values[index(anodes[r][c], cathodes[r][c]) if reversed_pair else index(cathodes[r][c], anodes[r][c])] else "."
            for c in range(17)
        )
        for r in range(7)
    ]


def main() -> None:
    frames = []
    for line in Path("i2c_packets.txt").read_text(encoding="ascii").splitlines():
        fields = line.split()
        values = [int(x, 16) for x in fields[2:]]
        # All display writes use device write address 0x60 and PWM memory
        # register address 0x18, followed by the 132 PWM cells.
        if len(values) == 134 and values[:2] == [0x60, 0x18]:
            frames.append(values[2:])

    anodes, cathodes = read_map()
    output = []
    for number, frame in enumerate(frames):
        output.append(f"FRAME {number}")
        output += render(frame, anodes, cathodes)
        output.append("")
    Path("frames.txt").write_text("\n".join(output), encoding="ascii")
    print(f"frames: {len(frames)}")
    for number in [0, 1, 2, 3, 4, 5, 10, 20, 50, 100, 200, 300, 400, 433, 434, 500, 600, 700]:
        frame = frames[number]
        print(f"FRAME {number}")
        print("\n".join(render(frame, anodes, cathodes)))
    print("REVERSED FRAME 3")
    print("\n".join(render(frames[3], anodes, cathodes, reversed_pair=True)))


if __name__ == "__main__":
    main()
