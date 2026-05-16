# Father and Sons - CTF Write-up

## Challenge Overview
- **Name**: Father and Sons
- **Category**: Cryptography / Blockchain
- **Points**: 500
- **Difficulty**: Hard

## Description
The challenge provides a captured list of public keys (`keys.csv`) and some cryptic instructions in `exercise.txt`:

> We captured a bunch of public keys that are owned by some bad dudes but it seems that there are invalid ones among them. One of our sources told us that the keys we are looking for have been derived using unhardened BIP32 derivation, using the SECP256k1 curve and the hexadecimal string "c0ffee" as seed. He also said that the path (the classic "m/[number]") may be very important.
>
> Flag format : HACKDAY{sha256}

## Analysis

### 1. BIP32 & HD Wallets
BIP32 (Bitcoin Improvement Proposal 32) defines Hierarchical Deterministic (HD) wallets. These wallets allow deriving a tree of keys from a single seed.
- **Seed**: The starting point for all derivations (in this case, `c0ffee`).
- **Path**: A sequence of indices used to navigate the tree (e.g., `m/0/1`).
- **Unhardened Derivation**: Allows deriving child public keys from a parent public key without needing the parent private key. The path format for unhardened indices is `m/i` (where `i` is an integer).

### 2. Clues & Data
- **Seed**: `c0ffee` (hex).
- **Curve**: `SECP256k1` (Standard for Bitcoin).
- **Path**: `m/[number]`.
- **`keys.csv`**: Contains rows of `string,pubkey`. There are many keys, but only some are "valid" (derived from the seed).

### 3. The Flag Reconstitution
The `keys.csv` entries pair a long string with a public key. The challenge implies that the "valid" keys (those derived from the seed `c0ffee` at path `m/0`, `m/1`, etc.) hold pieces of the flag. Specifically, if the key at index `i` (path `m/i`) matches a key in the CSV, the character at index `i` of the associated string is a part of the flag.

## Solution Strategy

1.  **Initialize BIP32**: Use the seed `c0ffee` to create a master key.
2.  **Iterate Derivations**:
    - For `i` from 0 upwards (until the flag is complete):
    - Derive the child public key at path `m/i`.
    - Check if this public key exists in the provided `keys.csv`.
3.  **Reconstruct Flag**:
    - If found, extract the character at position `i` from the string associated with that key.
    - Concatenate these characters to build the flag.

## Solver Script

```python
from bip32 import BIP32
import csv

# Load the captured keys
pubkeys_dict = {}
with open('keys.csv', mode='r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pubkeys_dict[row['pubkey']] = row['string']

# Initialize BIP32 with the hex seed "c0ffee"
seed = bytes.fromhex("c0ffee")
bip32 = BIP32.from_seed(seed)

# Derive keys over path m/i and construct the flag
flag = ""
# Based on the data, we iterate through indices
for i in range(100): # Sufficient range to find the closing brace
    # Unhardened derivation: path m/i
    derived_pubkey = bip32.get_pubkey_from_path([i]).hex()
    
    # If the valid pubkey exists in our captured list, extract the i-th character
    if derived_pubkey in pubkeys_dict:
        associated_string = pubkeys_dict[derived_pubkey]
        if i < len(associated_string):
            flag += associated_string[i]
            # Stop if we find the closing brace
            if associated_string[i] == '}':
                break
    else:
        # If an index is missing, add a placeholder (or skip)
        flag += "?"

print(f"Recovered Flag: {flag}")
```

## Flag
The script recovers the following flag:

**`HACKDAY{e6e85c3e1c626ca6c04a9a994682b2fd2336a5f0e7522bc660cf12ccffdd75af}`**
