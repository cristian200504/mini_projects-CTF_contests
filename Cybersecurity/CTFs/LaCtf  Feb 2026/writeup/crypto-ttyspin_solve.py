
import struct
import base64
import sys
import time
import os
import argparse

try:
    from pwn import *
except ImportError:
    pass # Only needed for auto mode

# Winning Board Layout from game.py
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

# Simple SHA256 implementation supporting state injection
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
            # ... truncated for brevity ...
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

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        self._h = (
            (self._h[0] + a) & 0xFFFFFFFF,
            (self._h[1] + b) & 0xFFFFFFFF,
            (self._h[2] + c) & 0xFFFFFFFF,
            (self._h[3] + d) & 0xFFFFFFFF,
            (self._h[4] + e) & 0xFFFFFFFF,
            (self._h[5] + f) & 0xFFFFFFFF,
            (self._h[6] + g) & 0xFFFFFFFF,
            (self._h[7] + h) & 0xFFFFFFFF,
        )

    def update(self, message):
        self._counter += len(message)
        message = bytearray(message)
        
        # Buffer handling
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

        # Process final chunk(s)
        h_backup = self._h
        
        while len(message) >= 64:
            self._process_chunk(message[:64])
            message = message[64:]
            
        result = struct.pack('!8L', *self._h)
        self._h = h_backup # Restore
        return result
    
    def hexdigest(self):
        return self.digest().hex()

    def set_state(self, hexdigest, counter):
        self._h = struct.unpack('!8L', bytes.fromhex(hexdigest))
        self._counter = counter
        self._buffer = bytearray()

# Generate Padding function
def get_padding(byte_length):
    padding = b'\x80'
    padding += b'\x00' * ((56 - (byte_length + 1) % 64) % 64)
    padding += struct.pack('!Q', byte_length * 8)
    return padding

# Construct Winning Save String
def get_winning_save():
    type_chars = ["T", "J", "L", "S", "Z", "O", "I"]
    current = "T"
    hold = " "
    nexts = "TTTT"
    queue = "T"
    board_str = ""
    for row in winning_board:
        for tile in row:
            if tile == 0:
                board_str += " "
            else:
                board_str += type_chars[tile - 1]
    return f"{current}|{hold}|{nexts}|{queue}|{board_str}"

def start_instance():
    # Use standard ssh command
    # -tt forces pseudo-tty allocation which the game likely needs
    # StrictHostKeyChecking=no avoids prompts
    cmd = ["ssh", "-tt", "-o", "StrictHostKeyChecking=no", "-p", "32123", "ttyspin@chall.lac.tf"]
    
    print(f"Starting process: {' '.join(cmd)}")
    io = process(cmd)
    
    # Handle password prompt
    try:
        # Wait for "password:" or similar
        # Might receive key fingerprint prompt if StrictHostKeyChecking=no doesn't catch it all
        # But we added option.
        output = io.recvrepeat(2.0).decode(errors='ignore')
        print("Initial output:", output)
        if "password" in output.lower():
            print("Sending password...")
            io.sendline(b"ttyspin")
    except Exception as e:
        print(f"Password handling exception: {e}")
    
    return io

def solve_manual():
    print("=== Manual Mode ===")
    print("1. SSH into chall.lac.tf manually: ssh -p 32123 ttyspin@chall.lac.tf")
    print("2. Enter username 'A'.")
    print("3. Start a new game (press Enter at import prompt).")
    print("4. Press 'e' immediately to Export.")
    print("5. Copy the 'Save code' (Base64) and 'Checksum' (Hex) from the terminal.")
    
    save_code_b64 = input("\nEnter Save Code (Base64): ").strip()
    checksum = input("Enter Checksum (Hex): ").strip()
    username = b"A" # Hardcoded for simplicity as per instructions
    
    if not save_code_b64 or not checksum:
        print("Error: Missing input.")
        return

    try:
        decoded_save = base64.b64decode(save_code_b64)
    except Exception as e:
        print(f"Error decoding base64: {e}")
        return

    original_msg_len = 40 + len(username) + len(decoded_save)
    padding = get_padding(original_msg_len)
    
    payload_extension = get_winning_save().encode()
    
    # Calculate New Checksum
    sha = Sha256()
    new_counter = original_msg_len + len(padding)
    sha.set_state(checksum, new_counter)
    sha.update(payload_extension)
    new_checksum = sha.hexdigest()
    
    # Calculate New Save
    new_data = decoded_save + padding + payload_extension
    new_save_b64 = base64.b64encode(new_data).decode()
    
    print("\n=== Forged Credentials ===")
    print(f"Forged Checksum: {new_checksum}")
    print(f"Forged Save Code (Base64): {new_save_b64}")
    
    print("\n=== Instructions ===")
    print("1. Close the current game connection (or start a new one).")
    print("2. Enter username 'A'.")
    print("3. At 'Import save code', paste the FORGED SAVE CODE above.")
    print("4. At 'Checksum (hex)', paste the FORGED CHECKSUM above.")
    print("5. The game should load in a winning state.")

