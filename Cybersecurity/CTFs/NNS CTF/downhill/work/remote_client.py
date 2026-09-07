"""
Talks to the real downhill instance over TLS. Like crypto-party-2, stdout is
likely fully buffered under socat EXEC (no -u), so send all 500 signing
requests blind, then read the whole buffered burst at process exit.
"""
import socket
import ssl
import re
import json
import sys

HOST = "downhill-80c80a52c77f.chall.nnsc.tf"
PORT = 1337
N_SIGS = 500


def run():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    names = [f"friend{i}" for i in range(N_SIGS)]

    with socket.create_connection((HOST, PORT), timeout=30) as sock:
        with ctx.wrap_socket(sock, server_hostname=HOST) as tls:
            payload = "".join(n + "\n" for n in names)
            tls.sendall(payload.encode())

            tls.settimeout(60)
            data = b""
            try:
                while True:
                    chunk = tls.recv(65536)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass

    text = data.decode(errors="replace")
    with open("remote_raw.txt", "w") as f:
        f.write(text)
    print(f"received {len(text)} bytes, saved to remote_raw.txt", file=sys.stderr)

    m = re.search(r"pk = (\[[^\]]*\])", text)
    assert m, "couldn't parse pk"
    pk = json.loads(m.group(1))

    m = re.search(r"ct = ([0-9a-f]+)", text)
    assert m, "couldn't parse ct"
    ct = m.group(1)

    sig_lines = re.findall(r"(\[-?\d+(?:,\s*-?\d+)*\])", text)
    print(f"found {len(sig_lines)} bracketed number-lists total (pk is one of them)", file=sys.stderr)

    # first bracketed list is pk itself; the rest (up to N_SIGS) are signatures
    sigs_raw = [json.loads(s) for s in sig_lines]
    # drop the pk list if it matches exactly
    if sigs_raw and sigs_raw[0] == pk:
        sigs_raw = sigs_raw[1:]

    # Sage's poly.list() drops trailing zero coefficients, so a signature
    # whose top coefficient(s) happen to be exactly 0 prints short; pad back.
    N = 251
    sigs = []
    for i in range(min(len(sigs_raw), N_SIGS)):
        s = sigs_raw[i]
        if len(s) < N:
            s = s + [0] * (N - len(s))
        sigs.append({"msg": names[i].encode().hex(), "sig": s})
    print(f"parsed {len(sigs)} signatures", file=sys.stderr)

    out = {"N": 251, "q": 128, "pk_h": pk, "ct": ct, "sigs": sigs}
    with open("remote_data.json", "w") as f:
        json.dump(out, f)
    print("wrote remote_data.json", file=sys.stderr)


if __name__ == "__main__":
    run()
