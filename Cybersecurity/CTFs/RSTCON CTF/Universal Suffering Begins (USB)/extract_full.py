import gzip
import time

pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'
out_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\full_ep10_stream.bin'

start_time = time.time()
print(f"Starting extraction from {pcap_path}...")

CHUNK_SIZE = 8 * 1024 * 1024
buf = bytearray()
pos = 0
pkt_num = 0

is_target_ep = False
pending_data = None
out_chunks = []
total_bytes = 0
acked_packets = 0

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
            # Unpack big-endian caplen at offset 8
            caplen = (buf[pos+8] << 24) | (buf[pos+9] << 16) | (buf[pos+10] << 8) | buf[pos+11]
            if pos + 16 + caplen > buflen:
                break
            
            pkt_num += 1
            pkt_start = pos + 16
            pos = pkt_start + caplen
            
            if caplen == 0:
                continue
                
            pid = buf[pkt_start]
            if pid == 0xe1: # OUT token
                if caplen >= 3:
                    raw = buf[pkt_start+1] | (buf[pkt_start+2] << 8)
                    is_target_ep = (raw & 0x7f == 7) and ((raw >> 7) & 0x0f == 10)
                else:
                    is_target_ep = False
            elif pid in (0x69, 0x2d): # IN, SETUP
                is_target_ep = False
            elif pid == 0xc3 or pid == 0x4b: # DATA0, DATA1
                if is_target_ep and caplen > 3: # at least PID + 2 CRC bytes
                    pending_data = bytes(buf[pkt_start+1 : pkt_start+caplen-2])
                else:
                    pending_data = None
            elif pid == 0xd2: # ACK
                if pending_data is not None:
                    out_chunks.append(pending_data)
                    total_bytes += len(pending_data)
                    acked_packets += 1
                    pending_data = None
            elif pid in (0x5a, 0x1e, 0xb4): # NAK, STALL, NYET
                pending_data = None
        
        # Buffer sliding
        if pos > 4 * 1024 * 1024:
            buf = buf[pos:]
            pos = 0
            
        now = time.time()
        if now - last_report > 15:
            last_report = now
            print(f"[{now - start_time:.1f}s] Processed {pkt_num} pkts, ACKed ep10 pkts: {acked_packets}, stream size: {total_bytes} bytes")

print(f"Finished in {time.time() - start_time:.1f}s.")
print(f"Total packets processed: {pkt_num}")
print(f"Total ACKed ep10 packets: {acked_packets}")
print(f"Total stream bytes: {total_bytes}")

with open(out_path, 'wb') as f_out:
    for chunk in out_chunks:
        f_out.write(chunk)

print(f"Saved to {out_path} successfully!")
