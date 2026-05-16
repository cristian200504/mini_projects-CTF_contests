# Write-up: How many 2K CTF Challenge

## Challenge Overview
We are given two files:
- `exercise.txt`: Explains the challenge, which requires finding the occurrences of the strings **'2000'**, **'HACKDAY'**, and **'PS2'** hidden within an image where letters and numbers are scattered. The occurrences can be placed in all 8 possible directions (horizontal, vertical, diagonal, backwards, forwards).
- `m4tr1x.png`: An image file containing the matrix of text.

The flag format is specified as:
`HACKDAY{h0w_m4ny_2K?_[count_2000]_[count_HACKDAY]_[count_PS2]}`

## Step 1: Image Analysis
The first step is understanding the contents of `m4tr1x.png`. The image size is 1600x1800 pixels. A simple pixel check showed only **222 unique RGB colors** and clearly defined contrast, indicating this was a cleanly generated text-matrix rather than a scanned dense text block. 

By analyzing the dark pixels, we detected a consistent grid structure. The text content spanned a specific bounding box containing exactly **100 rows and 100 columns**. Each cell bounding a specific character was perfectly measured to be 15 pixels wide and 17 pixels tall. 

## Step 2: Extracting the Grid and the Letters
Since we know the letters are drawn securely inside 15x17 grids on a plain background, standard OCR (like Tesseract) is prone to errors on random gibberish overlapping character boundaries. A 100% accurate strategy is directly comparing character bitmaps.

We split the 100x100 grid into 10,000 individual cell images and collected each unique matrix shape.
The result matched expectations: **there were exactly 36 unique character bitmaps.**
36 corresponds perfectly to the English alphabet (26 characters) plus single digits (10 numbers).

> [!TIP]
> When faced with simple text in images, especially monospace terminal-like designs, mapping unique binary pixel grids is much more reliable than using OCR, which might interpret an 'O' as a '0' or an 'I' as a '1'.

## Step 3: Mapping the Bitmaps
By dumping the unique bitmaps to ASCII art in the console, we could visually recognize and perfectly map each of the 36 shapes to their corresponding ascii values (e.g. `1` or `A` or `Z`). 

For instance, this unique shape mapped natively to the letter `S`:
```text
...####..
.#######.
###....#.
##.......
###......
.###.....
...####..
.....###.
.......##
.......##
#.....##.
########.
.#####...
```

## Step 4: Automating the Search
Once we had mapped all 36 characters to their respective alphabet counterpart, we reconstructed the entire 100x100 image grid logically into a precise 2D Python list grid.

The final piece of the puzzle is searching through this transparent grid to locate occurrences of our target words. We iterated over the entire 100x100 dataset looking sequentially outwards from every cell across all 8 possible directional combinations (Up, Down, Left, Right, Up-Left, Up-Right, Down-Left, Down-Right).

```python
words_to_find = ['2000', 'HACKDAY', 'PS2']
directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
counts = {w: 0 for w in words_to_find}

for r in range(100):
    for c in range(100):
        for word in words_to_find:
            for dr, dc in directions:
                match = True
                for i in range(len(word)):
                    nr, nc = r + dr * i, c + dc * i
                    if not (0 <= nr < 100 and 0 <= nc < 100) or grid[nr][nc] != word[i]:
                        match = False
                        break
                if match:
                    counts[word] += 1
```

Executing this logic on the reconstructed grid gave us precise, automated counts without any false positives:
- **2000**: 154
- **HACKDAY**: 91 
- **PS2**: 265

## Conclusion and Flag
Aligning the discovered counts sequentially within our given flag template format (`HACKDAY{h0w_m4ny_2K?_...}`), we get the final result.

**Flag:** `HACKDAY{h0w_m4ny_2K?_154_91_265}`
