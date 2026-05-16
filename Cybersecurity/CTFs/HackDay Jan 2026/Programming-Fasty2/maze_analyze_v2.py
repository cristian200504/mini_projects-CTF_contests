def solve():
    # Target 98, Path AAAABA
    # AAAABA = end -> rA -> rA -> rA -> rA -> rB -> rA
    # reversed: AAAAA B A
    # end -> /2 -> /2 -> /2 -> /2 -> *3+1 -> /2
    
    # Let's try end -> reverse Path
    # AAAABA: step 1:s*2, 2:s*4, 3:s*8, 4:s*16, 5:((s*16)-1)/3, 6:(((s*16)-1)/3)*2 = 98
    # (((s*16)-1)/3)*2 = 98 => ((s*16)-1)/3 = 49 => s*16-1 = 147 => s*16 = 148 => s=9.25. (No)
    
    # What if it is A, A, A, A, B, A (reversed B order?)
    # s -> 2s (A) -> 4s (A) -> 8s (A) -> 16s (A) -> (16s-1)/3 (B) -> (32s-2)/3 = 98. (No)
    
    # What if Path is AAAABA and start is 9?
    # 9 -> 18 -> 36 -> 72 -> 144 -> (143/3 no)
    # What if start is 13?
    # 13 -> 26 -> 52 -> 104 -> 208 -> 69 -> 138.
    
    # What if start is 6?
    # 6 -> 12 -> 24 -> 48 -> 96 -> (95/3 no)
    
    # What if target 98 is reached by AAAABA differently?
    # Maybe B is first? B A A A A A
    # (s-1)/3 -> 2(...) -> ...
    # 98 / 2 / 2 / 2 / 2 / 2 = 3.06.
    # 3.06 * 3 + 1 = 10.18.
    
    # Let's check start 1 again.
    # 1 -> 2 -> 4 -> 8 -> 16 -> (15/3)=5 -> 10. (No)
    # 1 -> A -> 2 -> A -> 4 -> A -> 8 -> A -> 16 -> A -> 32 -> B -> (31/3 no)
    
    # Let's try 98 / 2 = 49. (49*3)+1 = 148. 148/2/2/2 = 18.5. 
    # 148/2/2/2/2 = 9.25.
    
    # What if Start is 37?
    # 37 -> 74 -> 148 -> (147/3) = 49 -> 98. (Path AABA). 
    # To get AAAABA, we need two more A's.
    # 37 / 2 / 2 = 9.25.
    
    # Wait! Start 4 or something?
    # 4 -> 8 -> 16 -> 32 -> 64 -> (63/3)=21 -> 42.
    # 19 -> 38 -> 76 -> 152 -> 304 -> (303/3)=101 -> 202.
    # 18.5...
    
    pass
solve()
