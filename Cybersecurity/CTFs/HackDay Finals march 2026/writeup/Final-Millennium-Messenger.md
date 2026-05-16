# Millennium Messenger: Project Epoch CTF Write-up

## Challenge Overview
The "Millennium Messenger" CTF involves a series of vulnerabilities (CRLF Header Injection, Steganography, and Format String) to decrypt archived MSNP8 traffic captured on a legacy server.

**Final Flag:** `HACKDAY{f45fb4fb514e6b6e94c29873da4f36cfdc3a6f015fec816a2fe27368e88c4b5e}`

---

## 1. Web Reconnaissance
Analysis of the `static/js/messenger.js` script revealed:
- Custom Minesweeper game on the `index.html`.
- API endpoints: `/api/chat`, `/api/minesweeper`, `/api/set_displayname`.
- A critical comment about `X-Internal-Access: true` being required for restricted directories.
- A reflection vulnerability in the `/api/set_displayname` API.

---

## 2. CRLF Header Injection
The `/api/set_displayname` API reflects the `name` parameter directly in the `X-MSN-DisplayName` response header without sanitization. 

By sending a payload containing CRLF (`\r\n`), we could inject the `X-Internal-Access` header into the server's response:
- **Request**: `POST /api/set_displayname`
- **Body**: `{"name": "Admin\r\nX-Internal-Access: true"}`
- **Result**: Gained access to `/archives/download/` and `/cgi-bin/`.

---

## 3. Extracting the IV (Steganography)
In the `/archives/download/` directory, we found `smiley_y2k.png`. Using `zsteg` revealed a hidden string in the LSB:
- **LSB (Red)**: `Y2K_BuG_19990101`
- **IV**: `Y2K_BuG_19990101`

---

## 4. Extracting the Key (Format String + Logical Mapping)
The legacy CGI tool `/cgi-bin/msn_diag` handles MSNP commands. The `MSG` command's `body` parameter was found to be vulnerable to a format string attack (`printf(user_body)`).

By scanning memory (`0x0804a010`), we identified the internal path for the key file: `/app/data/msn_epoch.key`. Since we already had the internal access header, we downloaded the key directly.
- **Key**: `M1ll3nn1um_K3y!!`

---

## 5. Decrypting the Ciphertext
The `millennium_traffic.pcap` file contained an encrypted message with the following hex-encoded payload:
`336879c45d3b02dcd2048688541269206e496787d0a0e77995e57df88391b40427b64eec09d0634ccb684d3ffb6e52561c3d99cb5cc23d5794e0f396d52ee9fd9a6483024ec36ca5180c7988579fa43a`

Using **AES-128-CBC** decryption:
- **Key**: `M1ll3nn1um_K3y!!`
- **IV**: `Y2K_BuG_19990101`

**Final Decrypted Flag**: `HACKDAY{f45fb4fb514e6b6e94c29873da4f36cfdc3a6f015fec816a2fe27368e88c4b5e}`
