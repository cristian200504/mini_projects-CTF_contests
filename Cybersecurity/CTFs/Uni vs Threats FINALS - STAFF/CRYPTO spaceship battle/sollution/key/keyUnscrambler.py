import os

def unscramble_from_symbols(input_filename="symbols.txt", output_filename="symbols_unscrambled.txt"):
    with open(input_filename, 'r', encoding='utf-8') as file:
        scrambled = file.read()

    L = len(scrambled)
    step = 7
    base_len = L // step
    extra = L % step
        
    chunk_lengths = [base_len + 1 if i < extra else base_len for i in range(step)]
        
    chunks = []
    current_pos = 0
    for length in chunk_lengths:
        chunks.append(scrambled[current_pos:current_pos + length])
        current_pos += length
            
    reversed_content_list = []
    for i in range(max(chunk_lengths)):
        for chunk in chunks:
            if i < len(chunk):
                reversed_content_list.append(chunk[i])
                    
    reversed_text = "".join(reversed_content_list)
        
    original_text = reversed_text[::-1]

    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(original_text)

    full_path = os.path.abspath(output_filename)


input_file = "symbols.txt" 
unscramble_from_symbols(input_file)