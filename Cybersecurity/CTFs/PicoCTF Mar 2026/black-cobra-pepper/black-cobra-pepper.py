def xor_hex(a, b):
    return bytes([x ^ y for x, y in zip(bytes.fromhex(a), bytes.fromhex(b))]).hex()

def to_matrix(key):
    bytes_list = [int(key[i:i+2], 16) for i in range(0, 32, 2)]
    array = [[0] * 4 for _ in range(4)]
    for i in range(16):
        row = i % 4
        col = i // 4
        array[row][col] = hex(bytes_list[i])[2:].zfill(2)
    return array

def from_matrix(matrix):
    reconstructed = ""
    for col in range(4):
        for row in range(4):
            reconstructed += matrix[row][col].zfill(2)
    return reconstructed

def gmul(a, b):
    b = int(b, 16) if isinstance(b, str) else b
    a = int(a, 16) if isinstance(a, str) else a
    p = 0
    for c in range(8):
        if b & 1:
            p ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11b
        b >>= 1
    return p

def inv_shift_rows(state):
    state[1][0], state[1][1], state[1][2], state[1][3] = state[1][3], state[1][0], state[1][1], state[1][2]
    state[2][0], state[2][1], state[2][2], state[2][3] = state[2][2], state[2][3], state[2][0], state[2][1]
    state[3][0], state[3][1], state[3][2], state[3][3] = state[3][1], state[3][2], state[3][3], state[3][0]
    return state

def inv_mix_columns(s):
    ss = [[0] * 4 for _ in range(4)]
    for c in range(4):
        ss[0][c] = hex(gmul(0x0e, s[0][c]) ^ gmul(0x0b, s[1][c]) ^ gmul(0x0d, s[2][c]) ^ gmul(0x09, s[3][c]))[2:].zfill(2)
        ss[1][c] = hex(gmul(0x09, s[0][c]) ^ gmul(0x0e, s[1][c]) ^ gmul(0x0b, s[2][c]) ^ gmul(0x0d, s[3][c]))[2:].zfill(2)
        ss[2][c] = hex(gmul(0x0d, s[0][c]) ^ gmul(0x09, s[1][c]) ^ gmul(0x0e, s[2][c]) ^ gmul(0x0b, s[3][c]))[2:].zfill(2)
        ss[3][c] = hex(gmul(0x0b, s[0][c]) ^ gmul(0x0d, s[1][c]) ^ gmul(0x09, s[2][c]) ^ gmul(0x0e, s[3][c]))[2:].zfill(2)
    for i in range(4):
        for j in range(4):
            s[i][j] = ss[i][j]
    return s

# 1. Inputs provided by the challenge
pt1    = "72616e646f6d64617461313131313131"
c_pt1  = "d7481d89f1aaf5a857f56edd2ae8994c"
c_flag = "8c7d66558130eb5796d131beb43c9934"

# 2. XOR the ciphertexts to eliminate the keys entirely
delta_c = xor_hex(c_pt1, c_flag)

# 3. Reverse the linear layers (10 rounds)
state = to_matrix(delta_c)

# Reverse round 10 (which has no MixColumns in standard AES and this script)
state = inv_shift_rows(state)

# Reverse rounds 9 down to 1
for _ in range(9):
    state = inv_mix_columns(state)
    state = inv_shift_rows(state)

delta_p = from_matrix(state)

# 4. Recover the flag
flag_hex = xor_hex(pt1, delta_p)
print(f"Recovered Flag: {bytes.fromhex(flag_hex).decode('utf-8')}")