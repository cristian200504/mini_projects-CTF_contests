def find_tap():
    # Try Galois shift Left
    for tap in range(256):
        state = 0xd5
        for _ in range(10):
            msb = (state >> 7) & 1
            state = (state << 1) & 0xFF
            if msb: state ^= tap
        if state == 0xf2:
            state2 = 0xaa
            for _ in range(10):
                msb2 = (state2 >> 7) & 1
                state2 = (state2 << 1) & 0xFF
                if msb2: state2 ^= tap
            if state2 == 0xe5:
                print(f"Tap Left-Galois: {hex(tap)}")
                return tap
    return None
find_tap()
