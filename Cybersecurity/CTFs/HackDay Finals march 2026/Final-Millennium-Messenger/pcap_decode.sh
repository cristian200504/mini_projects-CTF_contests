#!/bin/bash
cd /tmp

echo "=== Full PCAP decode ==="
tshark -r millennium_traffic.pcap -T fields -e frame.number -e ip.src -e ip.dst -e tcp.payload 2>/dev/null

echo ""
echo "=== TCP Streams ==="
tshark -r millennium_traffic.pcap -z follow,tcp,ascii,0 2>/dev/null

echo ""
echo "=== All strings in PCAP ==="
strings millennium_traffic.pcap

echo ""
echo "=== PCAP hex around the ciphertext ==="
xxd millennium_traffic.pcap | grep -A 60 "MSG "

echo ""
echo "=== Python parse PCAP ==="
python3 << 'PYEOF'
with open('/tmp/millennium_traffic.pcap', 'rb') as f:
    data = f.read()

# Find all MSG sections
import re
# Data after TCP headers - look for MSG patterns
text = data.decode('latin-1', errors='replace')
idx = 0
while True:
    pos = text.find('MSG ', idx)
    if pos < 0:
        break
    end = text.find('\n', pos + 200)
    print(f"Position {pos}: {repr(text[pos:min(pos+300, end+1 if end > 0 else pos+300)])}")
    idx = pos + 1
PYEOF
