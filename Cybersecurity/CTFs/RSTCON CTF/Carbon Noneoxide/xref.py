#!/usr/bin/env python3
"""Comprehensive cross-reference finder for the LM3S6965 firmware.
Finds (a) literal-pool words pointing into rodata/string range,
and (b) PC-relative ADR/add/sub instructions that resolve into that range.
Also dumps every string in the rodata region."""
import re
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

FIRMWARE = r"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Carbon Noneoxide\extracted\firmware.bin.chal"
RODATA_LO, RODATA_HI = 0x1F00, 0x2344

def le32(data, off):
    return int.from_bytes(data[off:off+4], "little")

def cstr(data, off):
    end = off
    while end < len(data) and 0x20 <= data[end] <= 0x7e:
        end += 1
    # include trailing newline/control if right next
    return data[off:end].decode("ascii", "replace")

def main():
    data = open(FIRMWARE, "rb").read()
    n = len(data)

    # (a) literal pool words
    print("=== all 4-byte words in range [0x1F00,0x2344] (literal pools -> strings) ===")
    refs = {}  # target -> list of lit offsets
    for off in range(0, n-3, 2):
        v = le32(data, off)
        if RODATA_LO <= v < RODATA_HI:
            refs.setdefault(v, []).append(off)
    for v in sorted(refs):
        s = cstr(data, v)
        locs = ", ".join(f"0x{o:04X}" for o in refs[v])
        print(f"  0x{v:04X} [{s!r}]  <- lit at {locs}")

    # (b) PC-relative ADR / add/sub pc
    print("\n=== PC-relative ADR/add/sub resolving into rodata range ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    addr = 0x48
    found = []
    while addr < n:
        code = data[addr:n]
        il = list(md.disasm(code, addr))
        if not il:
            addr += 2
            continue
        for ins in il:
            a = ins.address
            m = ins.mnemonic
            op = ins.op_str
            # ADR Rd, #imm  OR  add Rd, pc, #imm  OR  sub Rd, pc, #imm
            if m in ("adr", "add", "sub") and ("pc" in op.split(",")[1] if op.count(",")>=2 else False):
                pass
            if m == "adr":
                mm = re.search(r"#(0x[0-9a-fA-F]+|\-?\d+)", op)
                if mm:
                    v = mm.group(1)
                    imm = int(v,16) if v.startswith("0x") else int(v)
                    tgt = (a & ~3) + 4 + imm
                    if RODATA_LO <= tgt < RODATA_HI:
                        found.append((a, m, op, tgt, cstr(data, tgt)))
            addr = ins.address + ins.size
            break  # re-disasm from next addr to keep aligned sweep
    for a,m,op,t,s in found:
        print(f"  0x{a:04X}: {m} {op} -> 0x{t:04X} [{s!r}]")

    # (c) every LDR Rt,[pc,#imm] resolved literal -> if literal value in rodata
    print("\n=== LDR Rt,[pc,#imm] whose literal points into rodata ===")
    addr = 0x48
    found2 = []
    while addr < n:
        code = data[addr:n]
        il = list(md.disasm(code, addr))
        if not il:
            addr += 2
            continue
        for ins in il:
            a = ins.address; m = ins.mnemonic; op = ins.op_str
            if m == "ldr":
                mm = re.search(r"\[pc,\s*#?(0x[0-9a-fA-F]+|\d+)\]", op)
                if mm:
                    v = mm.group(1)
                    imm = int(v,16) if v.startswith("0x") else int(v)
                    lit = ((a & ~3) + 4) + imm
                    if 0 <= lit < n-3:
                        val = le32(data, lit)
                        if RODATA_LO <= val < RODATA_HI:
                            found2.append((a, op, lit, val, cstr(data, val)))
            addr = ins.address + ins.size
            break
    for a,op,lit,val,s in found2:
        print(f"  0x{a:04X}: ldr {op}  lit@0x{lit:04X}=0x{val:04X} -> 0x{val:04X} [{s!r}]")

    # (d) dump every null-terminated printable string in rodata with offset
    print("\n=== all strings in rodata ===")
    i = RODATA_LO
    while i < RODATA_HI:
        if 0x20 <= data[i] <= 0x7e:
            s = cstr(data, i)
            if len(s) >= 2:
                print(f"  0x{i:04X}: {s!r}")
            i += len(s)
        else:
            i += 1

if __name__ == "__main__":
    main()
