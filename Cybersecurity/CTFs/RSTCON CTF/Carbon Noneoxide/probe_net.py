#!/usr/bin/env python3
import socket, time, sys

def probe(host, port=1337, timeout=12):
    print(f"=== {host}:{port} ===", flush=True)
    try:
        s = socket.create_connection((host, port), timeout=timeout)
    except Exception as e:
        print(f"  connect failed: {e}")
        return
    s.settimeout(timeout)
    buf = b""
    # read banner (up to ~3s of silence)
    s.settimeout(3)
    try:
        while len(buf) < 8192:
            chunk = s.recv(1024)
            if not chunk:
                break
            buf += chunk
            time.sleep(0.3)
    except socket.timeout:
        pass
    print(f"  banner ({len(buf)} bytes): {buf!r}")
    try:
        print("  decoded:", buf.decode("utf-8", "replace"))
    except: pass
    # send charlotte password
    if buf:
        s.settimeout(5)
        for line in [b"charlotte\n", b"h\n", b"i 100\n", b"s\n", b"r\n", b"x\n"]:
            try:
                s.sendall(line)
                print(f"  >> sent {line!r}")
                time.sleep(0.5)
                try:
                    r = s.recv(2048)
                    print(f"  << {r!r}")
                except socket.timeout:
                    print("  << (timeout)")
            except Exception as e:
                print(f"  send/recv err: {e}")
                break
    s.close()

for h in ["18.215.143.250", "18.145.136.91"]:
    probe(h)
