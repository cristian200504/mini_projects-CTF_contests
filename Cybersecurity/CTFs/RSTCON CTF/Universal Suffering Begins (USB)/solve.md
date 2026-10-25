# Universal Suffering Begins (USB) - Solve & Writeup

## Challenge Information
- **Category:** Forensics / Hardware / Network / USB
- **Points:** 210
- **Author:** Veryyes
- **Files Provided:** `data.pcap.gz` (~437 MB compressed, ~1.8 GB uncompressed)
- **Description:** 
  > IN DATA1 ACK IN DATA1 ACK IN NACK IN NACK

---

## 1. Challenge Overview & Packet Capture Format

The provided capture file `data.pcap.gz` is a raw low-level USB 2.0 bus trace containing over 60 million packets.
Inspecting the global PCAP header:
- **Magic:** `0xa1b23c4d` (Big-endian PCAP)
- **Link Layer Type:** `288` (`LINKTYPE_USB_2_0`)

Unlike higher-level `LINKTYPE_USBPCAP` or Linux `usbmon` captures which only record complete URB transfers, `LINKTYPE_USB_2_0` records individual raw USB tokens and packet identifiers (PIDs) transmitted across the bus:
- `0x69`: `IN` Token
- `0xe1`: `OUT` Token
- `0x2d`: `SETUP` Token
- `0xa5`: `SOF` (Start of Frame)
- `0x78`: `SPLIT` Token (High-speed split transactions for Full/Low-speed devices)
- `0xc3` / `0x4b`: `DATA0` / `DATA1`
- `0xd2`: `ACK`
- `0x5a`: `NAK`
- `0xb4`: `NYET`

---

## 2. Bus Reconnaissance & Device Enumeration

Scanning through the capture reveals several USB devices connected to the host via hubs:

| USB Address | Endpoints | Device Type | Protocol / Traffic |
|:---:|:---:|:---:|:---|
| **3** | EP 1 IN | High-Speed Hub | Periodic status change polling (returning NAK) |
| **4** | EP 1 IN | High-Speed Hub | Periodic status change polling (returning NAK) |
| **5** | EP 1 IN, EP 2 IN | USB HID Composite | Low-speed split transactions: Keyboard (EP 1) & Mouse (EP 2) |
| **6** | EP 1 IN, EP 2 OUT | USB Mass Storage | USB Mass Storage Bulk-Only Transport (BOT) / SCSI |
| **7** | EP 3, 6, 10, 11 | USB IPP Printer | Canon MG3600 Series (IPP-over-USB / CUPS) |

---

## 3. Investigating the Devices: Red Herrings & Author Trolls

### A. The IPP-over-USB Printer (Device Address 7)
Device 7 communicated via IPP (Internet Printing Protocol over USB). Reassembling the bulk OUT stream on endpoint 10 (`full_ep10_stream.bin`) revealed HTTP/IPP print requests containing Apple Raster (`UNIRAST\0`) documents:
- **Job 1:** A medical encounter visit summary for `Okonkwo, Desmond A.`. Decoding the raster image and running OCR revealed:
  ```text
  Visit Date: 07/19/2026
  Diagnosis: Lack of a rstcon{} flag Imao
  ```
- **Job 2:** A laboratory results report for `Villareal, Susan K.`.

The author deliberately embedded a troll message in Job 1.

### B. The USB HID Keyboard (Device Address 5)
Address 5, Endpoint 1 sent 888 HID reports (8 bytes each). Extracting the reports and mapping the USB HID keycodes to characters:
```text
Patient Visit Summary

Patient: Jordan A. Whitfield
DOB 03/14/1989
Visit Date: 07/25/2026

Primary Complaint:
Patient presents with intermittend lower back pain, mild fatigue, and occasinal tension headaches over the pas three weeks

Notes:
Mechnical lower back strain, ;ikely related to prologned sendary posture
Playing too many VTFs and not finding any flags LOL
```
Another intentional troll from the challenge author.

---

## 4. The Solution: USB Mass Storage & Deleted Files (Device Address 6)

### SCSI Extraction & Filesystem Forensics
Device Address 6 uses the USB Mass Storage Bulk-Only Transport protocol (SCSI Command Block Wrappers - `USBC` / Command Status Wrappers - `USBS`).
By parsing all `WRITE(10)` (opcode `0x2a`) and `READ(10)` (opcode `0x28`) SCSI commands, we reconstructed the disk sectors read and written by the host.

Inspecting the NTFS Master File Table (MFT) records stored across the disk sectors revealed resident and deleted records in `.Trash-1000`:
- `Alzheimer_Disease_A_Report.docx`
- `chainsaw_guy.png`

### Carving `chainsaw_guy.png`
Carving the PNG file directly from the SCSI write buffer at byte offset 12,288 yielded a 199,460-byte PNG image (`387 x 516` pixels).

The image depicts a Chainsaw Man comic panel meme with speech bubbles:
1. First speech bubble (top panel):
   ```text
   rstcon{
   yu_es_b
   e_m0n}
   TAANK YOU---
   BECAu5E... this is a ctf.
   ```
2. Second speech bubble (middle panel):
   ```text
   rstcon{yu_es_be_m0n}??
   ```

### Character Verification
A pixel-by-pixel inspection of the raster font inside `chainsaw_guy.png` confirmed every character:
- Line 1: `rstcon{`
- Line 2: `yu_es_b`
- Line 3: `e_m0n}`

Pronouncing the segments aloud:
- `yu` = **U**
- `es` = **S**
- `be` = **B**
- `m0n` = **mon** (`usbmon`)

---

## 5. Flag

```text
rstcon{yu_es_be_m0n}
```
