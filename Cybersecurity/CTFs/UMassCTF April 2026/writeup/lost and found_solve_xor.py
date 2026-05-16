import os

def xor_bytes(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

key = b"z09huvhu33i"
target_dir = r"C:\Users\crist\OneDrive\Desktop\lost and found\extract\forensics\home_files"

for root, dirs, files in os.walk(target_dir):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                decrypted = xor_bytes(content, key)
                if b"UMASS{" in decrypted:
                    print(f"Found in {file_path}")
                    print(f"Decrypted: {decrypted}")
                # Also check if the filename itself is the flag
                # Filename is in hex
                try:
                    name_bytes = bytes.fromhex(file)
                    decrypted_name = xor_bytes(name_bytes, key)
                    if b"UMASS{" in decrypted_name:
                        print(f"Flag found in filename: {file}")
                        print(f"Decrypted filename: {decrypted_name}")
                except:
                    pass
        except Exception as e:
            pass

print("Search complete.")
