# Blowfish — solve

Flag: `K17{great_work_infiltrating_as_the_head_fish_perhaps_one_could_call_you_james_pond}`

## Vulnerability

The service signs each 8-byte block independently with `SHA256(signing_key || block)`. The tag does not bind a block to its position, neighbours, or role as IV, plaintext, or ciphertext, so any known block/tag pair can be replayed.

The initial fish has about 150 signed blocks. Encrypting it through option 1 returns signed CBC ciphertext blocks `C_i`. Because the original plaintext block `P_i` is known, this reveals the AES/Blowfish decrypt intermediate value:

```text
D_K(C_i) = P_i XOR C_(i-1)
```

The resulting random-looking 64-bit values span GF(2)^64.

## Turning the decryption endpoint into a tag oracle

Let `current` be any block with a valid tag. Submit this signed three-block ciphertext to option 2:

```text
current || C_i || C_j
```

The second signed output block is `D_K(C_i) XOR current`. Thus it produces a valid tag for a new value. Choose `C_j` so its output's final byte is nonzero; this keeps `unpad()` from stripping the useful result.

Starting with the signed initial IV as `current`, solve a GF(2) system to select `D_K(C_i)` values whose XOR equals:

```text
current XOR b": true }"
```

Apply a signed decryption transition for every selected value. The final `current` is `b": true }"` and carries a valid tag.

## Final payload

The initial fish already has a signed `b'{"admin"'` block. Combine it with the forged one:

```python
payload = initial_iv + b'{"admin"' + b': true }'
signature = tag(initial_iv) + tag(b'{"admin"') + forged_tag(b': true }')
```

After removing the IV, the payload is valid JSON:

```json
{"admin": true }
```

The strict `is True` test passes before option 1 attempts encryption.

## Run

```powershell
python .\solve.py
```

The included solver performs the initial encryption, basis construction, signed CBC transitions, and final submission.
