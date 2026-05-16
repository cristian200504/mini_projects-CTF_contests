import os

def scramble_to_symbols(input_filename, output_filename="symbols.txt"):

    with open(input_filename, 'r', encoding='utf-8') as file:
        content = file.read()

    reversed_content = content[::-1]
        
    step = 7
    scrambled_text = ""
    for i in range(step):
        scrambled_text += reversed_content[i::step]

    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(scrambled_text)

    full_path = os.path.abspath(output_filename)

input_file = "symbols_unscrambled.txt" 
scramble_to_symbols(input_file)