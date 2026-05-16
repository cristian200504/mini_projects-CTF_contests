import os

def vigenere_encrypt(text, key):
    key = key.upper()
    key_len = len(key)
    key_index = 0
    encrypted_text = []

    for char in text:
        if char.isalpha():
            offset = 65 if char.isupper() else 97
            shift = ord(key[key_index]) - 65
            encrypted_char = chr((ord(char) - offset + shift) % 26 + offset)
            encrypted_text.append(encrypted_char)
            key_index = (key_index + 1) % key_len
        else:
            encrypted_text.append(char)

    return "".join(encrypted_text)

def encrypt_file(input_filename, key):
    output_filename = f"encrypted_{input_filename}"
    
    if not os.path.exists(input_filename):
        print(f"File not found: {input_filename}")
        return

    with open(input_filename, 'r', encoding='utf-8') as file:
        plaintext = file.read()

    ciphertext = vigenere_encrypt(plaintext, key)

    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(ciphertext)
    print(f"Successfully encrypted into: {output_filename}")


MASTER_KEY = "STARUFO"
files_to_encrypt = ["spaceship_arsenal.txt", "front_camera_POV.txt"]

for target_file in files_to_encrypt:
    encrypt_file(target_file, MASTER_KEY)