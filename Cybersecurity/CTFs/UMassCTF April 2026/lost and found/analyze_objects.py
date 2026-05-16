import os, zlib

keylong = b'z09huvhu33i3bbuvuxzciohzcxviho3wryyudsfyuzcvxhyuhyuwrhyufdsuhhyuzvxcijlfkdasjknvoxzcihuwefij'
base = r'C:\Users\crist\OneDrive\Desktop\lost and found\extract\forensics\home_files\home\5457501C\1552530D16021B'

def xor_bytes(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

# Read 8fadc480 commit object
fpath = os.path.join(base, '4256', '1B545A5C4D46094D55005857500614154448435A0A090A18534B17510A095142161C4C435D15')
with open(fpath, 'rb') as f:
    raw = f.read()

dec = xor_bytes(raw, keylong)
print('First 4 bytes of 8fadc480 decrypted:', dec[:4].hex(), dec[:4])
print()

for i in range(20):
    c = chr(dec[i]) if 32<=dec[i]<127 else '?'
    print(f'byte {i}: raw={raw[i]:02x} xordec={dec[i]:02x}={c}')

print()
print('Trying zlib decompress on raw:')
try:
    obj = zlib.decompress(raw)
    print('RAW decompress OK:', obj[:100])
except Exception as e:
    print('RAW decompress failed:', e)

# Maybe the content is not XOR encrypted at all? Maybe just the filenames are?
print()
print('Checking if raw bytes are a valid zlib stream:')
print('First 2 bytes:', hex(raw[0]), hex(raw[1]))
# zlib magic: 0x78 0x01, 0x78 0x9C, 0x78 0xDA
