import struct
import sys

def analyze(filename):
    print(f"Analyzing {filename}...")
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # 1. Check chunks
    pos = 8
    chunks = []
    while pos < len(data):
        try:
            length = struct.unpack('>I', data[pos:pos+4])[0]
            chunk_type = data[pos+4:pos+8].decode()
            print(f"Found Chunk: {chunk_type}, Length: {length}")
            chunks.append((chunk_type, length, pos))
            if chunk_type in ['tEXt', 'zTXt', 'iTXt']:
                content = data[pos+8:pos+8+length]
                print(f"Text Chunk Content: {content}")
            pos += length + 12
        except Exception as e:
            print(f"Error parsing at {pos}: {e}")
            break
            
    # 2. Search for common file headers
    headers = {
        'ZIP': b'\x50\x4b\x03\x04',
        'JPEG': b'\xff\xd8\xff',
        'PDF': b'%PDF',
        '7Z': b'7z\xbc\xaf\x27\x1c',
        'RAR': b'Rar!'
    }
    
    for name, header in headers.items():
        idx = data.find(header)
        if idx != -1:
            print(f"Found {name} header at offset {idx}")

    # 3. Search for strings
    import re
    # Look for anything that looks like a flag format: XXXX{...}
    flags = re.findall(b'[a-zA-Z0-9_-]+\\{[a-zA-Z0-9_-]+\\}', data)
    if flags:
        print(f"Potential flags found: {flags}")
    
    # Also just look for any strings length > 10
    all_strings = re.findall(b'[a-zA-Z0-9_{}-]{10,}', data)
    for s in all_strings:
        if b'UMASS' in s.upper() or b'FLAG' in s.upper() or b'CTF' in s.upper():
            print(f"Interesting string: {s}")

if __name__ == "__main__":
    analyze('challenge.png')
