import ast
import re
from pwn import *
import hashpumpy
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def solve():
    # Loop until we get lucky with a length-1 vector
    while True:
        print("Connecting to server...")
        r = remote('lonely-island.picoctf.net', 62581)
        
        r.recvuntil(b"IV: ")
        iv = bytes.fromhex(r.recvline().strip().decode())
        
        r.recvuntil(b"Ciphertext: ")
        ct = bytes.fromhex(r.recvline().strip().decode())
        
        r.recvuntil(b"Here are the vectors I trust won't leak my key:\n")
        
        trusted = []
        for _ in range(5):
            line = r.recvline().strip().decode()
            match = re.match(r"\((.+), '(.+)'\)", line)
            if match:
                vec_str = match.group(1)
                h = match.group(2)
                parsed = ast.literal_eval(vec_str)
                trusted.append((parsed, vec_str, h))
        
        # Find a length 1 vector to act as our base
        len1_vecs = [t for t in trusted if len(t[0]) == 1]
        if not len1_vecs:
            r.close()
            print("No length 1 vector found, reconnecting (approx 15% chance)...\n")
            continue
        
        base_val, base_vec_str, base_hash = len1_vecs[0]
        X = base_val[0]
        if X == 0:
            r.close()
            continue
            
        print(f"Success! Found length 1 vector: {base_vec_str}")
        break 
        
    # Query the base vector to find k0
    r.recvuntil(b"Enter your vector: ")
    r.sendline(base_vec_str.encode())
    r.recvuntil(b"Enter its salted hash: ")
    r.sendline(base_hash.encode())
    
    res = r.recvline().decode()
    D_base = int(res.strip().split(": ")[1])
    
    # parse_vector strips negative signs, so the multiplier is always positive
    k0 = D_base // abs(X)
    key = [k0]
    print(f"Recovered k0: {k0}")
    
    # Leak the remaining 31 bytes of the key
    for i in range(1, 32):
        original_data = base_vec_str[1:-1]
        
        # We append comma-separated zeros, placing a '1' at the index of the key byte we want
        append_data = "," + "0," * (i-1) + "1"
        
        # Perform the Hash Length Extension Attack!
        new_hash, new_data = hashpumpy.hashpump(base_hash, original_data, append_data, 256)
        
        # Wrap the extended data in brackets and apply unicode escaping for the payload
        payload_str = (b'[' + new_data + b']').decode('latin-1').encode('unicode_escape').decode('latin-1')
        
        r.recvuntil(b"Enter your vector: ")
        r.sendline(payload_str.encode())
        
        r.recvuntil(b"Enter its salted hash: ")
        r.sendline(new_hash.encode())
        
        res = r.recvline().decode()
        if "Untrusted" in res:
            print("Hash extension failed!")
            break
            
        D_new = int(res.strip().split(": ")[1])
        k_i = D_new - D_base
        key.append(k_i)
        print(f"Recovered k{i}: {k_i}")
        
    print("\nFully Recovered Key:", key)
    key_bytes = bytes(key)
    
    # Decrypt the flag
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    flag = unpad(cipher.decrypt(ct), 16).decode()
    print("\n==============================")
    print("FLAG:", flag)
    print("==============================")

if __name__ == "__main__":
    solve()