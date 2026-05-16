#!/usr/bin/env python3
import argparse
import concurrent.futures as cf
import re
import socket
import ssl
import sys
import time
from typing import Dict, List, Optional, Tuple

FLAG_PATTERNS = [
    re.compile(rb'(flag\{[^\n\r}]{0,300}\})', re.I),
    re.compile(rb'([A-Z0-9_]*FLAG\{[^\n\r}]{0,300}\})', re.I),
    re.compile(rb'([A-Za-z0-9_\-]*ctf\{[^\n\r}]{0,300}\})', re.I),
    re.compile(rb'((?:HTB|THM|picoCTF|ictf|nite|uiuctf|corctf|amateurs|buckeye|vsctf)\{[^\n\r}]{0,300}\})', re.I),
]

COMMON_PATHS = [
    '/', '/flag', '/flag.txt', '/buddy', '/buddy/', '/hack', '/hack/',
    '/robots.txt', '/.env', '/.git/HEAD', '/index.php', '/index.html',
    '/api', '/api/', '/api/flag', '/api/v1/flag', '/debug', '/status',
]

COMMON_HOSTS = [
    None, 'localhost', '127.0.0.1', 'buddy', 'buddy.local', 'buddy.ctf',
    'hackbuddy', 'hack-buddy',
]

USER_AGENT = 'Mozilla/5.0 (compatible; CTFSolver/1.1)'


def find_flag(blob: bytes) -> Optional[str]:
    for pat in FLAG_PATTERNS:
        m = pat.search(blob)
        if m:
            return m.group(1).decode(errors='replace')
    return None


def recv_all(sock: socket.socket, timeout: float = 1.2, limit: int = 512_000) -> bytes:
    sock.settimeout(timeout)
    out = bytearray()
    while len(out) < limit:
        try:
            chunk = sock.recv(65535)
            if not chunk:
                break
            out += chunk
            # stop early once body likely complete for tiny responses
            if b'\r\n\r\n' in out and len(chunk) < 4096:
                time.sleep(0.05)
        except socket.timeout:
            break
        except OSError:
            break
    return bytes(out)


def split_http(resp: bytes) -> Tuple[bytes, bytes]:
    if b'\r\n\r\n' in resp:
        head, body = resp.split(b'\r\n\r\n', 1)
        return head, body
    return resp, b''


def status_code(resp: bytes) -> Optional[int]:
    line = resp.split(b'\r\n', 1)[0]
    m = re.match(rb'HTTP/\d\.\d\s+(\d{3})', line)
    return int(m.group(1)) if m else None


def make_request(host_header: str, path: str, http10: bool = False) -> bytes:
    version = 'HTTP/1.0' if http10 else 'HTTP/1.1'
    req = (
        f'GET {path} {version}\r\n'
        f'Host: {host_header}\r\n'
        f'User-Agent: {USER_AGENT}\r\n'
        'Accept: */*\r\n'
        'Connection: close\r\n'
        '\r\n'
    )
    return req.encode()


def try_http(host: str, port: int, connect_timeout: float, io_timeout: float,
             host_header: str, path: str, use_tls: bool = False, http10: bool = False) -> bytes:
    with socket.create_connection((host, port), timeout=connect_timeout) as sock:
        conn: socket.socket
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = ctx.wrap_socket(sock, server_hostname=host_header)
        else:
            conn = sock
        conn.sendall(make_request(host_header, path, http10=http10))
        return recv_all(conn, timeout=io_timeout)


