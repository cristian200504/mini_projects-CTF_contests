import re
with open('/tmp/millennium_traffic.pcap', 'rb') as f:
    data = f.read()

# Pattern: Content-Type: application/x-epoch-encrypted\r\n
# X-Epoch-Cipher: AES-128-CBC\r\n\r\n
# <hex_string>\r\n

# Use bytes pattern to find the hex string precisely
pattern = b'AES-128-CBC\r\n\r\n([0-9a-f]+)'
m = re.search(pattern, data)
if m:
    hex_str = m.group(1).decode()
    print(f"HEX_LEN: {len(hex_str)}")
    print(f"HEX_STR: {hex_str}")
else:
    # Try looking for just digits in case of line breaks
    print("Trying alternative pattern...")
    start_tag = b'AES-128-CBC\r\n\r\n'
    idx = data.find(start_tag)
    if idx >= 0:
        segment = data[idx+len(start_tag):idx+len(start_tag)+300]
        # Clean up segment to get hex only
        clean_hex = re.findall(b'[0-9a-f]', segment)
        hex_str = b"".join(clean_hex).decode()
        print(f"CLEAN_HEX_LEN: {len(hex_str)}")
        print(f"CLEAN_HEX_STR: {hex_str}")
    else:
        print("Could not find start tag.")
