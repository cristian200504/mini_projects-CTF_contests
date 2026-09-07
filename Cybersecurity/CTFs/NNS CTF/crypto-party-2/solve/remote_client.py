"""
Talks to the real crypto-party-2 instance over TLS: sends 6 chosen friend
names blind (the server's stdout is likely fully buffered under
socat EXEC:uv run chall.py, so nothing may arrive until the process exits),
then parses the full buffered output. Pure stdlib + re - no sage needed here.
"""
import socket
import ssl
import re
import json
import sys

HOST = "crypto-party-2-545961fde41a.chall.nnsc.tf"
PORT = 1337

NAMES = [f"friend{i}" for i in range(6)]


def run():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with socket.create_connection((HOST, PORT), timeout=20) as sock:
        with ctx.wrap_socket(sock, server_hostname=HOST) as tls:
            payload = "".join(n + "\n" for n in NAMES)
            tls.sendall(payload.encode())

            tls.settimeout(20)
            data = b""
            try:
                while True:
                    chunk = tls.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass

    text = data.decode(errors="replace")
    print(text, file=sys.stderr)

    m = re.search(r"ct:\s*(\d+)", text)
    assert m, f"couldn't parse ct from output:\n{text}"
    ct = int(m.group(1))

    codes = re.findall(r"Invitation code = (\d+):(\d+)", text)
    assert len(codes) == len(NAMES), f"expected {len(NAMES)} invite codes, got {len(codes)}:\n{text}"

    results = [{"name": name, "r": int(r), "s": int(s)} for name, (r, s) in zip(NAMES, codes)]
    out = {"ct": ct, "invites": results}
    print(json.dumps(out))


if __name__ == "__main__":
    run()
