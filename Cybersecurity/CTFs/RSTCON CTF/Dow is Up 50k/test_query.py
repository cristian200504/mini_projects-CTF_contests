import urllib.request, json

BASE = "http://18.215.143.250:3000"
ACTION_SEARCH = "40881a01be516941afc21e3145707ceff4a34545af"
ACTION_ALERT = "4052fdcd2e0b2bd97d604c084f5d0c698a3baad18a"
ACTION_WATCHLIST = "40390aa0b377f579ba99d3ef8a86705be6ed7896c7"

def search(q):
    req = urllib.request.Request(
        BASE,
        data=json.dumps([q]).encode(),
        headers={
            'Content-Type': 'text/plain;charset=UTF-8',
            'Next-Action': ACTION_SEARCH
        }
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode('utf-8', 'replace')

for ticker in ["SHOP", "NOW", "PAY", "DASH", "BOX", "DOW", "DJIA", ""]:
    try:
        res = search(ticker)
        print(f"=== {ticker} ===")
        print(res.strip())
    except Exception as e:
        print(f"=== {ticker} ERR: {e} ===")
