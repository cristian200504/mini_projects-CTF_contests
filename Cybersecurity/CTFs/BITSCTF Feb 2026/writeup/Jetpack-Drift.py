#!/usr/bin/env python3
"""
solve.py — Jetpack Drift forensic CTF solver

Pipeline:
1) Parse chall.pcap (LINKTYPE_LINUX_SLL2) + TCP reassembly
2) Extract /database.sql (get tyler13bradley password)
3) Extract /send-chunks.php (hash-chained encrypted chunks)
4) Order chunks by forward hash-chain, decrypt with AES-CTR + sha256(key=plaintext) chaining
5) Carve embedded PNG and (optionally) OCR the flag

Deps:
  pip install pycryptodome pillow pytesseract
System (for OCR):
  tesseract binary must be installed and on PATH
"""

import re
import struct
import socket
import hashlib
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util import Counter

from PIL import Image

try:
    import pytesseract
    _HAVE_OCR = True
except Exception:
    _HAVE_OCR = False


PCAP_PATH = Path("chall.pcap")
OUT_PNG = Path("extracted.png")
OUT_BIN = Path("decrypted.bin")  # helpful for debugging if needed


# ---------------- PCAP parsing (classic pcap + LINKTYPE_LINUX_SLL2) ----------------

def read_pcap_packets(path: Path):
    data = path.read_bytes()
    if len(data) < 24:
        raise ValueError("PCAP too small")

    magic = data[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):  # little-endian
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):  # big-endian
        endian = ">"
    else:
        raise ValueError("Unknown PCAP magic")

    off = 24
    while off + 16 <= len(data):
        _, _, incl_len, _ = struct.unpack(endian + "IIII", data[off:off + 16])
        off += 16
        pkt = data[off:off + incl_len]
        off += incl_len
        if len(pkt) != incl_len:
            break
        yield pkt


def parse_sll2_ipv4_tcp_payload(pkt: bytes):
    """
    Linux cooked capture v2 header (SLL2) is 20 bytes.
    We only handle IPv4 + TCP payloads here.
    """
    if len(pkt) < 20:
        return None
    proto = struct.unpack("!H", pkt[0:2])[0]
    if proto != 0x0800:  # IPv4
        return None

    ip = pkt[20:]
    if len(ip) < 20:
        return None

    ver_ihl = ip[0]
    if (ver_ihl >> 4) != 4:
        return None
    ihl = (ver_ihl & 0x0F) * 4
    if len(ip) < ihl + 20:
        return None

    if ip[9] != 6:  # TCP
        return None

    src = socket.inet_ntoa(ip[12:16])
    dst = socket.inet_ntoa(ip[16:20])

    tcp = ip[ihl:]
    sport, dport = struct.unpack("!HH", tcp[:4])
    seq = struct.unpack("!I", tcp[4:8])[0]
    data_offset = (tcp[12] >> 4) * 4
    payload = tcp[data_offset:]
    return src, sport, dst, dport, seq, payload


def reassemble_tcp(segments):
    """
    Simple TCP reassembly:
    - sort by seq
    - merge overlaps
    - fill gaps with zeros (rare for this CTF)
    """
    segments = sorted(segments, key=lambda x: x[0])
    out = bytearray()
    cur = None
    for seq, pay in segments:
        if not pay:
            continue
        if cur is None:
            cur = seq
        if seq < cur:
            trim = cur - seq
            if trim >= len(pay):
                continue
            pay = pay[trim:]
            seq = cur
        if seq > cur:
            out.extend(b"\x00" * (seq - cur))
            cur = seq
        out.extend(pay)
        cur += len(pay)
    return bytes(out)


# ---------------- HTTP parsing ----------------