def main():
    parser = argparse.ArgumentParser(description="CTF Solver for ttyspin")
    parser.add_argument("--manual", action="store_true", help="Run in manual mode (input/output only)")
    args = parser.parse_args()

    if args.manual:
        solve_manual()
        return

    # Check for pwntools
    if 'pwn' not in sys.modules:
        print("Error: pwntools required for auto mode. Use --manual if unavailable.")
        sys.exit(1)
        
    context.log_level = 'info'
    
    print("Connecting...")
    try:
        io = start_instance()
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Tip: Try manual mode: python3 solve.py --manual")
        return
    
    # Game interaction logic (same as before)
    # ...
    # Wait, I should wrap this in try-except block to suggest manual mode on failure.
    
    try:
        # Send Username
        username = b"A"
        print("Sending username...")
        io.sendline(username)
        
        # Wait for Import prompt
        time.sleep(1)
        print("Starting new game...")
        io.sendline(b"") # Empty for new game
        
        time.sleep(1) # Wait for game loop
        print("Exporting game...")
        io.send(b"e") # 'e' command
        
        print("Reading export data...")
        # ... (rest of logic)
        # For brevity, I'm assuming the previous logic was correct but failed on connection.
        # I'll just restore the logic from the previous file content here, but cleaner.
        
        try:
            data = io.recvrepeat(3.0).decode(errors='ignore')
        except Exception:
            data = ""
            
        print("Snapshot received (len: {}).".format(len(data)))

        import string
        
        if "Save code:" not in data:
            print("Failed to find 'Save code:' marker.")
            print("Tip: Try manual mode: python3 solve.py --manual")
            io.close()
            return

        # Extract
        save_idx = data.find("Save code:")
        check_idx = data.find("Checksum:")
        
        if save_idx != -1 and check_idx != -1:
            raw_save = data[save_idx+10 : check_idx]
            b64_chars = string.ascii_letters + string.digits + "+/="
            save_code_b64 = "".join([c for c in raw_save if c in b64_chars])
            
            raw_check = data[check_idx+9:]
            checksum = "".join([c for c in raw_check if c in string.hexdigits])[:64]
            
            print(f"Original Save (B64): {save_code_b64}")
            print(f"Original Checksum: {checksum}")
            
            decoded_save = base64.b64decode(save_code_b64)
            original_msg_len = 40 + len(username) + len(decoded_save)
            padding = get_padding(original_msg_len)
            
            payload_extension = get_winning_save().encode()
            
            # Calculate New Checksum
            sha = Sha256()
            new_counter = original_msg_len + len(padding)
            sha.set_state(checksum, new_counter)
            sha.update(payload_extension)
            new_checksum = sha.hexdigest()
            
            # Calculate New Save
            new_data = decoded_save + padding + payload_extension
            new_save_b64 = base64.b64encode(new_data)
            
            print(f"Forged Checksum: {new_checksum}")
            
            io.close()
            
            # Phase 2
            print("Reconnecting to inject payload...")
            io2 = start_instance()
            
            time.sleep(1)
            io2.sendline(username)
            time.sleep(0.5)
            
            # Send Forged Save
            print("Sending forged save...")
            io2.sendline(new_save_b64)
            time.sleep(0.5)
            
            # Send Checksum
            print("Sending forged checksum...")
            io2.sendline(new_checksum.encode())
            
            # Listen for flag
            print("Listening for flag...")
            start = time.time()
            while time.time() - start < 10:
                try:
                    chunk = io2.recv(1024).decode(errors='ignore')
                    if chunk:
                        clean = "".join([c for c in chunk if c in string.printable])
                        print(clean, end="")
                        if "lactf{" in chunk:
                            print("\n\nFLAG FOUND!!!")
                            io2.close()
                            return
                except EOFError:
                    break
                except Exception:
                    pass
                time.sleep(0.1)
            
            io2.close()
        else:
            print("Markers not found in output.")
            io.close()
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Tip: Try manual mode: python3 solve.py --manual")

if __name__ == "__main__":
    main()
