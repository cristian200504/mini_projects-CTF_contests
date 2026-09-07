# Min Beste Venn - Challenge Solution

## Overview
This challenge involves forensic analysis of a network capture (`capture.pcap`). The capture contains HTTP traffic that reveals a data exfiltration technique using blind CSS injection. The scenario involves a chat application (referred to as "chatflare") where messages are exfiltrated character-by-character over HTTP `HEAD` requests.

## Step-by-Step Analysis

### 1. Initial Discovery
Upon extracting the provided `forensics_min-beste-venn.tar.gz` archive, we find a `capture.pcap` file. Analyzing the PCAP (e.g., using Wireshark or `scapy`), we notice a large volume of HTTP `HEAD` requests directed towards a Cloudflare-hosted server on port 80.

The requested URLs follow a very specific pattern:
`/cf1787417395/d/h/0/06.css`
`/cf1787417395/d/c/1/231.css`

The server responds to most of these requests with a `404 Not Found`, indicating that the exfiltration relies on the *requests themselves* rather than the server's responses.

### 2. URL Structure Breakdown
By parsing all the requested URLs, we can identify the following structure:
`/cf<session_id>/d/<message_type>/<message_id>/<payload>.css`

*   **`message_type`**: Appears as either `h` or `c`. Based on the context of a chat application, these likely stand for "header" (or hash/metadata) and "content".
*   **`message_id`**: Identifies the message being sent (`0` and `1` are present in the capture).
*   **`payload`**: Numeric values like `06`, `12`, `157`, `547`.

### 3. Decoding the Payload
At first glance, the payload numbers might seem like octal values or direct ASCII codes. However, looking closely at the sequence, we notice values like `81`, `95`, etc., ruling out strict octal. 

The breakthrough comes from observing that the last digit (the ones place) is **always between 0 and 7**, while the tens place scales up linearly (up to `54` for message 1). 
This indicates a binary encoding scheme where the payload represents the index of a bit set to `1`:
*   `payload // 10` = **Byte index** of the character in the string.
*   `payload % 10`  = **Bit index** (0-7) within that byte.

For example, a payload of `157` means: **Byte 15, Bit 7** is a `1`.

### 4. Bypassing the CSS Spam Phase
In CSS injection attacks, the browser constantly re-evaluates CSS rules as the DOM updates (e.g., as a user types a message character by character). Because of this, the PCAP contains many duplicate requests. 

To reconstruct the actual string, we only need to look at the **first occurrence** of each payload value before duplicates begin appearing.

### 5. Reconstructing the Data
By grouping the bits into bytes (using Most Significant Bit first) for the unique initial payload requests, we decode the underlying messages:

**Message 0:**
*   **Header (`h`)**: `\x0fmin beste venn?`
*   **Content (`c`)**: `\x03ja?`

**Message 1:**
*   **Header (`h`)**: `\x0fcan i haz flag?`
*   **Content (`c`)**: `\x36NNS{1_l0v3_ch4tt1ng_w1th_m1n_b3st3_v3nn_1n_th3_cl0ud5}`

*(Note: The first byte of each decoded string represents its length, a common trait in Pascal-style strings).*

## Conclusion
The flag is found within the content of Message 1:
**`NNS{1_l0v3_ch4tt1ng_w1th_m1n_b3st3_v3nn_1n_th3_cl0ud5}`**
