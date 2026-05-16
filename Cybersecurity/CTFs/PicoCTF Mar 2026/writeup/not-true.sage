from sage.all import *

# Challenge Parameters
N = 48
p = 3
q = 509

# Public Key & Ciphertext
h = [467, 204, 459, 435, 40, 88, 86, 107, 358, 235, 12, 500, 491, 90, 44, 414, 474, 130, 199, 229, 274, 59, 298, 253, 70, 107, 64, 134, 240, 349, 419, 159, 109, 437, 357, 133, 244, 423, 205, 115, 405, 464, 458, 174, 85, 59, 503, 301]

ct = [
    [392, 352, 271, 299, 247, 452, 360, 362, 23, 459, 307, 15, 5, 178, 451, 130, 358, 88, 218, 91, 462, 385, 166, 435, 363, 32, 326, 17, 322, 271, 2, 193, 126, 311, 135, 232, 51, 240, 141, 104, 172, 227, 465, 323, 376, 135, 378, 41],
    [33, 344, 504, 138, 202, 327, 208, 248, 82, 9, 79, 143, 369, 101, 158, 222, 122, 366, 331, 433, 445, 217, 16, 57, 242, 455, 170, 376, 221, 469, 130, 14, 413, 20, 43, 75, 74, 148, 278, 7, 369, 379, 153, 75, 443, 42, 273, 171],
    [295, 304, 78, 132, 149, 287, 322, 39, 308, 274, 341, 100, 184, 496, 11, 157, 228, 475, 184, 504, 233, 288, 316, 385, 252, 20, 120, 28, 92, 400, 500, 56, 131, 476, 435, 281, 177, 474, 358, 254, 97, 156, 329, 37, 184, 312, 500, 422],
    [381, 28, 346, 142, 53, 18, 214, 89, 375, 408, 294, 497, 104, 99, 444, 429, 489, 275, 156, 76, 19, 449, 229, 268, 328, 57, 383, 374, 76, 339, 498, 127, 24, 88, 289, 126, 409, 230, 364, 226, 414, 458, 345, 241, 324, 455, 314, 349],
    [253, 478, 368, 299, 464, 214, 191, 155, 48, 318, 376, 83, 215, 248, 59, 114, 16, 252, 220, 113, 120, 226, 253, 31, 269, 403, 59, 271, 243, 427, 132, 362, 491, 41, 18, 486, 396, 34, 159, 351, 505, 329, 96, 479, 226, 182, 404, 227],
    [457, 90, 115, 229, 460, 65, 136, 421, 263, 482, 426, 49, 131, 205, 269, 153, 111, 14, 336, 338, 118, 209, 444, 208, 412, 222, 9, 338, 192, 10, 121, 353, 318, 410, 235, 416, 223, 309, 489, 226, 391, 452, 66, 395, 106, 391, 260, 411]
]

print("[+] Building NTRU Lattice Matrix...")
M = matrix(ZZ, 2*N, 2*N)
for i in range(N):
    M[i, i] = 1
    M[i+N, i+N] = q
    for j in range(N):
        M[i, N + ((i+j)%N)] = h[j]

print("[+] Running LLL Algorithm...")
M_lll = M.LLL()

print("[+] Extracting Private Key Polynomial...")
f_list = list(M_lll[0][:N])

# Setup Polynomial Rings
R_p = PolynomialRing(Integers(p), 'x')
x_p = R_p.gen()
R_modp = R_p.quotient(x_p**N - 1, 'xbar')
f_p_inv = R_modp(f_list)**-1

R_Z = PolynomialRing(ZZ, 'x')
x_Z = R_Z.gen()
R_quot = R_Z.quotient(x_Z**N - 1, 'xbar')
f_R = R_quot(f_list)

print("[+] Decrypting Ciphertext...")
recovered_bits = []
for c_list in ct:
    c_R = R_quot(c_list)
    a_R = f_R * c_R
    
    # Pad missing high-degree zero coefficients
    a_list = a_R.list()
    a_list += [0] * (N - len(a_list))
    
    # Center lift modulo q
    a_centered = []
    for coeff in a_list:
        val = coeff % q
        if val > q // 2:
            val -= q
        a_centered.append(val)
        
    a_mod_p = R_modp(a_centered)
    m_poly = a_mod_p * f_p_inv
    
    m_list = m_poly.list()
    m_list += [0] * (N - len(m_list))
    
    for coeff in m_list:
        recovered_bits.append(int(coeff) % p)

print("[+] Decoding Flag...")
flag_str = ""
for i in range(0, len(recovered_bits), 8):
    chunk = recovered_bits[i:i+8]
    if len(chunk) == 8:
        bits_str = "".join(str(b) for b in chunk)
        char_val = int(bits_str, 2)
        if char_val > 0:  # Ignore zero-padding
            flag_str += chr(char_val)

print(f"\nFlag: {flag_str}")