#!/usr/bin/env python3
import fitz
PDF = r"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Carbon Noneoxide\extracted\ChudMaxxing_AirSensor_v1.23.0_ProductSheet.pdf"
doc = fitz.open(PDF)
def chx(c):
    try: return f"#{c:06X}" if isinstance(c,int) else f"#{int(c*255):06X}"
    except: return str(c)

print("=== spans whose text contains rstcon/flag/{/}/? or is light-colored (#F5F7FA, #FFFFFF, near-white) ===")
for pno, page in enumerate(doc):
    d = page.get_text("dict")
    for block in d.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text","")
                c = span.get("color",0)
                ch = chx(c)
                light = ch in ("#F5F7FA","#FFFFFF","#FEFEFE","#F8F8F8","#FAFAFA") or (isinstance(c,int) and c != 0 and ((c>>16)&255)>200 and ((c>>8)&255)>200 and (c&255)>200)
                if "rstcon" in t.lower() or "flag" in t.lower() or "{" in t or "}" in t or "????" in t or light:
                    print(f"p{pno} color={ch} size={span.get('size',0):.1f} font={span.get('font','')} bbox={[round(x,1) for x in span.get('bbox',[])]}")
                    print(f"    {t!r}")

print("\n=== raw text of page 2 & 3 (where the HIDDEN INSTRUCTION appeared) ===")
for pno in (2,3):
    print(f"--- page {pno} ---")
    print(doc[pno].get_text())

print("\n=== any drawing/vector text or hidden form fields? ===")
for pno, page in enumerate(doc):
    for x in page.get_drawings():
        # look for text-like or unusual
        pass
    # annotations / form fields
    for w in page.get_texttrace() if hasattr(page,'get_texttrace') else []:
        print(pno, w)
