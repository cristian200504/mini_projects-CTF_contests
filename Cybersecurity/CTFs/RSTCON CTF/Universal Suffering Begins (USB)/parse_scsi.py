import struct
import gzip

pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'

with gzip.open(pcap_path, 'rb') as f:
    f.read(24)
    CHUNK_SIZE = 8 * 1024 * 1024
    buf = bytearray()
    pos = 0
    pkt_num = 0
    last_tok = None
    
    current_cmd = None
    transfers = []
    
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
                addr = raw & 0x7f
                ep = (raw >> 7) & 0x0f
                last_tok = (pid, addr, ep)
            elif pid in (0xc3, 0x4b):
                if last_tok == (0xe1, 6, 2): # OUT to mass storage
                    data = bytes(buf[pkt_start+1:pkt_start+caplen-2])
                    if data[:4] == b'USBC':
                        tag, xfer_len, flags, lun, cmd_len = struct.unpack('<IIBBB', data[4:15])
                        cdb = data[15:15+cmd_len]
                        current_cmd = {'pkt': pkt_num, 'tag': tag, 'len': xfer_len, 'flags': flags, 'cdb': cdb, 'data': bytearray()}
                    elif current_cmd and (current_cmd['flags'] & 0x80) == 0:
                        current_cmd['data'].extend(data)
                elif last_tok == (0x69, 6, 1): # IN from mass storage
                    data = bytes(buf[pkt_start+1:pkt_start+caplen-2])
                    if data[:4] == b'USBS':
                        if current_cmd:
                            transfers.append(current_cmd)
                            current_cmd = None
                    elif current_cmd and (current_cmd['flags'] & 0x80) != 0:
                        current_cmd['data'].extend(data)
        
        if pos > 4 * 1024 * 1024:
            buf = buf[pos:]
            pos = 0

print(f'Total SCSI transfers captured: {len(transfers)}')
for t in transfers:
    op = t['cdb'][0] if len(t['cdb']) > 0 else 0
    op_name = {0x28: 'READ(10)', 0x2a: 'WRITE(10)', 0x12: 'INQUIRY', 0x25: 'READ_CAPACITY', 0x00: 'TEST_UNIT_READY', 0x23: 'READ_FORMAT_CAPACITIES', 0x1a: 'MODE_SENSE(6)', 0x5a: 'MODE_SENSE(10)'}.get(op, hex(op))
    lba = struct.unpack('>I', t['cdb'][2:6])[0] if op in (0x28, 0x2a) and len(t['cdb']) >= 6 else 0
    p = t['pkt']
    tl = t['len']
    dl = len(t['data'])
    print(f'Pkt {p}: {op_name} LBA={lba} len={tl} actual={dl}')
    if b'rstcon' in t['data'] or b'flag' in t['data']:
        print('  *** FLAG KEYWORD FOUND IN THIS TRANSFER! ***')
        idx = t['data'].find(b'rstcon')
        if idx != -1:
            print('  FLAG:', t['data'][idx:idx+60])
