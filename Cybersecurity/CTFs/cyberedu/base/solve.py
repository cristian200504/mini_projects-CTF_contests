import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('34.159.231.80', 30720))

# Question 1: hex
data = s.recv(4096).decode(errors='ignore')
print(data)
val = data.split('<<')[1].split('>>')[0]
ans = hex(int(val))
print(ans)
s.sendall((ans + '\n').encode())

# Question 2: hex to ASCII
data = s.recv(4096).decode(errors='ignore')
print(data)
val = data.split('<<')[1].split('>>')[0]
ans = bytes.fromhex(val).decode()
print(ans)
s.sendall((ans + '\n').encode())

# Question 3: octal to ASCII
data = s.recv(4096).decode(errors='ignore')
print(data)
val = data.split('<<')[1].split('>>')[0]
ans = ''.join(chr(int(x, 8)) for x in val.split())
print(ans)
s.sendall((ans + '\n').encode())

# Get final output / flag
data = s.recv(4096).decode(errors='ignore')
print(data)

s.close()