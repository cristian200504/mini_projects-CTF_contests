#!/usr/bin/env python3
import base64

# The base64-encoded blob from the flag file
b64_blob = "NTY0Nzc4NTM1NjZkNTY3MjRkNTU1NjU3NTY0NTcwNTA1NTZiNjQ0ZTY1NDY1MjU4NjM0NjRhNGU2MTdhNTY0OTU2NTY1MjRmNTQzMjU2NzM1NjU4Njg1NTYyNTQ0NjRiNTQ1NTVhNzM1NjU2NWE1NTU1NmIzOTU3NTIzMDMxMzM1NjQ0NDI1MzU2NmQ1NjU2NGU1NTY4NTQ1NjQ1NWE1MDVhNTc3ODQ2NjQzMTUyNzI1NTZiNzA0ZTU2NTQ0Njc4NTYzMTUyNDc1NDMxNGE0NzYxMzM3MDU1NTY1NjRhNTM1NDZiNTUzMTUzNDY1YTU1NTI2YjM5NTM1MjZiNTkzMTU2NDc3ODUzNjM2YjMxNDc2MzQ1NTY1ODYyNTg2ODUwNTY2YjU2NzM0ZTZjNTI1NzU1NmM1YTRmNTY1NDU2MzA1NTZjNTI0MzU5NTY1YTQ3NjM0ODQyNTU2MjQ3NTI0NzU0NTc3ODc3NTI1NjVhNTk2MTQ1Mzk2YzYyNTg0ZTM0NTYzMTVhNTM2MTMyNDY0NjRlNTU1NjU0NTY0NTcwNjE1OTU3Nzg1NzRlNTY1Mjc0NGQ1NTVhNGU2MjQ3NzczMjU2NTczMTczNTQzMTVhNDg1NDU4NjQ1NTYxMzE0YTUzNTQ1NzczMzE1MjU2NTI1NTUzNmIzOTU3NTI2YzU2MzQ1NjQ2Njg3NzUxNmIzMDc3NGY1NjU2NTc1NjQ1MzU1MDU2NmI2NDZhNjU2YzUyNTY1NTZkNDY2ODUyNTQ1Njc4NTUzMTUyNDM1NDMxNGE0NzYzNDg0NjU1NjEzMTRhNTM1NDU2NTUzMTUyNTY1YTU1NTE2YjM5NTM0ZDU2NTYzNDU2NDY2ODc3NTUzMjQ1Nzc0ZDU0NWE1MzU2NDUzNTRmNTU2YjVhNTY0ZDQ2NTI3MzU1NmM3MDRlNjI0ODQyNTY1NjZjNTI0YjU0MzE1YTQ4NjMzMzY0NTg2MTMxNGE1NzU0NTY1NTMxNGU2YzQ2NTU1NDZiMzU2YzYyNDY3MDc2NTY0Nzc0NTM2MTZiMzA3NzRlNTQ1YTU1NTY0NTVhNTA1NjZiNTY1NjY1NTY2NDcyNTU2YzRlNjg1MjU0NTUzMjU2NTY1MjQ3NTQzMTVhNDc2MzQ4NGE1NTYyNDc1MjQ3NTQ1NjU1MzE0ZTZjNjQ1NTUyNmIzOTY5NTY1Nzc3MzI1NjQ3Nzg1MzYxNmQ1MTc3NGU1NjU2NTc1NjQ1NzA2MTVhNTc3ODcyNGQ0NjUyNzQ0ZDU2NWE0ZTYxN2E0NjU2NTY1NjUyNGY1NDMxNTk3NzU2NTg2ODU1NTYzMzQyNTc1YTQ0NDEzMTU2NTY1NjU5NjM0NTM1NTM1MjU0NTY3OQ=="

print("=== Step 1: base64 decode ===")
layer1 = base64.b64decode(b64_blob).decode('ascii', errors='replace')
print(f"Layer 1 (as ASCII): {layer1[:200]}")
print()

print("=== Step 2: check if layer 1 is hex ===")
# The output looks like hex characters: 564778...
try:
    layer2 = bytes.fromhex(layer1).decode('ascii', errors='replace')
    print(f"Layer 2 (hex decoded): {layer2[:500]}")
except Exception as e:
    print(f"Not valid hex: {e}")
    layer2 = None

print()
if layer2:
    print("=== Step 3: check if layer 2 is base64 ===")
    try:
        layer3 = base64.b64decode(layer2 + '==').decode('ascii', errors='replace')
        print(f"Layer 3 (b64 decoded): {layer3[:500]}")
    except Exception as e:
        print(f"Not base64: {e}")
    
    print()
    print("=== Step 3: check if layer 2 is more hex ===")
    try:
        layer3b = bytes.fromhex(layer2).decode('ascii', errors='replace')
        print(f"Layer 3 (hex decoded again): {layer3b[:500]}")
    except Exception as e:
        print(f"Not hex: {e}")
    
    print()
    print("=== Raw layer 2 analysis ===")
    print(f"Length: {len(layer2)}")
    print(f"First 100 chars: {layer2[:100]}")
    print(f"Unique chars: {sorted(set(layer2))}")
    
    # Check if it's printable ASCII that contains a flag
    if 'HACKDAY' in layer2:
        import re
        flags = re.findall(r'HACKDAY\{[^}]+\}', layer2)
        print(f"\nFLAG FOUND: {flags}")
