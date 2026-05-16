def solve():
    # 104 -> AABAAA.
    for start in range(1, 1000):
        x = start
        # A, A, B, A, A, A
        x *= 2
        x *= 2
        if (x-1)%3 != 0: continue
        x = (x-1)//3
        x *= 2
        x *= 2
        x *= 2
        if x == 104:
            print(f"Start found: {start}")
solve()
