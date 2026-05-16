import re


url = input("URL: ").strip()

username = url.replace("https://www.facebook.com/", "")

matches = re.search(r"^https://www\.facebook\.com/([a-zA-Z0-9]+)$", url,re.IGNORECASE)
if matches:
    print(f"Username: {matches.group(1)}")
else:
    print("Invalid URL or username not found.")