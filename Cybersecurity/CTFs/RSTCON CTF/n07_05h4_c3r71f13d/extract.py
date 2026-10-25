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

# ── Find the M (scenarios) array ─────────────────────────────────────────────
# It's defined as:  const M = [ ... ]  or  M=[...]
# Look for the function that builds scenario objects: {id:t,coil:e,brief:n,slot:i,...}
# The constructor call looks like: {id:"01", coil:"OUT_A", brief:"...", slot:1, ...}

# Find all occurrences of the scenario factory pattern
# Pattern: scenario constructor calls look like Ht("01","OUT_A","...",1,...)
# Let's find the factory function name first
factory_match = re.search(r'function\s+(\w+)\s*\(\s*t\s*,\s*e\s*,\s*n\s*,\s*i\s*,\s*s\s*,\s*r\s*,\s*a\s*,\s*o\s*\)\s*\{\s*return\s*\{id:t,coil:e,brief:n,slot:i', js)
if factory_match:
    fname = factory_match.group(1)
    print(f"Factory function: {fname}")
    # Find all calls to this factory
    calls = re.findall(rf'{fname}\(([^)]+)\)', js)
    print(f"Found {len(calls)} scenario calls")
    for c in calls[:30]:
        print(f"  {fname}({c})")
else:
    print("Factory not found by name, trying inline search...")

# ── Alternative: find all string literals that look like scenario IDs ─────────
# Scenario IDs appear to be "01","02",... etc.
# Find patterns like: "01","COIL_NAME","brief text",...
scenario_pattern = re.findall(
    r'"(\d{2})"\s*,\s*"([A-Z_0-9]+)"\s*,\s*"([^"]{5,200})"',
    js
)
print(f"\n=== Scenario strings (id, coil, brief) ===")
for s in scenario_pattern:
    print(f'  id={s[0]}  coil={s[1]}  brief={s[2][:100]}')

# ── Find 'given' objects ───────────────────────────────────────────────────────
# given: {IN_A:1, IN_B:0, ...}
given_pattern = re.findall(r'given:\s*(\{[^}]+\})', js)
print(f"\n=== given objects ({len(given_pattern)}) ===")
for g in given_pattern[:20]:
    print(f"  {g}")

# ── Find 'cases' arrays ────────────────────────────────────────────────────────
cases_pattern = re.findall(r'cases:\s*(\[[^\]]+\])', js)
print(f"\n=== cases arrays ({len(cases_pattern)}) ===")
for c in cases_pattern[:10]:
    print(f"  {c}")

# ── Find 'broken' values ───────────────────────────────────────────────────────
broken = re.findall(r'broken:\s*([^,}]+)', js)
print(f"\n=== broken values ({len(broken)}) ===")
for b in broken[:10]:
    print(f"  {b}")

# ── Dump full M array region ───────────────────────────────────────────────────
# Find where M is assigned
m_idx = js.find('const M=[')
if m_idx < 0:
    m_idx = js.find('M=[')
if m_idx >= 0:
    # Find closing bracket
    depth = 0
    end = m_idx
    started = False
    for i in range(m_idx, min(m_idx + 20000, len(js))):
        if js[i] == '[':
            depth += 1
            started = True
        elif js[i] == ']':
            depth -= 1
        if started and depth == 0:
            end = i + 1
            break
    print(f"\n=== M array ({end-m_idx} chars) ===")
    print(js[m_idx:end])
else:
    print("\nM array not found by 'const M=[' pattern")
    # Try to find it differently
    idx = js.find('"01"')
    if idx >= 0:
        print(f"'01' found at index {idx}, context:")
        print(repr(js[max(0,idx-100):idx+400]))
