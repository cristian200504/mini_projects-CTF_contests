"""
Step 3: invert `encode_msg_to_ruleset` (from the pasted encoder script) given
the fully-recovered 256-entry ruleset permutation, to get back the original
message bytes.

Forward direction (in the challenge's encoder):
    msg_num = int.from_bytes(msg.encode(), 'big')
    factoradic[i] = digit for place value i!  (extracted low-to-high via
                    repeated divmod by i+1, i = 0..255), then reversed
    l = list(range(256))
    for skip_count in factoradic:               # now high-to-low order
        ruleset.append(l.pop(skip_count))        # classic Lehmer-code -> permutation

Inverse (this script):
    for each ruleset[j], find its index in the shrinking list l -> that index
    is the original skip_count/digit. Undo the .reverse(), then sum
    digit[i] * i! to rebuild msg_num, then bytes -> utf-8.

Usage: run from this directory after solve.py -> prints the recovered message
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

with open(os.path.join(DATA_DIR, "mapping.json")) as f:
    mapping = json.load(f)

ruleset = [None] * 256
for k, v in mapping.items():
    ruleset[int(k)] = v

assert all(v is not None for v in ruleset), "incomplete ruleset recovered"
assert sorted(ruleset) == list(range(256)), "ruleset is not a valid permutation"

l = list(range(256))
digits = []
for val in ruleset:
    idx = l.index(val)
    digits.append(idx)
    l.pop(idx)

fac_orig = list(reversed(digits))  # undo the encoder's factoradic.reverse()

msg_num = 0
fact = 1
for i in range(256):
    msg_num += fac_orig[i] * fact
    fact *= (i + 1)

nbytes = (msg_num.bit_length() + 7) // 8 if msg_num else 0
msg_bytes = msg_num.to_bytes(nbytes, "big")

print("recovered bytes:", len(msg_bytes))
message = msg_bytes.decode("utf-8")
print("message:")
print(message)
