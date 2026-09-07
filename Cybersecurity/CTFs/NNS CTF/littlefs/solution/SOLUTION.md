# NNS CTF — `littlefs`

**Category:** Miscellaneous / hardware · **Difficulty:** beginner · **77 pts · 119 solves**

## Flag

```
NNS{l0g1c_an4ly53rs_c4n_pr0vid3_ins1ght_int0_th3_w0rk1ng5_0f_4n_3mb3dded_sy5t3m}
```

> *"logic analysers can provide insight into the workings of an embedded system"*
> — leetspeak substitutions: `o→0  i→1  a→4  e→3  s→5`

---

## 1. What we're given

* `misc_littlefs.tar.gz` containing
  * `littlefs.logicdata` — a **Saleae Logic 1.x** capture (86 KB)
  * `zephyrapp/` — the firmware source (Zephyr RTOS)
* `description.txt`:

  > I found this device with a NOR flash to that just prints out the flag.
  > Unfortunately, I could not read the terminal output. However, I was able to
  > connect my logic analyser … channel 0 was connected to **MOSI**, channel 1
  > to **CS**, channel 2 to **SCK** and channel 3 to **MISO**.

### The firmware (`zephyrapp/src/main.c`)

An nRF5340-DK talks to an external **Macronix mx25r64** SPI-NOR flash on `spi4`
(overlay `nrf5340dk_nrf5340_spi.overlay`). A `littlefs` filesystem is placed in
`lfs1_partition` (flash offset `0x0`, size `0x10000`) and `automount`ed. `main()`
then simply does:

```c
fs_open(&file, "/lfs1/flag.txt", FS_O_READ);
fs_read(&file, buf, sizeof(buf));          /* buf[100] */
LOG_INF("Flag is: %s", buf);
```

So the flag never leaves as UART text — but every byte of `flag.txt` is clocked
across the SPI bus when littlefs reads it. Recover it from the capture.

### Intended solution

Open `littlefs.logicdata` in **Saleae Logic 2** (it imports the legacy format),
add the **SPI analyser**:

| setting | value |
|---|---|
| Clock (SCK) | channel 2 |
| Enable (CS) | channel 1, *active low* |
| MOSI | channel 0 |
| MISO | channel 3 |
| CPOL / CPHA | 0 / 0 (clock idles low, sample on leading edge) |
| Bit order | MSB first, 8 bits |

…and read the flag straight out of the decoded data column. `solve.py` in this
folder does the same thing without the GUI (useful because the `.logicdata`
container is undocumented).

---

## 2. Reverse-engineering the `.logicdata` container

No public parser exists for Logic **1.x** `.logicdata` (Logic **2** uses `.sal`).
The relevant structure, worked out from this file:

### Header
`7F` magic, length-prefixed strings (`"Data save2"`, `"Channel 0" … "Channel 3"`),
a sample rate stored as `04 <u32 LE>` = **50 000 000** (50 MS/s), and a recurring
8-byte constant `D4 1D B7 A6 A0 CF BE 2F` per channel.

### Per channel (×4, in channel order 0..3)

**a) compact edge stream ("block1")** — after a `<01|02> <varint> 00` marker
repeated three times, a run of **one byte per signal edge**:

```
delta = byte & 0x7F      # samples elapsed since the previous edge
level = byte >> 7        # line level *after* this edge
```

This stream contains only the **active** edges of each SPI burst; the long idle
gaps *between* transactions are **not** encoded here.

**b) structured section** — a sparse timing index:
`FF*8`, then `u64 == 3`, then 32-byte records `(ts:u64, f1:u64, f2:u64, f3:u64)`.
For `f3 == 1` records:

```
f1 = cumulative edge count
ts = absolute sample time of edge #f1
```

There is roughly one checkpoint per ~10 edges, **plus** extra checkpoints that
bracket every idle gap.

**c) channel separator** — `01 16 01 0X 00 04 00 00 2F 04 …`

### Rebuilding a waveform

For a channel: walk `block1` accumulating `delta`s, and tie the running edge
index to absolute time with the `f3 == 1` checkpoints (linear interpolation
between them). Because `block1` has no gaps *and* checkpoints bracket every gap,
the result is sample-accurate. This is `timeline()` in `solve.py`.

Sanity check: within a "no-gap" checkpoint interval, the sum of `block1` deltas
equals `ts[next] − ts[prev]` **exactly**.

### Channel identification

By edge count (no need to trust the header order):

| section | edges | role |
|---|---|---|
| struct 2 | **16 077** | **SCK** — 2 edges/bit, ~8 038 clocks |
| struct 1 | **134**   | **CS** — 67 chip-select pulses |
| struct 0 | **1 423** | data line carrying the flash read-out (**the flag**) |
| struct 3 | **194**   | the other data line — near-idle command traffic |

---

## 3. Decoding the SPI

1. Reconstruct **SCK**; split its rising edges into **67 bursts** wherever the
   gap between edges exceeds ~30 samples. Bursts are byte-aligned
   (8 / 24 / 32 / 128 / 512 clocks).
2. Reconstruct the **data line** (struct 0). Snap each of its edges onto the
   nearest SCK edge index (the data line only ever changes on a clock edge).
3. For each SCK rising edge, sample the data line, MSB first, 8 bits per byte.

Two gotchas that cost me a first, wrong submission:

* **The data line is inverted on the wire — `XOR 0xFF` every byte.**
  Confirmation: littlefs's `"littlefs"` superblock magic appears in the metadata
  reads as `93 96 8B 8B 93 9A 99 8C`, i.e. `~"littlefs"`.

* **Byte 0 of every burst is corrupted by a clock-gap resync artefact.**
  The reconstruction emits one *phantom* rising edge at the very start of each
  burst, and the burst's first data edge is a *resync marker* whose stored
  `level` bit is the **pre-gap** level, not the real one. Uncorrected, this
  garbles the first byte of every read chunk.
  Fix: drop the phantom clock (first two rising edges < 5 samples apart) and
  flip the marker's level so the burst alternates correctly from the idle-high
  state. `solve.py` runs one straight pass for the body and one corrected pass
  purely to recover byte 0 of each chunk.

---

## 4. Reading the flag

`littlefs` has `cache-size = 64`, so `flag.txt` is read as a **64-byte** chunk
followed by a **16-byte** chunk — an **80-byte** file:

| burst | clocks | decoded (after `XOR 0xFF`) |
|---|---|---|
| 64 | 512 | `NNS{l0g1c_an4ly53rs_c4n_pr0vid3_ins1ght_int0_th3_w0rk1ng5_0f_4n_` |
| 65 | 32  | (next `03 <addr>` read command) |
| 66 | 512 | `3mb3dded_sy5t3m}` + `0xFF` padding (file ended) |

```
NNS{l0g1c_an4ly53rs_c4n_pr0vid3_ins1ght_int0_th3_w0rk1ng5_0f_4n_3mb3dded_sy5t3m}
```

### First-attempt mistake

I initially read the artefact-corrupted first byte of chunk 2 as `e`
(`emb3dded`) by filling it from context. It is actually **`3`** — the flag
leetspeaks *every* `e`. Recovering it properly (drop the phantom clock, flip the
resync marker) yields `3` directly from the capture.

---

## 5. Files in this folder

| file | purpose |
|---|---|
| `solve.py` | standalone solver: `python solve.py littlefs.logicdata` |
| `littlefs.logicdata` | the challenge capture |
| `main.c` | firmware source (from `zephyrapp/src/`) |
| `nrf5340dk_nrf5340_spi.overlay`, `prj.conf` | flash / littlefs config referenced above |
| `description.txt` | original challenge text |
