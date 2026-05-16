# Paste directly what you copied from Discord between the triple quotes

weird_flag = """BITSCTF​​​‌‍‬​​​‌‬‬​​​‌⁣​​​​‌⁢﻿​​​‌‍⁢{​​​‌⁣​​​​‌‬​​​​‍‬⁢​​​‍‌⁢​​​‌​‬​​​‍‌‍​​​‌​‍​​​‌﻿⁢​​​‌​⁢​​​‍‍⁣​​​‍‍‍​​​‌​‍​​​‌﻿⁢​​​‍‬‍​​​​﻿﻿your_​​​‍‍⁣​​​‌﻿⁢​​​‍‍‍​​​‌​‍​​​‌​‬​​​‍​‍​​​‌﻿⁢​​​‌​‍​​​‍‍﻿​​​‌​‍​​​‍‍‍​​​‍‬‍​​​‌​﻿​​​‍​﻿​​​‌​​​​​‍‌⁣​​​‍​⁣​​​‌﻿⁢​​​‍​‌flag​​​‌​‬​​​‍‍‍​​​‌​‍​​​‍​⁢​​​‍‍⁣​​​‍‌‬​​​‍‌‬​​​‍‬‍​​​‍‬﻿_goes_here}"""

# Proper base-7 zero-width decoder

alphabet = [
    '\u200b',
    '\u200c',
    '\u200d',
    '\u202c',
    '\u2062',
    '\u2063',
    '\ufeff'
]

# Extract only these
digits = [alphabet.index(c) for c in weird_flag if c in alphabet]

print("Digit count:", len(digits))

decoded_bytes = bytearray()

# 3 base-7 digits -> 1 byte
for i in range(0, len(digits), 3):
    chunk = digits[i:i+3]
    if len(chunk) == 3:
        value = chunk[0]*49 + chunk[1]*7 + chunk[2]  # base7
        decoded_bytes.append(value % 256)

print("Decoded (utf8 attempt):")
try:
    print(decoded_bytes.decode("utf-8"))
except:
    print(decoded_bytes)