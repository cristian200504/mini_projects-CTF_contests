import os

SPACE_ALPHABET = {
    'A': 'ASTEROID', 'B': 'BLACKHOLE', 'C': 'COMET', 'D': 'DARKMATTER',
    'E': 'ECLIPSE', 'F': 'FLARE', 'G': 'GALAXY', 'H': 'HALO',
    'I': 'INTERSTELLAR', 'J': 'JUPITER', 'K': 'KEPLER', 'L': 'LUNAR',
    'M': 'METEOR', 'N': 'NEBULA', 'O': 'ORBIT', 'P': 'PULSAR',
    'Q': 'QUASAR', 'R': 'ROVER', 'S': 'SUPERNOVA', 'T': 'TELESCOPE',
    'U': 'UNIVERSE', 'V': 'VOID', 'W': 'WORMHOLE', 'X': 'XRAY',
    'Y': 'YELLOWDWARF', 'Z': 'ZENITH'
}

def number_to_words(n):
    units = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN", 
             "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]

    if n < 20:
        return units[n]
    elif n < 100:
        return tens[n // 10] + (units[n % 10] if n % 10 != 0 else "")
    else:
        hundreds = units[n // 100] + "HUNDRED"
        remainder = n % 100
        if remainder == 0:
            return hundreds
        elif remainder < 20:
            return hundreds + units[remainder]
        else:
            return hundreds + tens[remainder // 10] + (units[remainder % 10] if remainder % 10 != 0 else "")

WORDS_TO_NUM = {number_to_words(i): chr(i) for i in range(256)}

WORD_LENGTHS = sorted(list(set(len(w) for w in WORDS_TO_NUM.keys())), reverse=True)

def decode_layer(encoded_str):
    words = encoded_str.split()
    letter_str = "".join(w[0] for w in words)
    n = len(letter_str)
    
    dp = [None] * (n + 1)
    dp[n] = True
    
    # Bottom-Up Dynamic Programming
    for i in range(n - 1, -1, -1):
        for length in WORD_LENGTHS:
            if i + length <= n:
                w = letter_str[i:i+length]
                if w in WORDS_TO_NUM and dp[i + length] is not None:
                    dp[i] = w
                    break
                    
    if dp[0] is None:
        raise ValueError("Failed to decode the sequence near index 0. Bad string structure.")
        
    result = []
    curr = 0
    while curr < n:
        w = dp[curr]
        result.append(WORDS_TO_NUM[w])
        curr += len(w)
        
    return "".join(result)

def solve():
    print("Reading file...")
    with open("output.txt", "r") as f:
        current_text = f.read().strip()

    valid_words = set(SPACE_ALPHABET.values())
    
    layer = 1
    while True:
        words = current_text.split()
        if not words:
            break
            
        if not all(w in valid_words for w in words[:15]):
            break
            
        print(f"Decoding echo layer {layer}...")
        current_text = decode_layer(current_text)
        layer += 1

    print("\n[+] Flag successfully untangled:")
    print(current_text)

if __name__ == "__main__":
    solve()