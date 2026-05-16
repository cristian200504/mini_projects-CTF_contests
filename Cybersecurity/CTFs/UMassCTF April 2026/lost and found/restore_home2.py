import os
import re

def xor_bytes(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

key = b'z09huvhu33i3bbuvuxzciohzcxviho3wryyudsfyuzcvxhyuhyuwrhyufdsuhhyuzvxcijlfkdasjknvoxzcihuwefij'
source_dir = r"C:\Users\crist\OneDrive\Desktop\lost and found\extract\forensics\home_files\home"
dest_dir = r"C:\Users\crist\OneDrive\Desktop\lost and found\decrypted_home2"

def sanitize_win_path(name):
    # allow alphanumeric, space, dot, dash, underscore
    return re.sub(r'[^A-Za-z0-9.\-_ ]', '_', name)

def process_dir(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)
    
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        
        # decrypt name
        try:
            name_bytes = bytes.fromhex(item)
            decrypted_name = xor_bytes(name_bytes, key).decode('utf-8', errors='ignore')
        except:
            decrypted_name = item # copy as is if not hex
            
        decrypted_name = sanitize_win_path(decrypted_name)
        dst_path = os.path.join(dst, decrypted_name)
        
        if os.path.isdir(src_path):
            process_dir(src_path, dst_path)
        else:
            with open(src_path, 'rb') as f:
                content = f.read()
            decrypted_content = xor_bytes(content, key)
            with open(dst_path, 'wb') as f:
                f.write(decrypted_content)

process_dir(source_dir, dest_dir)
print("Decryption complete.")
