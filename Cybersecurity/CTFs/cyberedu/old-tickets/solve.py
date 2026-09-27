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