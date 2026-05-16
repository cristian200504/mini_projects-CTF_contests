def find_tap():
    # Seed 0xb1 = 177, Result 0x9c = 156
    # Seed 0xa6 = 166, Result 0xa8 = 168
    # Seed 0xd5 = 213, Result 0xf2 = 242 
    # Seed 0x87 = 135, Result 0x6f = 111
    # Seed 0xaa = 170, Result 0xe5 = 229
    # Seed 0x86 = 134, Result 0x1e = 30
    
    for tap in range(256):
        state = 0xb1
        for _ in range(10):
            # Try Fibonacci right shift
            bit = bin(state & tap).count('1') % 2
            state = ((state >> 1) | (bit << 7)) & 0xFF
        if state == 156:
            # Check others
            state2 = 0xa6
            for _ in range(10):
                bit2 = bin(state2 & tap).count('1') % 2
                state2 = ((state2 >> 1) | (bit2 << 7)) & 0xFF
            if state2 == 168:
                print(f"Fib-Right tap: {hex(tap)}")
                return tap
    
    print("Trying Fibonacci Left...")
    for tap in range(256):
        state = 0xb1
        for _ in range(10):
            bit = bin(state & tap).count('1') % 2
            state = ((state << 1) | bit) & 0xFF
        if state == 156:
            state2 = 0xa6
            for _ in range(10):
                bit2 = bin(state2 & tap).count('1') % 2
                state2 = ((state2 << 1) | bit2) & 0xFF
            if state2 == 168:
                print(f"Fib-Left tap: {hex(tap)}")
                return tap
    return None

find_tap()
