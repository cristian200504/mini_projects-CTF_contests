from PIL import Image
import os

def extract_bit_planes(filename):
    img = Image.open(filename)
    r, g, b = img.split()
    
    os.makedirs('planes', exist_ok=True)
    
    for i, channel in enumerate(['R', 'G', 'B']):
        data = list(img.getdata())
        for bit in range(8):
            plane = Image.new('1', img.size)
            plane_data = []
            for pixel in data:
                val = pixel[i]
                plane_data.append((val >> bit) & 1)
            plane.putdata(plane_data)
            plane.save(f'planes/{channel}_bit_{bit}.png')
            print(f'Saved planes/{channel}_bit_{bit}.png')

if __name__ == "__main__":
    extract_bit_planes('challenge.png')
