def solve():
    # Target 172. Expected: ABABAA.
    # Start unknown. 
    # ABABAA = A(B(A(B(A(A(start))))))
    # A=x*2, B=(x-1)/3
    # start -> s*2 -> (s*2 - 1)/3 -> [(s*2 - 1)/3]*2 -> [[(s*2 - 1)/3]*2 - 1]/3 -> ...
    
    for start in range(1000):
        x = start
        x *= 2 # A
        if (x-1)%3 != 0: continue
        x = (x-1)//3 # B
        x *= 2 # A
        if (x-1)%3 != 0: continue
        x = (x-1)//3 # B
        x *= 2 # A
        x *= 2 # A
        if x == 172:
            print(f"Start: {start}")
            return start
solve()