def parse_http_response(stream: bytes, start=0):
    i = stream.find(b"HTTP/", start)
    if i == -1:
        return None

    hdr_end = stream.find(b"\r\n\r\n", i)
    if hdr_end == -1:
        return None

    hdr_blob = stream[i:hdr_end + 4]
    lines = hdr_blob.split(b"\r\n")
    status = lines[0].decode("latin1", errors="replace")

    headers = {}
    for line in lines[1:]:
        if not line or b":" not in line:
            continue
        k, v = line.split(b":", 1)
        headers[k.decode("latin1").strip().lower()] = v.decode("latin1").strip()

    body_start = hdr_end + 4

    # chunked transfer encoding
    if headers.get("transfer-encoding", "").lower() == "chunked":
        body = bytearray()
        p = body_start
        while True:
            line_end = stream.find(b"\r\n", p)
            if line_end == -1:
                raise ValueError("Bad chunked encoding (no size line end)")
            size_line = stream[p:line_end].decode("latin1").strip()
            size = int(size_line.split(";", 1)[0], 16)
            p = line_end + 2
            if size == 0:
                trailer_end = stream.find(b"\r\n\r\n", p)
                end = (trailer_end + 4) if trailer_end != -1 else (p + 2)
                return status, headers, bytes(body), end
            body.extend(stream[p:p + size])
            p += size + 2  # data + \r\n

    # content-length
    if "content-length" in headers:
        size = int(headers["content-length"])
        body = stream[body_start:body_start + size]
        end = body_start + size
        return status, headers, body, end

    # fallback: rest of stream
    return status, headers, stream[body_start:], len(stream)


# ---------------- Crypto / chaining ----------------

