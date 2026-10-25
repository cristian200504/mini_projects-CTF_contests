import struct
import gzip

pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'

with gzip.open(pcap_path, 'rb') as f:
    f.read(24)
    CHUNK_SIZE = 8 * 1024 * 1024
    buf = bytearray()
    pos = 0
    pkt_num = 0
    
    last_in = None
    in_stats = {}
    
    while pkt_num < 5000000:
        chunk = f.read(CHUNK_SIZE)
        if not chunk and pos >= len(buf): break
        buf.extend(chunk)
        
        while pos + 16 <= len(buf):
            caplen = (buf[pos+8] << 24) | (buf[pos+9] << 16) | (buf[pos+10] << 8) | buf[pos+11]
            if pos + 16 + caplen > len(buf): break
            pkt_num += 1
            pkt_start = pos + 16
            pos = pkt_start + caplen
            
            if caplen == 0: continue
            pid = buf[pkt_start]
            if pid == 0x69: # IN token
                raw = buf[pkt_start+1] | (buf[pkt_start+2] << 8)
                addr = raw & 0x7f
                ep = (raw >> 7) & 0x0f
                last_in = (addr, ep)
            elif pid in (0xc3, 0x4b): # DATA
                if last_in:
                    in_stats.setdefault(last_in, {'data0': 0, 'data1': 0, 'nak': 0, 'seq': []})
                    key = 'data1' if pid == 0x4b else 'data0'
                    in_stats[last_in][key] += 1
                    if len(in_stats[last_in]['seq']) < 100:
                        in_stats[last_in]['seq'].append(1 if pid == 0x4b else 0)
                    last_in = None
            elif pid == 0x5a: # NAK
                if last_in:
                    in_stats.setdefault(last_in, {'data0': 0, 'data1': 0, 'nak': 0, 'seq': []})
                    in_stats[last_in]['nak'] += 1
                    last_in = None
            elif pid in (0xe1, 0x2d): # OUT, SETUP
                last_in = None
        
        if pos > 4 * 1024 * 1024:
            buf = buf[pos:]
            pos = 0

print('IN stats in first 5M pkts:')
for k, v in in_stats.items():
    d0 = v['data0']
    d1 = v['data1']
    nak = v['nak']
    seq = v['seq'][:30]
    print(f'Addr {k[0]} ep {k[1]}: DATA0={d0}, DATA1={d1}, NAK={nak}')
    print(f'  First sequence: {seq}')
