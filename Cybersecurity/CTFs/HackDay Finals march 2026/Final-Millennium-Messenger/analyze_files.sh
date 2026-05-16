#!/bin/bash
cd /tmp

echo "=== PCAP analysis ==="
tshark -r millennium_traffic.pcap -V 2>/dev/null

echo ""
echo "=== PCAP strings ==="
strings millennium_traffic.pcap

echo ""
echo "=== PCAP hex dump ==="
xxd millennium_traffic.pcap

echo ""
echo "=== PNG hex dump ==="
xxd smiley_y2k.png

echo ""
echo "=== PNG strings ==="
strings smiley_y2k.png

echo ""
echo "=== Exiftool on PNG ==="
exiftool smiley_y2k.png 2>/dev/null || echo "exiftool not available"

echo ""
echo "=== Steghide on PNG ==="
steghide info -sf smiley_y2k.png 2>&1 || echo "steghide not available"

echo ""
echo "=== zsteg on PNG ==="
zsteg smiley_y2k.png 2>&1 || echo "zsteg not available"
