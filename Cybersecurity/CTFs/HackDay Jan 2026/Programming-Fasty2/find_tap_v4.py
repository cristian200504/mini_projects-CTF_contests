def find_tap():
    # Try shifts to the LEFT
    for tap in range(256):
        state = 0xaa
        for _ in range(10):
            msb = (state >> 7) & 1
            state = (state << 1) & 0xFF
            if msb: state ^= tap
        if state == 0xe5:
            state2 = 0x86
            for _ in range(10):
                msb2 = (state2 >> 7) & 1
                state2 = (state2 << 1) & 0xFF
                if msb2: state2 ^= tap
            if state2 == 0x1e:
                print(f"Verified Left-Galois tap: {hex(tap)}")
                return tap
    return None

find_tap()
