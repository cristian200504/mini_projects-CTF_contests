#!/usr/bin/env python3

target = [
    204, 229, 231, 215, 210, 221, 233, 237, 231, 227, 220, 215,
    215, 213, 198, 210, 232, 226, 204, 212, 227, 229, 224, 215,
    210, 215, 210, 200, 215, 205, 209, 215, 219, 219, 215, 229,
    216, 226
]

prev = 90
flag = []

for val in target:
    c = (val - prev) % 256
    flag.append(c)
    prev = c

flag_str = bytes(flag).decode('utf-8')
print("Flag:", flag_str)
