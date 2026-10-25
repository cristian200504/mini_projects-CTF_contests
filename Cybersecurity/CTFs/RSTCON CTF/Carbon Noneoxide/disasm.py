#!/usr/bin/env python3
"""Disassemble LM3S6965 Cortex-M3 firmware (raw flat binary @ 0x0) and map strings."""
import sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

import os
FIRMWARE = r"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Carbon Noneoxide\extracted\firmware.bin.chal"

def load():
    with open(FIRMWARE, "rb") as f:
        return f.read()

def find_all(data, pat):
    offs = []
    i = data.find(pat)
    while i != -1:
        offs.append(i)
        i = data.find(pat, i+1)
    return offs

def strings_of_interest(data):
    names = [
        b"rstcon{", b"RsTcOnS", b"charlotte", b"Admin", b"Monitor",
        b"--- Debug Shell ---", b"Threshold:", b"Target:", b"VER:",
        b"[Sensor] Reading", b"[ALERT]", b"[Admin] Task", b"0123456789abcdef",
        b"Cannot do negative CO reading", b"LM3S6965", b"v1.23.0",
        b"Starting FreeRTOS", b"(null)", b"bcd%",
    ]
    res = {}
    for n in names:
        offs = find_all(data, n)
        res[n] = offs
    return res

def disasm_thumb(data, start, end):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    out = []
    addr = start
    while addr < end:
        code = data[addr:end]
        ins_list = list(md.disasm(code, addr))
        if not ins_list:
            # skip 2 bytes (data / misaligned); record as word
            out.append((addr, ".word", f"0x{le32(data,addr):08X}" if addr+4<=end else ""))
            addr += 2
            continue
        for ins in ins_list:
            out.append((ins.address, ins.mnemonic, ins.op_str))
            addr = ins.address + ins.size
    return out

def le32(data, off):
    return int.from_bytes(data[off:off+4], "little")

def main():
    data = load()
    print(f"firmware size = {len(data)} (0x{len(data):x})")
    print("\n=== vector table ===")
    for i in range(0, 0x48, 4):
        v = le32(data, i)
        print(f"  0x{i:02X}: 0x{v:08X}")

    print("\n=== string offsets ===")
    so = strings_of_interest(data)
    for name, offs in so.items():
        for o in offs:
            ctx = data[o:o+40].split(b'\x00')[0]
            print(f"  0x{o:04X}: {name!r}  -> {ctx!r}")

    print("\n=== literal-pool cross-refs (4-byte LE words pointing at a string offset) ===")
    # collect target offsets
    targets = {}
    for name, offs in so.items():
        for o in offs:
            targets[o] = name
    # scan every aligned 4-byte word
    for off in range(0, len(data)-3, 4):
        v = le32(data, off)
        if v in targets:
            print(f"  @0x{off:04X}: word 0x{v:08X} -> {targets[v]!r} (string @0x{v:04X})")

    print("\n=== full Thumb disassembly from 0x48 to end ===")
    out = disasm_thumb(data, 0x48, len(data))
    with open("disasm.txt", "w", encoding="utf-8") as f:
        for addr, m, op in out:
            f.write(f"0x{addr:04X}: {m:8s} {op}\n")
    print(f"  wrote {len(out)} lines to disasm.txt")

    # Cross-ref: resolve PC-relative LDR/ADR to absolute target and map to strings
    print("\n=== PC-relative loads resolving to known string offsets ===")
    targets = {}
    for name, offs in so.items():
        for o in offs:
            targets[o] = name
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    seen = set()
    for addr, m, op in out:
        if m not in ("ldr", "adr", "ldrb", "ldrh", "add"):
            continue
        # parse [pc, #imm] or pc + imm
        import re
        mm = re.search(r'\[pc,\s*#?(0x[0-9a-f]+|\d+)\]', op)
        imm = None
        if mm:
            v = mm.group(1)
            imm = int(v, 16) if v.startswith("0x") else int(v)
        else:
            mm2 = re.search(r'pc,\s*#?(0x[0-9a-f]+|\d+)', op)
            if mm2 and m == "adr":
                v = mm2.group(1)
                imm = int(v, 16) if v.startswith("0x") else int(v)
        if imm is None:
            continue
        # effective addr
        pc = (addr & ~3) + 4
        eff = pc + imm
        if m == "ldr" and eff+4 <= len(data):
            val = le32(data, eff)
            if val in targets:
                key = (addr, val)
                if key not in seen:
                    seen.add(key)
                    print(f"  0x{addr:04X}: {m} {op}  -> lit@0x{eff:04X}=0x{val:04X} -> {targets[val]!r}")
        elif m == "adr" and eff <= len(data):
            if eff in targets:
                key = (addr, eff)
                if key not in seen:
                    seen.add(key)
                    print(f"  0x{addr:04X}: adr {op} -> 0x{eff:04X} -> {targets[eff]!r}")

if __name__ == "__main__":
    main()
