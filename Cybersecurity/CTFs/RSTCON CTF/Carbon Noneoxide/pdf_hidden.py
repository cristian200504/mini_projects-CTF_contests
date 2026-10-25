#!/usr/bin/env python3
"""Extract every text span in the PDF with its color, font, size, and bbox.
Look for hidden/light-colored text (white-on-white) that may contain the real flag."""
import fitz

PDF = r"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Carbon Noneoxide\extracted\ChudMaxxing_AirSensor_v1.23.0_ProductSheet.pdf"
doc = fitz.open(PDF)

def color_to_hex(c):
    # c is an int (sRGB packed) or float
    if isinstance(c, int):
        return f"#{c:06X}"
    return f"#{int(c*255):06X}"

print("=== spans with non-black or tiny color (possible hidden text) ===")
for pno, page in enumerate(doc):
    d = page.get_text("dict")
    for block in d.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                color = span.get("color", 0)
                size = span.get("size", 0)
                font = span.get("font", "")
                bbox = span.get("bbox", [])
                # convert color
                try:
                    chex = color_to_hex(color)
                except Exception:
                    chex = str(color)
                # flag non-black text OR very small text OR text containing flag-ish chars
                is_hidden = False
                reason = []
                # color: black is 0. anything else is "colored"
                if color != 0:
                    reason.append(f"color={chex}")
                    is_hidden = True
                if size < 4:
                    reason.append(f"tiny size={size}")
                    is_hidden = True
                if "rstcon" in text.lower() or "flag" in text.lower() or "{" in text or "}" in text:
                    reason.append("flag-ish")
                    is_hidden = True
                if is_hidden:
                    print(f"p{pno} color={chex} size={size:.1f} font={font} bbox={[round(x,1) for x in bbox]}")
                    print(f"    TEXT: {text!r}")

print("\n=== ALL spans (full dump) ===")
for pno, page in enumerate(doc):
    d = page.get_text("dict")
    for block in d.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text","")
                c = span.get("color",0)
                try: ch = color_to_hex(c)
                except: ch=str(c)
                if t.strip():
                    print(f"p{pno} {ch} sz{span.get('size',0):.1f}: {t!r}")
