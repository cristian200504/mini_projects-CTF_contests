# etch-a-sketch — solve

**Flag:** `K17{my_masterpiece}`

## Challenge

Given a single file, `etchasketch`: a not-stripped x86-64 ELF (dynamically linked,
PIE). Description: *"I drew you a picture, hope you like it <3"*.

## Static analysis

`nm`/`objdump` show three interesting functions: `dab`, `line`, `main` (plus a
global `brush_r`, `canvas`, and `points` array visible in the symbol table).

- `main` reads an array of 0x145 (325) packed 32-bit entries from `.rodata` at
  address `0x2020` (symbol `points`). Each entry is two little-endian `int16_t`
  values: `x` (low 16 bits) and `y` (high 16 bits).
- The point stream is a simple vector "pen" plotter:
  - `x == -2` (`0xfffe`) terminates the stream.
  - `x < 0` (e.g. `(-1, -1)`) is a **pen-up** marker — just move, don't draw.
  - Otherwise, if the previous point was valid, `line(prev, cur)` is called to
    draw a line from the previous point to the current one (Bresenham-style,
    implemented by hand in `line`/`dab`).
- `dab(x, y)` plots a filled square of radius `brush_r` (global at `0x4020`,
  initial value `10`) around `(x, y)` into `canvas` (a `120 x 82` byte grid at
  `0x4060`, `.bss`).
- `main` then prints `canvas` as ASCII art: `#` for set pixels, space
  otherwise, row by row (120 cols × 82 rows).

## The trap

Running the binary as-is (in WSL, since it's a Linux ELF) just prints a solid
black blob — `brush_r = 10` is large enough relative to the 120x82 canvas that
every stroke gets fattened into an unreadable mass of `#`.

## Fix: shrink the brush / re-render as a vector image

Two options, both used here:

1. **Patch `brush_r` to 0** in a copy of the binary (file offset `0x3020`,
   4 bytes, `0a 00 00 00` → `00 00 00 00`) and re-run in WSL. This gives a
   thin-outline ASCII rendering — readable, but still fiddly to eyeball as
   letters.
2. **Better: parse `points` directly from the file** and replay the same
   pen-up / line-to logic in Python with Pillow, drawing at a large scale
   (e.g. 12–14x) with anti-aliased lines. This turns the vector "sketch" into
   a crisp image of a hand-drawn font.

```python
import struct
from PIL import Image, ImageDraw

with open('etchasketch', 'rb') as f:
    data = f.read()

points_off = 0x2020
pts = []
for i in range(0x145):
    x, y = struct.unpack_from('<hh', data, points_off + i*4)
    if x == -2:
        break
    pts.append((x, y))

SCALE = 14
img = Image.new('RGB', (120*SCALE, 82*SCALE), 'white')
draw = ImageDraw.Draw(img)

prev = None
for (x, y) in pts:
    if x < 0:
        prev = None
        continue
    if prev is not None:
        if prev == (x, y):
            r = 5  # isolated point (e.g. an "i" dot) — draw as a dot
            draw.ellipse([x*SCALE-r, y*SCALE-r, x*SCALE+r, y*SCALE+r], fill='black')
        else:
            draw.line([(prev[0]*SCALE, prev[1]*SCALE), (x*SCALE, y*SCALE)],
                       fill='black', width=4)
    prev = (x, y)

img.save('flag_render.png')
```

## Reading the picture

The rendered image spells out, across three wrapped rows of a stick/vector
font:

```
K17{my_
master
piece}
```

One easy misread: the second character of the third row looks like a bare
vertical stroke with a serif (same shape as the "1" in "K17"), but it is
actually a lowercase **i** — its dot is a separate zero-length "line" segment
(a single point repeated twice in the `points` array) sitting well above the
letter's x-height. Rendering zero-length segments as a small filled dot (as
above) makes this unambiguous. Concatenating the three rows exactly as drawn
(no inserted separators except the underscore that's actually present after
"my") gives:

```
K17{my_masterpiece}
```

## Flag

```
K17{my_masterpiece}
```
