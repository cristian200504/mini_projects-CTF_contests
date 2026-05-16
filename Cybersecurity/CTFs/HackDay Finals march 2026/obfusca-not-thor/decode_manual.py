#!/usr/bin/env python3
import base64
import re

b64_blob = "NTY0Nzc4NTM1NjZkNTY3MjRkNTU1NjU3NTY0NTcwNTA1NTZiNjQ0ZTY1NDY1MjU4NjM0NjRhNGU2MTdhNTY0OTU2NTY1MjRmNTQzMjU2NzM1NjU4Njg1NTYyNTQ0NjRiNTQ1NTVhNzM1NjU2NWE1NTU1NmIzOTU3NTIzMDMxMzM1NjQ0NDI1MzU2NmQ1NjU2NGU1NTY4NTQ1NjQ1NWE1MDVhNTc3ODQ2NjQzMTUyNzI1NTZiNzA0ZTU2NTQ0Njc4NTYzMTUyNDc1NDMxNGE0NzYxMzM3MDU1NTY1NjRhNTM1NDZiNTUzMTUzNDY1YTU1NTI2YjM5NTM1MjZiNTkzMTU2NDc3ODUzNjM2YjMxNDc2MzQ1NTY1ODYyNTg2ODUwNTY2YjU2NzM0ZTZjNTI1NzU1NmM1YTRmNTY1NDU2MzA1NTZjNTI0MzU5NTY1YTQ3NjM0ODQyNTU2MjQ3NTI0NzU0NTc3ODc3NTI1NjVhNTk2MTQ1Mzk2YzYyNTg0ZTM0NTYzMTVhNTM2MTMyNDY0NjRlNTU1NjU0NTY0NTcwNjE1OTU3Nzg1NzRlNTY1Mjc0NGQ1NTVhNGU2MjQ3NzczMjU2NTczMTczNTQzMTVhNDg1NDU4NjQ1NTYxMzE0YTUzNTQ1NzczMzE1MjU2NTI1NTUzNmIzOTU3NTI2YzU2MzQ1NjQ2Njg3NzUxNmIzMDc3NGY1NjU2NTc1NjQ1MzU1MDU2NmI2NDZhNjU2YzUyNTY1NTZkNDY2ODUyNTQ1Njc4NTUzMTUyNDM1NDMxNGE0NzYzNDg0NjU1NjEzMTRhNTM1NDU2NTUzMTUyNTY1YTU1NTE2YjM5NTM0ZDU2NTYzNDU2NDY2ODc3NTUzMjQ1Nzc0ZDU0NWE1MzU2NDUzNTRmNTU2YjVhNTY0ZDQ2NTI3MzU1NmM3MDRlNjI0ODQyNTY1NjZjNTI0YjU0MzE1YTQ4NjMzMzY0NTg2MTMxNGE1NzU0NTY1NTMxNGU2YzQ2NTU1NDZiMzU2YzYyNDY3MDc2NTY0Nzc0NTM2MTZiMzA3NzRlNTQ1YTU1NTY0NTVhNTA1NjZiNTY1NjY1NTY2NDcyNTU2YzRlNjg1MjU0NTUzMjU2NTY1MjQ3NTQzMTVhNDc2MzQ4NGE1NTYyNDc1MjQ3NTQ1NjU1MzE0ZTZjNjQ1NTUyNmIzOTY5NTY1Nzc3MzI1NjQ3Nzg1MzYxNmQ1MTc3NGU1NjU2NTc1NjQ1NzA2MTVhNTc3ODcyNGQ0NjUyNzQ0ZDU2NWE0ZTYxN2E0NjU2NTY1NjUyNGY1NDMxNTk3NzU2NTg2ODU1NTYzMzQyNTc1YTQ0NDEzMTU2NTY1NjU5NjM0NTM1NTM1MjU0NTY3OQ=="

print("[*] Manual step-by-step decoding")
print()

# Step 1: base64 -> hex string  
layer1_hex_str = base64.b64decode(b64_blob).decode('ascii')
print(f"Step 1 (base64 -> hex): {layer1_hex_str[:80]}...")
print(f"  Length: {len(layer1_hex_str)}")
print()

# Step 2: hex -> ascii (which is another base64)
layer2_b64 = bytes.fromhex(layer1_hex_str).decode('ascii')
print(f"Step 2 (hex -> b64): {layer2_b64[:80]}...")
print(f"  Length: {len(layer2_b64)}")
print()

# Step 3: base64 -> another base64 (already confirmed)
layer3_b64 = base64.b64decode(layer2_b64 + '==').decode('ascii')
print(f"Step 3 (base64 -> b64): {layer3_b64[:80]}...")
print(f"  Length: {len(layer3_b64)}")
print()

# Step 4: base64 -> another base64?
layer4 = base64.b64decode(layer3_b64 + '==').decode('ascii')
print(f"Step 4 (base64): {layer4[:80]}...")
print(f"  Length: {len(layer4)}")
print()

# Check for flag at each stage
for name, val in [('layer1', layer1_hex_str), ('layer2', layer2_b64), ('layer3', layer3_b64), ('layer4', layer4)]:
    flags = re.findall(r'HACKDAY\{[^}]+\}', val)
    if flags:
        print(f"\n*** FLAG in {name}: {flags} ***")

# Is layer4 hex?
print(f"\nIs layer4 hex? Unique chars: {sorted(set(layer4))}")
try:
    layer4_from_hex = bytes.fromhex(layer4).decode('ascii')
    print(f"Step 4 as hex: {layer4_from_hex[:200]}")
    flags = re.findall(r'HACKDAY\{[^}]+\}', layer4_from_hex)
    if flags:
        print(f"\n*** FLAG from hex: {flags} ***")
except Exception as e:
    print(f"layer4 not hex: {e}")

# Continue down base64 chain from layer4
print()
print("Continuing base64 chain from layer4...")
layer = layer4
for i in range(5, 15):
    try:
        next_layer = base64.b64decode(layer + '==')
        try:
            next_str = next_layer.decode('ascii')
            print(f"Step {i}: {next_str[:100]}")
            flags = re.findall(r'HACKDAY\{[^}]+\}', next_str)
            if flags:
                print(f"\n*** FLAG: {flags} ***")
                break
            # Check if it's hex
            try:
                h = bytes.fromhex(next_str).decode('ascii')
                print(f"  -> hex decoded: {h[:100]}")
                flags = re.findall(r'HACKDAY\{[^}]+\}', h)
                if flags:
                    print(f"\n*** FLAG from hex: {flags} ***")
                    break
                next_str = h
            except:
                pass
            layer = next_str
        except UnicodeDecodeError:
            print(f"Step {i}: non-ASCII bytes: {next_layer[:30]}")
            break
    except Exception as e:
        print(f"Step {i}: decode failed: {e}")
        break
