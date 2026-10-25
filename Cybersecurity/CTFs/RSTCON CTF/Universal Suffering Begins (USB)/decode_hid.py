import gzip
import struct

pcap_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\data.pcap.gz'

# USB HID keycode map
hid_map = {
    0x04: ('a', 'A'), 0x05: ('b', 'B'), 0x06: ('c', 'C'), 0x07: ('d', 'D'),
    0x08: ('e', 'E'), 0x09: ('f', 'F'), 0x0a: ('g', 'G'), 0x0b: ('h', 'H'),
    0x0c: ('i', 'I'), 0x0d: ('j', 'J'), 0x0e: ('k', 'K'), 0x0f: ('l', 'L'),
    0x10: ('m', 'M'), 0x11: ('n', 'N'), 0x12: ('o', 'O'), 0x13: ('p', 'P'),
    0x14: ('q', 'Q'), 0x15: ('r', 'R'), 0x16: ('s', 'S'), 0x17: ('t', 'T'),
    0x18: ('u', 'U'), 0x19: ('v', 'V'), 0x1a: ('w', 'W'), 0x1b: ('x', 'X'),
    0x1c: ('y', 'Y'), 0x1d: ('z', 'Z'),
    0x1e: ('1', '!'), 0x1f: ('2', '@'), 0x20: ('3', '#'), 0x21: ('4', '$'),
    0x22: ('5', '%'), 0x23: ('6', '^'), 0x24: ('7', '&'), 0x25: ('8', '*'),
    0x26: ('9', '('), 0x27: ('0', ')'),
    0x28: ('\n', '\n'), # Enter
    0x2a: ('[BACKSPACE]', '[BACKSPACE]'),
    0x2b: ('\t', '\t'),
    0x2c: (' ', ' '),
    0x2d: ('-', '_'), 0x2e: ('=', '+'), 0x2f: ('[', '{'), 0x30: (']', '}'),
    0x31: ('\\', '|'), 0x33: (';', ':'), 0x34: ("'", '"'), 0x35: ('`', '~'),
    0x36: (',', '<'), 0x37: ('.', '>'), 0x38: ('/', '?'),
}

typed_chars = []
prev_keys = set()

with gzip.open(pcap_path, 'rb') as f:
    f.read(24)
    CHUNK = 8 * 1024 * 1024
    buf = bytearray()
    pos = 0
    last_in = None
    
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
                if pid == 0x69 and caplen >= 3:
                    raw = buf[pkt_start+1] | (buf[pkt_start+2] << 8)
                    last_in = (raw & 0x7f, (raw >> 7) & 0x0f)
                elif pid in (0xc3, 0x4b):
                    if last_in == (5, 1):
                        data = bytes(buf[pkt_start+1:pkt_start+caplen-2])
                        if len(data) >= 8:
                            mod = data[0]
                            shift = bool(mod & 0x22)
                            keys = set(k for k in data[2:8] if k != 0)
                            new_keys = keys - prev_keys
                            for k in new_keys:
                                if k in hid_map:
                                    ch = hid_map[k][1 if shift else 0]
                                    typed_chars.append(ch)
                                else:
                                    typed_chars.append(f'[{hex(k)}]')
                            prev_keys = keys
                        last_in = None
                elif pid == 0x5a:
                    last_in = None
                elif pid in (0xe1, 0x2d):
                    last_in = None
        if pos > 4 * 1024 * 1024:
            buf = buf[pos:]
            pos = 0

raw_text = ''.join(typed_chars)
with open(r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\keystrokes.txt', 'w', encoding='utf-8') as out:
    out.write(raw_text)

clean = []
for ch in typed_chars:
    if ch == '[BACKSPACE]':
        if clean: clean.pop()
    else:
        clean.append(ch)

clean_text = ''.join(clean)
with open(r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\keystrokes_clean.txt', 'w', encoding='utf-8') as out:
    out.write(clean_text)

print('Done decoding keystrokes!')
print('Length clean:', len(clean_text))
print('--- Clean text ---')
print(clean_text)
