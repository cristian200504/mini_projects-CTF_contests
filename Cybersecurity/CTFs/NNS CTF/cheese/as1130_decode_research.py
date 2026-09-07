from __future__ import annotations

import csv
import sys
from pathlib import Path


SOURCE = Path(r"C:\Users\santey\Desktop\NNS CTF\cheese\dotmatrix_raw.csv")


def decode() -> list[tuple[int, list[int]]]:
    """Decode Channel 1 as SCL and Channel 2 as SDA from a change-only CSV."""
    scl = sda = 0
    in_message = False
    bits: list[int] = []
    messages: list[tuple[int, list[int]]] = []
    start_sample = 0

    with SOURCE.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sample, next_scl, next_sda = map(lambda x: int(x.strip()), row)

            # I2C START and STOP occur when SDA changes while SCL is high.
            if scl and next_scl and sda != next_sda:
                if sda and not next_sda:
                    if in_message and bits:
                        # A repeated START closes the prior transaction.
                        messages.append((start_sample, bits))
                    in_message = True
                    bits = []
                    start_sample = sample
                elif not sda and next_sda:
                    if in_message:
                        messages.append((start_sample, bits))
                    in_message = False
                    bits = []

            # Data is clocked in on SCL's rising edge.
            if in_message and not scl and next_scl:
                bits.append(next_sda)

            scl, sda = next_scl, next_sda

    if in_message and bits:
        messages.append((start_sample, bits))
    return messages


def as_bytes(bits: list[int]) -> tuple[list[int], list[int]]:
    data, acks = [], []
    for offset in range(0, len(bits) // 9 * 9, 9):
        byte = 0
        for bit in bits[offset : offset + 8]:
            byte = byte * 2 + bit
        data.append(byte)
        acks.append(bits[offset + 8])
    return data, acks


if __name__ == "__main__":
    messages = decode()
    txs = [(sample, as_bytes(bits)[0]) for sample, bits in messages]
    frames = [
        (i, sample, data[2:134])
        for i, (sample, data) in enumerate(txs)
        if len(data) >= 134 and data[:2] == [0x60, 0x18]
    ]
    print("messages", len(messages), "PWM frames", len(frames))

    # The supplied wiring table gives a physical 17x7 pixel location's
    # AS1130 matrix coordinates.  A PWM data byte is indexed by
    # `cathode * 11 + anode` in 12x11 mode.
    anodes = [
        [8,1,0,1,1,9,2,2,5,2,6,5,9,6,5,1,5],
        [1,0,0,0,9,1,6,6,2,6,7,6,7,9,0,6,6],
        [0,0,9,1,8,1,2,3,2,2,3,3,3,9,0,2,3],
        [4,4,5,8,3,1,6,4,2,3,9,4,3,3,0,3,8],
        [8,6,8,8,0,8,7,3,8,1,9,9,2,8,5,8,4],
        [5,5,9,0,4,5,6,3,4,4,1,5,5,4,2,4,4],
        [5,8,9,7,0,7,7,7,7,7,1,6,7,2,7,7,4],
    ]
    cathodes = [
        [11,11,0,2,1,2,10,11,2,6,11,0,6,10,1,6,3],
        [0,11,1,6,0,7,6,7,7,2,11,3,10,7,7,0,1],
        [2,10,1,10,1,3,1,6,2,3,11,7,10,3,3,0,8],
        [11,6,4,4,1,4,4,7,4,2,4,10,3,4,4,0,9],
        [8,9,6,0,9,7,9,9,3,9,9,10,9,2,9,5,9],
        [11,10,5,5,0,7,5,5,3,1,5,6,5,2,5,5,4],
        [8,10,8,0,8,7,8,5,3,1,8,8,6,8,2,4,8],
    ]

    def render(data: list[int], flip_x: bool = False) -> str:
        return "\n".join(
            "".join(
                "#" if data[cathodes[y][16 - x if flip_x else x] * 11 + anodes[y][16 - x if flip_x else x]] else "."
                for x in range(17)
            )
            for y in range(7)
        )

    # First, last and each non-identical frame are useful for locating text.
    photo = [
        "#...#.#...#..###.",
        "#...#.#...#.#...#",
        "##..#.##..#.#....",
        "#.#.#.#.#.#..###.",
        "#..##.#..##.....#",
        "#...#.#...#.#...#",
        "#...#.#...#..###.",
    ]
    ranked = []
    for n, (_, _, data) in enumerate(frames):
        bits = render(data).splitlines()
        difference = sum(a != b for arow, brow in zip(bits, photo) for a, b in zip(arow, brow))
        ranked.append((difference, n))
    print("photo nearest", sorted(ranked)[:15])

    flipped = "--flip" in sys.argv[1:]
    wanted = {int(x) for x in sys.argv[1:] if x != "--flip"}
    last = None
    for n, (i, sample, data) in enumerate(frames):
        pixels = render(data, flipped)
        if (wanted and n in wanted) or (not wanted and pixels != last):
            print(f"\nFRAME {n} transaction {i} sample {sample}\n{pixels}")
        last = pixels
