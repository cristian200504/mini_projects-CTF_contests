import os, zlib

# The commit object 55a10e0874b6d37a8b9c2d70468d91f5b8c78cf5 is 214 bytes.
# We know it starts with 'commit '
# We know it probably has a tree and a parent.

keylong_guess = b'z09huvhu33i3bbuvuxzciohzcxviho3wryyudsfyuzcvxhyuhyuwrhyufdsuhhyuzvxcijlfkdasjknvoxzcihuwefij'

fpath = r'C:\Users\crist\OneDrive\Desktop\lost and found\extract\forensics\home_files\home\5457501C\1552530D16021B\4F05\1B01090D454E5F4151050D0055034D144C1B48075E5F5C4C5B1C4F580E5A514F114E41160246'
with open(fpath, 'rb') as f:
    raw = f.read()

# Try to find the key by guessing the plaintext
# A commit starts with 'commit '
# Let's try to decompress and see where it fails, then guess more.

def try_decode(data, key):
    dec = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    d = zlib.decompressobj()
    try:
        res = d.decompress(dec)
        return res, None
    except Exception as e:
        return d.unconsumed_tail, e

# We already saw: Partial decode (308 bytes): b'commit 291\x00tree 6764da9116f608795b2a2e27695ec314b7e9e9ac\nparent 8fadc480\x00dr...'
# Wait, 308 bytes? The file only 214 bytes. Oh, zlib expansion.
# 'commit 291\x00tree 6764da9116f608795b2a2e27695ec314b7e9e9ac\nparent 8fadc480'
# 11 bytes + 5+40+1 = 46 bytes = 57 bytes.
# 'parent ' + 40 bytes = 47 bytes. Total 104 bytes.
# After parent 8fadc480 (8 chars), it became '\x00dr'.
# So at index 57+7+8 = 72 of the UNCOMPRESSED data, it's garbled.

# Wait! The key is applied to the COMPRESSED data.
# Each compressed byte corresponds to some uncompressed bytes.
# If the key is wrong at some compressed index, the decompression will fail or produce garbage.

# Let's find the key index that corresponds to the start of the garbled data.
# In the previous run, it said 'Result so far: b'''.
# Let's try to get the partial result again more carefully.

d = zlib.decompressobj()
dec = bytes([raw[i] ^ keylong_guess[i % len(keylong_guess)] for i in range(len(raw))])
result = b''
for i in range(len(dec)):
    try:
        new_data = d.decompress(dec[i:i+1])
        if new_data:
            result += new_data
    except:
        print(f"Decompression failed at compressed byte {i}")
        break

print(f"Result so far: {result}")
print(f"Last successful compressed index: {i-1}")
