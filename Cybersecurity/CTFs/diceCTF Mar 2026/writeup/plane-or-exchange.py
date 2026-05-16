import ast
import hashlib
import re
from pathlib import Path


def parse_public_file(path: str):
    text = Path(path).read_text()
    m = re.search(r"Ciphertext:\s*([0-9a-fA-F]+)", text)
    if not m:
        raise ValueError("Could not find ciphertext")
    return bytes.fromhex(m.group(1))


def decrypt(ciphertext: bytes, shared_secret_hex: str) -> bytes:
    key = bytes.fromhex(shared_secret_hex)
    while len(key) < len(ciphertext):
        key += hashlib.sha256(key).digest()
    return bytes(c ^ k for c, k in zip(ciphertext, key))


def main():
    ciphertext = parse_public_file("public.txt")

    # Recovered from the invariant:
    # normalize(calculate(connect(a, b)))) = normalize(calculate(AlicePub))
    #                                       * normalize(calculate(BobPub))
    #                                       / normalize(calculate(PublicInfo))
    shared_poly = (
        "2*t**22 - 31*t**21 + 234*t**20 - 1136*t**19 + 3959*t**18 - "
        "10514*t**17 + 22120*t**16 - 37997*t**15 + 54813*t**14 - "
        "68477*t**13 + 76653*t**12 - 79253*t**11 + 76653*t**10 - "
        "68477*t**9 + 54813*t**8 - 37997*t**7 + 22120*t**6 - 10514*t**5 + "
        "3959*t**4 - 1136*t**3 + 234*t**2 - 31*t + 2"
    )

    shared_secret = hashlib.sha256(shared_poly.encode()).hexdigest()
    plaintext = decrypt(ciphertext, shared_secret).decode()

    print(f"shared polynomial = {shared_poly}")
    print(f"shared secret sha256 = {shared_secret}")
    print(f"flag = {plaintext}")


if __name__ == "__main__":
    main()
