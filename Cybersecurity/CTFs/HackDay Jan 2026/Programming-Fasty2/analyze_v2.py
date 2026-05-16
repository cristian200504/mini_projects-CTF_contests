def analyze():
    # DBEBDBEE 
    # D=4, B=2, E=5, B=2, D=4, B=2, E=5, E=5
    # Sum: 4+2+5+2+4+2+5+5 = 29.
    # Expected: 56.
    # 29 * 2 = 58 (My script).
    # 56 / 2 = 28.
    # So sum was 28? 29 - 28 = 1 error.
    
    # Maybe A=0?
    # D=3, B=1, E=4, B=1, D=3, B=1, E=4, E=4
    # Sum: 3+1+4+1+3+1+4+4 = 21. 
    # 21 * 2 = 42. (Still not 56)
    
    # What if it's A=1, B=2, C=3, but D and E vary?
    # Or just sum of ordinals again?
    # D=68, B=66, E=69, B=66, D=68, B=66, E=69, E=69
    # Sum: 68+66+69+66+68+66+69+69 = 541 (Wait, same sum as before!)
    # Let's check math: 68+66=134. 69+66=135. 68+66=134. 69+69=138.
    # 134+135+134+138 = 541. 
    # Previous: CDECBAED -> 67+68+69+67+66+65+69+68 = 541.
    # BOTH had sum 541!
    # Expected for CDECBAED: 54.
    # Expected for DBEBDBEE: 56.
    
    # 541 -> 54? Maybe sum of digits? 5+4+1 = 10. No.
    # Maybe (sum // 10) ? 541 // 10 = 54. 
    # 541 // 10 = 54.
    # BUT 541 // 10 is also 54 for both.
    # Expected for DBEBDBEE was 56.
    
    # Let's re-sum DBEBDBEE: 68+66+69+66+68+66+69+69 = 541. Exact.
    # Wait, 56?
    # What if it's sum of ordinals MOD something?
    # What if it's simpler?
    
    # MSN Encoding: 'f0H4ier=', 'e0ugf1ej', 'j1Oxn1r='
    # 'f0H4ier=' -> 8 chars.
    # 'e0ugf1ej' -> 8 chars.
    # 'j1Oxn1r=' -> 8 chars.
    # These look like Leet Speak or Rot13? 
    # f0H4ier -> f o l i e r ? (0=o, 4=l)
    # e0ugf1ej -> e o u g h t y ? (0=o, 1=i or t?)
    # j1Oxn1r -> j i n x e r ? (1=i, x=x)
    # decode 'f0H4ier=' -> 'folier' or 'folie'?
    # Actually, MSN emoticons/codes were like (Y), (N).
    # But this looks like custom Alpha-Numeric map.
    
    # Let's try 0=o, 1=i, 4=l, x=x, H=h? 
    # f o H i e r = 
    # e o u g f i e j
    # j i o x n i r
    
    pass

analyze()
