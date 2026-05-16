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

def process_flag(filename="flag.txt", output_file="output.txt"):
    if not os.path.exists(filename):
        return

    with open(filename, "r") as file:
        flag = file.read().strip()

    final_output = []

    for char in flag:
        ascii_val = ord(char)
        word_representation = number_to_words(ascii_val)
        
        space_words = []
        for letter in word_representation:
            if letter in SPACE_ALPHABET:
                space_words.append(SPACE_ALPHABET[letter])
            else:
                space_words.append(letter) 
                
        final_output.append(' '.join(space_words))

    with open(output_file, "w") as out_file:
        out_file.write(' '.join(final_output))

if __name__ == "__main__":
    if not os.path.exists("flag.txt"):
        with open("flag.txt", "w") as f:
            f.write("F")
            
    process_flag("flag.txt", "output.txt")