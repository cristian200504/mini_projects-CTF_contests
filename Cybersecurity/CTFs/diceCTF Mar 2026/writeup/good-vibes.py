#!/usr/bin/env python3
import struct
import socket
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PCAP = "challenge.pcap"
VPN_PORT = 5959


def derive_session_key(ts_sec: int) -> bytes:
    # Matches vpn_derive_session_key()
    x = ts_sec & 0xFFFFFFFF
    out = bytearray()
    for _ in range(32):
        x = (x * 0x19660D + 0x3C6EF35F) & 0xFFFFFFFF
        out.append(x & 0xFF)
    return bytes(out)


def iter_vibepn_packets(path):
    with open(path, "rb") as f:
        gh = f.read(24)
        if len(gh) != 24:
            raise ValueError("bad pcap")

        while True:
            ph = f.read(16)
            if not ph:
                break

            ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", ph)
            data = f.read(incl_len)

            # Linux cooked v2 header is 20 bytes in this capture
            if len(data) < 20:
                continue
            if data[:2] != b"\x08\x00":  # IPv4
                continue

            ip = data[20:]
            if not ip or (ip[0] >> 4) != 4:
                continue
            if ip[9] != 17:  # UDP
                continue

            ihl = (ip[0] & 0x0F) * 4
            src = socket.inet_ntoa(ip[12:16])
            dst = socket.inet_ntoa(ip[16:20])

            udp = ip[ihl:ihl + 8]
            if len(udp) < 8:
                continue

            sport, dport, ulen, csum = struct.unpack("!HHHH", udp)
            payload = ip[ihl + 8:ihl + ulen]

            if sport != VPN_PORT and dport != VPN_PORT:
                continue
            if not payload or payload[0] != 0xBE:
                continue

            pkt_type = payload[1]
            plen = struct.unpack("!H", payload[2:4])[0]
            seq = struct.unpack("!I", payload[4:8])[0]

            yield {
                "ts": ts_sec,
                "src": src,
                "dst": dst,
                "sport": sport,
                "dport": dport,
                "type": pkt_type,
                "plen": plen,
                "seq": seq,
                "raw": payload,
            }


def main():
    pkts = list(iter_vibepn_packets(PCAP))
    if len(pkts) < 4:
        raise RuntimeError("not enough VPN packets found")

    hello = pkts[0]
    challenge = pkts[1]
    response = pkts[2]
    established = pkts[3]

    print("[*] HELLO      ", hello["src"], "->", hello["dst"])
    print("[*] CHALLENGE  ", challenge["src"], "->", challenge["dst"])
    print("[*] RESPONSE   ", response["src"], "->", response["dst"])
    print("[*] ESTABLISHED", established["src"], "->", established["dst"])

    # Key is derived from the CHALLENGE packet second
    key = derive_session_key(challenge["ts"])
    aes = AESGCM(key)

    print(f"[*] Session key: {key.hex()}")

    # CHALLENGE layout:
    #   body[0:65]   = server pubkey
    #   body[65:77]  = nonce
    #   body[77:]    = AES-GCM(ciphertext||tag) of 32-byte challenge
    body = challenge["raw"][20:]
    server_pub = body[:65]
    chall_nonce = body[65:77]
    chall_ct = body[77:]

    chall_plain = aes.decrypt(chall_nonce, chall_ct, None)
    print(f"[*] Decrypted server challenge: {chall_plain.hex()}")

    # Decrypt data packets
    print("\n[*] Decrypted data packets:\n")
    for i, pkt in enumerate(pkts[4:], start=4):
        if pkt["type"] not in (0x10, 0x20):
            continue

        raw = pkt["raw"]
        nonce = raw[8:20]
        aad = raw[:20]
        ct = raw[20:]

        try:
            pt = aes.decrypt(nonce, ct, aad)
        except Exception:
            continue

        ascii_preview = "".join(chr(b) if 32 <= b < 127 else "." for b in pt)
        print(
            f"pkt#{i:04d} type=0x{pkt['type']:02x} seq={pkt['seq']:>4} "
            f"len={len(pt):>4}  {ascii_preview}"
        )

        if b"dice{" in pt:
            start = pt.index(b"dice{")
            end = pt.find(b"}", start)
            if end != -1:
                flag = pt[start:end + 1].decode()
                print(f"\n[+] FLAG = {flag}")
                return

    print("\n[-] No flag found")


if __name__ == "__main__":
    main()