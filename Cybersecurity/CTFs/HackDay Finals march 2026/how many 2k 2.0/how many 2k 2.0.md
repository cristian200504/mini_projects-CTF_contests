# Write-up: How many 2K? 2.0 CTF Challenge

## Challenge Overview
Following the "How many 2K?" challenge, we are presented with a new iteration: "How many 2K? 2.0". We are given two files:
- `exercise.txt`: Explains the challenge. As before, we need to find occurrences of the strings **'2000'**, **'HACKDAY'**, and **'PS2'** hidden within a massive image filled with scattered letters and numbers. The text can be placed in all 8 possible directions (horizontal, vertical, diagonal, forwards, backwards).
- `m4tr1x.png`: An enormous image file (`6900x6100` pixels) containing the new text matrix.

The flag format is specified as:
`HACKDAY{h0w_m4ny_2K?_2.0_[count_2000]_[count_HACKDAY]_[count_PS2]}`

## Step 1: Image Analysis
The first step was to understand `m4tr1x.png`. The image size has vastly increased from the previous challenge (which was 1600x1800) to **6900x6100 pixels**, making manual analysis completely impossible.

However, examining the margins and the structure revealed that the cell boundaries matched the previous challenge exactly:
- **Left Margin:** 50 pixels
- **Top Margin:** 52 pixels
- **Cell Size:** 15 pixels wide, 17 pixels tall

Given the image footprint, calculating the grid size yields a mammoth **400 columns** (`(6100 - 100 margins) / 15`) and **400 rows** (`(6900 - 100 margins) / 17`). Instead of 10,000 cells like the previous iteration, this challenge contains an overwhelming **160,000 cells**.

## Step 2: Extracting Characters (The Reusable Bitmap Strategy)
Since the font and cell size (`15x17`) were identical to those from the original "How many 2K?", we hypothesized that the unique bitmaps for each character were unchanged. 

Instead of manually re-mapping the characters from scratch, we reused the bitmap dictionary from the original challenge's script. We generated a static mapping of binary visual shapes directly linking to their respective ASCII counterparts. 

> [!TIP]
> Always check for reusable assets across challenge series! By using the exact binary pixel layout of the 36 unique characters (A-Z, 0-9) from the old `m4tr1x.png`, we skipped the tedious manual mapping phase completely.

Applying this pre-built mapping dictionary to the 160,000 cells in the new `m4tr1x.png` returned a 100% success rate. **Zero unknown characters were found**, confirming our approach.

## Step 3: Automating the Search
With the entire 400x400 grid accurately transformed into a 2D Python list, we utilized an 8-directional search pattern. The script sequentially scans outwards from each of the 160,000 cells looking for our target words.

```python
words_to_find = ['2000', 'HACKDAY', 'PS2']
directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
counts = {w: 0 for w in words_to_find}

for r in range(400): # Updated bounds
    for c in range(400):
        for word in words_to_find:
            for dr, dc in directions:
                match = True
                for i in range(len(word)):
                    nr, nc = r + dr * i, c + dc * i
                    if not (0 <= nr < 400 and 0 <= nc < 400) or grid[nr][nc] != word[i]:
                        match = False
                        break
                if match:
                    counts[word] += 1
```

Executing this search on the massive grid gave the following exact occurrences:
- **2000**: 420
- **HACKDAY**: 406
- **PS2**: 331

## Conclusion and Flag
Structuring the discovered counts sequentially within the provided flag template (`HACKDAY{h0w_m4ny_2K?_2.0_...}`), we get the final correct result.

**Flag:** `HACKDAY{h0w_m4ny_2K?_2.0_420_406_331}`
