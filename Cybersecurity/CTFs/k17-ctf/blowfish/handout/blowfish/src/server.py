#!/usr/bin/env python3
from Crypto.Cipher import Blowfish
from hashlib import sha256
from random import choice as rand_choice, randbytes
from secrets import FLAG

import json

SECRET_KEY = randbytes(8)
SECRET_SIGNING_KEY = randbytes(8)

CHOICE_PROMPT = """Would you like to
1. blow a fish up/blow an unfish down/unblow a fish down/unblow an unfish up, or
2. unblow a fish up/blow a fish down/blow an unfish up/unblow an unfish down? """

def pad(data):
    if len(data) % 8 != 0:
        data += b'\x00' * (8 - len(data) % 8)
    return data

def unpad(data):
    return data.rstrip(b'\x00')

def sign(raw_fish):
    return "".join(sha256(SECRET_SIGNING_KEY + raw_fish[i:i+8]).hexdigest() for i in range(0, len(raw_fish), 8))

def decrypt(ciphertext):
    iv = ciphertext[:8]
    return iv + unpad(Blowfish.new(SECRET_KEY, Blowfish.MODE_CBC, iv=iv).decrypt(ciphertext[8:]))

def encrypt(plaintext):
    iv = plaintext[:8]
    return iv + Blowfish.new(SECRET_KEY, Blowfish.MODE_CBC, iv=iv).encrypt(pad(plaintext[8:]))

def blow_fish(plaintext_hex):
    try:
        raw_fish = encrypt(bytes.fromhex(plaintext_hex))
    except:
        return "THE FISH EXPLODED", "😭"

    return raw_fish.hex(), sign(raw_fish)

def unblow_fish(ciphertext_hex):
    try:
        raw_fish = decrypt(bytes.fromhex(ciphertext_hex))
    except:
        return "THE FISH IMPLODED", "🤣🤣🤣"

    return raw_fish.hex(), sign(raw_fish)

def verify_signature(blocks_hex, signature_hex):
    try: 
        return sign(bytes.fromhex(blocks_hex)) == signature_hex
    except:
        return False

def is_admin(plaintext_hex):
    try:
        return json.loads(bytes.fromhex(plaintext_hex)[8:]).get("admin") is True
    except:
        return False

print("""Welcome to the blowfish factory! Here we blow fish
up
What kind of fish are you?!?!
Generating ...""")

your_fish = {"admin": "ABSOLUTELY NOT"}
FISH_PARTS = 50
for i in range(FISH_PARTS - 1):
    # fishiology
    fish_part = "".join(rand_choice("abcdefghijhklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8))
    fish_meat = "".join(rand_choice("abcdefghijhklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8))

    your_fish[fish_part] = fish_meat

assert len(your_fish) == FISH_PARTS, "that's super fishy, please restart the server"

# json did WHAT TO MY FISH!??!
cooked_fish = json.dumps(your_fish)
iv = randbytes(8)

# don't ask what happened to the first 3
iv_fish = iv + cooked_fish.encode()

print(f"Fish: {iv_fish.hex()}")
print(f"Signature: {sign(iv_fish)}")

print("SUCH A BIG FISH!!!!!!")

while True:
    user_choice = input(CHOICE_PROMPT)
    if user_choice == "1":
        plaintext_hex = input("Enter fish: ")
        signature_hex = input("Sign the fish: ")
        if not verify_signature(plaintext_hex, signature_hex):
            print("Sign the fish properly please")
        elif is_admin(plaintext_hex):
            print(f"So you're the boss of the school? Then let's make it offishial: {FLAG}")
            break
        else:
            fish, new_signature_hex = blow_fish(plaintext_hex)
            print(f"That went swimmingly: {fish}\nSignature: {new_signature_hex}")
    elif user_choice == "2":
        ciphertext_hex = input("Enter up-blown/unup-unblown fish: ")
        signature_hex = input("Sign the fish: ")
        if not verify_signature(ciphertext_hex, signature_hex):
            print("Sign the fish properly please")
        else:
            fish, new_signature_hex = unblow_fish(ciphertext_hex)
            print(f"They made a swordfish and a spearfish, but no axefish. Anyway that's bass-sides the point: {fish}\nSignature: {new_signature_hex}")
    else:
        print("Can't do that buddy... you're fin-ished")
        break