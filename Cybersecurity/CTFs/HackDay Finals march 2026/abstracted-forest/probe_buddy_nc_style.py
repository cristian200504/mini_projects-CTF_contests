#!/usr/bin/env python3
import argparse
import itertools
import re
import socket
import ssl
from typing import Iterable, Optional

DEFAULT_VLANS = [109, 112]
PATHS = ['/', '/buddy', '/buddy/', '/flag', '/flag.txt', '/robots.txt', '/api', '/api/flag']
HOSTS = [
    '{ip}',
    '{ip}:{port}',
    'localhost',
    'localhost:{port}',
    '127.0.0.1',
    '127.0.0.1:{port}',
    'buddy',
    'buddy:{port}',
]
METHODS = ['GET', 'HEAD', 'OPTIONS']
VERSIONS = ['HTTP/1.1', 'HTTP/1.0']

FLAG_RE = [
    re.compile(rb'flag\{[^\r\n}]{0,300}\}', re.I),
    re.compile(rb'[A-Za-z0-9_\-]*ctf\{[^\r\n}]{0,300}\}', re.I),
    re.compile(rb'[A-Z0-9_]*FLAG\{[^\r\n}]{0,300}\}', re.I),
]


def recv_all(sock: socket.socket, timeout: float, cap: int = 262144) -> bytes:
    sock.settimeout(timeout)
    chunks = bytearray()
    while len(chunks) < cap:
        try:
            data = sock.recv(8192)
        except socket.timeout:
            break
        if not data:
            break
        chunks.extend(data)
    return bytes(chunks)


def find_flag(data: bytes) -> Optional[str]:
    for rx in FLAG_RE:
        m = rx.search(data)
        if m:
            return m.group(0).decode('utf-8', 'replace')
    return None


def request_bytes(method: str, path: str, version: str, host: str) -> bytes:
    return (
        f'{method} {path} {version}\r\n'
        f'Host: {host}\r\n'
        'User-Agent: nc-style-probe/1.0\r\n'
        'Accept: */*\r\n'
        'Connection: close\r\n'
        '\r\n'
    ).encode()


def try_once(ip: str, port: int, req: bytes, connect_timeout: float, read_timeout: float, tls: bool = False) -> bytes:
    with socket.create_connection((ip, port), timeout=connect_timeout) as s:
        conn = s
        if tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = ctx.wrap_socket(s, server_hostname=ip)
        conn.sendall(req)
        return recv_all(conn, timeout=read_timeout)


def iter_candidates(ip: str, port: int) -> Iterable[tuple[str, str, str, str, bool]]:
    for method, path, version, host_t in itertools.product(METHODS, PATHS, VERSIONS, HOSTS):
        yield method, path, version, host_t.format(ip=ip, port=port), False
    for path in ['/', '/buddy', '/flag']:
        for host_t in HOSTS[:4]:
            yield 'GET', path, 'HTTP/1.1', host_t.format(ip=ip, port=port), True


def main() -> int:
    ap = argparse.ArgumentParser(description='Small raw HTTP probe, suitable to mimic with nc/ncat')
    ap.add_argument('--vlans', nargs='*', type=int, default=DEFAULT_VLANS)
    ap.add_argument('--port', type=int, default=3840)
    ap.add_argument('--connect-timeout', type=float, default=1.0)
    ap.add_argument('--read-timeout', type=float, default=1.0)
    ap.add_argument('--show-all', action='store_true')
    args = ap.parse_args()

    for vlan in args.vlans:
        ip = f'192.168.{vlan}.132'
        print(f'=== VLAN {vlan} ({ip}:{args.port}) ===')
        seen_good = 0
        for method, path, version, host, tls in iter_candidates(ip, args.port):
            req = request_bytes(method, path, version, host)
            try:
                resp = try_once(ip, args.port, req, args.connect_timeout, args.read_timeout, tls=tls)
            except Exception:
                continue
            if not resp:
                continue
            first = resp.split(b'\r\n', 1)[0].decode('latin1', 'replace')
            flag = find_flag(resp)
            interesting = flag is not None or (' 400 ' not in first and ' 404 ' not in first)
            if interesting or args.show_all:
                scheme = 'https' if tls else 'http'
                print(f'[{scheme}] {method} {path} {version} Host={host} -> {first}')
                header, _, body = resp.partition(b'\r\n\r\n')
                preview = (body[:220] or header[:220]).decode('utf-8', 'replace').replace('\r', ' ').replace('\n', ' | ')
                if preview:
                    print(f'    {preview}')
                seen_good += 1
            if flag:
                print(f'\nFLAG: {flag}')
                return 0
        if seen_good == 0:
            print('No non-400/non-404 replies found with this small probe set.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
