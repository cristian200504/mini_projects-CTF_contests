import os, zlib

repo_path = r"C:\Users\crist\OneDrive\Desktop\lost and found\restored_repo\.git\objects"

commits = []
for root, dirs, files in os.walk(repo_path):
    for f in files:
        sha = os.path.basename(root) + f
        fpath = os.path.join(root, f)
        try:
            with open(fpath, "rb") as fh:
                raw = fh.read()
                # Git objects are zlib compressed
                # But wait, my solve_ctf.py decrypted them.
                # If decryption is correct, they are just zlib streams.
                data = zlib.decompress(raw)
                if data.startswith(b"commit"):
                    print(f"Commit {sha}:")
                    print(data.decode('ascii', errors='ignore'))
                    print("-" * 20)
        except:
            pass
