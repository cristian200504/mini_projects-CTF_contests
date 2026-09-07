# keyboard — Solve Writeup

**Flag:** `NNS{typ1ng!_4way@_th3/_0n_USB?_"k3ybofla[MY]_gg)4r$"}`  
*(Alternative without trailing quote if delete handled differently: `NNS{typ1ng!_4way@_th3/_0n_USB?_"k3ybofla[MY]_gg)4r$}`)*

---

## 1. Challenge Overview

- **Category:** Hardware / Forensics / USB
- **Description:** `"I thought I was writing confidentially on my USB keyboard, but it seems like someone has been analysing my bus."`
- **Provided file:** `misc_keyboard.tar.gz` containing `misc_keyboard/keyboard.logicdata` (18.3 MB).

The file is a Saleae Logic logic analyzer session file capturing raw digital and analog signals of a physical bus.

---

## 2. Saleae Logic Extraction

`keyboard.logicdata` is an internal binary serialization format created by the Saleae Logic software (version 1.2.x). To parse the proprietary data without reverse engineering the complex serialization format from scratch:

1. Installed the standalone 64-bit Linux release of Saleae Logic (v1.2.18) in WSL (Kali Linux).
2. Ran Logic headlessly using `xvfb-run -a Logic -disablepopups` with its built-in socket automation server on port 10429 enabled.
3. Connected to the socket interface via Python (`saleae` API) and loaded `/tmp/keyboard.logicdata`.
4. Queried the active channels:
   - **Digital channels:** `[0, 1, 2, 3, 4]`
   - **Analog channels:** `[5, 6]`
5. Discovered that Channel 1 and Channel 2 contained digital activity representing a differential pair.
6. Exported the digital transitions of Channels 1 and 2 to CSV using `EXPORT_DATA2`.

---

## 3. Physical Layer & Protocol Analysis

Inspecting the exported CSV data revealed:
- **Idle state:** Channel 1 = 1, Channel 2 = 0.
- **Bit duration:** Approximately $667\text{ ns}$ ($1.5\text{ Mbps}$).
- **Periodic pulses:** SE0 ($0, 0$) lasting $\approx 1.36\ \mu\text{s}$ occurring every $1.0\text{ ms}$ (Keep-Alive End-of-Packet).

This uniquely identifies **USB Low Speed (1.5 Mbps)**:
- **D-** = Channel 1 (pulled high by device pull-up resistor in Low-Speed idle state).
- **D+** = Channel 2.
- **States:**
  - **J state (Idle / Differential 0 for Low Speed):** D- = 1, D+ = 0
  - **K state (Differential 1 for Low Speed):** D- = 0, D+ = 1
  - **SE0 (Single-Ended Zero):** D- = 0, D+ = 0 (used for EOP / reset)
  - **SE1 (Illegal):** D- = 1, D+ = 1

### Signal Glitches and Filtering
Due to slight rise/fall time mismatch between D+ and D-:
- **Crossover glitches:** When transitioning between J and K, both lines momentarily drop low ($0, 0$), creating $40\text{ ns}$ to $160\text{ ns}$ SE0 glitches.
- Filtering rule: Any SE0 shorter than $400\text{ ns}$ is treated as a crossover skew and ignored. A true USB EOP must persist for at least $\approx 1.0\ \mu\text{s}$ (1.5 to 2 bit times).

---

## 4. USB Packet & HID Decoding

Each packet is framed between SOP (transition from J to K) and EOP (SE0 $\ge 1.0\ \mu\text{s}$):
1. **Clock Recovery & NRZI:**
   - Every transition represents a bit `0`.
   - Intervals without a transition represent consecutive bit `1`s ($N = \text{round}(\Delta t / T_{bit})$).
2. **Bit Unstuffing:**
   - After six consecutive `1`s, the transmitter inserts a stuffed `0` bit which is discarded.
3. **SYNC Verification:**
   - First byte must be `0x80` (`00000001` in transmission order).
4. **PID Validation:**
   - Low nibble must equal bitwise NOT of high nibble.
5. **Decoded Packet Distribution:**
   - `IN` tokens: 18,960
   - `NAK` handshakes: 18,317
   - `DATA0` / `DATA1`: 725
   - `ACK` handshakes: 725

The 725 DATA packets contained standard 8-byte USB HID keyboard reports:
- `Byte 0`: Modifier bitmap (Ctrl, Shift, Alt, GUI)
- `Byte 1`: Reserved (`0x00`)
- `Byte 2..7`: Up to 6 active HID keycodes.

---

## 5. Keyboard Layout & Terminal Simulation

The challenge author typed Norwegian song lyrics ("Tore Tang" by Mods) around the flag:
```
tore tang
ein gammal mann
...
han som leve av gammalt br;d og vann
```

### Layout Identification: Norwegian / Nordic
Analyzing the modifiers used for brackets and symbols confirmed a **Norwegian keyboard layout**:
- `AltGr + 7` (key `0x24`) $\rightarrow$ `{`
- `AltGr + 0` (key `0x27`) $\rightarrow$ `}`
- `AltGr + 8` (key `0x25`) $\rightarrow$ `[`
- `AltGr + 9` (key `0x26`) $\rightarrow$ `]`
- `AltGr + 2` (key `0x1F`) $\rightarrow$ `@`
- `AltGr + 4` (key `0x21`) $\rightarrow$ `$`
- `Shift + 7` (key `0x24`) $\rightarrow$ `/`
- `Shift + +` (key `0x2D`) $\rightarrow$ `?`
- `Shift + -` (key `0x38`) $\rightarrow$ `_`
- `Shift + 1` (key `0x1E`) $\rightarrow$ `!`
- `Shift + 2` (key `0x1F`) $\rightarrow$ `"`
- `Shift + 9` (key `0x26`) $\rightarrow$ `)`

### Reconstructing Buffer Edits
The typist used interactive cursor navigation (Home, End, Left, Right, Delete, Backspace, Insert):
1. Typed `NNS{USB?_"`
2. Pressed `Home`, then moved right 4 times (right after `{`).
3. Typed `typing!_`, then `0n_`.
4. Navigated left to fix `typing` $\rightarrow$ backspaced `i` and inserted `1` (`typ1ng!`).
5. Navigated back and inserted `4way@_th3/_` before `0n_USB?_"`:
   `NNS{typ1ng!_4way@_th3/_0n_USB?_"k3yboard"}`
6. Navigated into `"k3yboard"`:
   - After `k3ybo`, inserted `flagg)_`
   - Moved before `gg`, inserted `[MY]_`
   - Backspaced `_`, inserted `4`, deleted `a`
   - Inserted `$`, deleted `d`
   Result inside quotes: `"k3ybofla[MY]_gg)4r$"`
7. Navigated to the end and pressed Enter.

Final assembled flag:
```
NNS{typ1ng!_4way@_th3/_0n_USB?_"k3ybofla[MY]_gg)4r$"}
```
