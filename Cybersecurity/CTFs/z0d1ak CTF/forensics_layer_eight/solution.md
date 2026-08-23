# Forensics Layer Eight - Solution Guide

## Overview

**Flag:** `zdk{whL7e0UT_lAYers_s711l_reMEMber_53CRe7S}`

The challenge is focused on Docker/OCI image forensics, specifically around the way container images handle deleted files. When a file is created in one layer and deleted in a subsequent layer, it is simply marked as deleted in the new layer. The original file still exists in the image and can be extracted if we break down the layers manually.

## Step-by-Step Solution

### 1. Investigating the Image
The challenge provides an OCI image tarball (`app-image.tar`). Our first step is to unpack it:
```bash
mkdir image_extract
tar -xf app-image.tar -C image_extract/
```

Inspecting the configuration file (`blobs/sha256/5f6db9b4...`) reveals several intriguing labels stored under `config.Labels`:
```json
"com.nimbusnotes.provenance.layout": "c,a,b",
"com.nimbusnotes.provenance.part-a": "VZ5MaluN8tzx4YMgh5t7H7kXOSdNBFAK",
"com.nimbusnotes.provenance.part-b": "O7f31BRPFt4DcSf344xWO/2EiCKmMWhA",
"com.nimbusnotes.provenance.part-c": "AU5pbWJ1c05vdGVzIUHvlVyex7p2cVqI",
"com.nimbusnotes.provenance.step": "sha256:25df7c6f6beec6e2eef55ec64cfa91125098d4adc1cf327f5897bfc6642383d8"
```
The history array inside the same configuration file reveals that the build process involved managing secrets and running scripts, which were eventually deleted to "clean up":
```bash
rm -f /app/.secrets/deploy_key /app/scripts/postinstall.sh /usr/lib/nimbus/provenance.py
```

### 2. Extracting Layer Secrets
Because the files were deleted via a simple `rm` command, they are still present in older layers. We can find which layer contains them by inspecting the blob layer archives (`blobs/sha256/`).
By unpacking the layers, we find the following deleted files:

1. **/app/.secrets/deploy_key**:
   ```
   -----BEGIN NIMBUS DEPLOY KEY-----
   nk_live_8f2c1ad0e94b47c6b3d5a071f6e2c9184a7d0b3e5c9f21764e8a0d2b6c4f19a3
   -----END NIMBUS DEPLOY KEY-----
   ```

2. **/usr/lib/nimbus/provenance.py**:
   This script reveals how the data in the labels was encrypted and assembled:
   ```python
   key_bytes = open('/app/.secrets/deploy_key','rb').read()
   step = os.environ['NIMBUS_STEP_DIGEST']
   k = hashlib.sha256(key_bytes + bytes.fromhex(step.split(':',1)[1])).digest()
   aad = ('nimbusnotes:1.4.2|' + step).encode()
   # envelope v1: version || nonce[12] || ciphertext || tag[16]
   # the registry adapter shards base64(envelope) across provenance labels
   ```

### 3. Decrypting the Payload
The python script shows us that AES-GCM is used to encrypt the payload. The key is derived by hashing the bytes of `deploy_key` and the `step` digest (which we found in the labels). 

The ciphertext payload (the envelope) can be reconstructed from the image labels based on the `layout` label (`c,a,b`).

We can write a decryption script using `pycryptodome` to retrieve the flag:

```python
import base64, hashlib
from Crypto.Cipher import AES

# Recovered from the older layer
key_bytes = b"-----BEGIN NIMBUS DEPLOY KEY-----\nnk_live_8f2c1ad0e94b47c6b3d5a071f6e2c9184a7d0b3e5c9f21764e8a0d2b6c4f19a3\n-----END NIMBUS DEPLOY KEY-----\n"

# From the com.nimbusnotes.provenance.step label
step = "sha256:25df7c6f6beec6e2eef55ec64cfa91125098d4adc1cf327f5897bfc6642383d8"

k = hashlib.sha256(key_bytes + bytes.fromhex(step.split(':',1)[1])).digest()
aad = ('nimbusnotes:1.4.2|' + step).encode()

# Reconstruct base64 envelope in c,a,b layout format
part_c = "AU5pbWJ1c05vdGVzIUHvlVyex7p2cVqI"
part_a = "VZ5MaluN8tzx4YMgh5t7H7kXOSdNBFAK"
part_b = "O7f31BRPFt4DcSf344xWO/2EiCKmMWhA"
b64_env = part_c + part_a + part_b

env = base64.b64decode(b64_env)

# Envelope mapping: version[1] || nonce[12] || ciphertext || tag[16]
nonce = env[1:13]
tag = env[-16:]
ciphertext = env[13:-16]

cipher = AES.new(k, AES.MODE_GCM, nonce=nonce)
cipher.update(aad)

plaintext = cipher.decrypt_and_verify(ciphertext, tag)
print(plaintext.decode('utf-8'))
```

Running this script yields the flag: `zdk{whL7e0UT_lAYers_s711l_reMEMber_53CRe7S}`.