def probe_http_variants(vlan_id: int, port: int, connect_timeout: float, io_timeout: float,
                        verbose: bool = False) -> Dict[str, object]:
    ip = f'192.168.{vlan_id}.132'
    result: Dict[str, object] = {
        'vlan': vlan_id,
        'ip': ip,
        'live': False,
        'flag': None,
        'best_preview': b'',
        'hits': [],
    }

    host_headers = []
    for h in COMMON_HOSTS:
        host_headers.append(ip if h is None else h)
        host_headers.append(f'{ip}:{port}' if h is None else h)
    # dedupe preserving order
    seen = set()
    host_headers = [h for h in host_headers if not (h in seen or seen.add(h))]

    attempts = []
    for hh in host_headers:
        for p in COMMON_PATHS:
            attempts.append((hh, p, False, False))
            attempts.append((hh, p, False, True))
    # only try TLS sparingly
    for hh in host_headers[:4]:
        for p in ['/', '/flag', '/buddy']:
            attempts.append((hh, p, True, False))

    for host_header, path, use_tls, http10 in attempts:
        try:
            resp = try_http(ip, port, connect_timeout, io_timeout, host_header, path, use_tls=use_tls, http10=http10)
        except Exception:
            continue

        if not resp:
            continue
        result['live'] = True
        if not result['best_preview']:
            result['best_preview'] = resp[:250]

        flag = find_flag(resp)
        code = status_code(resp)
        head, body = split_http(resp)
        location = b''
        m = re.search(rb'(?im)^Location:\s*(.+?)\s*$', head)
        if m:
            location = m.group(1)

        hit = {
            'host_header': host_header,
            'path': path,
            'tls': use_tls,
            'http10': http10,
            'status': code,
            'location': location.decode(errors='replace') if location else '',
            'preview': (body[:180] or head[:180]).decode(errors='replace',),
        }
        result['hits'].append(hit)

        if flag:
            result['flag'] = flag
            result['response'] = resp
            result['winning_hit'] = hit
            return result

        # successful-ish responses are interesting enough to keep
        if code and code not in (400, 404):
            text = (body[:5000] or head[:5000]).lower()
            # find hints for next-step automation
            for extra in [b'href="', b"href='", b'src="', b'action="', b'buddy', b'flag', b'admin', b'login', b'token']:
                if extra in text:
                    pass

    return result


def summarize_preview(blob: bytes) -> str:
    return blob[:200].decode(errors='replace').replace('\r', ' ').replace('\n', ' | ')


def main() -> int:
    ap = argparse.ArgumentParser(description='HTTP-focused solver for Abstracted Forest')
    ap.add_argument('--start', type=int, default=1)
    ap.add_argument('--end', type=int, default=254)
    ap.add_argument('--port', type=int, default=3840)
    ap.add_argument('--connect-timeout', type=float, default=1.0)
    ap.add_argument('--io-timeout', type=float, default=1.2)
    ap.add_argument('--workers', type=int, default=48)
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    responsive: List[Dict[str, object]] = []
    found: Optional[Dict[str, object]] = None

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [
            ex.submit(probe_http_variants, vlan, args.port, args.connect_timeout, args.io_timeout, args.verbose)
            for vlan in range(args.start, args.end + 1)
        ]
        for fut in cf.as_completed(futs):
            res = fut.result()
            if not res['live']:
                continue
            responsive.append(res)
            print(f"[+] VLAN {res['vlan']} -> {res['ip']}:{args.port} responded")
            if res['hits']:
                best = next((h for h in res['hits'] if h['status'] and h['status'] not in (400, 404)), res['hits'][0])
                tls = 'https' if best['tls'] else 'http'
                v10 = ' HTTP/1.0' if best['http10'] else ''
                print(f"    best: {tls} Host={best['host_header']} Path={best['path']} Status={best['status']}{v10}")
                if best['location']:
                    print(f"    redirect: {best['location']}")
                if args.verbose and best['preview']:
                    print(f"    preview: {best['preview'][:180]}")
            if res['flag']:
                found = res
                break

    if found:
        hit = found['winning_hit']
        print(f"\n[FLAG] VLAN {found['vlan']} ({found['ip']}:{args.port}) -> {found['flag']}")
        print(f"[HIT] scheme={'https' if hit['tls'] else 'http'} host_header={hit['host_header']} path={hit['path']} status={hit['status']}")
        print('\n--- raw response start ---')
        sys.stdout.buffer.write(found['response'])
        if not found['response'].endswith(b'\n'):
            print()
        print('--- raw response end ---')
        return 0

    print('\n[-] No flag recovered automatically.')
    if responsive:
        print('[*] Best candidates:')
        for res in sorted(responsive, key=lambda r: r['vlan']):
            best = next((h for h in res['hits'] if h['status'] and h['status'] not in (400, 404)), res['hits'][0] if res['hits'] else None)
            if not best:
                print(f"    VLAN {res['vlan']:>3} -> {res['ip']}:{args.port} :: {summarize_preview(res['best_preview'])}")
                continue
            tls = 'https' if best['tls'] else 'http'
            extra = f" -> {best['location']}" if best['location'] else ''
            print(f"    VLAN {res['vlan']:>3} -> {res['ip']}:{args.port} :: {tls} Host={best['host_header']} Path={best['path']} Status={best['status']}{extra}")
            if args.verbose and best['preview']:
                print(f"        {best['preview'][:200]}")
    else:
        print('[*] No HTTP-like service responded in the tested range.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
