# monoid — solve

## Challenge

We're given three files:

- `Main.dump-simpl` / `Main.dump-asm` — GHC Core/asm dumps (`-ddump-simpl` / `-ddump-asm`) of a Haskell program with three modules: `Decode`, `Fractal`, `Main`.
- `out.txt` — ASCII-art render of a Julia set fractal.
- `description.txt` — hints that the fractal's parameters were encrypted.

No source `.hs` files are provided, so the logic has to be reconstructed from the GHC Core dump in `Main.dump-simpl`.

## Reconstructing the decode pipeline

### `Decode` module

```haskell
xorChar :: Char -> Char -> Char
xorChar a b = chr (xor (ord a) (ord b))

unsubsChar :: Char -> Char
unsubsChar a = chr ((ord a - 67) `mod` 128)

decipher :: String -> String -> String
decipher ct key
  | null key  = error "boop"
  | otherwise = zipWith (\c k -> unsubsChar (xorChar k c)) ct (cycle key)

fromHex :: String -> String   -- pairs up hex digits, readHex's each pair, chr's the result
```

So `decipher ct key` walks the ciphertext byte-by-byte against a repeating key, XORs, then undoes a Caesar-style shift of 67 mod 128.

### `Main` module

```haskell
main = writeFile "out.txt" $
  (\(cx, cy, maxIter, w, h) -> renderJulia cx cy maxIter w h) $
  case words (decipher (fromHex hexBlob) "#!s3kur1ty") of
    (_ : real : imag : maxIter : width : height : []) ->
      (read real, read imag, read maxIter, read width, read height)
    _ -> error ""
```

Key detail: `words` splits the decoded plaintext into tokens, and the **first token is discarded** (bound to `_`, marked `Occ=Dead` in Core) — only tokens 2–6 are used as `(cx, cy, maxIter, width, height)`. That first, unused token is where the flag lives.

### `Fractal` module

`renderJulia cx cy maxIter width height` iterates `z -> z^2 + c` (with `c = cx :+ cy`) over a `width x height` grid mapped to `[-1.8, 1.8] x [-1.0, 1.0]`, and indexes into the palette `" .-:=+*#%@"` by escape iteration count — a standard Julia-set ASCII renderer. This confirms `out.txt` (96 columns x 32 rows) is the rendered output once the params are decoded.

## Extracting the flag

The embedded hex blob:

```
2d55090d4f576242655d24030705490250210748502d54111f4450065f0f010704041d5f6024485b500851457a5201384c68255b000613351141070859560b4a1c03094a0e1a505007471d0e0749080a5442074818160e48170f56
```

Reversing the pipeline (hex-decode -> XOR with repeating key `"#!s3kur1ty"` -> `(byte - 67) mod 128`):

```python
hexstr = "2d55090d4f576242655d24030705490250210748502d54111f4450065f0f010704041d5f6024485b500851457a5201384c68255b000613351141070859560b4a1c03094a0e1a505007471d0e0749080a5442074818160e48170f56"
ct = bytes.fromhex(hexstr)
key = "#!s3kur1ty"

result = []
for i, c in enumerate(ct):
    k = key[i % len(key)]
    x = ord(k) ^ c            # xorChar
    u = (x - 67) % 128        # unsubsChar
    result.append(chr(u))

print(''.join(result))
```

Output:

```
K17{a_M0NaD_1s_4_M0n0Id_1n_th3_c4t3gORy_0f_3Nd0FuNC70r5} -0.745643887 0.113825904 180 96 32
```

Splitting on whitespace: the first word is the flag (discarded by `main`), and the remaining five words are `(cx, cy, maxIter, width, height) = (-0.745643887, 0.113825904, 180, 96, 32)` — which line up with the 96x32 fractal in `out.txt`, confirming the decode.

## Flag

```
K17{a_M0NaD_1s_4_M0n0Id_1n_th3_c4t3gORy_0f_3Nd0FuNC70r5}
```
