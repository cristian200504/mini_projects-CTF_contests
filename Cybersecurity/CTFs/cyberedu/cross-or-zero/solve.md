saw this code

```
import itertools
import base64

def string_xor(s, key):
    key = key * (len(s) / len(key) + 1)
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in itertools.izip(s, key)) 

flag = ""
key = ""

print base64.b64encode(string_xor(flag, key))

# dHNkdktTAVUHAABUA1VWVgIHBAlSBAFTBAMFUwECAgcAAAFWAFUFCFMACFFUAwQAVgBSBwQJBVZTAFYGCQYHVQABB1IJTQ==
```
and reversed it

```
import base64

enc64 = "dHNkdktTAVUHAABUA1VWVgIHBAlSBAFTBAMFUwECAgcAAAFWAFUFCFMACFFUAwQAVgBSBwQJBVZTAFYGCQYHVQABB1IJTQ=="
key = 0x30 
decoded_bytes = base64.b64decode(enc64)
flag = ''.join(chr(b ^ key) for b in decoded_bytes)

print("Decoded Flag:", flag)
```

and got the flag:
**DCTF{c1e700d3eff2749b41c435c1227001f0e58c08ad340f0b7495fc0f6967e017b9}**