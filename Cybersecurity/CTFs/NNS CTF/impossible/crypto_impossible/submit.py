import socket, ssl, sys

payload = open("proof_payload.txt").read().strip()
host = "impossible-06edd53a9ac5.chall.nnsc.tf"
port = 1337

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with socket.create_connection((host, port), timeout=15) as sock:
    with ctx.wrap_socket(sock, server_hostname=host) as tls:
        tls.sendall((payload + "\n").encode())
        tls.settimeout(10)
        chunks = []
        try:
            while True:
                data = tls.recv(4096)
                if not data:
                    break
                chunks.append(data)
        except socket.timeout:
            pass
        resp = b"".join(chunks).decode(errors="replace")
        print("=== SERVER RESPONSE ===")
        print(resp)
