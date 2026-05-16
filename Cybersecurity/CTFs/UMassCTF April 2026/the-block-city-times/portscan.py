"""Port scan the Block City Times server to find the actual app instance."""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

IP = "34.106.57.61"

def check_port(port):
    try:
        r = requests.get(f"http://{IP}:{port}/", timeout=2)
        return port, r.status_code, len(r.text), r.text[:150].replace('\n',' ')
    except:
        return port, None, 0, ""

# Scan common web ports and higher ranges
ports = list(range(80, 100)) + list(range(3000, 3010)) + list(range(4000, 4010))
ports += list(range(5000, 5050)) + list(range(8000, 8100)) + list(range(9000, 9010))
ports += [443, 8443, 8888, 9090, 9999, 10000, 10080]
# Also try random high ports that instances might be on
ports += list(range(30000, 30050)) + list(range(31000, 31050)) + list(range(32000, 32050))
ports += list(range(40000, 40010)) + list(range(50000, 50010))

print(f"Scanning {len(ports)} ports on {IP}...")
results = []

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(check_port, p): p for p in ports}
    for f in as_completed(futures):
        port, status, length, text = f.result()
        if status is not None:
            results.append((port, status, length, text))

results.sort()
for port, status, length, text in results:
    print(f"  Port {port}: HTTP {status} | {length} bytes | {text}")

if not results:
    print("No open ports found in scanned range")
