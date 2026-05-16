import os

def vigenere_decrypt(text, key):
    key = key.upper()
    key_len = len(key)
    key_index = 0
    decrypted_text = []

    for char in text:
        if char.isalpha():
            offset = 65 if char.isupper() else 97
            shift = ord(key[key_index]) - 65
            
            decrypted_char = chr((ord(char) - offset - shift + 26) % 26 + offset)
            decrypted_text.append(decrypted_char)
            key_index = (key_index + 1) % key_len
        else:
            decrypted_text.append(char)

    return "".join(decrypted_text)

def decrypt_file(input_filename, key):
    if not os.path.exists(input_filename):
        return

    with open(input_filename, 'r', encoding='utf-8') as file:
        ciphertext = file.read()

    plaintext = vigenere_decrypt(ciphertext, key)
    output_filename = input_filename.replace("encrypted_", "decrypted_")

    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(plaintext)

MASTER_KEY = "" #TODO: Insert the master key obtained from the key folder here to decrypt the files
files_to_decrypt = ["encrypted_spaceship_arsenal.txt", "encrypted_front_camera_POV.txt"]

for target_file in files_to_decrypt:
    decrypt_file(target_file, MASTER_KEY)