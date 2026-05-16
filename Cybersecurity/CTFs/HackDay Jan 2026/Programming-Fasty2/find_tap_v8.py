def find_tap():
    # Seed 0x87 = 135
    # Steps 10, Result 0x6f = 111
    # Seed 0xd5 = 213, Result 0xf2 = 242 
    # Seed 0xaa = 170, Result 0xe5 = 229
    # Seed 0x86 = 134, Result 0x1e = 30
    
    for tap in range(256):
        state = 0x87
        for _ in range(10):
            bit = 0
            temp = state & tap
            while temp:
                bit ^= (temp & 1)
                temp >>= 1
            state = ((state >> 1) | (bit << 7)) & 0xFF
        if state == 111:
            state2 = 0x86
            for _ in range(10):
                bit2 = 0; temp2 = state2 & tap
                while temp2: bit2 ^= (temp2 & 1); temp2 >>= 1
                state2 = ((state2 >> 1) | (bit2 << 7)) & 0xFF
            if state2 == 30:
                print(f"Verified Fibonacci tap: {hex(tap)}")
                return tap
    print("Fibonacci failed. Trying Galois...")
    for tap in range(256):
        state = 0x87
        for _ in range(10):
            lsb = state & 1; state >>= 1
            if lsb: state ^= tap
        if state == 111:
            state2 = 0x86
            for _ in range(10):
                lsb2 = state2 & 1; state2 >>= 1
                if lsb2: state2 ^= tap
            if state2 == 30:
                print(f"Verified Galois tap: {hex(tap)}")
                return tap
    return None

find_tap()
