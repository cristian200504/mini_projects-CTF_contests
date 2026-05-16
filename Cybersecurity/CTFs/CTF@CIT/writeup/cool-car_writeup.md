CTF Writeup: Cool Car

Challenge Name: Cool Car 


Author: ronnie 

Difficulty: Medium

Category: Forensics / Steganography

1. Challenge Description
The challenge provides a high-resolution image of a red Ferrari and a hint file containing the number 955. The goal is to find a flag in the format CIT{example_flag}.

2. Initial Reconnaissance
An initial inspection of the file cool_car.png using standard forensics tools revealed several anomalies:

Metadata Chunks: Running pngcheck -v and exiftool identified six custom tEXt chunks labeled x-random-00 through x-random-05.

Transparency Channel: The image was saved as a 32-bit RGBA file. For a standard photograph, an alpha (transparency) channel is unusual and often indicates steganographic data.

3. Data Extraction
The metadata chunks contained fragmented Base64 strings. When concatenated in order, they formed a large block of encoded data:
mhfTqX6RDOY...QnGM

Initially, decoding this Base64 resulted in a 390-byte binary file (payload.bin) that appeared to be encrypted noise. Attempts to decrypt this via XOR, AES, and RC4 (a nod to the author "ronnie" / Ron Rivest) initially failed, suggesting the binary itself was a decoy or further encoded.

4. Visual Analysis (The "Aha!" Moment)
By isolating the Least Significant Bits (LSB) and the Alpha Channel using Python's PIL library, a secondary layer of data was discovered. The resulting "anomaly" images showed a wall of text tiled across the bit planes.

This confirmed that the "noise" in the metadata chunks was mirrored visually in the pixels: the data was not encrypted, but nested.

5. The Capture
The final breakthrough came from treating the extracted metadata not as raw binary, but as a secondary encoding layer.

First Layer: Concatenate the six x-random chunks.

Second Layer: Decode from Base64. This yielded another Base64-looking string: Q0lUezRWdTF1MXpofQ==.

Third Layer: Decode the second string from Base64.

Command:

Bash
echo "Q0lUezRWdTF1MXpofQ==" | base64 -d
Flag Captured:


CIT{4Vu1u1z}

6. Tools Used
Exiftool: For metadata extraction.

Pngcheck: To identify custom PNG chunks.

Python (PIL/Base64): For visual bit-plane extraction and automated decoding.

CyberChef: For multi-stage decoding and "Magic" analysis.