#!/usr/bin/env python3
"""Interactive client for the Carbon Noneoxide debug shell.
Reads with an inactivity timeout so we don't hang on slow servers."""
import socket, sys, time

HOSTS = ["18.215.143.250", "18.145.136.91"]
PORT = 1337

def recv_until_quiet(s, inactivity=2.0, max_wait=15.0):
    """Read until `inactivity` seconds pass with no new data, or max_wait reached."""
    s.settimeout(inactivity)
    buf = b""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            start = time.time()  # reset inactivity clock on data
        except socket.timeout:
            break
    return buf

def session(host, commands):
    print(f"\n========== {host}:{PORT} ==========", flush=True)
    try:
        s = socket.create_connection((host, PORT), timeout=15)
    except Exception as e:
        print("connect failed:", e)
        return
    # initial banner (server may or may not send before input)
    banner = recv_until_quiet(s, inactivity=2.0, max_wait=8.0)
    print(f"[banner {len(banner)}B]: {banner!r}", flush=True)
    try:
        print("BANNER>>", banner.decode("utf-8", "replace"), flush=True)
    except Exception: pass

    for cmd in commands:
        payload = (cmd + "\n").encode()
        try:
            s.sendall(payload)
            print(f"\n>>> sent {payload!r}", flush=True)
        except Exception as e:
            print("send err:", e); break
        time.sleep(0.6)
        resp = recv_until_quiet(s, inactivity=2.0, max_wait=8.0)
        print(f"[resp {len(resp)}B]: {resp!r}", flush=True)
        try:
            print("RESP>>", resp.decode("utf-8", "replace"), flush=True)
        except Exception: pass
        if not resp:
            # try reading more aggressively
            time.sleep(1.0)
            resp2 = recv_until_quiet(s, inactivity=2.0, max_wait=5.0)
            if resp2:
                print(f"[resp2 {len(resp2)}B]: {resp2!r}", flush=True)
                try: print("RESP2>>", resp2.decode("utf-8","replace"), flush=True)
                except: pass
    s.close()

# First, just authenticate and look at banner + help
cmds1 = ["charlotte", "h", "?", "help", "i 100", "s", "r", "x"]
session(HOSTS[0], cmds1)
