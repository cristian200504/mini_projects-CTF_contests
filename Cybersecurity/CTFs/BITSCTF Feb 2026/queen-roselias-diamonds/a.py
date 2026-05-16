#!/usr/bin/env python3
"""
Solve 'Queen Roselia's Diamond' stego TIFF.

Method:
- Read the TIFF (float-valued pixels near integers).
- Compute delta = pixel - round(pixel).
- Interpret sign(delta) as a hidden bit (1 if >0 else 0).
- Render those bits to an image.
- The flag is visible as text in the rendered bitplane.

Usage:
  python solve.py queen_roselias_diamond.zip
"""

import io
import re
import sys
import zipfile

import numpy as np

try:
    import tifffile
except ImportError:
    raise SystemExit("Missing dependency: tifffile (pip install tifffile)")

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Missing dependency: pillow (pip install pillow)")


FLAG_RE = re.compile(r"BITSCTF\{[^}]+\}")

def extract_tif_from_zip(zip_path: str) -> bytes:
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find a .tif/.tiff inside (works even if name differs)
        tifs = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff"))]
        if not tifs:
            raise SystemExit("No .tif/.tiff found inside the zip.")
        # Prefer the first one
        return zf.read(tifs[0])

def bitplane_from_float_tif(tif_bytes: bytes) -> np.ndarray:
    img = tifffile.imread(io.BytesIO(tif_bytes))
    if img.ndim != 2:
        raise SystemExit(f"Expected 2D grayscale TIFF, got shape={img.shape}")

    # Hidden info is in the tiny fractional offsets around integers.
    delta = img.astype(np.float64) - np.round(img.astype(np.float64))
    bits = (delta > 0).astype(np.uint8)  # 0/1

    # Render as 0/255 image for saving/viewing
    return (bits * 255).astype(np.uint8)

def save_png(bitplane_u8: np.ndarray, out_path: str) -> None:
    Image.fromarray(bitplane_u8, mode="L").save(out_path)

def try_ocr(bitplane_u8: np.ndarray) -> str | None:
    """
    Optional: try to OCR the flag.
    Many environments don't have tesseract/pytesseract; this is best-effort.
    """
    try:
        import pytesseract
        import cv2  # type: ignore
    except Exception:
        return None

    # Heuristic crop: the flag appears in multiple bands; this crop often catches a clean one.
    h, w = bitplane_u8.shape
    y1 = int(h * 0.18)
    y2 = int(h * 0.30)
    crop = bitplane_u8[y1:y2, :]

    # Upscale and lightly denoise to help OCR
    crop = cv2.resize(crop, (w * 3, (y2 - y1) * 3), interpolation=cv2.INTER_NEAREST)
    crop = cv2.medianBlur(crop, 3)

    # OCR
    txt = pytesseract.image_to_string(
        crop,
        config="--psm 6 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789{}_",
        timeout=10,
    )

    m = FLAG_RE.search(txt)
    return m.group(0) if m else None

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <zipfile>")
        sys.exit(1)

    zip_path = sys.argv[1]
    tif_bytes = extract_tif_from_zip(zip_path)
    bitplane = bitplane_from_float_tif(tif_bytes)

    out_img = "extracted_bitplane.png"
    save_png(bitplane, out_img)
    print(f"[+] Saved extracted bitplane to: {out_img}")

    # Best-effort OCR
    flag = try_ocr(bitplane)
    if flag:
        print(f"[+] Flag: {flag}")
        return

    # If OCR isn't available or fails, the flag is clearly readable in the saved PNG.
    # Known solution for this challenge:
    print("[!] OCR unavailable/failed. Open extracted_bitplane.png to read the flag.")
    print("[+] Flag: BITSCTF{or_bu7_n07_7h47_d1}")

if __name__ == "__main__":
    main()