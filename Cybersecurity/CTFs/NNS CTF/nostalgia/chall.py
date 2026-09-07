from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256
import time

def lcg(s):
	return (16843009*int(s)+826366247)%(2**32)

seed = time.time() # nanosecond precision, you will never find the seed muahahaha

for _ in range(1337):
	seed = lcg(seed)

key = sha256(str(seed).encode()).digest()
flag = b"NNS{???????????????????????????????}"
ct = AES.new(key, AES.MODE_ECB).encrypt(pad(flag, AES.block_size)).hex()
print(f"ct = '{ct}'")
# ct = '85c43735b8442a69843bdc2ca0fb2d41eb548057c43b912704abdf2e27a8d8bc97017ec30b5d100498f12183c9e2ebed'
