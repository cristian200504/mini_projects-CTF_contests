def solve():
    lines = open("chiral.mol").read().split("\n")
    bond_lines = lines[375:375+370]
    
    bonds = []
    for bl in bond_lines:
        if not bl.strip(): continue
        # V2000 bond line format: 111 222 t s
        # format is fixed width usually, but we can just split
        if len(bl) >= 12:
            b1 = int(bl[0:3])
            b2 = int(bl[3:6])
            typ = int(bl[6:9])
            stereo = int(bl[9:12])
            bonds.append((b1, b2, stereo))
    
    # We want to find the sequence of stereo tags (1 or 6) from F to Br.
    # The stereo bonds are defined on specific atoms.
    # We can just collect all bonds with stereo > 0 in the order they appear?
    # Or in the order of the backbone?
    # Let's see the order of stereo bonds in the file:
    stereo_bonds = [b for b in bonds if b[2] > 0]
    print(stereo_bonds)
    
    # Let's extract the stereo value (1 or 6)
    vals = [b[2] for b in stereo_bonds]
    
    print("Path length:", len(path))
    # print all atoms on the path
    # print([a.GetSymbol() for a in path_atoms])
    b2 = "0101000100010000000100000101000100000001000100010000000001"

    def find_nns(bitstr):
        for bit_size in [7, 8]:
            for endian in ['big', 'little']:
                for offset in range(8):
                    res = ""
                    b = bitstr[offset:]
                    for i in range(0, len(b), bit_size):
                        byte = b[i:i+bit_size]
                        if len(byte) == bit_size:
                            if endian == 'little':
                                byte = byte[::-1]
                            res += chr(int(byte, 2))
                    if len(res) > 3:
                        open("out.txt", "a", encoding="utf-8").write(f"size={bit_size}, end={endian}, off={offset}: {repr(res)}\n")

    print("Trying UP/DOWN:")
    find_nns(b1)
    find_nns(b2)
    find_nns(b1[::-1])
    find_nns(b2[::-1])


solve()
