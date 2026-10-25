import os
import struct
from PIL import Image

def dechunk_http(data, offset=0):
    pos = offset
    dechunked = bytearray()
    while pos < len(data):
        crlf = data.find(b'\r\n', pos)
        if crlf == -1:
            break
        line = data[pos:crlf].strip()
        try:
            chunk_size = int(line.split(b';')[0], 16)
        except ValueError:
            break
        pos = crlf + 2
        if chunk_size == 0:
            break
        chunk = data[pos : pos + chunk_size]
        dechunked.extend(chunk)
        pos += chunk_size
        if pos < len(data) and data[pos:pos+2] == b'\r\n':
            pos += 2
    return bytes(dechunked)

def decode_urf_stream(urf_bytes, output_prefix="page"):
    pos = 0
    if len(urf_bytes) < 12:
        print("Data too short for URF")
        return []
        
    magic = urf_bytes[pos:pos+8]
    pos += 8
    if magic != b'UNIRAST\x00':
        print(f"Invalid URF magic: {magic}")
        return []
        
    page_count = struct.unpack('>I', urf_bytes[pos:pos+4])[0]
    pos += 4
    print(f"URF header: magic={magic}, declared page_count={page_count}")
    
    page_idx = 0
    saved_images = []
    
    while pos + 32 <= len(urf_bytes):
        page_hdr = urf_bytes[pos:pos+32]
        pos += 32
        
        bpp = page_hdr[0]
        colorspace = page_hdr[1]
        duplex = page_hdr[2]
        quality = page_hdr[3]
        width, height, dpi = struct.unpack('>III', page_hdr[12:24])
        
        print(f"--- Page {page_idx + 1} ---")
        print(f"Dimensions: {width} x {height}, BPP: {bpp}, DPI: {dpi}, Colorspace: {colorspace}")
        
        if width == 0 or height == 0 or bpp not in (8, 24, 32):
            print(f"Unreasonable dimensions or BPP, stopping page parsing at pos {pos-32}")
            break
            
        pixel_size = bpp // 8
        mode = 'L' if bpp == 8 else ('RGB' if bpp == 24 else 'RGBA')
        
        # We can construct raw bytes row by row
        raw_rows = []
        cur_line = 0
        eof = False
        
        while cur_line < height and not eof:
            if pos >= len(urf_bytes):
                print(f"Unexpected end of data at line {cur_line}/{height}")
                eof = True
                break
                
            line_repeat = urf_bytes[pos] + 1
            pos += 1
            
            line_buf = bytearray(b'\xff' * (width * pixel_size))
            col = 0
            
            while col < width:
                if pos >= len(urf_bytes):
                    eof = True
                    break
                code = struct.unpack('b', urf_bytes[pos:pos+1])[0]
                pos += 1
                
                if code == -128:
                    # blank rest of line (white)
                    # already white in line_buf
                    col = width
                    break
                elif 0 <= code <= 127:
                    n = code + 1
                    pix = urf_bytes[pos : pos + pixel_size]
                    pos += pixel_size
                    count = min(n, width - col)
                    line_buf[col*pixel_size : (col+count)*pixel_size] = pix * count
                    col += n
                else: # -127 <= code < 0
                    n = (-code) + 1
                    pix = urf_bytes[pos : pos + n * pixel_size]
                    pos += n * pixel_size
                    count = min(n, width - col)
                    line_buf[col*pixel_size : (col+count)*pixel_size] = pix[:count*pixel_size]
                    col += n
            
            # Append line line_repeat times
            row_bytes = bytes(line_buf)
            for _ in range(min(line_repeat, height - cur_line)):
                raw_rows.append(row_bytes)
                cur_line += 1
                
        # Fill remaining lines with white if any
        white_line = b'\xff' * (width * pixel_size)
        while cur_line < height:
            raw_rows.append(white_line)
            cur_line += 1
            
        full_raw = b''.join(raw_rows)
        img = Image.frombytes(mode, (width, height), full_raw)
        out_name = f"{output_prefix}_{page_idx+1}.png"
        img.save(out_name)
        print(f"Saved {out_name} ({width}x{height})")
        saved_images.append(out_name)
        
        page_idx += 1
        if page_count != 0 and page_idx >= page_count:
            break
            
    return saved_images

if __name__ == "__main__":
    stream_path = r'C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\full_ep10_stream.bin'
    if not os.path.exists(stream_path):
        print(f"Stream file {stream_path} not found!")
        exit(1)
        
    with open(stream_path, 'rb') as f:
        data = f.read()
        
    print(f"Read {len(data)} bytes from {stream_path}")
    
    # Locate all HTTP requests
    req_indices = []
    p = 0
    while True:
        idx = data.find(b'POST ', p)
        if idx == -1:
            break
        req_indices.append(idx)
        p = idx + 5
        
    print(f"Found {len(req_indices)} POST requests at indices: {req_indices}")
    
    for req_num, idx in enumerate(req_indices):
        hdr_end = data.find(b'\r\n\r\n', idx)
        if hdr_end == -1:
            continue
        hdr = data[idx:hdr_end].decode('latin1', errors='replace')
        print(f"\n================ Request {req_num + 1} ================")
        print(hdr[:300])
        body = data[hdr_end+4:]
        
        if 'Transfer-Encoding: chunked' in hdr:
            print("Dechunking HTTP body...")
            payload = dechunk_http(body)
        else:
            payload = body
            
        unirast_idx = payload.find(b'UNIRAST\x00')
        if unirast_idx != -1:
            print(f"Found UNIRAST at offset {unirast_idx} in payload (payload size: {len(payload)})")
            urf_data = payload[unirast_idx:]
            prefix = rf"C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Universal Suffering Begins (USB)\doc_req{req_num+1}"
            decode_urf_stream(urf_data, output_prefix=prefix)
        else:
            print("No UNIRAST found in this request payload.")