def sha256_bytes(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def aes_ctr_xor(data: bytes, key32: bytes) -> bytes:
    # encryption.py behavior: nonce = key[:16], counter init = int.from_bytes(nonce, 'big')
    nonce = key32[:16]
    ctr = Counter.new(128, initial_value=int.from_bytes(nonce, "big"))
    cipher = AES.new(key32, AES.MODE_CTR, counter=ctr)
    return cipher.encrypt(data)  # CTR decrypt == encrypt


# ---------------- PNG carving + OCR ----------------

PNG_SIG = b"\x89PNG\r\n\x1a\n"

def carve_png(blob: bytes) -> bytes:
    start = blob.find(PNG_SIG)
    if start == -1:
        raise ValueError("No PNG signature found in decrypted blob")

    p = start + 8
    while True:
        if p + 8 > len(blob):
            raise ValueError("Truncated PNG while parsing chunks")
        length = struct.unpack(">I", blob[p:p+4])[0]
        ctype = blob[p+4:p+8]
        p += 8
        p += length + 4  # data + CRC
        if ctype == b"IEND":
            return blob[start:p]


def ocr_flag_from_png(png_path: Path) -> str:
    if not _HAVE_OCR:
        raise RuntimeError("pytesseract not available (pip install pytesseract)")

    img = Image.open(png_path)
    text = pytesseract.image_to_string(img)

    m = re.search(r"BITSCTF\{[^}]+\}", text)
    if not m:
        raise ValueError(f"OCR did not find flag-like pattern. OCR text was:\n{text}")

    flag = m.group(0)
    # normalize a couple common OCR slips
    flag = flag.replace(" ", "_")
    flag = flag.replace("O", "0").replace("o", "0")
    return flag


# ---------------- Main solve flow ----------------

def extract_password_from_db(db_text: str) -> str:
    """
    Robustly extract the 3rd column (password) for tyler13bradley from common SQL dump formats.
    Your dump line looks like:
      ('tyler13bradley', 'email', '1VL7p6Rcli8mxgkh'),
    """
    patterns = [
        r"\(\s*'tyler13bradley'\s*,\s*'[^']*'\s*,\s*'([^']+)'\s*\)",  # tuple in VALUES list
        r"VALUES\s*\(\s*'tyler13bradley'\s*,\s*'[^']*'\s*,\s*'([^']+)'\s*\)",  # insert values(...)
        r"'tyler13bradley'\s*,\s*'[^']*'\s*,\s*'([^']+)'",  # looser
    ]
    for pat in patterns:
        m = re.search(pat, db_text, re.IGNORECASE | re.DOTALL)
        if m:
            pw = m.group(1).strip()
            if pw and pw != ",":  # sanity
                return pw

    # helpful snippet for debugging
    idx = db_text.lower().find("tyler13bradley")
    snippet = db_text[max(0, idx - 200): idx + 200] if idx != -1 else db_text[:400]
    raise ValueError(f"Failed to parse password from database.sql. Snippet:\n{snippet}")


def main():
    if not PCAP_PATH.exists():
        raise SystemExit(f"Missing {PCAP_PATH}. Put solve.py next to chall.pcap, or edit PCAP_PATH.")

    # Build TCP segment lists per 4-tuple
    segs = {}
    for pkt in read_pcap_packets(PCAP_PATH):
        parsed = parse_sll2_ipv4_tcp_payload(pkt)
        if not parsed:
            continue
        src, sport, dst, dport, seq, payload = parsed
        if payload:
            segs.setdefault((src, sport, dst, dport), []).append((seq, payload))

    # Reassemble all TCP streams
    streams = {k: reassemble_tcp(v) for k, v in segs.items()}

    def find_stream_containing(needle: bytes):
        for k, v in streams.items():
            if needle in v:
                return k, v
        raise ValueError(f"Could not find stream containing {needle!r}")

    # Extract /database.sql -> password
    k_db, _ = find_stream_containing(b"GET /database.sql")
    s2c_db = streams[(k_db[2], k_db[3], k_db[0], k_db[1])]
    parsed = parse_http_response(s2c_db)
    if not parsed:
        raise ValueError("Could not parse HTTP response for /database.sql")
    _, _, db_body, _ = parsed

    db_text = db_body.decode("utf-8", errors="replace")
    password = extract_password_from_db(db_text)
    print(f"[+] Password recovered: {password}")

    # Extract /send-chunks.php response (chunked encoding)
    k_sc, _ = find_stream_containing(b"GET /send-chunks.php")
    s2c_sc = streams[(k_sc[2], k_sc[3], k_sc[0], k_sc[1])]
    parsed = parse_http_response(s2c_sc)
    if not parsed:
        raise ValueError("Could not parse HTTP response for /send-chunks.php")
    _, _, chunks_body, _ = parsed

    # Parse repeated: NXTCHNKHASH:<64hex>DATA:<binary...>NXTCHNKHASH:...
    marker = b"NXTCHNKHASH:"
    positions = [m.start() for m in re.finditer(re.escape(marker), chunks_body)]
    if not positions:
        raise ValueError("No chunk markers found in send-chunks.php body")

    entries = []
    for i, pos in enumerate(positions):
        nxt_pos = positions[i + 1] if i + 1 < len(positions) else len(chunks_body)
        entry = chunks_body[pos:nxt_pos]
        h_end = entry.find(b"DATA:")
        if h_end == -1:
            raise ValueError("Chunk entry missing DATA: delimiter")
        next_hash = entry[len(marker):h_end].decode("ascii", errors="replace").strip()
        enc = entry[h_end + 5:]
        entries.append((next_hash, enc))

    # Order chunks by forward hash chain: sha256(enc_chunk) -> next_hash
    by_hash = {sha256_hex(enc): (next_hash, enc) for (next_hash, enc) in entries}
    referenced = {nh for (nh, _) in entries if nh != "0" * 64}
    heads = [h for h in by_hash.keys() if h not in referenced]
    if len(heads) != 1:
        raise ValueError(f"Expected exactly 1 chain head, got {len(heads)}")
    head = heads[0]

    ordered_enc = []
    cur = head
    while True:
        next_hash, enc = by_hash[cur]
        ordered_enc.append(enc)
        if next_hash == "0" * 64:
            break
        cur = next_hash

    # Decrypt sequentially (key chain depends on plaintext sha256)
    prev_key = sha256_bytes(password.encode("utf-8"))
    out = bytearray()
    for enc in ordered_enc:
        plain = aes_ctr_xor(enc, prev_key)
        out.extend(plain)
        prev_key = sha256_bytes(plain)

    OUT_BIN.write_bytes(bytes(out))
    print(f"[+] Decrypted blob written to: {OUT_BIN.resolve()}")

    # Carve PNG
    png_bytes = carve_png(bytes(out))
    OUT_PNG.write_bytes(png_bytes)
    print(f"[+] PNG extracted to: {OUT_PNG.resolve()}")

    # OCR flag (optional)
    try:
        flag = ocr_flag_from_png(OUT_PNG)
        print(f"[+] FLAG: {flag}")
    except Exception as e:
        print(f"[!] OCR unavailable/failed: {e}")
        print("[!] Open extracted.png manually to read the flag, or install Tesseract and rerun.")


if __name__ == "__main__":
    main()