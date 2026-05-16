def find_tap():
    # Seed 0x86 = 10000110
    # Steps 10, Result 0x1e = 00011110
    # Let's try common 8-bit LFSR taps (Fibonacci)
    # Taps are often represented as a bitmask where bits set are the taps.
    # Common polynomials for n=8:
    # 0xB4 (8,6,5,4), 0x1D (8,5,4,3,1), 0x2D, 0x39, 0x4D, 0x53, 0x5F, 0x63, 0x65, 0x69, 0x6D, 0x71, 0x77, 0x7B, 0x87, 0x8E
    
    # Try simulating:
    taps = [0xB4, 0x1D, 0x8E, 0x95, 0x96, 0xA6, 0xAF, 0xB1, 0xB2, 0xB4, 0xB8, 0xC3, 0xC6, 0xD4, 0xE1, 0xE7, 0xF2, 0xFA]
    for tap in range(256):
        state = 0x86
        for _ in range(10):
            # Fibonacci LFSR
            # Check parity of (state & tap)
            bit = 0
            temp = state & tap
            while temp:
                bit ^= (temp & 1)
                temp >>= 1
            state = ((state >> 1) | (bit << 7)) & 0xFF
        if state == 0x1e:
            print(f"Found tap: {hex(tap)}")
            # Test with another seed if we had one, but let's try this.
            return tap
    return None

find_tap()
