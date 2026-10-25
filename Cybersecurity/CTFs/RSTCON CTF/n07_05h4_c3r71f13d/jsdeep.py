import urllib.request
import re

HOST = 'http://18.215.143.250:8080'

req = urllib.request.Request(
    f"{HOST}/assets/index-CnN86lsh.js",
    headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode('utf-8', errors='replace')

# ── 1. Find the /api/solve POST handler and what it does with the response ───
print("=== Full /api/solve context (600 chars each side) ===")
idx = js.find('/api/solve')
print(repr(js[max(0,idx-600):idx+600]))

# ── 2. Find how a rung's 'q' property is set (scenario linkage) ──────────────
print("\n=== rung.q context ===")
for m in re.finditer(r'\.q\b', js):
    ctx = js[max(0,m.start()-80):m.end()+80]
    if 'rung' in ctx.lower() or 'q' in ctx:
        print(repr(ctx))
        print('---')

# ── 3. Find the server-side evaluation function Ne() more completely ──────────
print("\n=== Ne() function full body ===")
idx2 = js.find('async function Ne()')
if idx2 >= 0:
    # find end by brace counting
    depth = 0
    end = idx2
    started = False
    for i in range(idx2, min(idx2+3000, len(js))):
        if js[i] == '{':
            depth += 1
            started = True
        elif js[i] == '}':
            depth -= 1
        if started and depth == 0:
            end = i+1
            break
    print(repr(js[idx2:end]))

# ── 4. Find what 'q' property on rungs means — how M scenarios match rungs ──
print("\n=== scenario coil / rung.q matching ===")
idx3 = js.find('rung.q')
if idx3 < 0:
    idx3 = js.find('.q===')
if idx3 >= 0:
    print(repr(js[max(0,idx3-200):idx3+300]))

# ── 5. Look for how the broken (reference) solution rungs are structured ─────
print("\n=== broken solution rung builders F/q/qt/Y ===")
for fname in ['function F(', 'function q(', 'function qt(', 'function Y(', 'function R(']:
    idx4 = js.find(fname)
    if idx4 >= 0:
        print(f"\n{fname}...")
        print(repr(js[idx4:idx4+300]))

# ── 6. Find how rungs are tagged with scenario id (the 'q' field) ─────────────
print("\n=== rung q= assignment ===")
for m in re.finditer(r'q\s*:\s*["\'](\w+)["\']', js):
    ctx = js[max(0,m.start()-100):m.end()+100]
    print(repr(ctx))
    print('---')
