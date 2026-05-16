#!/usr/bin/env python3
import os
import re
import sys
import zipfile
import tempfile

import numpy as np
from PIL import Image

# Optional OCR (recommended). If not installed, script still extracts the hidden image.
try:
    import pytesseract  # type: ignore
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


FLAG_RE = re.compile(r"(BHSCTF\{[^}]+\})")


def find_first_tiff(extract_dir: str) -> str:
    candidates = []
    for root, _, files in os.walk(extract_dir):
        for fn in files:
            low = fn.lower()
            if low.endswith((".tif", ".tiff")):
                candidates.append(os.path.join(root, fn))
    if not candidates:
        raise FileNotFoundError("No .tif/.tiff found after extracting the zip.")
    # Prefer something with "challenge" in the name if present
    candidates.sort(key=lambda p: ("challenge" not in os.path.basename(p).lower(), p))
    return candidates[0]


def load_tiff_as_array(tiff_path: str) -> np.ndarray:
    # Use tifffile if available (handles more TIFF variants)
    try:
        import tifffile  # type: ignore
        arr = tifffile.imread(tiff_path)
        return np.asarray(arr)
    except Exception:
        # Fall back to PIL (may fail on some float TIFFs)
        img = Image.open(tiff_path)
        return np.asarray(img)


def extract_sign_bitplane(arr: np.ndarray) -> np.ndarray:
    """
    The challenge hides bits in the *sign of the tiny fractional offset*
    from each pixel's nearest integer.

    bit = 1 if (pixel - round(pixel)) < 0 else 0
    """
    # If multi-channel, reduce to one channel
    if arr.ndim == 3:
        # Take first channel (often it's actually 1-channel stored oddly)
        arr = arr[..., 0]

    arr = arr.astype(np.float64)

    nearest = np.rint(arr)            # nearest integer
    frac = arr - nearest              # signed fractional residue
    bits = (frac < 0).astype(np.uint8)  # 1 where negative, else 0

    # Convert to viewable black/white image
    bw = (bits * 255).astype(np.uint8)
    return bw


def maybe_ocr_flag(bw_img: Image.Image) -> str | None:
    if not OCR_AVAILABLE:
        return None

    # Try a few OCR-friendly transforms
    candidates = []

    # 1) raw
    candidates.append(bw_img)

    # 2) inverted
    candidates.append(Image.fromarray(255 - np.array(bw_img)))

    # 3) upscaled (OCR likes bigger text)
    up = bw_img.resize((bw_img.width * 4, bw_img.height * 4), Image.NEAREST)
    candidates.append(up)
    candidates.append(Image.fromarray(255 - np.array(up)))

    for im in candidates:
        try:
            txt = pytesseract.image_to_string(im, config="--psm 6")
        except Exception:
            continue
        m = FLAG_RE.search(txt)
        if m:
            return m.group(1)
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_flag.py /path/to/queen_roselias_diamond.zip")
        sys.exit(1)

    zip_path = sys.argv[1]
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(zip_path)

    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(td)

        tiff_path = find_first_tiff(td)
        print(f"[+] Found TIFF: {tiff_path}")

        arr = load_tiff_as_array(tiff_path)
        print(f"[+] TIFF shape={arr.shape}, dtype={arr.dtype}")

        bw = extract_sign_bitplane(arr)
        out_path = os.path.abspath("extracted_bitplane.png")
        Image.fromarray(bw).save(out_path)
        print(f"[+] Saved extracted image: {out_path}")

        flag = maybe_ocr_flag(Image.fromarray(bw))
        if flag:
            print(f"[+] FLAG: {flag}")
        else:
            if OCR_AVAILABLE:
                print("[-] OCR ran but no flag matched the pattern.")
            else:
                print("[-] pytesseract not installed; skipping OCR.")
            print("[i] Open extracted_bitplane.png and read the flag visually,")
            print("    or install OCR: pip install pytesseract (and system tesseract).")


if __name__ == "__main__":
    main()