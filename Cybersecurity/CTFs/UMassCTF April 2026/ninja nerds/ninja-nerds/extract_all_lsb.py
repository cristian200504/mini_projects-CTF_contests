from PIL import Image
import struct

def bitstring_to_bytes(s):
    return bytes(int(s[i:i+8], 2) for i in range(0, len(s), 8))

def extract_advanced_lsb(filename):
    img = Image.open(filename)
    pixels = list(img.getdata())
    width, height = img.size
    
    # 1. Pixel interleaved (RGB RGB RGB ...)
    all_bits = ""
    for p in pixels:
        for val in p:
            all_bits += str(val & 1)
    
    data = bitstring_to_bytes(all_bits[:len(all_bits)//8*8])
    if b'UMASS' in data.upper():
        print(f"Found UMASS in RGB interleaved LSB!")
        print(data[data.upper().find(b'UMASS'):data.upper().find(b'UMASS')+100])

    # 2. Channel-wise (All R, then all G, then all B)
    for i, name in enumerate(['R', 'G', 'B']):
        bits = "".join(str(p[i] & 1) for p in pixels)
        data = bitstring_to_bytes(bits[:len(bits)//8*8])
        if b'UMASS' in data.upper():
            print(f"Found UMASS in {name} channel LSB!")
            print(data[data.upper().find(b'UMASS'):data.upper().find(b'UMASS')+100])

    # 3. Try BGR interleaved
    all_bits_bgr = ""
    for p in pixels:
        for val in reversed(p):
            all_bits_bgr += str(val & 1)
    data = bitstring_to_bytes(all_bits_bgr[:len(all_bits_bgr)//8*8])
    if b'UMASS' in data.upper():
        print(f"Found UMASS in BGR interleaved LSB!")
        print(data[data.upper().find(b'UMASS'):data.upper().find(b'UMASS')+100])

if __name__ == "__main__":
    extract_advanced_lsb('challenge.png')
