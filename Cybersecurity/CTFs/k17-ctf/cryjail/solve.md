# Cryjail — solve

## Bug

The challenge decrypts AES-CBC input and interpolates the result into a Python bytes literal. Bytes outside printable ASCII are escaped, but printable double quotes and backslashes are copied directly into source code.

```python
'print(b"... AS: ' + escape(name) + '!", file=devnull)\n'
```

The child process returns success or failure to the parent, creating a Python source-validity oracle.

## Recovering an AES intermediate block

Use one fixed ciphertext block `C = 00 * 16` and call its AES decrypt intermediate value `I = D_K(C)`. CBC decryption gives `P = I XOR IV`.

Recover `I` from left to right. For every recovered index `j`, set `IV[j] = I[j]`; this makes `P[j] = 0`, which `escape()` safely renders as `\\x00`.

At the next index, scan all 256 IV-byte values while keeping the suffix random. A clean scan has exactly one failure: it is the candidate that makes the raw plaintext byte a double quote, prematurely terminating the bytes literal.

```text
I[position] = failed_iv_byte XOR 0x22
```

Retry a scan unless it has exactly one failure, because a random suffix can occasionally contain another source-breaking character. The solver validates the recovered block before using it.

## Injection

Once `I` is known, choose the decrypted name directly through the IV:

```python
name = b'");breakpoint()#'
iv = I XOR name
```

This creates a source line equivalent to:

```python
print(b"IMPLANTING ... AS: "); breakpoint() # !", file=devnull)
```

The comment removes the fixed suffix. `breakpoint()` opens PDB over the same socket. The service's explicit unbuffered parent input is what lets PDB read the next line reliably.

At the PDB prompt, run:

```python
!print(open("/flag").read())
```

Landlock permits reads from `/`, and the Dockerfile places the flag at `/flag`.

## Run

Instantiate the challenge, then pass its host and port to the included solver:

```powershell
python .\solve.py HOST PORT
```

If the instantiator gave an instance password, add it as an option:

```powershell
python .\solve.py HOST PORT --password INSTANCE_PASSWORD
```

The run needs roughly 4,100 requests on one connection, so do not reconnect between oracle probes.
