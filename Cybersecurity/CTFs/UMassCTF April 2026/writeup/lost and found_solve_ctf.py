import os, zlib, struct, hashlib

# Setup paths
base_dir = r"C:\Users\crist\OneDrive\Desktop\lost and found"
forensics_dir = os.path.join(base_dir, r"extract\forensics\home_files\home")
repo_root_enc = os.path.join(forensics_dir, "5457501C") # .git dir in hex
config_path = os.path.join(repo_root_enc, "195F570E1C11") # config in hex
index_path = os.path.join(repo_root_enc, "135E5D0D0D")   # index in hex

# 1. Recover first 92 bytes of key from config
config_raw = open(config_path, "rb").read()
config_plain = b"[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = true\n"
key_period = 165
key = [None] * key_period
for i in range(min(len(config_raw), len(config_plain))):
    key[i % key_period] = config_raw[i] ^ config_plain[i]

# 2. Recover more from index file SHA-1 repetitions
index_raw = open(index_path, "rb").read()
blob_sha = bytes.fromhex("7bf1e19cf8d86b529526756fb8aca833102c99f9")
for i in range(len(index_raw) - 20):
    for j in range(i + key_period, len(index_raw) - 20, key_period):
        if index_raw[i:i+20] == index_raw[j:j+20]:
            for k in range(20):
                p = (i + k) % key_period
                val = index_raw[i+k] ^ blob_sha[k]
                if key[p] is None: key[p] = val

# 3. Use metadata structure to fill gaps (zeros in uid/gid, padding)
curr = 12
while curr < len(index_raw) - 62:
    pk0, pk1 = key[(curr+60)%key_period], key[(curr+61)%key_period]
    if pk0 is not None and pk1 is not None:
        name_len = ( (index_raw[curr+60] ^ pk0) << 8 | (index_raw[curr+61] ^ pk1) ) & 0x0FFF
        # Recover from meta zeros
        for k in [28, 29, 30, 31, 32, 33, 34, 35]: # uid/gid
            p = (curr + k) % key_period
            if key[p] is None: key[p] = index_raw[curr+k] ^ 0
        pad_len = 8 - ((62 + name_len) % 8)
        if pad_len == 0: pad_len = 8
        for k in range(pad_len):
            p = (curr + 62 + name_len + k) % key_period
            if key[p] is None: key[p] = index_raw[curr + 62 + name_len + k] ^ 0
        curr += 62 + name_len + pad_len
    else:
        # If flags key is missing, we try to slide
        curr += 1

# If still missing, fill with 0 (should be nearly full)
for p in range(key_period):
    if key[p] is None: key[p] = 0 # Fallback

key_final = bytes(key)
print(f"Key Recovered: {key_final.hex()}")

# 4. Decrypt function
def decrypt(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

# 5. Restore Repository
restored_root = os.path.join(base_dir, "restored_repo")
os.makedirs(restored_root, exist_ok=True)
git_dir = os.path.join(restored_root, ".git")
os.makedirs(git_dir, exist_ok=True)

# Decrypt objects
obj_dir_enc = os.path.join(repo_root_enc, "1552530D16021B") # objects
for d in os.listdir(obj_dir_enc):
    dp_enc = os.path.join(obj_dir_enc, d)
    if not os.path.isdir(dp_enc): continue
    # Decrypt dir name
    d_raw = bytes.fromhex(d)
    d_dec = decrypt(d_raw, key_final).decode('ascii', errors='ignore')[:2]
    dp_dec = os.path.join(git_dir, "objects", d_dec)
    os.makedirs(dp_dec, exist_ok=True)
    for f in os.listdir(dp_enc):
        fp_enc = os.path.join(dp_enc, f)
        if len(f) <= 20: continue # Skip red-herrings
        f_raw = bytes.fromhex(f)
        f_dec = decrypt(f_raw, key_final).decode('ascii', errors='ignore')
        fp_dec = os.path.join(dp_dec, f_dec)
        with open(fp_enc, "rb") as fe:
            content_enc = fe.read()
            with open(fp_dec, "wb") as fd:
                fd.write(decrypt(content_enc, key_final))

# Decrypt basic files
files_to_decrypt = {
    "195F570E1C11": "config",
    "135E5D0D0D": "index",
    "3275782C": "HEAD",
    "3562702F2A3E2D3477": "ORIG_HEAD",
    "1E554A0B071F18015A5C07": "description"
}

for enc, dec_name in files_to_decrypt.items():
    f_enc = os.path.join(repo_root_enc, enc)
    if os.path.exists(f_enc):
        with open(f_enc, "rb") as fe:
            c_enc = fe.read()
            with open(os.path.join(git_dir, dec_name), "wb") as fd:
                fd.write(decrypt(c_enc, key_final))

# Decrypt refs
refs_dir_enc = os.path.join(repo_root_enc, "08555F1B")
for root, dirs, files in os.walk(refs_dir_enc):
    for fn in files:
        if len(fn) <= 20: continue
        fp_enc = os.path.join(root, fn)
        rel = os.path.relpath(fp_enc, refs_dir_enc)
        # Decrypt path components
        parts = rel.split(os.sep)
        dec_parts = []
        for p in parts:
            pb = bytes.fromhex(p)
            dec_parts.append(decrypt(pb, key_final).decode('ascii', errors='ignore'))
        fp_dec = os.path.join(git_dir, "refs", *dec_parts)
        os.makedirs(os.path.dirname(fp_dec), exist_ok=True)
        with open(fp_enc, "rb") as fe:
            c_enc = fe.read()
            with open(fp_dec, "wb") as fd:
                fd.write(decrypt(c_enc, key_final))

print("Repository restored in restored_repo")
