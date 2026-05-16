import numpy as np
from PIL import Image
import pickle
import os

def get_mapping():
    mapping = {
        0: 'D', 1: 'S', 2: 'K', 3: '1', 4: 'Z', 5: '7', 6: '8', 7: '2', 8: 'U', 9: 'E',
        10: 'G', 11: 'M', 12: '5', 13: '3', 14: 'C', 15: '6', 16: 'J', 17: 'P', 18: 'I', 19: 'T',
        20: 'A', 21: '4', 22: 'N', 23: 'F', 24: 'Q', 25: '9', 26: 'R', 27: '0', 28: 'W', 29: 'X',
        30: 'V', 31: 'H', 32: 'L', 33: 'O', 34: 'B', 35: 'Y'
    }
    return mapping

old_img_path = r'C:\Users\crist\OneDrive\Desktop\How_many_2K\m4tr1x.png'
img = Image.open(old_img_path).convert('L')
arr = np.array(img) < 128

chars = {}

cell_w = 15
cell_h = 17

for r in range(100):
    y_start = 52 + r * cell_h
    for c in range(100):
        x_start = 50 + c * cell_w
        cell = arr[y_start:y_start+cell_h, x_start:x_start+cell_w]
        y_ind, x_ind = np.where(cell)
        if len(y_ind) > 0:
            crop = cell[np.min(y_ind):np.max(y_ind)+1, np.min(x_ind):np.max(x_ind)+1]
            shape_str = crop.tobytes()
            if shape_str not in chars:
                chars[shape_str] = len(chars)

mapping = get_mapping()

# Create actual shape bytes to char map
bytes_to_char = {}
# shapes are stored in chars as shape_str -> index
for shape_str, idx in chars.items():
    if idx in mapping:
        bytes_to_char[shape_str] = mapping[idx]

print(f"Generated map with {len(bytes_to_char)} characters.")

# Test on new image
new_img_path = 'm4tr1x.png'
print(f"Loading {new_img_path}...")
img_new = Image.open(new_img_path).convert('L')
arr_new = np.array(img_new) < 128

grid = []
ROWS = 400
COLS = 400

unknown_chars = {}

for r in range(ROWS):
    row_chars = []
    y_start = 52 + r * cell_h
    for c in range(COLS):
        x_start = 50 + c * cell_w
        cell = arr_new[y_start:y_start+cell_h, x_start:x_start+cell_w]
        y_ind, x_ind = np.where(cell)
        if len(y_ind) > 0:
            crop = cell[np.min(y_ind):np.max(y_ind)+1, np.min(x_ind):np.max(x_ind)+1]
            shape_str = crop.tobytes()
            if shape_str in bytes_to_char:
                row_chars.append(bytes_to_char[shape_str])
            else:
                if shape_str not in unknown_chars:
                    unknown_chars[shape_str] = len(unknown_chars)
                row_chars.append('?') # Unknown character
        else:
            row_chars.append(' ')
    grid.append(''.join(row_chars))

print(f"Found {len(unknown_chars)} unknown characters.")
if len(unknown_chars) > 0:
    for shape, idx in unknown_chars.items():
        print(f"Unknown char idx {idx}")

# Now count the words
words_to_find = ['2000', 'HACKDAY', 'PS2']
counts = {w: 0 for w in words_to_find}

directions = [
    (0, 1), (1, 0), (1, 1), (1, -1),
    (0, -1), (-1, 0), (-1, -1), (-1, 1)
]

for r in range(ROWS):
    for c in range(COLS):
        for word in words_to_find:
            for dr, dc in directions:
                match = True
                for i in range(len(word)):
                    nr = r + dr * i
                    nc = c + dc * i
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if grid[nr][nc] != word[i]:
                            match = False
                            break
                    else:
                        match = False
                        break
                if match:
                    counts[word] += 1

print(f"Counts:")
for w in words_to_find:
    print(f"{w}: {counts[w]}")

with open('flag.txt', 'w') as f:
    f.write(f"HACKDAY{{h0w_m4ny_2K?_2.0_{counts['2000']}_{counts['HACKDAY']}_{counts['PS2']}}}")
print("Done!")

