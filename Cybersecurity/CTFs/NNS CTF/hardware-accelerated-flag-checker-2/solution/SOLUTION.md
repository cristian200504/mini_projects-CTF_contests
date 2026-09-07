# NNS CTF — `hardware-accelerated-flag-checker-2`

**Category:** Miscellaneous / hardware

## Flag

```
NNS{fl4g_ver1f1ed_1n_SKY130_IC}
```

---

## 1. The challenge

> The previous hardware accelerated flag checker was not quite ready for
> production. I made a new one using the **SKY130A PDK**, ready for tapeout.

Given two files — the same design in two formats:

| file | what it is |
|---|---|
| `flag_checker.gds` | GDSII: the final mask layout, hierarchical (top cell `flag_checker` + `SREF`s to `sky130_fd_sc_hd__*` standard cells, whose geometry is also embedded) |
| `flag_checker.mag` | the same layout as a Magic database (`<< metalN >>` / `<< viaN >>` sections of axis-aligned `rect`s, `use <cell> <inst>` + `transform`, and a `<< labels >>` section) |

There is **no RTL and no netlist**. The design was placed & routed from the
open `sky130_fd_sc_hd` (high-density) cell library — the `_NNN_` instance names,
`inputN` / `outputN` / `fanoutN` buffers and `clkbuf_*` tree are the OpenLane
signature.

The I/O, from the `.mag` `<< labels >>` block:

| port | layer | dir | meaning |
|---|---|---|---|
| `character[6:0]` | met2 | in  | one **7-bit character** presented per clock |
| `clk`            | met2 | in  | clock |
| `reset_n`        | met2 | in  | **active-low** reset |
| `found_flag`     | met2 | out | asserted once the correct string has been streamed in |
| `VPWR` / `VGND`  | met4/met5 | power | |

So this is a **streaming flag checker**: feed one ASCII byte per clock and watch
`found_flag`. The design has **5 D flip-flops** (`sky130_fd_sc_hd__dfxtp_2`) →
≤ 32 states of hidden state → recover the string it accepts.

Two options: model the analog/serial protocol at the bus (there is none — it's a
plain synchronous digital block), or **reverse the logic**. We reverse the logic.

---

## 2. Rebuilding the gate-level netlist from the layout

This is the whole difficulty of the challenge. A standard-cell layout has no
explicit connectivity; you must do LVS-style **extraction** — recover which cell
pins are electrically the same net from the metal/via geometry. Magic's
`extract` would do it in one command, but the point here is to do it from the
GDS directly.

`solution/extract_netlist.py` (only dependency: `pip install gdstk`).

### 2.1 SKY130 GDS layers used

| purpose | layer/datatype |
|---|---|
| li1 (local interconnect) | `67/20`  ·  li1 pin label `67/5` |
| mcon (li1 ↔ met1)        | `67/44` |
| met1 | `68/20` · via1 (met1↔met2) `68/44` |
| met2 | `69/20` · via2 `69/44` · met2 port label `69/5` |
| met3 | `70/20` · via3 `70/44` |
| met4 | `71/20` · via4 `71/44` |
| met5 | `72/20` |

Cell instance names live in a per-`SREF` `S_GDS_PROPERTY` (attribute **61**).

### 2.2 Algorithm

1. **Flatten** the top cell (`top.copy().flatten()`) so every standard-cell
   internal shape and every route are in one absolute coordinate space.
2. For each conductor layer li1…met5, **boolean-OR all polygons together**
   (`gdstk.boolean(polys, [], "or")`) → a list of disjoint *merged regions*.
   Each merged region is a candidate "piece of a net on that layer".
3. **Bridge layers through vias**: for every via polygon on `mcon/via1…via4`,
   if it geometrically intersects a merged region on the layer **below** and one
   on the layer **above**, `union()` those two regions (union-find over all
   merged regions). Grow the via a hair (~7 nm) first so an edge-only landing
   still counts as an intersection; also union two vias that overlap and share a
   metal layer (stacked via arrays).
4. **Name nets**: for each top-level `met2` port label, point-in-polygon it into
   a merged met2 region and tag that region's union-find root with the port
   name (`character[0]`, …, `found_flag`, `clk`, `reset_n`).
5. **Resolve every cell pin**: take the cell's `li1` pin label point(s), apply
   the instance transform, and find which merged li1 region contains the point
   → that region's net.  Some pins are labelled at several li1 spots inside the
   cell; try them all and pick the candidate the rest of the netlist actually
   uses (breaks ties on stray internal li1 fragments).

### 2.3 Pitfalls that make a naïve version wrong

* **Bounding-box overlap shorts everything.** The sky130 cell li1 pin shapes
  are T/cross/comb polygons; their *bounding box* overlaps the VPWR/VGND li1
  rails, so a plain bbox-vs-bbox union-find fuses every gate output to power and
  collapses the design to one net. → work with the real polygon geometry
  (booleans / point-in-polygon), not bboxes.
* **Non-rectangular routing.** An L-shaped or staircase met2 wire's bbox
  contains other nets that pass through its concave notch. Same fix.
  *(The `.mag` file sidesteps this — it stores everything as axis-aligned
  `rect`s — so an alternative extractor can parse the `.mag` routing directly
  and only needs the GDS for cell pin geometry.)*
