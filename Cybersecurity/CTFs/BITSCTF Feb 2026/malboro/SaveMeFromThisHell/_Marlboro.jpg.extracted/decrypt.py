from binascii import unhexlify

key_hex = "c7027f5fdeb20dc7308ad4a6999a8a3e069cb5c8111d56904641cd344593b657"
key = unhexlify(key_hex)

with open("encrypted.bin", "rb") as f:
    data = f.read()

decrypted = bytearray()
for i in range(len(data)):
    decrypted.append(data[i] ^ key[i % len(key)])

with open("decrypted.bin", "wb") as f:
    f.write(decrypted)

print("Decryption complete.")