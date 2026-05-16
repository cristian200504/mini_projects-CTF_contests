def find_tap():
    # Try Galois LFSR instead of Fibonacci
    # Seed 0xaa (170) -> 0xe5 (229) after 10
    # Seed 0x86 (134) -> 0x1e (30) after 10
    for tap in range(256):
        state = 0xaa
        for _ in range(10):
            lsb = state & 1
            state >>= 1
            if lsb: state ^= tap
        if state == 0xe5:
            state2 = 0x86
            for _ in range(10):
                lsb2 = state2 & 1
                state2 >>= 1
                if lsb2: state2 ^= tap
            if state2 == 0x1e:
                print(f"Verified Galois tap: {hex(tap)}")
                return tap
    return None

find_tap()
