# Truck-kun — CTF Challenge Writeup

## Challenge Information
- **Name:** Truck-kun
- **Points:** 10
- **Author:** Veryyes
- **Description:** `頑張ってトラックくん!` — *Note: flag is case-insensitive.*
- **Provided:** `truck-kun.x86_64` (70 MB Linux ELF)
- **Flag:** `RSTCON{REBORN-IN-ANOTHER-WORLD-BUT-IM-PLAYING-CTFS}` (case-insensitive)

---

## 1. Reconnaissance

`truck-kun.x86_64` is a **Godot 4.5** game (truck delivery sim: pick up cargo, deliver it to waypoints). The `GDPC` magic appears in the binary, so the game data is an embedded PCK. The challenge is a *"don't play the game, read the files"* type.

The PCK trailer (last 12 bytes) is `<uint64 pck_size><"GDPC">`, with `pck_size = 366204`. So the PCK starts at `len(file) - 12 - 366204 = 70285592`.

## 2. Extracting the PCK

PCK v3 header: `magic, pack_ver=3, godot 4.5.0, flags=2, file_base (u64)=104, dir_offset (u64)=363000`. The files are not encrypted, so the directory can be parsed directly (`path_len, path, offset, size, md5[16], flags`) and dumped. It contains 40 files:

- `scripts/*.gdc` — compiled GDScript (HUD, Main, NPC, Truck, Waypoint)
- `.godot/exported/.../*.scn` — binary scenes (Bush, Tree, HUD, Main, NPC, Waypoint, CoolingTower, Cow, Truck, PowerPole, **Substrate**)
- `audio/bgm.ogg`, `icon.svg`, `project.binary`

## 3. Dead end: the scripts

The `.gdc` files are tokenized GDScript (v101) wrapped in a zstd frame; identifiers are UTF-32 XOR `0xB6`. Decoding all five scripts shows only ordinary gameplay logic (engine force, steering, waypoints, HUD labels) — no flag, no secrets.

## 4. The real hiding place: `Substrate.scn`

Every other scene is a normal game object, but `Substrate.scn` (75 KB) is a `Node3D` with **713 `MeshInstance3D` children** (`P100`…`P714`), each a 1-unit `BoxMesh` ("pixel") with a `Transform3D`. All boxes sit on the same plane (`z = -300`), at multiples of `1.4` units on x and on **7 distinct y rows** — i.e. a 7-pixel-tall dot-matrix text banner floating far away from the playable area (so you would never see it by driving around).

Parsing the Transform3D variants (type `0x11`, 12 floats; the last three are the origin) and plotting `(x/1.4, y/1.4)` as pixels reveals the text (`flag_pixels.png` in this folder):

```
RSTCON{REBORN-IN-ANOTHER-WORLD-BUT-IM-PLAYING-CTFS}
```

(Fitting for a "Truck-kun" challenge — the isekai trope of being hit by a truck.)

## 5. Solver (summary)

```python
import struct, glob
from PIL import Image

# 1) carve PCK out of the ELF
d = open("truck-kun.x86_64", "rb").read()
sz = struct.unpack("<Q", d[-12:-4])[0]
pck = d[len(d) - 12 - sz : len(d) - 12]
file_base, dir_off = struct.unpack("<QQ", pck[24:40])

# 2) walk the directory, find Substrate.scn
pos = dir_off
n = struct.unpack("<I", pck[pos:pos+4])[0]; pos += 4
for _ in range(n):
    l = struct.unpack("<I", pck[pos:pos+4])[0]; pos += 4
    name = pck[pos:pos+l].rstrip(b"\0").decode(); pos += l
    off, size = struct.unpack("<QQ", pck[pos:pos+16]); pos += 16 + 16 + 4
    if name.endswith("Substrate.scn"):
        scn = pck[file_base+off : file_base+off+size]

# 3) pull every Transform3D origin and plot it
pts, i = [], scn.find(b"variants")
while (i := scn.find(b"\x11\x00\x00\x00", i)) >= 0:
    v = struct.unpack("<12f", scn[i+4:i+52])
    pts.append((round(v[9]/1.4), round(v[10-0]/1.4)))   # x, y (see note)
    i += 1
```

> Note: in the transform the origin is `v[9], v[10], v[11]` = `(x, y, z)`; plot `x` horizontally and `y` vertically (flip y), `z` is constant. Wrapping the 305-pixel-wide banner into 3 rows and scaling up makes it readable.

## Flag

```
RSTCON{REBORN-IN-ANOTHER-WORLD-BUT-IM-PLAYING-CTFS}
```
