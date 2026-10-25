import struct
import gzip
import time

pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'

start_time = time.time()
print(f"Starting extraction of IN streams from {pcap_path}...")

CHUNK_SIZE = 8 * 1024 * 1024
buf = bytearray()
pos = 0
pkt_num = 0

last_tok = None
pending_data = None
pending_tok = None

streams = {
    (0x69, 7, 11): bytearray(), # IN addr 7 ep 11
    (0x69, 7, 6): bytearray(),  # IN addr 7 ep 6
    (0xe1, 7, 3): bytearray(),  # OUT addr 7 ep 3
}

target_tokens = set(streams.keys())

with gzip.open(pcap_path, 'rb') as f:
    f.read(24) # pcap header
    
    last_report = time.time()
    
    while True:
        chunk = f.read(CHUNK_SIZE)
        if not chunk and pos >= len(buf):
            break
        buf.extend(chunk)
        
        buflen = len(buf)
        while pos + 16 <= buflen:
            caplen = (buf[pos+8] << 24) | (buf[pos+9] << 16) | (buf[pos+10] << 8) | buf[pos+11]
            if pos + 16 + caplen > buflen:
                break
            
            pkt_num += 1
            pkt_start = pos + 16
            pos = pkt_start + caplen
            
            if caplen == 0:
                continue
                
            pid = buf[pkt_start]
            if pid in (0xe1, 0x69, 0x2d): # OUT, IN, SETUP
                if caplen >= 3:
                    raw = buf[pkt_start+1] | (buf[pkt_start+2] << 8)
                    addr = raw & 0x7f
                    ep = (raw >> 7) & 0x0f
                    last_tok = (pid, addr, ep)
                else:
                    last_tok = None
            elif pid in (0xc3, 0x4b): # DATA0, DATA1
                if last_tok in target_tokens and caplen > 3:
                    pending_data = bytes(buf[pkt_start+1 : pkt_start+caplen-2])
                    pending_tok = last_tok
                else:
                    pending_data = None
                    pending_tok = None
            elif pid == 0xd2: # ACK
                if pending_data is not None:
                    streams[pending_tok].extend(pending_data)
                    pending_data = None
                    pending_tok = None
            elif pid in (0x5a, 0x1e, 0xb4): # NAK, STALL, NYET
                pending_data = None
                pending_tok = None
        
        if pos > 4 * 1024 * 1024:
            buf = buf[pos:]
            pos = 0
            
        now = time.time()
        if now - last_report > 20:
            last_report = now
            print(f"[{now - start_time:.1f}s] Processed {pkt_num} pkts... ep11={len(streams[(0x69, 7, 11)])}, ep6={len(streams[(0x69, 7, 6)])}, ep3={len(streams[(0xe1, 7, 3)])}")

print(f"Extraction complete in {time.time() - start_time:.1f}s.")
for tok, data in streams.items():
    pname = 'IN' if tok[0] == 0x69 else 'OUT'
    name = f"addr{tok[1]}_ep{tok[2]}_{pname}"
    path = rf"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\{name}.bin"
    with open(path, 'wb') as f_out:
        f_out.write(data)
    print(f"Saved {name}.bin: {len(data)} bytes")
    
    # Check for rstcon or flag
    for kw in [b'rstcon', b'flag', b'CTF', b'RSTCON']:
        idx = data.find(kw)
        if idx != -1:
            print(f"  *** KEYWORD {kw} FOUND in {name}! ***")
            print(f"  {data[max(0, idx-20) : idx+60]}")
