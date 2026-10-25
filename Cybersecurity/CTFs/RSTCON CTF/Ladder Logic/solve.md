# Ladder Logic — CTF Challenge Writeup

## Challenge Information
- **Name:** Ladder Logic
- **Points:** 10
- **Author:** f8al
- **Description:** `We pulled the program off a safety interlock controller guarding an access cabinet. It will not release the solenoid until the right combination is keyed in. Files: interlock.st`
- **Flag:** `rstcon{rung_7_holds_the_key}` (Raw payload: `rung_7_holds_the_key`)

---

## 1. Initial Reconnaissance

We are provided `interlock.st`, an IEC 61131-3 **Structured Text (ST)** program dumped from an OpenPLC runtime controlling a safety interlock solenoid (`%QX0.0`).

---

## 2. Code Analysis

Inspecting `interlock.st`:

1. **Four-Step Keypad Combination (`%IW0..%IW3`):**
   - **Rung 1 (`state = 0`):** Checks `step1 = 7` $\rightarrow$ advances to `state := 1`
   - **Rung 2 (`state = 1`):** Checks `step2 = 1965` $\rightarrow$ advances to `state := 2`
   - **Rung 3 (`state = 2`):** Checks `step3 = 42` $\rightarrow$ advances to `state := 3`
   - **Rung 4 (`state = 3`):** Checks `step4 = 16#CAFE` (`51966`) $\rightarrow$ jumps to `state := 7`
   - **Rung 7 (`state = 7`):** Sets `unlocked := TRUE`

2. **Output Stage (`%QW0..%QW19`):**
   Once `unlocked` is `TRUE`, the controller descrambles the 20-byte `enc` array by XORing each element with `KEY = 16#5A` (`0x5A`) and writes the resulting characters into holding registers `id_out[0..19]`:

```iecst
KEY : BYTE := 16#5A;
enc : ARRAY [0..19] OF BYTE := [
    16#28, 16#2F, 16#34, 16#3D, 16#05, 16#6D, 16#05, 16#32,
    16#35, 16#36, 16#3E, 16#29, 16#05, 16#2E, 16#32, 16#3F,
    16#05, 16#31, 16#3F, 16#23 ];
```

---

## 3. Solver Script (`solve.py`)

```python
enc = [
    0x28, 0x2F, 0x34, 0x3D, 0x05, 0x6D, 0x05, 0x32,
    0x35, 0x36, 0x3E, 0x29, 0x05, 0x2E, 0x32, 0x3F,
    0x05, 0x31, 0x3F, 0x23,
]
key = 0x5A

secret = "".join(chr(b ^ key) for b in enc)
print(f"[+] Keypad Combination: step1=7, step2=1965, step3=42, step4=0xCAFE")
print(f"[+] Decoded Cabinet ID: {secret}")
print(f"[+] Flag: rstcon{{{secret}}}")
```

### Output

```text
[+] Keypad Combination: step1=7, step2=1965, step3=42, step4=0xCAFE
[+] Decoded Cabinet ID: rung_7_holds_the_key
[+] Flag: rstcon{rung_7_holds_the_key}
```
