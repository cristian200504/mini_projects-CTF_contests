import urllib.request
import re
import json

HOST = 'http://18.215.143.250:8080'

req = urllib.request.Request(
    f"{HOST}/assets/index-CnN86lsh.js",
    headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode('utf-8', errors='replace')

# Find the ue() function — it's used to evaluate a single-rung scenario
# Ge calls ue(t, e) for single-rung scenarios
idx = js.find('function ue(')
if idx >= 0:
    depth=0; end=idx; started=False
    for i in range(idx, min(idx+2000,len(js))):
        if js[i]=='{': depth+=1; started=True
        elif js[i]=='}': depth-=1
        if started and depth==0: end=i+1; break
    print("=== ue() function ===")
    print(repr(js[idx:end]))

# Find A() - evaluates rungs
idx2 = js.find('function A(')
if idx2 >= 0:
    depth=0; end=idx2; started=False
    for i in range(idx2, min(idx2+2000,len(js))):
        if js[i]=='{': depth+=1; started=True
        elif js[i]=='}': depth-=1
        if started and depth==0: end=i+1; break
    print("\n=== A() function ===")
    print(repr(js[idx2:end]))

# Find ae() / Be() - node evaluators
for fname in ['function ae(', 'function Be(', 'function ie(', 'function re(']:
    idx3 = js.find(fname)
    if idx3 >= 0:
        depth=0; end=idx3; started=False
        for i in range(idx3, min(idx3+1000,len(js))):
            if js[i]=='{': depth+=1; started=True
            elif js[i]=='}': depth-=1
            if started and depth==0: end=i+1; break
        print(f"\n=== {fname} ===")
        print(repr(js[idx3:end]))

# Find L() - checks if node has "or"
idx4 = js.find('function L(')
if idx4 >= 0:
    print("\n=== L() ===")
    print(repr(js[idx4:idx4+200]))

# Find wt() - the step evaluator
idx5 = js.find('function wt(')
if idx5 >= 0:
    depth=0; end=idx5; started=False
    for i in range(idx5, min(idx5+2000,len(js))):
        if js[i]=='{': depth+=1; started=True
        elif js[i]=='}': depth-=1
        if started and depth==0: end=i+1; break
    print("\n=== wt() ===")
    print(repr(js[idx5:end]))

# Find Ge() - scenario evaluator
idx6 = js.find('function Ge(')
if idx6 >= 0:
    depth=0; end=idx6; started=False
    for i in range(idx6, min(idx6+3000,len(js))):
        if js[i]=='{': depth+=1; started=True
        elif js[i]=='}': depth-=1
        if started and depth==0: end=i+1; break
    print("\n=== Ge() scenario evaluator ===")
    print(repr(js[idx6:end]))
