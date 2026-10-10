import base64

enc64 = "dHNkdktTAVUHAABUA1VWVgIHBAlSBAFTBAMFUwECAgcAAAFWAFUFCFMACFFUAwQAVgBSBwQJBVZTAFYGCQYHVQABB1IJTQ=="
key = 0x30 
decoded_bytes = base64.b64decode(enc64)
flag = ''.join(chr(b ^ key) for b in decoded_bytes)

print("Decoded Flag:", flag)