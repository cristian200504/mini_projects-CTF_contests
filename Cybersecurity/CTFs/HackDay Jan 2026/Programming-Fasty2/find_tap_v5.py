def find_tap():
    # Seed 0xd5 = 213
    # Steps 10, Result 0xf2 = 242
    # Seed 0xaa = 170
    # Steps 10, Result 0xe5 = 229
    # Seed 0x86 = 134
    # Steps 10, Result 0x1e = 30
    for tap in range(256):
        state = 0xd5
        for _ in range(10):
            bit = 0
            temp = state & tap
            while temp:
                bit ^= (temp & 1)
                temp >>= 1
            state = ((state >> 1) | (bit << 7)) & 0xFF
        if state == 242:
            state2 = 170
            for _ in range(10):
                bit2 = 0
                temp2 = state2 & tap
                while temp2:
                    bit2 ^= (temp2 & 1)
                    temp2 >>= 1
                state2 = ((state2 >> 1) | (bit2 << 7)) & 0xFF
            if state2 == 229:
                print(f"Tap: {hex(tap)}")
                return tap
    return None
find_tap()
