import gzip

pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'

# Let's search for the pattern IN -> DATA1 -> ACK -> IN -> DATA1 -> ACK -> IN -> NAK -> IN -> NAK
# PIDs:
# IN = 0x69
# DATA1 = 0x4b
# ACK = 0xd2
# NAK = 0x5a

pattern = [0x69, 0x4b, 0xd2, 0x69, 0x4b, 0xd2, 0x69, 0x5a, 0x69, 0x5a]

print("Searching for pattern in pcap...")
with gzip.open(pcap_path, 'rb') as f:
    f.read(24)
    CHUNK = 8 * 1024 * 1024
    buf = bytearray()
    pos = 0
    pkt_num = 0
    
    pids = []
    pkt_indices = []
    
    found_matches = []
    
    while True:
        c = f.read(CHUNK)
        if not c and pos >= len(buf): break
        buf.extend(c)
        while pos + 16 <= len(buf):
            caplen = (buf[pos+8] << 24) | (buf[pos+9] << 16) | (buf[pos+10] << 8) | buf[pos+11]
            if pos + 16 + caplen > len(buf): break
            pkt_start = pos + 16
            pos = pkt_start + caplen
            if caplen > 0:
                pid = buf[pkt_start]
                pids.append(pid)
                pkt_indices.append((pkt_num, pkt_start, caplen))
                
                # Check match against pattern
                if len(pids) >= len(pattern):
                    if pids[-len(pattern):] == pattern:
                        found_matches.append(pkt_num - len(pattern) + 1)
                        print(f"Match found ending at pkt {pkt_num}!")
                
                if len(pids) > 1000:
                    pids = pids[-100:]
                    pkt_indices = pkt_indices[-100:]
                    
            pkt_num += 1
        if pos > 4 * 1024 * 1024:
            buf = buf[pos:]
            pos = 0

print(f"Total pattern matches found: {len(found_matches)}")
