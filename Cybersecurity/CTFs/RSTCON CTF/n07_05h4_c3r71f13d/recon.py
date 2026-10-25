import urllib.request
import re
import json

HOST = 'http://18.215.143.250:8080'

# ── 1. Fetch the JS bundle and extract routes / API strings ──────────────────
req = urllib.request.Request(
    f"{HOST}/assets/index-CnN86lsh.js",
    headers={"User-Agent": "Mozilla/5.0"}
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        js = resp.read().decode('utf-8', errors='replace')
        print(f"JS bundle size: {len(js)} bytes\n")
except Exception as e:
    print(f"Failed to fetch JS: {e}")
    js = ""

if js:
    # paths starting with /
    routes = sorted(set(re.findall(r'["\'`](/[a-zA-Z0-9/_.\-?=&%]+)["\'`]', js)))
    print(f"=== Potential routes ({len(routes)}) ===")
    for r in routes:
        print(f"  {r}")

    # WebSocket URLs
    ws = re.findall(r'ws[s]?://[^\'"` ]+', js)
    if ws:
        print(f"\n=== WebSocket URLs ===")
        for w in set(ws):
            print(f"  {w}")

    # fetch/axios/XHR call patterns
    fetches = re.findall(r'fetch\s*\(\s*["`\']([^"`\']+)["`\']', js)
    if fetches:
        print(f"\n=== fetch() calls ===")
        for f in set(fetches):
            print(f"  {f}")

    # any string containing 'flag', 'program', 'ladder', 'run', 'coil'
    keywords = re.findall(r'["\'`]([^"\'`]*(?:flag|program|ladder|run|coil|plc|rung|rung|io|input|output)[^"\'`]*)["\'`]', js, re.I)
    if keywords:
        print(f"\n=== Keyword matches ===")
        for k in sorted(set(keywords))[:50]:
            print(f"  {repr(k)}")

# ── 2. Probe the routes we found ─────────────────────────────────────────────
print("\n=== Probing discovered routes ===")
candidates = [
    '/ws', '/socket', '/socket.io/', '/events',
    '/save', '/load', '/project', '/project.json',
    '/plc', '/plc/run', '/plc/state', '/plc/io',
    '/api/save', '/api/load', '/api/project',
]

for path in candidates:
    try:
        r2 = urllib.request.urlopen(
            urllib.request.Request(HOST + path, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=3
        )
        body = r2.read().decode('utf-8', errors='replace')
        print(f"  GET {path} -> {r2.status}: {body[:150]}")
    except urllib.error.HTTPError as e:
        print(f"  GET {path} -> HTTP {e.code}")
    except Exception as e:
        print(f"  GET {path} -> {type(e).__name__}: {e}")
