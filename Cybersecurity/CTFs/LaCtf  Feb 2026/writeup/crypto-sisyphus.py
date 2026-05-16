#!/usr/bin/env python3
# Install dependencies: pip install pwntools pycryptodome

from pwn import *
from Crypto.Cipher import AES
import re

# Set up context
context.log_level = 'debug'

# Connect to the server
conn = remote('chall.lac.tf', 31182)

# Read initial prompt
conn.recvuntil(b"decide your fate: ")

# Send our choice (0)
# This corresponds to Input 1 = 0
conn.sendline(b"0")

# Receive all output until the next prompt
# This ensures we get the wire labels, table, and IV
output = conn.recvuntil(b"Show me the output, and I will believe the rock has made it up the mountain: ").decode()
lines = output.split('\n')

# Parse Wire Labels
# Expected format: "wire 0: <key> <ptr>"
wire0_line = [l for l in lines if 'wire 0:' in l][0]
wire1_line = [l for l in lines if 'wire 1:' in l][0]

def parse_wire(line):
    parts = line.strip().split()
    key_hex = parts[2]
    ptr = int(parts[3])
    return bytes.fromhex(key_hex), ptr

keyA, ptrA = parse_wire(wire0_line)
keyB, ptrB = parse_wire(wire1_line)

print(f"KeyA: {keyA.hex()}, PtrA: {ptrA}")
print(f"KeyB: {keyB.hex()}, PtrB: {ptrB}")

# Parse Table
# The server prints 3 rows corresponding to indices (0,1), (1,0), (1,1)
# Format is simple hex bytes then a space and integer
table_lines = [l for l in lines if re.match(r'^[0-9a-f]{32} [0-1]$', l.strip())]

if len(table_lines) != 3:
    print("Error parsing table lines")
    print(lines)
    exit()

def parse_row(line):
    parts = line.strip().split()
    return bytes.fromhex(parts[0])

# Store table in a dictionary keyed by (ptrA_idx, ptrB_idx)
# The server prints rows for (0, 1), (1, 0), (1, 1) in that order
table = {}
table[(0, 1)] = parse_row(table_lines[0])
table[(1, 0)] = parse_row(table_lines[1])
table[(1, 1)] = parse_row(table_lines[2])
# table[(0, 0)] corresponds to encrypting zeros, so no table entry.

# Parse IV
# Look for line starting with "iv: "
iv_line = [l for l in lines if 'iv: ' in l][0]
iv_hex = iv_line.split('iv: ')[1].strip()
iv = bytes.fromhex(iv_hex)
print(f"IV: {iv.hex()}")

# Helper to compute stream for a key
def get_stream(key, iv):
    # AES-CTR stream generation
    aes = AES.new(key, AES.MODE_CTR, nonce=iv)
    return aes.encrypt(bytes(16))

streamA = get_stream(keyA, iv) # KeyA is L0_0
streamB = get_stream(keyB, iv) # KeyB is L1_0

# Logic to find L_out_1
# We have L0_0 (KeyA) and L1_0 (KeyB).
# Active Row Index: (ptrA, ptrB)

# Step 1: Find L_out_0 (Value 0 output key)
# Corresponds to input (0,0) -> 0
if (ptrA, ptrB) == (0, 0):
    # Direct computation: L_out_0 = StreamA ^ StreamB
    l_out_0 = xor(streamA, streamB)
else:
    # Decrypt the table entry for (ptrA, ptrB)
    # Ciphertext = L_out_0 ^ StreamA ^ StreamB
    # L_out_0 = Ciphertext ^ StreamA ^ StreamB
    row_ctxt = table[(ptrA, ptrB)]
    l_out_0 = xor(row_ctxt, streamA, streamB)

print(f"L_out_0: {l_out_0.hex()}")

# Step 2: Find Stream(KeyB_not) - Key for input B=1
# Use Cross Row 1: (ptrA, ptrB ^ 1)
# Input A=0, B=1 -> Output 0
# Ciphertext = L_out_0 ^ StreamA ^ Stream(KeyB_not)
idx_cross1 = (ptrA, ptrB ^ 1)
if idx_cross1 == (0, 0):
    # Implies table entry was skipped, meaning L_out_0 = StreamA ^ Stream(KeyB_not)
    streamB_not = xor(l_out_0, streamA)
else:
    streamB_not = xor(table[idx_cross1], l_out_0, streamA)

# Step 3: Find Stream(KeyA_not) - Key for input A=1
# Use Cross Row 2: (ptrA ^ 1, ptrB)
# Input A=1, B=0 -> Output 0
# Ciphertext = L_out_0 ^ Stream(KeyA_not) ^ StreamB
idx_cross2 = (ptrA ^ 1, ptrB)
if idx_cross2 == (0, 0):
    streamA_not = xor(l_out_0, streamB)
else:
    streamA_not = xor(table[idx_cross2], l_out_0, streamB)

# Step 4: Find L_out_1 (Value 1 output key)
# Use Target Row: (ptrA ^ 1, ptrB ^ 1)
# Input A=1, B=1 -> Output 1
# Ciphertext = L_out_1 ^ Stream(KeyA_not) ^ Stream(KeyB_not)
idx_target = (ptrA ^ 1, ptrB ^ 1)
if idx_target == (0, 0):
    l_out_1 = xor(streamA_not, streamB_not)
else:
    l_out_1 = xor(table[idx_target], streamA_not, streamB_not)

print(f"L_out_1: {l_out_1.hex()}")

# Send answer
print("Sending answer...")
conn.sendline(l_out_1.hex().encode())

# Capture flag
flag = conn.recvall().decode()
print("\n[+] Flag Output:")
print(flag)
conn.close()
