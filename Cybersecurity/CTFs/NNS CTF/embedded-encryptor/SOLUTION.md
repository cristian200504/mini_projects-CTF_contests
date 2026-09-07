# Embedded Encryptor — solution

## Flag

```
NNS{1e4k_by_pwr}
```

## Overview

The source code contains an AES-128-CBC encryptor and an `output.txt` file
containing its ciphertext.  The key in `main.c` is a decoy:

```c
const uint8_t flag[AES_BLOCKLEN] = "NNS{faake_flaag}";
```

The real secret is recoverable from `embedded_encryptor.jls`, a Joulescope
power trace.  The trace contains 652 executions of the same software AES
routine, one for each 16-byte block of the Hávamál plaintext.

## Preparing known inputs

For CBC encryption, the first AES input is `P[0] xor IV`; for every later
block it is `P[i] xor C[i - 1]`.  The plaintext is the `havamal` string in
the supplied source and `C` is parsed from `output.txt`.  This gives the
input byte to the first AES round for every captured encryption except that
the first block's IV is not needed for the attack.

The active AES regions in the one-megahertz power signal occur every roughly
13.4 ms.  Extracting their rising edges produces 652 aligned traces.

## Correlation power analysis

The implementation uses a table-based S-box.  For each key-byte guess `k`
and known AES input byte `x`, calculate the Hamming-weight leakage model:

```
HW(SBOX[x xor k])
```

Correlating each of the 256 models with every sample point of the aligned
power traces reveals the printable key layout:

```
NNS{1e??_by_pwr}
```

The two middle bytes are the closest candidates, so they should not be
chosen solely from the largest noisy correlation peak.

## Verifying the ambiguous bytes

CBC block 1 has a fully known AES input, independent of the IV:

```
X1 = P1 xor C0
C1 = AES_encrypt(K, X1)
```

Enumerate the two printable unknown bytes in `NNS{1e??_by_pwr}` and encrypt
`X1` with each candidate.  Only one key reproduces the supplied second
ciphertext block:

```
NNS{1e4k_by_pwr}
```

For example, the verification can be performed with PyCryptodome:

```python
from Crypto.Cipher import AES

candidate = b"NNS{1e4k_by_pwr}"
assert AES.new(candidate, AES.MODE_ECB).encrypt(P1_xor_C0) == C1
```

The recovered AES-128 key is therefore also the flag.
