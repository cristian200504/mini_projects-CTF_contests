# Chiral - CTF Challenge Solution

## Overview
In this challenge, we are provided with a `.mol` file (`chiral.mol`) and a hint:
> A strange chiral molecule hides a message in its backbone. Decode it from fluorine to bromine.

The molecule consists of a long backbone of 58 Carbon atoms, starting with a Fluorine (F) atom and ending with a Bromine (Br) atom. Attached to every Carbon along the backbone is an alkyl branch.

## Analysis
To extract the message, we can analyze the structural properties of the molecule from the Fluorine end to the Bromine end. Using RDKit in Python, we can find the shortest path from F to Br, which gives us the sequence of the 58 backbone Carbons.

For each Carbon on the backbone, we can observe two key properties:
1. **The size of the attached branch:** Counting the number of carbon atoms in the substituent attached to the backbone carbon (excluding the backbone itself).
2. **The stereochemistry:** Whether the chiral center is in the (R) or (S) configuration.

If we extract these two properties for all 58 backbone carbons, we notice:
- The branch sizes always range from 1 to 8.
- The stereochemistry is a mix of R and S.

## Decoding the Message
The range of the branch sizes (1 to 8) strongly hints at a 3-bit value (0 to 7) if we simply subtract 1. 
The stereochemistry (R/S) provides a binary choice, perfectly fitting the 4th bit (the most significant bit of a hex nibble). 

Thus, each backbone Carbon encodes exactly a 4-bit nibble (a hexadecimal digit):
- `Value = (Branch_Size - 1) + (8 if Stereochemistry == 'S' else 0)`

Using this logic, we extract 58 nibbles (which perfectly pairs into 29 bytes/characters):

```python
from rdkit import Chem
import binascii

mol = Chem.MolFromMolFile('chiral.mol')
Chem.AssignStereochemistry(mol, flagPossibleStereoCenters=True, force=True)

# Find start (F) and end (Br)
f_idx = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'F'][0]
br_idx = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'Br'][0]
path = Chem.GetShortestPath(mol, f_idx, br_idx)
path_set = set(path)

hex_chars = []
for idx in path:
    a = mol.GetAtomWithIdx(idx)
    if a.GetSymbol() in ('F', 'Br'): continue
    
    # Get stereochemistry
    rs = a.GetProp('_CIPCode')
    
    # Calculate branch size using BFS
    neighbors = [n.GetIdx() for n in a.GetNeighbors() if n.GetIdx() not in path_set]
    q = neighbors[:]
    visited = set(q)
    size = 0
    while q:
        curr = q.pop(0)
        size += 1
        for n in mol.GetAtomWithIdx(curr).GetNeighbors():
            n_idx = n.GetIdx()
            if n_idx not in path_set and n_idx not in visited:
                visited.add(n_idx)
                q.append(n_idx)
                
    # Calculate hex nibble
    val = (size - 1) + (8 if rs == 'S' else 0)
    hex_chars.append(hex(val)[2:])

# Decode hex string to ASCII
hex_str = ''.join(hex_chars)
flag = binascii.unhexlify(hex_str).decode()
print("Flag:", flag)
```

Running this script yields the hex string `4e4e537b63683172346c3174795f666c3170735f7468335f623174737d`, which decodes to our flag!

**`NNS{ch1r4l1ty_fl1ps_th3_b1ts}`**
