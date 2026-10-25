#!/usr/bin/env python3
import fitz
doc = fitz.open(r"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Carbon Noneoxide\extracted\ChudMaxxing_AirSensor_v1.23.0_ProductSheet.pdf")
for i, page in enumerate(doc):
    print(f"=== PAGE {i} ===")
    print(page.get_text())
print("=== links/annotations ===")
for i, page in enumerate(doc):
    for link in page.get_links():
        print(i, link)
print("=== metadata ===")
print(doc.metadata)
