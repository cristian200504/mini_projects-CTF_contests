#!/usr/bin/env python3
# Analyze the exact route conditions in the obfuscated JS

code = open('/mnt/c/Users/crist/OneDrive/Desktop/obfusca-not-thor/obfuscated.js').read()

# The lookup table with rotation=15
arr_original = ['Welcome\x20guest','4yLTFPA','/vuln','30904Xqnjvn','2177UMQZVs','130hyXqvt','send','/vuqsqsddqsdln123','body','log','use','disable','get','post','/vuqsqsqdsddqsd2189ln','/vuqsqsqdsddqsdl1221n','4929897UCtxHg','722307QCOqZr','/vuqsqsqdsdqsddqsdln','/vuqsqsq11212dsddqsdln','Hello\x20World!','mi12n','3870270VguSFA','admin','203495djbriC','listen','328977RKzETf','Welcome\x20admin','/vuqsqsqdsddqsdln','data','92qCdBYq','/vuqsdqsdln','Server\x20is\x20running\x20on\x20port\x20','/vul18ddqsdln126','/vuqsq1212qsqdsddqsdln','node-serialize','53707093OWMjaY','unserialize','urlencoded','ad1','/vuqs1244qsqdsddqsdln','x-powered-by']

def lookup(idx, rotation=15):
    idx = idx - 0x74
    return arr_original[(idx + rotation) % len(arr_original)]

# Print all code segments to identify the state machine
# Search for the vuqsqsqdsddqsdln1 handler
print("=== Looking for /vuqsqsqdsddqsdln1 handler ===")
pos = code.find("'/vuqsqsqdsddqsdln1'")
if pos >= 0:
    print(f"Found at position {pos}")
    print(code[pos-50:pos+400])

print("\n=== Looking for /vul18ddqsdln126 in lookup ===")
# This should be 0x86 with rotation 15
print(f"lookup(0x86) = {lookup(0x86)}")

# Find 0x86 in code
print("\n=== Searching for _0x86 references ===")
import re
matches = re.finditer(r'0x86', code)
for m in matches:
    start = max(0, m.start()-30)
    end = min(len(code), m.end()+100)
    print(f"  pos {m.start()}: {code[start:end]}")

print("\n=== Searching for /vul18ddqsdln126 literal ===")
pos2 = code.find('/vul18ddqsdln126')
if pos2 >= 0:
    print(f"Found at position {pos2}")
    print(code[pos2-100:pos2+300])

print("\n=== The /vuqsqsddqsdln123 route (step 1) - exact condition ===")
pos3 = code.find('/vuqsqsddqsdln123')
if pos3 >= 0:
    print(f"Found at position {pos3}")
    print(code[pos3-100:pos3+400])

print("\n=== Looking for a.aa and a.za assignments ===")
for pattern in ["a\\['aa'\\]", "a\\['za'\\]", "a\\['ia'\\]"]:
    matches = re.finditer(pattern, code)
    for m in matches:
        start = max(0, m.start()-50)
        end = min(len(code), m.end()+100)
        print(f"\n  {pattern} at {m.start()}:")
        print(f"  {code[start:end]}")
