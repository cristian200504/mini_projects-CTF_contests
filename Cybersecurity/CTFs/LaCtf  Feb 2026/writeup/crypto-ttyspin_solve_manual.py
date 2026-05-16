
import struct
import base64
import sys

# Standard SHA256 with State Injection
class Sha256:
    def __init__(self, message=None):
        self._h = (
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
        )
        self._counter = 0
        self._buffer = bytearray()
        if message:
            self.update(message)

    def _rotate_right(self, num, shift):
        return ((num >> shift) | (num << (32 - shift))) & 0xFFFFFFFF

    def _process_chunk(self, chunk):
        w = [0] * 64
        w[0:16] = struct.unpack('!16L', chunk)
        for i in range(16, 64):
            s0 = self._rotate_right(w[i-15], 7) ^ self._rotate_right(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = self._rotate_right(w[i-2], 17) ^ self._rotate_right(w[i-2], 19) ^ (w[i-2] >> 10)
            w[i] = (w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF
        a, b, c, d, e, f, g, h = self._h
        k = (
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        )
        for i in range(64):
            s1 = self._rotate_right(e, 6) ^ self._rotate_right(e, 11) ^ self._rotate_right(e, 25)
            ch = (e & f) ^ ((~e) & g)
            temp1 = (h + s1 + ch + k[i] + w[i]) & 0xFFFFFFFF
            s0 = self._rotate_right(a, 2) ^ self._rotate_right(a, 13) ^ self._rotate_right(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & 0xFFFFFFFF
            h = g; g = f; f = e; e = (d + temp1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (temp1 + temp2) & 0xFFFFFFFF
        self._h = ((self._h[0] + a) & 0xFFFFFFFF, (self._h[1] + b) & 0xFFFFFFFF, (self._h[2] + c) & 0xFFFFFFFF,
                   (self._h[3] + d) & 0xFFFFFFFF, (self._h[4] + e) & 0xFFFFFFFF, (self._h[5] + f) & 0xFFFFFFFF,
                   (self._h[6] + g) & 0xFFFFFFFF, (self._h[7] + h) & 0xFFFFFFFF)

    def update(self, message):
        self._counter += len(message)
        message = bytearray(message)
        if self._buffer:
            message = self._buffer + message
            self._buffer = bytearray()
        while len(message) >= 64:
            self._process_chunk(message[:64])
            message = message[64:]
        self._buffer = message

    def digest(self):
        message = self._buffer
        original_bit_len = self._counter * 8
        message.append(0x80)
        while (len(message) + 8) % 64 != 0:
            message.append(0x00)
        message += struct.pack('!Q', original_bit_len)
        self_h_backup = self._h
        while len(message) >= 64:
            self._process_chunk(message[:64])
            message = message[64:]
        res = struct.pack('!8L', *self._h)
        self._h = self_h_backup
        return res
    
    def hexdigest(self):
        return self.digest().hex()

    def set_state(self, hexdigest, counter):
        self._h = struct.unpack('!8L', bytes.fromhex(hexdigest))
        self._counter = counter
        self._buffer = bytearray()

def get_padding(byte_length):
    padding = b'\x80'
    padding += b'\x00' * ((56 - (byte_length + 1) % 64) % 64)
    padding += struct.pack('!Q', byte_length * 8)
    return padding

# Winning Winning Board Configuration
winning_board = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [7, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 6, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 7, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 5, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 0, 0, 0, 0],
    [0, 0, 0, 0, 7, 0, 0, 0, 0, 0],
    [0, 0, 0, 4, 0, 0, 0, 0, 0, 0],
    [0, 0, 6, 0, 0, 0, 0, 0, 0, 0],
    [0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
    [5, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

def get_winning_save():
    type_chars = ["T", "J", "L", "S", "Z", "O", "I"]
    current = "T"
    hold = " "
    nexts = "TTTT"
    queue = "T"
    board_str = ""
    for row in winning_board:
        for tile in row:
            if tile == 0: board_str += " "
            else: board_str += type_chars[tile - 1]
    return f"{current}|{hold}|{nexts}|{queue}|{board_str}"

def main():
    print("="*60)
    print("      TTYSPIN MANUAL BUILDER")
    print("="*60)
    print("This script helps you forge a save file to win the game.")
    print("\nINSTRUCTIONS:")
    print("1. Open a new terminal window.")
    print("2. Connect to the challenge: ssh -p 32123 ttyspin@chall.lac.tf")
    print("   (Password: ttyspin)")
    print("3. Enter 'A' as your username.")
    print("4. Press Enter to start a new game (skip import).")
    print("5. IMMEDIATELY press 'e' to Export the game.")
    print("6. Copy the entire 'Save code' (Base64) and 'Checksum' (Hex).")
    print("="*60)
    
    save_code_b64 = input("\n[1] Paste the BASE64 Save Code here:\n> ").strip()
    checksum = input("\n[2] Paste the HEX Checksum here:\n> ").strip()
    
    if not save_code_b64 or not checksum:
        print("Error: Missing input!")
        return

    # Critical fix: The server strips trailing whitespace from the save before hashing!
    # We must match that behavior.
    decoded_save = base64.b64decode(save_code_b64)
    decoded_save_stripped = decoded_save.rstrip() 
    
    username = b"A"
    secret_padding = 40 # len(SECRET)
    
    original_msg_len = secret_padding + len(username) + len(decoded_save_stripped)
    padding = get_padding(original_msg_len)
    
    # CRITICAL FIX for UTF-8 padding issue:
    # SHA-256 padding starts with 0x80.
    # 0x80 is an invalid start byte in UTF-8.
    # By ending our payload with 0xC2, we create the sequence 0xC2 0x80.
    # 0xC2 0x80 decodes to U+0080, which is valid UTF-8!
    # The game parser ignores extra characters at the end of the board string.
    payload_extension = get_winning_save().encode() + b'\xc2'
    
    # Generate new checksum
    sha = Sha256()
    new_counter = original_msg_len + len(padding)
    sha.set_state(checksum, new_counter)
    
    # Crucial: The server strips trailing whitespace from the ENTIRE message before hashing.
    # Since our extension is at the end, it gets stripped too.
    sha.update(payload_extension.rstrip())
    new_checksum = sha.hexdigest()
    
    # Generate new save data
    # We send the full data, but the server will strip it before verifying.
    new_data = decoded_save_stripped + padding + payload_extension
    new_save_b64 = base64.b64encode(new_data).decode()
    
    print("\n" + "="*60)
    print("      FORGED CREDENTIALS GENERATED")
    print("="*60)
    print("\n[STEP 1] Copy this NEW Save Code (it is one long line):")
    print("-" * 20)
    print(new_save_b64)
    print("-" * 20)
    
    print("\n[STEP 2] Copy this NEW Checksum:")
    print("-" * 20)
    print(new_checksum)
    print("-" * 20)
    
    print("\nFINAL STEPS:")
    print("1. Relaunch the game (or reconnect) as user 'A'.")
    print("2. When asked 'Import save code', paste the [STEP 1] code above.")
    print("3. When asked 'Checksum', paste the [STEP 2] code above.")
    print("4. The game should load and give you the flag.")

if __name__ == "__main__":
    main()
