# UMASS CTF - Ninja-Nerds Writeup

- **Category:** Forensics
- **Difficulty:** Medium
- **Flag Format:** `UMASS{...}`
- **Challenge File:** `challenge.png`

## 1. Description
The challenge provided a PNG image of a LEGO Ninjago scene with the cryptic clue: *"where are your little ninja-nerds?"*

## 2. Initial Investigation

### File Analysis
The file `challenge.png` is a standard 640x360 PNG image. Initial forensic checks were performed:
- **Strings:** No human-readable flag or interesting strings found.
- **Metadata:** EXIF data was stripped/empty.
- **Embedded Files:** `binwalk` (simulated via Python header search) revealed no hidden ZIPs, JPEGs, or other standard payloads.
- **Chunk Analysis:** All PNG chunks (IHDR, IDAT, IEND) were verified with valid CRCs. No data was hidden between chunks.

## 3. Clue Interpretation
The description *"where are your little ninja-nerds?"* is a specific quote from **The LEGO Ninjago Movie**, spoken by Lord Garmadon. Master Wu responds:
> *"They are surrounding you, **perfectly hidden**, ready to strike!"*

In the film, the ninjas are hiding in plain sight. This hinted that the flag was hidden within the pixel data themselves, likely using steganography rather than file-level manipulation.

## 4. Technical Solution

### LSB Extraction
Since visual inspection and standard tools failed to show a flag in the color planes, a deeper analysis of the **Least Significant Bits (LSB)** was conducted. LSB steganography hides data in the lowest bit of pixel values, making the change invisible to the human eye.

A Python script was used to extract bitstreams from various channels (Red, Green, Blue) and interleaving patterns.

```python
from PIL import Image

def extract_channel_lsb(filename, channel_index):
    img = Image.open(filename)
    pixels = list(img.getdata())
    
    # Extract the LSB of the specified channel
    bits = "".join(str(p[channel_index] & 1) for p in pixels)
    
    # Convert bits to bytes
    bytes_data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return bytes_data

# The flag was found in the Blue (B) channel LSB
blue_lsb = extract_channel_lsb('challenge.png', 2)
if b'UMASS' in blue_lsb:
    print(blue_lsb[blue_lsb.find(b'UMASS'):blue_lsb.find(b'UMASS')+41])
```

### Result
Running the extraction on the **Blue Channel** revealed the flag:
`UMASS{perfectly-hidden-ready-to-strike}`

## 5. Flag
**`UMASS{perfectly-hidden-ready-to-strike}`**
