import numpy as np
from PIL import Image

def get_mapping():
    mapping = {
        0: 'D', 1: 'S', 2: 'K', 3: '1', 4: 'Z', 5: '7', 6: '8', 7: '2', 8: 'U', 9: 'E',
        10: 'G', 11: 'M', 12: '5', 13: '3', 14: 'C', 15: '6', 16: 'J', 17: 'P', 18: 'I', 19: 'T',
        20: 'A', 21: '4', 22: 'N', 23: 'F', 24: 'Q', 25: '9', 26: 'R', 27: '0', 28: 'W', 29: 'X',
        30: 'V', 31: 'H', 32: 'L', 33: 'O', 34: 'B', 35: 'Y'
    }
    return mapping

img = Image.open('m4tr1x.png').convert('L')
arr = np.array(img) < 128

chars = {}
unique_shapes = []

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

grid = []
for r in range(100):
    row_chars = []
    y_start = 52 + r * cell_h
    for c in range(100):
        x_start = 50 + c * cell_w
        cell = arr[y_start:y_start+cell_h, x_start:x_start+cell_w]
        y_ind, x_ind = np.where(cell)
        if len(y_ind) > 0:
            crop = cell[np.min(y_ind):np.max(y_ind)+1, np.min(x_ind):np.max(x_ind)+1]
            shape_str = crop.tobytes()
            row_chars.append(mapping[chars[shape_str]])
        else:
            row_chars.append(' ')
    grid.append(''.join(row_chars))

words_to_find = ['2000', 'HACKDAY', 'PS2']
counts = {w: 0 for w in words_to_find}

directions = [
    (0, 1), (1, 0), (1, 1), (1, -1),
    (0, -1), (-1, 0), (-1, -1), (-1, 1)
]

for r in range(100):
    for c in range(100):
        for word in words_to_find:
            for dr, dc in directions:
                match = True
                for i in range(len(word)):
                    nr = r + dr * i
                    nc = c + dc * i
                    if 0 <= nr < 100 and 0 <= nc < 100:
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
