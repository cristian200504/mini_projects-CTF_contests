def find_tap():
    # Try Left Galois
    for tap in range(256):
        state = 0x87
        for _ in range(10):
            msb = (state >> 7) & 1
            state = (state << 1) & 0xFF
            if msb: state ^= tap
        if state == 0x6f:
            state2 = 0x86
            for _ in range(10):
                msb2 = (state2 >> 7) & 1; state2 = (state2 << 1) & 0xFF
                if msb2: state2 ^= tap
            if state2 == 0x1e:
                print(f"Verified Left-Galois tap: {hex(tap)}")
                return tap
    
    # Try bits coming from MSB vs LSB
    print("Trying Left Fibonacci...")
    for tap in range(256):
        state = 0x87
        for _ in range(10):
            bit = bin(state & tap).count('1') % 2
            state = ((state << 1) | bit) & 0xFF
        if state == 0x6f:
            print(f"Left-Fib tap: {hex(tap)}")
            return tap
    return None

find_tap()
