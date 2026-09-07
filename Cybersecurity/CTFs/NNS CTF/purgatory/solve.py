import ssl
import socket

REMOTE_HOST = 'purgatory-da8b8ebf1fbc.chall.nnsc.tf'
REMOTE_PORT = 1337

old_l0 = [
    (0, 247, 40, 120), (1, 195, 0, 68), (2, 89, 105, 45), (3, 77, 179, 70),
    (4, 107, 221, 62), (5, 37, 117, 101), (6, 11, 232, 52), (7, 205, 46, 5),
    (8, 93, 161, 36), (9, 47, 220, 181), (10, 195, 222, 49), (11, 191, 233, 251),
    (12, 69, 35, 108)
]

new_l1 = [
    (13, 87, 33, 108), (14, 233, 61, 201), (15, 197, 97, 245), (16, 155, 124, 72),
    (17, 75, 219, 93), (18, 115, 213, 5), (19, 219, 87, 227), (20, 221, 230, 166),
    (21, 69, 83, 123), (22, 139, 156, 253), (23, 193, 229, 111), (24, 93, 241, 181)
]

old_mask = [114, 157, 234, 123, 50, 120, 87, 159, 59, 45, 110, 181]

def solve_linear(a, b, c):
    for x in range(256):
        if ((a * x + b) & 255) == c:
            return x
    raise ValueError(f'No solution for ({a}*x + {b}) & 255 == {c}')

def get_passphrase():
    first_half = [solve_linear(a, b, c) for _, a, b, c in old_l0]
    second_half = [
        solve_linear(a, b, c) ^ old_mask[idx - 13]
        for idx, a, b, c in new_l1
    ]
    return bytes(first_half + second_half)

def get_flag(passphrase):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with socket.create_connection((REMOTE_HOST, REMOTE_PORT)) as sock:
        with ctx.wrap_socket(sock, server_hostname=REMOTE_HOST) as conn:
            buf = b''
            while b'passphrase> ' not in buf:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buf += chunk
            conn.sendall(passphrase + b'\n')
            response = b''
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                response += chunk
            return response.decode('utf-8', errors='replace').strip()

if __name__ == '__main__':
    pw = get_passphrase()
    print(f'[+] Recovered Passphrase: {pw.decode()}')
    flag = get_flag(pw)
    print(f'[+] Flag: {flag}')
