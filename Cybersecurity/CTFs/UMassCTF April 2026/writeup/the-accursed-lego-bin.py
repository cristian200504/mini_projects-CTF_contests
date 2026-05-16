import random

def main():
    # 1. Calculate the original seed
    # Since M^7 < n, there is no modulo reduction. We can compute the seed directly.
    plain_text = "I_LOVE_RNG"
    plain_num = int.from_bytes(plain_text.encode(), "big")
    seed = plain_num ** 7
    
    # 2. Load the encrypted flag from output.txt
    enc_flag_hex = "a9fa3c5e51d4cea498554399848ad14aa0764e15a6a2110b6613f5dc87fa70f17fafbba7eb5a2a5179"
    enc_flag_bytes = bytes.fromhex(enc_flag_hex)
    
    # Convert bytes to a list of bits (characters '0' and '1')
    shuffled_bits = []
    for byte in enc_flag_bytes:
        shuffled_bits.extend(list(bin(byte)[2:].zfill(8)))
        
    # 3. Reconstruct the shuffle mapping
    # Create an array of indices representing the original bit positions
    indices = list(range(len(shuffled_bits)))
    
    # Apply the exact same 10 shuffles to our indices
    for i in range(10):
        random.seed(seed * (i + 1))
        random.shuffle(indices)
        
    # 4. Unshuffle the bits
    original_bits = [''] * len(shuffled_bits)
    for i in range(len(shuffled_bits)):
        # The bit currently at position 'i' originally came from 'indices[i]'
        original_bits[indices[i]] = shuffled_bits[i]
        
    # 5. Convert the original bits back to characters
    flag = ""
    for i in range(0, len(original_bits), 8):
        byte_str = "".join(original_bits[i:i+8])
        flag += chr(int(byte_str, 2))
        
    print(f"Successfully decoded flag: {flag}")
    
    # 6. Write the decrypted flag to Flag.txt
    with open("Flag.txt", "w") as f:
        f.write(flag)
    print("Saved to Flag.txt")

if __name__ == "__main__":
    main()