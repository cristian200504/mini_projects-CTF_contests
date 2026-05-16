```markdown
# Whisper APK CTF — Solution Write-Up (Step-by-Step)

This write-up documents exactly what I did to recover the access token and retrieve the flag.

---

## 0) Context / Goal

The challenge provides an Android APK. The task is to recover an **access token** and use it to authenticate to a remote endpoint and retrieve the flag.

Key hint: *“Something in the local signal path is leaking more than it should.”*

---

## 1) Extract the APK (initial inspection)

I first extracted the APK using 7zip to inspect its contents.

**Why:** APKs are zip archives. This lets you quickly see if anything obvious is stored in `assets/`, `res/raw/`, etc.

> Note: `AndroidManifest.xml` inside the APK is in *binary AXML* format, so it looks like garbage if opened raw. That’s normal.

---

## 2) Decompile / Reverse to find how tokens are formed

I used JADX (or any decompiler) to inspect the app code and understand the protocol.

**What I was looking for:**
- API endpoints / Socket.IO usage
- token fields (`auth_token`, `session_id`)
- crypto / obfuscation logic
- native libraries (`.so`) and JNI methods

From reversing the logic, the important findings were:

- The app connects to a remote **Socket.IO** server.
- It receives an event named **`session_bundle`** with:
  - `encrypted` (hex string)
  - `length` (integer)
- After decryption, the bundle contains JSON including:
  - `session_id`
  - `auth_token`

I then wrote a Python script to reproduce this:
- Connect to the Socket.IO server
- Capture the `session_bundle`
- Decrypt it
- Extract `auth_token`
- Use it to fetch the flag

---

## 3) Prepare Python environment (Windows)

### 3.1 Fixing the common Socket.IO dependency mistake

At first I hit:

```

ModuleNotFoundError: No module named 'socketio'

````

I mistakenly installed the package named `socketio` (wrong, ancient).

✅ Correct fix: install **python-socketio** client.

**Commands:**

```powershell
py -m pip uninstall socketio -y
py -m pip install "python-socketio[client]" requests
````

**Why:**

* `python-socketio` is the maintained Socket.IO client for Python.
* `requests` is used to call the HTTP flag endpoint.

---

## 4) Run the cracker script against the remote instance

The CTF gave a target:

```
194.102.62.166:29795
```

I ran my script using the explicit Python path (because `python` wasn’t in PATH / Windows alias issue):

```powershell
& "C:\Users\crist\AppData\Local\Programs\Python\Python312\python.exe" `
  "c:\Users\crist\OneDrive\Desktop\Uni vs Threats 2026\whisper\whisper_crack.py" `
  --host 194.102.62.166 --port 29795 --verbose --dump --auto-try-paths
```

### What this does

* Connects to the Socket.IO server:

  * `http://194.102.62.166:29795/socket.io/…`
* Waits for the event `session_bundle`
* Prints the raw payload (`--dump`)
* Decrypts the `encrypted` blob
* Prints the decrypted JSON
* Tries a few common HTTP paths (`--auto-try-paths`)

### What I observed

The server sent `session_bundle` like this:

```json
{
  "encrypted": "<hex>",
  "length": 181
}
```

After decryption, it produced:

```json
{
  "session_id": "d3e4b6b99af4bbd49a5a1ab9a5c84481",
  "auth_token": "ba5fbab33a44079edc8ff3b4bd9a5c1a8dac64107ffcdfc1dcdf5d5d83dfb55b",
  "timestamp": 1772202524,
  "type": "session_init"
}
```

---

## 5) Find the correct flag endpoint

My script tried several endpoints. The key clue was:

* `/api/flag` returned `401` with: `Missing token parameter`

This told me the server expects the token as a **query parameter**, not an Authorization header.

---

## 6) Retrieve the flag using the leaked token

I used the extracted token directly:

### PowerShell (works but uses Invoke-WebRequest alias)

```powershell
curl "http://194.102.62.166:29795/api/flag?token=ba5fbab33a44079edc8ff3b4bd9a5c1a8dac64107ffcdfc1dcdf5d5d83dfb55b"
```

It returned:

```json
{
  "flag":"UVT{1a25b4cdcf840068a67d7cd556020c3bd7149e9848be5603ba06fddcef1a258e}",
  "message":"Access granted. The broadcast was whispering secrets."
}
```

### Cleaner Windows option (real curl)

```powershell
curl.exe "http://194.102.62.166:29795/api/flag?token=ba5fbab33a44079edc8ff3b4bd9a5c1a8dac64107ffcdfc1dcdf5d5d83dfb55b"
```

---

## ✅ Final Flag

`UVT{1a25b4cdcf840068a67d7cd556020c3bd7149e9848be5603ba06fddcef1a258e}`

---

## Summary of Tools & Techniques Used

* 7zip — unpack the APK quickly
* JADX — decompile / inspect Java/Kotlin logic
* Python (`python-socketio`, `requests`) — recreate protocol and decrypt session bundle
* curl / HTTP GET — call flag endpoint with token query parameter

The “local signal path leaking secrets” was effectively the session bundle/token being obtainable from the client’s normal communication flow.

```
```
