from PIL import Image
import struct

def check_lsb(filename):
    img = Image.open(filename)
    pixels = list(img.getdata())
    
    # Check LSB of each channel
    for channel in range(3): # R, G, B
        bits = ""
        for p in pixels[:1000]: # Check first 1000 bits
            bits += str(p[channel] & 1)
        
        # Convert bits to bytes
        bytes_data = []
        for i in range(0, len(bits), 8):
            byte = int(bits[i:i+8], 2)
            bytes_data.append(byte)
        
        print(f"Channel {channel} LSB (starts with): {bytes(bytes_data[:20])}")

def check_metadata(filename):
    img = Image.open(filename)
    print(f"Metadata: {img.info}")

if __name__ == "__main__":
    check_lsb('challenge.png')
    check_metadata('challenge.png')
