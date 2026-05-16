#!/usr/bin/env python3
import base64
import re

def try_decode(data, label=""):
    """Try various decodings and return what works"""
    results = {}
    
    # Try base64
    try:
        # Pad if needed
        padded = data + '==' 
        decoded = base64.b64decode(padded)
        results['base64'] = decoded
    except:
        pass
    
    # Try hex
    try:
        decoded = bytes.fromhex(data)
        results['hex'] = decoded
    except:
        pass
    
    return results

# Start with the original blob
b64_blob = "NTY0Nzc4NTM1NjZkNTY3MjRkNTU1NjU3NTY0NTcwNTA1NTZiNjQ0ZTY1NDY1MjU4NjM0NjRhNGU2MTdhNTY0OTU2NTY1MjRmNTQzMjU2NzM1NjU4Njg1NTYyNTQ0NjRiNTQ1NTVhNzM1NjU2NWE1NTU1NmIzOTU3NTIzMDMxMzM1NjQ0NDI1MzU2NmQ1NjU2NGU1NTY4NTQ1NjQ1NWE1MDVhNTc3ODQ2NjQzMTUyNzI1NTZiNzA0ZTU2NTQ0Njc4NTYzMTUyNDc1NDMxNGE0NzYxMzM3MDU1NTY1NjRhNTM1NDZiNTUzMTUzNDY1YTU1NTI2YjM5NTM1MjZiNTkzMTU2NDc3ODUzNjM2YjMxNDc2MzQ1NTY1ODYyNTg2ODUwNTY2YjU2NzM0ZTZjNTI1NzU1NmM1YTRmNTY1NDU2MzA1NTZjNTI0MzU5NTY1YTQ3NjM0ODQyNTU2MjQ3NTI0NzU0NTc3ODc3NTI1NjVhNTk2MTQ1Mzk2YzYyNTg0ZTM0NTYzMTVhNTM2MTMyNDY0NjRlNTU1NjU0NTY0NTcwNjE1OTU3Nzg1NzRlNTY1Mjc0NGQ1NTVhNGU2MjQ3NzczMjU2NTczMTczNTQzMTVhNDg1NDU4NjQ1NTYxMzE0YTUzNTQ1NzczMzE1MjU2NTI1NTUzNmIzOTU3NTI2YzU2MzQ1NjQ2Njg3NzUxNmIzMDc3NGY1NjU2NTc1NjQ1MzU1MDU2NmI2NDZhNjU2YzUyNTY1NTZkNDY2ODUyNTQ1Njc4NTUzMTUyNDM1NDMxNGE0NzYzNDg0NjU1NjEzMTRhNTM1NDU2NTUzMTUyNTY1YTU1NTE2YjM5NTM0ZDU2NTYzNDU2NDY2ODc3NTUzMjQ1Nzc0ZDU0NWE1MzU2NDUzNTRmNTU2YjVhNTY0ZDQ2NTI3MzU1NmM3MDRlNjI0ODQyNTY1NjZjNTI0YjU0MzE1YTQ4NjMzMzY0NTg2MTMxNGE1NzU0NTY1NTMxNGU2YzQ2NTU1NDZiMzU2YzYyNDY3MDc2NTY0Nzc0NTM2MTZiMzA3NzRlNTQ1YTU1NTY0NTVhNTA1NjZiNTY1NjY1NTY2NDcyNTU2YzRlNjg1MjU0NTUzMjU2NTY1MjQ3NTQzMTVhNDc2MzQ4NGE1NTYyNDc1MjQ3NTQ1NjU1MzE0ZTZjNjQ1NTUyNmIzOTY5NTY1Nzc3MzI1NjQ3Nzg1MzYxNmQ1MTc3NGU1NjU2NTc1NjQ1NzA2MTVhNTc3ODcyNGQ0NjUyNzQ0ZDU2NWE0ZTYxN2E0NjU2NTY1NjUyNGY1NDMxNTk3NzU2NTg2ODU1NTYzMzQyNTc1YTQ0NDEzMTU2NTY1NjU5NjM0NTM1NTM1MjU0NTY3OQ=="

print("[*] Decoding chain:")
print()

# Layer 0: original blob
layer = b64_blob
for i in range(10):
    print(f"--- Layer {i}: length={len(layer)}, first 80='{str(layer)[:80]}' ---")
    
    # Check for flag
    layer_str = str(layer) if isinstance(layer, str) else layer.decode('ascii', errors='replace')
    flags = re.findall(r'HACKDAY\{[^}]+\}', layer_str)
    if flags:
        print(f"\n*** FLAG FOUND: {flags} ***\n")
        break
    
    # Try base64 decode
    try:
        if isinstance(layer, str):
            decoded = base64.b64decode(layer + '==')
        else:
            decoded = base64.b64decode(layer + b'==')
        
        # Check if result is printable ASCII
        try:
            decoded_str = decoded.decode('ascii')
            print(f"  base64 => '{decoded_str[:80]}...' (printable ASCII)")
            layer = decoded_str
            continue
        except:
            # Try as hex
            try:
                hex_decoded = bytes.fromhex(decoded.decode('ascii', errors='replace'))
                try:
                    hex_str = hex_decoded.decode('ascii')
                    print(f"  base64 then hex => '{hex_str[:80]}...'")
                    layer = hex_str
                    continue
                except:
                    layer = hex_decoded
                    print(f"  base64 then hex => bytes: {layer[:40]}")
                    continue
            except:
                pass
        
        layer = decoded
        print(f"  base64 => bytes: {layer[:40]}")
        continue
    except Exception as e:
        print(f"  base64 failed: {e}")
    
    # Try hex decode
    try:
        layer_hex = layer if isinstance(layer, str) else layer.decode('ascii', errors='replace')
        decoded = bytes.fromhex(layer_hex)
        try:
            decoded_str = decoded.decode('ascii')
            print(f"  hex => '{decoded_str[:80]}...'")
            layer = decoded_str
            continue
        except:
            layer = decoded
            print(f"  hex => bytes: {layer[:40]}")
            continue
    except Exception as e:
        print(f"  hex failed: {e}")
    
    print("  No more decodings possible")
    break

print()
print(f"Final value: {str(layer)[:500]}")
