import zlib
import struct
import sys

def deep_analyze(filename):
    print(f"Deep analyzing {filename}...")
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Check signature
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        print("Not a standard PNG signature")
        return

    pos = 8
    while pos < len(data):
        try:
            length = struct.unpack('>I', data[pos:pos+4])[0]
            chunk_type = data[pos+4:pos+8]
            chunk_data = data[pos+8:pos+8+length]
            crc_bytes = data[pos+8+length:pos+12+length]
            expected_crc = struct.unpack('>I', crc_bytes)[0]
            
            # Calculate CRC
            calculated_crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
            
            type_str = chunk_type.decode(errors='ignore')
            print(f"Chunk: {type_str}, Length: {length}, CRC: {expected_crc:08X}", end="")
            
            if expected_crc != calculated_crc:
                print(f" [MISMATCH! Calculated: {calculated_crc:08X}]")
                # Hidden data in CRC?
                diff = expected_crc ^ calculated_crc
                print(f"  Diff: {diff:08X}")
            else:
                print(" [OK]")
            
            # Look for data between chunks
            next_pos = pos + 12 + length
            if next_pos < len(data):
                # Check for gap
                pass # Already handled by simple pos increment
            
            pos = next_pos
        except Exception as e:
            print(f"Error at pos {pos}: {e}")
            break

if __name__ == "__main__":
    deep_analyze('challenge.png')
