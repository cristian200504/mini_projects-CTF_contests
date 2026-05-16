import re

# --- Copied from chall.py ---
phonetic_map = {"A":"ALPHA","B":"BRAVO","C":"CHARLIE","D":"DELTA","E":"ECHO","F":"FOXTROT","G":"GOLF","H":"HOTEL","I":"INDIA","J":"JULIETT","K":"KILO","L":"LIMA","M":"MIKE","N":"NOVEMBER","O":"OSCAR","P":"PAPA","Q":"QUEBEC","R":"ROMEO","S":"SIERRA","T":"TANGO","U":"UNIFORM","V":"VICTOR","W":"WHISKEY","X":"XRAY","Y":"YANKEE","Z":"ZULU","_":"UNDERSCORE","{":"OPENCURLYBRACE","}":"CLOSECURLYBRACE","0":"ZERO","1":"ONE","2":"TWO","3":"THREE","4":"FOUR","5":"FIVE","6":"SIX","7":"SEVEN","8":"EIGHT","9":"NINE"}

def phonetic_mapping(ptext):
    cleanptext = re.sub(r'[^a-zA-Z0-9_{}]', '', ptext).upper()
    mapped = "".join([phonetic_map[c] for c in cleanptext])
    if (len(mapped) % 2 == 1):
        mapped += "X"
    return mapped

# --- Solver Logic ---

def solve():
    with open("ct.txt", "r") as f:
        ciphertext = f.read().strip()
    
    # Split ciphertext into bigrams
    ct_bigrams = [ciphertext[i:i+2] for i in range(0, len(ciphertext), 2)]
    
    # Known start of the flag
    current_flag = "lactf{"
    
    # We will try to extend char by char.
    # The flag consists of lowercase letters, digits, _, {, }
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789_{}"
    
    # To handle the padding 'X' properly:
    # `phonetic_mapping` adds 'X' if length is odd.
    # But usually, intermediate results don't have this padding unless we finish.
    # Since we are building character by character, we just check if the NEW bigrams match constraints.
    
    while not current_flag.endswith("}"):
        found_next_char = False
        
        # We need to maintain the mapping consistency.
        # But for each candidate extension, we must re-evaluate.
        
        for char in alphabet:
            candidate = current_flag + char
            
            # Simulate the DOUBLE phonetic mapping process
            # Note: We simulate strictly without the final padding 'X' *until* we might need it?
            # Actually, `phonetic_mapping` on the intermediate string will produce `mapped1`.
            # `mapped1` is input to the second mapping.
            # If `len(mapped1)` is odd, it gets an 'X' appended only at the very end.
            # However, since we are building a PREFIX, the true `mapped1` is a prefix of the final `mapped1`.
            # If `len(mapped1_prefix)` is odd, we shouldn't act on it yet.
            # We just take the characters generated so far.
            
            # Step 1: First mapping
            clean1 = re.sub(r'[^a-zA-Z0-9_{}]', '', candidate).upper()
            mapped1 = "".join([phonetic_map[c] for c in clean1])
            
            # Step 2: Second mapping
            # The input to second mapping is `mapped1`.
            # `mapped1` only contains uppercase letters.
            clean2 = re.sub(r'[^a-zA-Z0-9_{}]', '', mapped1).upper()
            mapped2 = "".join([phonetic_map[c] for c in clean2])
            
            # Resulting plaintext for bigram substitution
            pt = mapped2
            
            # Split into bigrams
            pt_bigrams = [pt[i:i+2] for i in range(0, len(pt), 2)]
            
            # Check consistency against ciphertext
            is_consistent = True
            
            # We need to check if the generated bigrams are consistent with the KNOWN ciphertext.
            # We can't verify bigrams beyond the ciphertext length.
            if len(pt_bigrams) > len(ct_bigrams) + 1: # allow slight overshoot due to incomplete last bigram
                 is_consistent = False
            
            forward_map = {}
            reverse_map = {}
            
            for i, p_bi in enumerate(pt_bigrams):
                if len(p_bi) < 2:
                    continue # incomplete last bigram, ignore
                
                if i >= len(ct_bigrams):
                    # We generated more bigrams than exist in ciphertext?
                    # This means our candidate string is too long or wrong path.
                    is_consistent = False
                    break
                
                c_bi = ct_bigrams[i]
                
                # Check mapping consistency
                if p_bi in forward_map and forward_map[p_bi] != c_bi:
                    is_consistent = False
                    break
                if c_bi in reverse_map and reverse_map[c_bi] != p_bi:
                    is_consistent = False
                    break
                
                forward_map[p_bi] = c_bi
                reverse_map[c_bi] = p_bi
            
            if is_consistent:
                # Found a valid extension!
                # But wait, could there be multiple valid extensions?
                # The search space is small (38 chars), so maybe.
                # Let's assume the first valid one is correct for now or greedy.
                # Or even better, let's collect ALL valid extensions and if >1, maybe branch?
                # For now let's just pick the first one and print.
                current_flag = candidate
                found_next_char = True
                print(f"Extended: {current_flag}")
                break
        
        if not found_next_char:
            print(f"Dead end at: {current_flag}")
            break

    print(f"Final Flag: {current_flag}")

if __name__ == "__main__":
    solve()
