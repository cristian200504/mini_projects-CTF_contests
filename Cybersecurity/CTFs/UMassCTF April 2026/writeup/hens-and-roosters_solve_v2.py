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

free_sig = r.text.split("signature: ")[1].strip().lower()
print(f"Sig: {free_sig}")

# Generate 15 variations of the signature by uppercasing different characters
variants = []

# Find indices of 'a' through 'f'
alpha_indices = [i for i, c in enumerate(free_sig) if c in "abcdef"]

for i in range(15):
    if i < len(alpha_indices):
        idx = alpha_indices[i]
        variant = free_sig[:idx] + free_sig[idx].upper() + free_sig[idx+1:]
        variants.append(variant)
    else:
        # If not enough alpha characters, just mutate multiple or randomly
        variant = list(free_sig)
        for _ in range(3):
            ridx = random.choice(alpha_indices)
            variant[ridx] = variant[ridx].upper()
        variants.append("".join(variant))

print("Sending concurrent POSTs with slow verification...")
threads = []

# We want them to fire at exactly the same time to maximize race condition.
# We will use threading barriers if needed, or just slow server response will be enough.
def send_req(i, sig_variant):
    post_url = f"{url}/work?bypass={bypass_qs()}"
    try:
        res = sess.post(post_url, json={"uid": uid, "sig": sig_variant})
        print(f"Thread {i} (variant): {res.text}")
    except Exception as e:
        print(f"Thread {i} error: {e}")

for i in range(15):
    t = threading.Thread(target=send_req, args=(i, variants[i]))
    threads.append(t)

# Start all simultaneously
for t in threads:
    t.start()
    
for t in threads:
    t.join()

time.sleep(2)
print("Checking studs...")
r = sess.get(f"{url}/buy?uid={uid}&abc={bypass_qs()}")
print(r.text)
