import struct
import gzip
import os
import pickle

dump_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\mft_sectors.pkl'
pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'

if not os.path.exists(dump_path):
    print("Reading pcap to extract MFT sectors...")
    with gzip.open(pcap_path, 'rb') as f:
        f.read(24)
        CHUNK_SIZE = 8 * 1024 * 1024
        buf = bytearray()
        pos = 0
        pkt_num = 0
        last_tok = None
        current_cmd = None
        mft_sectors = {}
        
        while True:
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
                if pid in (0xe1, 0x69, 0x2d):
                    raw = buf[pkt_start+1] | (buf[pkt_start+2] << 8)
                    last_tok = (pid, raw & 0x7f, (raw >> 7) & 0x0f)
                elif pid in (0xc3, 0x4b):
                    if last_tok == (0xe1, 6, 2):
                        data = bytes(buf[pkt_start+1:pkt_start+caplen-2])
                        if data[:4] == b'USBC':
                            tag, xfer_len, flags, lun, cmd_len = struct.unpack('<IIBBB', data[4:15])
                            cdb = data[15:15+cmd_len]
                            op = cdb[0] if len(cdb) > 0 else 0
                            lba = struct.unpack('>I', cdb[2:6])[0] if op in (0x28, 0x2a) and len(cdb) >= 6 else 0
                            current_cmd = {'op': op, 'lba': lba, 'flags': flags, 'data': bytearray()}
                    elif last_tok == (0x69, 6, 1):
                        data = bytes(buf[pkt_start+1:pkt_start+caplen-2])
                        if data[:4] == b'USBS':
                            if current_cmd and current_cmd['op'] == 0x28:
                                mft_sectors[current_cmd['lba']] = bytes(current_cmd['data'])
                            current_cmd = None
                        elif current_cmd and (current_cmd['flags'] & 0x80) != 0:
                            current_cmd['data'].extend(data)
            
            if pos > 4 * 1024 * 1024:
                buf = buf[pos:]
                pos = 0

    with open(dump_path, 'wb') as f_out:
        pickle.dump(mft_sectors, f_out)
    print(f"Saved {len(mft_sectors)} sectors to {dump_path}")
else:
    print(f"Loading cached sectors from {dump_path}...")
    with open(dump_path, 'rb') as f_in:
        mft_sectors = pickle.load(f_in)

print(f"Total read transfers: {len(mft_sectors)}")

file_records = []
for lba, sdata in sorted(mft_sectors.items()):
    p = 0
    while True:
        idx = sdata.find(b'FILE', p)
        if idx == -1: break
        rec = sdata[idx:idx+1024]
        if len(rec) == 1024:
            file_records.append((lba, idx, rec))
        p = idx + 4

print(f"Found {len(file_records)} FILE (MFT) records!")

all_files = []

for lba, idx, rec in file_records:
    # Search for all strings in this record
    p = 0
    names = []
    while True:
        fn_idx = rec.find(b'\x30\x00\x00\x00', p)
        if fn_idx == -1: break
        if fn_idx + 8 <= len(rec):
            attr_len = struct.unpack('<I', rec[fn_idx+4:fn_idx+8])[0]
            if 0 < attr_len <= len(rec) - fn_idx:
                attr_data = rec[fn_idx:fn_idx+attr_len]
                if len(attr_data) >= 22 and attr_data[8] == 0: # resident
                    content_offset = struct.unpack('<H', attr_data[20:22])[0]
                    content = attr_data[content_offset:]
                    if len(content) > 66:
                        fn_len = content[64]
                        if len(content) >= 66 + fn_len*2:
                            fn = content[66:66+fn_len*2].decode('utf-16le', errors='replace')
                            names.append(fn)
        p = fn_idx + 4
        
    if names:
        all_files.append((lba, idx, names))
        print(f"Record at LBA {lba}+{idx}: {names}")
        
    # Check for $DATA attribute (0x80)
    data_idx = rec.find(b'\x80\x00\x00\x00')
    if data_idx != -1 and data_idx + 8 <= len(rec):
        attr_len = struct.unpack('<I', rec[data_idx+4:data_idx+8])[0]
        if 0 < attr_len <= len(rec) - data_idx:
            attr_data = rec[data_idx:data_idx+attr_len]
            if len(attr_data) >= 22 and attr_data[8] == 0: # resident data
                val_len = struct.unpack('<I', attr_data[16:20])[0]
                val_off = struct.unpack('<H', attr_data[20:22])[0]
                val = attr_data[val_off:val_off+val_len]
                if any(kw in val.lower() for kw in [b'rstcon', b'flag', b'{', b'pass', b'secret']):
                    print(f"  *** INTERESTING RESIDENT DATA in record ({names}): {val} ***")
                    
    # Also check raw bytes of record for rstcon
    if b'rstcon' in rec:
        k = rec.find(b'rstcon')
        print(f"  *** RAW 'rstcon' IN MFT RECORD ({names}): {rec[k:k+60]} ***")
