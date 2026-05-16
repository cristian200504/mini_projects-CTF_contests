#!/bin/bash
BASE="http://millenium-messenger.hackday.fr:8000"
COOKIE="msn_internal=granted"

echo "=== /archives with cookie ==="
curl -s -i "$BASE/archives" -H "Cookie: $COOKIE"
echo ""

echo "=== /api/debug with cookie ==="
curl -s -i "$BASE/api/debug" -H "Cookie: $COOKIE"
echo ""

echo "=== /archives with X-Internal-Access header ==="
curl -s -i "$BASE/archives" -H "X-Internal-Access: true"
echo ""

echo "=== /archives with both ==="
curl -s "$BASE/archives" -H "Cookie: $COOKIE" -H "X-Internal-Access: true"
echo ""

echo "=== Try /api/archives with cookie ==="
curl -s -i "$BASE/api/archives" -H "Cookie: $COOKIE"
echo ""

echo "=== Chat: archives with cookie ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d '{"message":"archives"}'
echo ""

echo "=== Try epoch_admin chatting with cookie ==="
curl -s -i -X POST "$BASE/api/chat" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d '{"message":"epoch","contact":"epoch_admin"}'
echo ""

echo "=== Chat with epoch_admin directly ==="
curl -s -i -X POST "$BASE/api/chat" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d '{"message":"hello","contact":"epoch"}'
echo ""

echo "=== Chat about traffic/capture ==="
curl -s -X POST "$BASE/api/chat" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d '{"message":"traffic"}'
echo ""

echo "=== Nudge epoch_admin ==="
curl -s -i -X POST "$BASE/api/nudge" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d '{"contact":"epoch"}'
echo ""
