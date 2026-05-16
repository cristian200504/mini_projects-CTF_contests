def decrypt_ctf():
    ciphertext = (
        "095 181 145 039 245 091 212 232 123 220 167 069 091 208 245 164 245 145 123 094 "
        "062 150 094 172 083 135 096 153 002 208 096 172 201 005 019 "
        "131 091 090 053 095 218 238 211 091 004 201 182 135 245 167 074 090 145 096 238"
    ).split()

    decryption_key = {
        '095': 'M', '181': 'a', '145': 'y', '039': 't', '245': 'h',
        '091': 'e', '212': 'F', '232': 'o', '123': 'r', '220': 'c',
        '167': 'e', '069': 'b', '208': 'w', '164': 't', '094': 'u',
        '062': 'y', '150': 'o', '172': 'n', '083': 'g', '135': 'p',
        '096': 'a', '153': 'd', '002': 'a', '201': 'C', '005': 'I',
        '019': 'T'
    }

    extended_key = {
        '131': 'J', '090': 'd', '053': 'i', '218': 'a', '238': 's',
        '211': 't', '004': 'r', '182': 'i', '074': 'r'
    }
    
    decryption_key.update(extended_key)

    decrypted_text = ""
    for index, number in enumerate(ciphertext):
        if index == 20:
            decrypted_text += ", "
        elif index == 32:
            decrypted_text += ". "
        elif index == 35:
            decrypted_text += " {"
            
        decrypted_text += decryption_key.get(number, '?')

    decrypted_text += "}"
    
    return decrypted_text

result = decrypt_ctf()
print("Decrypted Output:")
print(result)