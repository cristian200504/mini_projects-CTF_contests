import sys
from Cryptodome.Cipher import AES

def parse_intel_hex(hex_path):
    flash = bytearray(0x30000)
    ext_addr = 0
    with open(hex_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith(':'):
                continue
            length = int(line[1:3], 16)
            addr = int(line[3:7], 16)
            rectype = int(line[7:9], 16)
            data = bytes.fromhex(line[9:9 + length * 2])
            if rectype == 4:
                ext_addr = int(line[9:13], 16) << 16
            elif rectype == 0:
                full_addr = ext_addr + addr
                if 0x1000000 <= full_addr < 0x1030000:
                    offset = full_addr - 0x1000000
                    flash[offset:offset + length] = data
    return flash

def solve():
    flash = parse_intel_hex('rev_harald/harald-blatann.hex')
    
    key_addr = 0x1028163
    ct_addr = 0x1028103
    
    key = flash[key_addr - 0x1000000 : key_addr - 0x1000000 + 32]
    ct_blob = flash[ct_addr - 0x1000000 : ct_addr - 0x1000000 + 96]
    
    iv = ct_blob[:16]
    ciphertext = ct_blob[16:]
    
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = cipher.decrypt(ciphertext)
    
    flag = plaintext.split(b'\x00')[0].decode('ascii')
    print(f"[+] Flag recovered: {flag}")
    return flag

if __name__ == '__main__':
    solve()
