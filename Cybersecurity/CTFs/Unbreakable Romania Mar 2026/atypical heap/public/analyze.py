import sys
import re

def analyze_elf(path):
    with open(path, "rb") as f:
        elf = f.read()

    print(f"--- {path} ---")
    if elf[:4] != b"\x7fELF":
        print("Not an ELF")
        return

    ei_class = elf[4]
    print(f"Class: {'64-bit' if ei_class == 2 else '32-bit'}")

    e_type = int.from_bytes(elf[16:18], "little")
    types = {1: "REL", 2: "EXEC", 3: "DYN", 4: "CORE"}
    print(f"Type: {types.get(e_type, str(e_type))}")

    if b"musl" in elf:
        print("musl libc detected!")
    if b"glibc" in elf or b"GNU C Library" in elf:
        print("glibc detected!")
    
    strings = re.findall(b"[ -~]{4,}", elf)
    libc_strings = [s.decode() for s in strings if b"libc" in s.lower()]
    print("Some libc strings:")
    for s in libc_strings[:10]:
        print("-", s)

analyze_elf(sys.argv[1])
