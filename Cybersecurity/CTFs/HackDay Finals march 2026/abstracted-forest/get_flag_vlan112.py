#!/usr/bin/env python3
import re
import socket

HOST = '192.168.112.132'
PORT = 3840

FLAG_RE = re.compile(rb'(HACKDAY\{[^\r\n<>]{1,300}\})')


def http_get(host: str, port: int, path: str = '/') -> bytes:
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: Mozilla/5.0\r\n"
        "Accept: */*\r\n"
        "Connection: close\r\n\r\n"
    ).encode()

    chunks = []
    with socket.create_connection((host, port), timeout=3.0) as s:
        s.settimeout(3.0)
        s.sendall(req)
        while True:
            try:
                data = s.recv(4096)
            except socket.timeout:
                break
            if not data:
                break
            chunks.append(data)
    return b''.join(chunks)


def main() -> int:
    resp = http_get(HOST, PORT, '/')
    m = FLAG_RE.search(resp)
    if not m:
        print('[-] No flag found in response.')
        print(resp[:800].decode('utf-8', 'replace'))
        return 1

    flag = m.group(1).decode('utf-8', 'replace')
    print(f'[+] Correct connection: {HOST}:{PORT}')
    print(f'[+] Flag: {flag}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
