# Layered Catch — CTF Challenge Writeup

## Challenge Information
- **Name:** Layered Catch
- **Points:** 10
- **Author:** f8al
- **Description:** `Someone sent us a harmless looking image. It opens fine, shows nothing interesting, and yet it weighs more than a 64 by 64 teal square has any right to. Provided: catch.png.`
- **Flag:** `rstcon{p0lyglot_png_h1des_a_zip}`

---

## 1. Initial Reconnaissance

We are given `catch.png` (`475` bytes), which renders as a plain $64 \times 64$ solid teal square. The description hints that the file size is larger than expected for a simple single-color PNG and that the challenge involves "layers".

Inspecting the raw bytes / strings of `catch.png` reveals both PNG metadata chunks (`tEXt`) and a trailing ZIP archive appended after the PNG `IEND` chunk.

---

## 2. PNG Chunk & Polyglot Analysis

Parsing the structure of `catch.png`:

1. **PNG Header & `IHDR`:** Standard $64 \times 64$ 8-bit RGB PNG header.
2. **PNG `tEXt` Metadata Chunks:**
   - `Comment`: `decoy: the catch is layered, look past the picture`
   - `Passphrase`: `t1de_p00ls_run_deep`
3. **PNG `IDAT` & `IEND`:** The image data and end-of-image marker (`IEND\xae\x42\x60\x82`) end at byte offset `248`.
4. **Appended ZIP Archive (PNG/ZIP Polyglot):** Immediately at offset `248` (`0xF8`), a ZIP local file header (`PK\x03\x04`) begins, containing a single password-protected file named `flag.txt`.

---

## 3. Exploitation & Solution

Using the passphrase found in the PNG `tEXt` chunk (`t1de_p00ls_run_deep`), we can extract and decrypt `flag.txt` from the appended ZIP archive.

### Solver Script (`solve.py`)

```python
import io
import zipfile

with open("catch.png", "rb") as f:
    data = f.read()

# Locate the appended ZIP archive after the PNG IEND chunk
zip_offset = data.index(b"PK\x03\x04")
print(f"[+] Found embedded ZIP archive at byte offset: {zip_offset}")

# Open the embedded ZIP and decrypt flag.txt using the passphrase from the PNG tEXt chunk
with zipfile.ZipFile(io.BytesIO(data[zip_offset:])) as z:
    print("[+] ZIP contents:", z.namelist())
    flag = z.read("flag.txt", pwd=b"t1de_p00ls_run_deep").decode().strip()
    print(f"[+] Flag: {flag}")
```

### Output

```text
[+] Found embedded ZIP archive at byte offset: 248
[+] ZIP contents: ['flag.txt']
[+] Flag: rstcon{p0lyglot_png_h1des_a_zip}
```
