import hashlib
from Crypto.Cipher import AES
from PIL import Image

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def get_primes(count):
    primes = []
    i = 2
    while len(primes) < count:
        if is_prime(i): primes.append(i)
        i += 1
    return primes

def decrypt(enc_file, key, iv):
    with open(enc_file, 'rb') as f: ciphertext = f.read()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(ciphertext)

avatars = [
    r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\avatars\dark_admin.bmp",
    r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\avatars\neo_hacker.bmp",
    r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\avatars\princess2003.bmp",
    r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\avatars\sk8erboi.bmp"
]

primes = get_primes(256)

for av in avatars:
    im = Image.open(av).convert('RGB')
    
    pixels_topdown = list(im.getdata())
    
    pixels_bottomup = []
    width, height = im.size
    for y in range(height-1, -1, -1):
        for x in range(width):
            pixels_bottomup.append(im.getpixel((x, y)))

    # also try row-major but right-to-left?
    # what about the raw bytes of the file itself?
    with open(av, 'rb') as f:
        raw_data = f.read()
    
    # 54 bytes is header
    raw_pixels = raw_data[54:]
    
    for direction, pixels in [("topdown", pixels_topdown), ("bottomup", pixels_bottomup)]:
        for offset in [0, 1]:  # offset for primes (index = p or p-1)
            bits = []
            for p in primes:
                idx = p - offset
                if idx < len(pixels):
                    b = pixels[idx][2]  # RGB -> Blue is index 2
                    bits.append(b & 1)
                else:
                    bits.append(0)
            
            if len(bits) < 256: continue
            
            for bit_order in ["big", "little"]:
                key = bytearray()
                for i in range(0, 256, 8):
                    byte_val = 0
                    for j in range(8):
                        if bit_order == "big":
                            byte_val |= (bits[i+j] << (7-j))
                        else:
                            byte_val |= (bits[i+j] << j)
                    key.append(byte_val)
                
                # We can just test with a dummy IV because the padding is in the last block
                iv_dummy = b'\x00' * 16
                try:
                    dec = decrypt(r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\secret_message.enc", key, iv_dummy)
                    # Check padding
                    pad_byte = dec[-1]
                    if 1 <= pad_byte <= 16:
                        # Validate all pad bytes
                        pad_valid = True
                        for i in range(1, pad_byte + 1):
                            if dec[-i] != pad_byte:
                                pad_valid = False
                                break
                        
                        if pad_valid and pad_byte > 5:  # require at least some meaningful padding to avoid random chances
                            print(f"\nVALID PAD! Avatar: {av.split(chr(92))[-1]}, dir:{direction}, offset:{offset}, bits:{bit_order}")
                            print("Decrypted (wrong IV for block 1):", dec)
                            # Now let's try real IVs to get block 1
                            for iv_str in [b"~xX_D4rK_Adm1n_Xx~", b"dark_admin", b"dark_admin@hotmail.com", b"admin_nickname", b"xX_D4rK_Adm1n_Xx"]:
                                real_iv = hashlib.md5(iv_str).digest()
                                real_dec = decrypt(r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\secret_message.enc", key, real_iv)
                                print(f"IV {iv_str.decode()}: {real_dec}")
                except Exception:
                    pass



