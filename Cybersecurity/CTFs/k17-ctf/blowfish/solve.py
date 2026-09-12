#!/usr/bin/env python3
"""Solve the supplied Blowfish mock challenge."""

from __future__ import annotations

import argparse
import re
import socket


BS = 8
TAG = 64
PROMPT = b"unblow an unfish down? "
INITIAL = re.compile(rb"Fish: ([0-9a-f]+)\r?\nSignature: ([0-9a-f]+)")
PAIR = re.compile(rb"([0-9a-f]+)\r?\nSignature: ([0-9a-f]+)")


def split_blocks(data: bytes) -> list[bytes]:
    if len(data) % BS:
        raise ValueError("expected complete 8-byte blocks")
    return [data[i : i + BS] for i in range(0, len(data), BS)]


def split_tags(signature: bytes) -> list[bytes]:
    if len(signature) % TAG:
        raise ValueError("invalid tag length")
    return [signature[i : i + TAG] for i in range(0, len(signature), TAG)]


def bxor(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


class Remote:
    def __init__(self, host: str, port: int) -> None:
        self.sock = socket.create_connection((host, port), timeout=30)
        self.sock.settimeout(60)
        self.buffer = b""

    def recvuntil(self, marker: bytes) -> bytes:
        while marker not in self.buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError(f"connection closed before {marker!r}")
            self.buffer += chunk
        end = self.buffer.index(marker) + len(marker)
        result, self.buffer = self.buffer[:end], self.buffer[end:]
        return result

    def sendline(self, data: bytes) -> None:
        self.sock.sendall(data + b"\n")

    @staticmethod
    def parse(response: bytes) -> tuple[bytes, bytes]:
        pairs = PAIR.findall(response)
        if not pairs:
            raise RuntimeError(response.decode(errors="replace"))
        raw, signature = pairs[-1]
        return bytes.fromhex(raw.decode()), signature

    def start(self) -> tuple[bytes, bytes]:
        response = self.recvuntil(PROMPT)
        match = INITIAL.search(response)
        if not match:
            raise RuntimeError("initial fish was not found")
        return bytes.fromhex(match.group(1).decode()), match.group(2)

    def request(self, choice: int, raw: bytes, signature: bytes) -> tuple[bytes, bytes]:
        self.sendline(str(choice).encode())
        self.recvuntil(b"Enter fish: " if choice == 1 else b"Enter up-blown/unup-unblown fish: ")
        self.sendline(raw.hex().encode())
        self.recvuntil(b"Sign the fish: ")
        self.sendline(signature)
        return self.parse(self.recvuntil(PROMPT))

    def finish(self, raw: bytes, signature: bytes) -> bytes:
        self.sendline(b"1")
        self.recvuntil(b"Enter fish: ")
        self.sendline(raw.hex().encode())
        self.recvuntil(b"Sign the fish: ")
        self.sendline(signature)
        parts = [self.buffer]
        self.buffer = b""
        while True:
            try:
                chunk = self.sock.recv(4096)
            except TimeoutError:
                break
            if not chunk:
                break
            parts.append(chunk)
        return b"".join(parts)


class Basis:
    """A GF(2) basis with the selected input-vector mask retained."""

    def __init__(self) -> None:
        self.rows: dict[int, tuple[int, int]] = {}

    def add(self, value: int, source: int) -> None:
        mask = source
        for bit in range(63, -1, -1):
            if not (value >> bit) & 1:
                continue
            if bit not in self.rows:
                self.rows[bit] = value, mask
                return
            row, row_mask = self.rows[bit]
            value, mask = value ^ row, mask ^ row_mask

    def solve(self, target: int) -> int:
        mask = 0
        for bit in range(63, -1, -1):
            if not (target >> bit) & 1:
                continue
            try:
                row, row_mask = self.rows[bit]
            except KeyError as error:
                raise ValueError("initial blocks were not full rank; reconnect") from error
            target, mask = target ^ row, mask ^ row_mask
        return mask


def exploit(host: str, port: int) -> bytes:
    remote = Remote(host, port)
    plain, plain_signature = remote.start()
    p, ptag = split_blocks(plain), split_tags(plain_signature)
    if p[1] != b'{"admin"':
        raise ValueError("unexpected initial JSON layout")

    # Get a signed CBC ciphertext for the known plaintext.
    cipher, cipher_signature = remote.request(1, plain, plain_signature)
    c, ctag = split_blocks(cipher), split_tags(cipher_signature)
    if len(c) != len(p):
        raise ValueError("unexpected ciphertext length")

    # CBC gives D(C_i) = P_i xor C_(i-1), i >= 1.
    d = [bxor(p[i], c[i - 1]) for i in range(1, len(c))]
    basis = Basis()
    for index, value in enumerate(d):
        basis.add(int.from_bytes(value, "big"), 1 << index)
    if len(basis.rows) != 64:
        raise ValueError("retry for a full-rank connection")

    target = b": true }"
    current, current_tag = p[0], ptag[0]
    selected = basis.solve(int.from_bytes(bxor(current, target), "big"))

    # C_i decrypts to D(C_i) xor current. C_j is a guard that prevents
    # unpad() from removing the useful block when it ends in a NUL byte.
    for index, value in enumerate(d):
        if not (selected >> index) & 1:
            continue
        guard = next(
            candidate
            for candidate, guard_value in enumerate(d)
            if (int.from_bytes(guard_value, "big") ^ int.from_bytes(c[index + 1], "big")) & 0xFF
        )
        output, output_signature = remote.request(
            2,
            current + c[index + 1] + c[guard + 1],
            current_tag + ctag[index + 1] + ctag[guard + 1],
        )
        out, out_tag = split_blocks(output), split_tags(output_signature)
        expected = bxor(current, value)
        if len(out) != 3 or out[1] != expected:
            raise RuntimeError("unexpected CBC transition")
        current, current_tag = out[1], out_tag[1]

    if current != target:
        raise RuntimeError("failed to create the admin block")

    final = p[0] + b'{"admin"' + target
    final_signature = ptag[0] + ptag[1] + current_tag
    return remote.finish(final, final_signature)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="chal.secso.cc")
    parser.add_argument("--port", type=int, default=2001)
    args = parser.parse_args()
    print(exploit(args.host, args.port).decode(errors="replace"), end="")
