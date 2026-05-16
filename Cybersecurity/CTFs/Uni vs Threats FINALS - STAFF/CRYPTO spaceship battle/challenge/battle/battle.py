import os

def generate_alpha_masterkey(coords):
    sorted_coords = sorted(coords)
    
    numeric_masterkey = "".join(f"{x}{y}" for x, y in sorted_coords)
    
    alpha_masterkey = "".join(chr(int(digit) + 97) for digit in numeric_masterkey)
    
    print("\n--- MASTERKEY GENERATION ---")
    print(f"Sorted Coordinates: {sorted_coords}")
    print(f"Numeric Key: {numeric_masterkey}")
    print(f"Alpha Key:   {alpha_masterkey}\n")
    return alpha_masterkey

def decrypt_vigenere(ciphertext, alpha_key):
    plaintext = []
    key_length = len(alpha_key)
    key_idx = 0
    
    for char in ciphertext:
        if char.isalpha():
            key_char = alpha_key[key_idx % key_length].lower()
            shift = ord(key_char) - 97
            
            ascii_offset = 65 if char.isupper() else 97
            
            decrypted_char = chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
            plaintext.append(decrypted_char)
            
            key_idx += 1
        else:
            plaintext.append(char)
            
    return "".join(plaintext)

def main():
    print("=== ALIEN FLEET DECRYPTION TERMINAL ===")
    
    # Introduce the bomb coordinates here
    input_coords = [
        
    ]

    alpha_masterkey = generate_alpha_masterkey(input_coords)
    
    filename = "flag.txt"
    
    if not os.path.exists(filename):
        print(f"[ERROR] '{filename}' not found in the current directory.")
        print("Please create 'flag.txt' and paste the encrypted alien transmission inside it.")
        return

    with open(filename, "r", encoding="utf-8") as file:
       encrypted_data = file.read().strip()
            
    print("--- DECRYPTING TRANSMISSION ---")
    print(f"Ciphertext read: {encrypted_data[:50]}...\n")
    
    decrypted_flag = decrypt_vigenere(encrypted_data, alpha_masterkey)
    
    print("--- RESULT ---")
    print(f"DECRYPTED FLAG: UVT{{{decrypted_flag}}}")

if __name__ == "__main__":
    main()