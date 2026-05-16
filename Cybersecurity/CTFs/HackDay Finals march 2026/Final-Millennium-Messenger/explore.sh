#!/bin/bash
BASE="http://millenium-messenger.hackday.fr:8000"

echo "=== Chat: help ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"help"}'
echo ""

echo "=== Chat: epoch ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"epoch"}'
echo ""

echo "=== Chat: archives ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"archives"}'
echo ""

echo "=== Chat: cgi ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"cgi"}'
echo ""

echo "=== Chat: key ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"key"}'
echo ""

echo "=== Chat: protocol ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"protocol"}'
echo ""

echo "=== Chat: emoticons ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"emoticons"}'
echo ""

echo "=== Minesweeper board ==="
curl -s "$BASE/api/minesweeper"
echo ""

echo "=== Set displayname (header injection test) ==="
curl -s -i -X POST "$BASE/api/set_displayname" -H "Content-Type: application/json" -d '{"name":"TestUser"}'
echo ""

echo "=== Check /api/archives ==="
curl -s -i "$BASE/api/archives"
echo ""

echo "=== Check /api/archives with X-Internal-Access ==="
curl -s -i "$BASE/api/archives" -H "X-Internal-Access: true"
echo ""

echo "=== Check /cgi-bin/ ==="
curl -s -i "$BASE/cgi-bin/"
echo ""

echo "=== Check /api/epoch ==="
curl -s -i "$BASE/api/epoch"
echo ""

echo "=== Chat: epoch_admin ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"epoch_admin"}'
echo ""

echo "=== Chat with epoch contact ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -d '{"message":"hello","contact":"epoch"}'
echo ""
