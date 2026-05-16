def find_tap():
    # Try Galois shift Right
    for tap in range(256):
        state = 0xd5
        for _ in range(10):
            lsb = state & 1
            state >>= 1
            if lsb: state ^= tap
        if state == 0xf2:
            state2 = 0xaa
            for _ in range(10):
                lsb2 = state2 & 1
                state2 >>= 1
                if lsb2: state2 ^= tap
            if state2 == 0xe5:
                print(f"Tap Galois: {hex(tap)}")
                return tap
    return None
find_tap()