* **The full metal stack matters.** ~6 FSM nets dog-leg **up to met4 via
  via3** (a routing jog around congestion). If you only model li1…met3 those
  nets lose their driver. Model `via3`/`via4`/`met4`/`met5` too.
* **Stacked vias.** A `mcon` rect and a `via1` rect are often placed exactly
  coincident; they must be unioned (they share met1) or li1 never reaches met2.
* **Multi-location pin labels.** e.g. `clkdlybuf4s25__X` carries six li1 labels
  at different y; the router contacted only one. Use all of them.

Final quality: **163 nets, 154 logic instances, every net has exactly one
driver and ≥ 1 load** (`netlist.txt`). Zero shorts, zero floating nets.

---

## 3. Modelling and solving the FSM

`solution/solve_fsm.py`.

### 3.1 Cell semantics

A boolean function for every `sky130_fd_sc_hd` combinational cell in the design.
Naming rules used:

* output pin is `X` (buffering/AOI-style) or `Y` (inverting: `nand`, `nor`,
  `inv`, `*i`);
* a `b` / `bb` in the name means one / two inputs are inverted **inside** the
  cell, and those pins are suffixed `_N` (`and2b`: `X = ~A_N & B`;
  `or4b`: `X = A|B|C|~D_N`; `o2bb2a`: `X = (~A1_N|~A2_N) & (B1|B2)`; …);
* `aXYZ...` = AND-terms OR-ed; `oXYZ...` = OR-terms AND-ed
  (`a21oi`: `Y = ~((A1&A2)|B1)`; `o41a`: `X = (A1|A2|A3|A4)&B1`; …);
* every `clkbuf_*`, `clkdlybuf4s25`, `clkinv?` → **plain non-inverting buffer**
  `X = A` (these are only for timing: the `inputN` / `outputN` / `fanoutN`
  wrappers and the clock tree).

`dfxtp_2` is a bare rising-edge DFF (**no** reset pin) ⇒ `reset_n` must be
consumed **synchronously** inside the next-state combinational logic.

### 3.2 Simulation

Topologically sort the combinational cone and evaluate one cycle:

```
(next_state, found_flag) = step(state, character[6:0], reset_n)
```

* `found_flag` is read from the **current** state (before the edge).
* Reset state: drive `reset_n = 0` for a few cycles → **`00000`**.
* From the reset state, **BFS** over all printable bytes `0x20‥0x7e`, edge by
  edge, until `found_flag` is first observed.

### 3.3 What the circuit is

The extracted machine is a **strict 31-step linear counter**:

* the 5 flip-flops just hold a binary count `0 → 1 → 2 → … → 31`;
* from every state **exactly one** character advances it (`state → state+1`);
* **any** other character throws it back to state 0 (or to state 1 if that
  wrong character happens to be `N` — the checker immediately restarts the
  match); no character ever "stalls" the count;
* `found_flag` is purely `state == 31`, independent of `character` and
  `reset_n`.

So the flag is simply the unique advancing character of each state, in order:

| state | ch | state | ch | state | ch | state | ch |
|--:|:--|--:|:--|--:|:--|--:|:--|
| 0 | `N` | 8  | `_` | 16 | `d` | 24 | `1` |
| 1 | `N` | 9  | `v` | 17 | `_` | 25 | `3` |
| 2 | `S` | 10 | `e` | 18 | `1` | 26 | `0` |
| 3 | `{` | 11 | `r` | 19 | `n` | 27 | `_` |
| 4 | `f` | 12 | `1` | 20 | `_` | 28 | `I` |
| 5 | `l` | 13 | `f` | 21 | `S` | 29 | `C` |
| 6 | `4` | 14 | `1` | 22 | `K` | 30 | `}` |
| 7 | `g` | 15 | `e` | 23 | `Y` |    |     |

```
NNS{fl4g_ver1f1ed_1n_SKY130_IC}          (31 characters)
```

*"flag verified in SKY130 IC"* — consistent with the "ready for tapeout"
framing. Feeding those 31 bytes with `reset_n = 1` walks the counter to 31; on
the next clock `found_flag` is high (the byte on that 32nd clock is a
don't-care — the BFS just needs one extra `step` to *observe* the accept).

### 3.4 Verification

* Forward-replay the 31-byte string from the reset state → state reaches 31,
  `found_flag` asserts on the following cycle. ✓
* At every one of the 31 states, exactly one advancing character; ~93 of the 94
  other printable characters reset to state 0, and `N` resets to state 1.
  ⇒ the accepted string is **unique**. ✓
* `reset_n = 0` from any state forces state 0. ✓

---

## 4. Reproduce

```bash
pip install gdstk
python extract_netlist.py flag_checker.gds > netlist.txt
python solve_fsm.py  netlist.txt
# stderr: reset state (0,0,0,0,0)
# stdout: FLAG: NNS{fl4g_ver1f1ed_1n_SKY130_IC}
```

## 5. Files in this folder

| file | purpose |
|---|---|
| `extract_netlist.py` | GDS → gate-level netlist (geometric extraction with `gdstk`) |
| `solve_fsm.py`       | netlist → cycle-accurate FSM model → BFS for the accepted string |
| `netlist.txt`        | the extracted netlist, one line per cell: `inst  celltype  {pin: net}` |
| `flag_checker.gds` / `flag_checker.mag` | the challenge layout |
| `description.txt`    | original challenge text |
