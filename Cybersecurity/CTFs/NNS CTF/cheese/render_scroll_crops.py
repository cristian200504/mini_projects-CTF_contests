"""Make enlarged, human-readable crops of the recovered scroll ribbon."""
from pathlib import Path

from PIL import Image

import stitch_scroll


ROOT = Path(r"C:\Users\santey\Desktop\NNS CTF\cheese")


def save(rows: list[list[int]], path: Path) -> None:
    scale = 22
    height, width = len(rows), len(rows[0])
    image = Image.new("RGB", (width * scale, height * scale), (30, 30, 30))
    for y, row in enumerate(rows):
        for x, bit in enumerate(row):
            if bit:
                for dy in range(scale - 3):
                    for dx in range(scale - 3):
                        image.putpixel((x * scale + dx + 1, y * scale + dy + 1), (245, 245, 245))
    image.save(path)


def main() -> None:
    rows = stitch_scroll.ribbon(stitch_scroll.read_frames()[5::3])
    for vertical_name, oriented in (("raw", rows), ("upright", rows[::-1])):
        for number, start in enumerate(range(0, len(rows[0]), 48)):
            crop = [row[start : start + 48] for row in oriented]
            save(crop, ROOT / f"flag_{vertical_name}_{number}.png")


if __name__ == "__main__":
    main()
