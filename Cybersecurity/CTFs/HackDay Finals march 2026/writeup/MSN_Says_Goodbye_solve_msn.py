import hashlib
from Crypto.Cipher import AES
import struct

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def get_primes(count, max_val):
    primes = []
    for i in range(2, max_val):
        if is_prime(i):
            primes.append(i)
            if len(primes) == count:
                break
    return primes

def decrypt(enc_file, key, iv):
    with open(enc_file, 'rb') as f:
        ciphertext = f.read()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(ciphertext)

if __name__ == '__main__':
    iv_phrases = [
        b"~xX_D4rK_Adm1n_Xx~",
        b"dark_admin",
        b"dark_admin@hotmail.com",
        b"admin_nickname"
    ]
    ivs = [hashlib.md5(p).digest() for p in iv_phrases]
    
    avatar = r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\avatars\dark_admin.bmp"
    with open(avatar, 'rb') as f:
        data = f.read()
        
    pixel_offset = struct.unpack('<I', data[10:14])[0]
    
    base_primes = get_primes(256, 8000)
    
    for prime_offset in [0, 1]:  # 0-indexed or 1-indexed primes
        primes = [p - prime_offset for p in base_primes]
        
        for blue_idx in [0, 2]:  # BGR = 0, RGB = 2
            bits = []
            for p in primes:
                offset = pixel_offset + p * 3 + blue_idx
                if offset < len(data):
                    bits.append(data[offset] & 1)
                else:
                    bits.append(0)
                    
            if len(bits) < 256: continue
            
            for bit_order in ['big', 'little']:
                key = bytearray()
                for i in range(0, 256, 8):
                    byte_val = 0
                    for j in range(8):
                        if bit_order == 'big':
                            byte_val |= (bits[i+j] << (7-j))
                        else:
                            byte_val |= (bits[i+j] << j)
                    key.append(byte_val)
                
                for iv_idx, iv in enumerate(ivs):
                    try:
                        dec = decrypt(r"c:\Users\crist\OneDrive\Desktop\New folder\extracted\MSN_Says_Goodbye\secret_message.enc", key, iv)
                        if b"HACKDAY" in dec:
                            print(f"\nFOUND! prime_offset={prime_offset}, blue_idx={blue_idx}, bit_order={bit_order}, IV='{iv_phrases[iv_idx].decode()}'")
                            print("Decrypted block:", dec)
                    except Exception as e:
                        pass


