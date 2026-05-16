import os, zlib, struct

# THE TRUE 165-BYTE KEY
key_final = bytes.fromhex("7a30396875766875333369336262757675787a63696f687a63787669686f33777279797564736679757a637678687975687975777268797566647375686879757a767863696a6c666b6461736a6b6e766f787a63696875776566696a18f39499f882afe88f3c981e8a0d9b9728188bf20db2fb4aeff50af16afff234e5f31165ecc0f4f091c4786ac3c98d789f3b8bdffbf1fcf5847a684527d676d154ecb06579eaf69039")

base_dir = r"C:\Users\crist\OneDrive\Desktop\lost and found"
forensics_dir = os.path.join(base_dir, r"extract\forensics\home_files\home")
repo_root_enc = os.path.join(forensics_dir, "5457501C") # .git dir in hex

def decrypt(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

# 1. Restore Repository
restored_root = os.path.join(base_dir, "restored_repo_final")
os.makedirs(restored_root, exist_ok=True)
git_dir = os.path.join(restored_root, ".git")
os.makedirs(git_dir, exist_ok=True)

# Decrypt objects
obj_dir_enc = os.path.join(repo_root_enc, "1552530D16021B") # objects
for d in os.listdir(obj_dir_enc):
    dp_enc = os.path.join(obj_dir_enc, d)
    if not os.path.isdir(dp_enc): continue
    d_raw = bytes.fromhex(d)
    # The dir names are only 1 byte (2 hex chars) usually? 
    # Git objects are in dirs named with the first 2 chars of SHA.
    # So d_raw is 1 byte.
    d_dec_raw = decrypt(d_raw, key_final)
    d_dec = d_dec_raw.decode('ascii', errors='ignore')[:2]
    # For git, directories are exactly 2 chars.
    if len(d_dec) < 2: d_dec = d_dec.zfill(2)
    dp_dec = os.path.join(git_dir, "objects", d_dec)
    os.makedirs(dp_dec, exist_ok=True)
    for f in os.listdir(dp_enc):
        fp_enc = os.path.join(dp_enc, f)
        if len(f) <= 40: continue # Skip red-herrings
        f_raw = bytes.fromhex(f)
        # Decrypt filenames. Filenames are XORed starting from the beginning.
        # However, the key index depends on the offset in the logical filesystem?
        # No, the xor tool usually starts the key at 0 for each file.
        f_dec = decrypt(f_raw, key_final).decode('ascii', errors='ignore')
        # Sanitization: git filenames are 38 chars of hex
        f_dec_clean = "".join([c for c in f_dec if c in "0123456789abcdef"])[:38]
        if len(f_dec_clean) < 38: continue
        fp_dec = os.path.join(dp_dec, f_dec_clean)
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

# Decrypt refs/heads and refs/tags
# We know they contain 'master', 'stash', 'red-herring'
refs_dir_enc = os.path.join(repo_root_enc, "08555F1B")
for root, dirs, files in os.walk(refs_dir_enc):
    for fn in files:
        if len(fn) < 8: continue
        fp_enc = os.path.join(root, fn)
        fb = bytes.fromhex(fn)
        fn_dec = decrypt(fb, key_final).decode('ascii', errors='ignore')
        # Clean up fn_dec (it might have trash at the end)
        fn_dec_clean = "".join([c for c in fn_dec if c.isalnum() or c in "._-/"])
        
        rel = os.path.relpath(root, refs_dir_enc)
        # Decrypt relative path if it's hex
        if rel != ".":
            try:
                rb = bytes.fromhex(rel)
                rel_dec = decrypt(rb, key_final).decode('ascii', errors='ignore')
            except: rel_dec = rel
        else: rel_dec = ""
        
        fp_dec = os.path.join(git_dir, "refs", rel_dec, fn_dec_clean)
        os.makedirs(os.path.dirname(fp_dec), exist_ok=True)
        with open(fp_enc, "rb") as fe:
            c_enc = fe.read()
            with open(fp_dec, "wb") as fd:
                fd.write(decrypt(c_enc, key_final))

print("Repository restored in restored_repo_final")
