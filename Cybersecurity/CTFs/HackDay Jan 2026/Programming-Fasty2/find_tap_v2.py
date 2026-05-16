def find_tap():
    # Seed 0xaa = 170
    # Steps 10, Result 0xe5 = 229
    for tap in range(256):
        state = 0xaa
        for _ in range(10):
            bit = 0
            temp = state & tap
            while temp:
                bit ^= (temp & 1)
                temp >>= 1
            state = ((state >> 1) | (bit << 7)) & 0xFF
        if state == 0xe5:
            # Check if this also works for 0x86 -> 0x1e
            state2 = 0x86
            for _ in range(10):
                bit2 = 0
                temp2 = state2 & tap
                while temp2:
                    bit2 ^= (temp2 & 1)
                    temp2 >>= 1
                state2 = ((state2 >> 1) | (bit2 << 7)) & 0xFF
            if state2 == 0x1e:
                print(f"Verified tap: {hex(tap)}")
                return tap
    return None

find_tap()
