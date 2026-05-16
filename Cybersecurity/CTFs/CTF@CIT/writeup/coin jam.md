# Coin Jam CTF Writeup

## Objective
The goal of this challenge was to collect all the coins in the `coinjam.exe` game to retrieve the hidden flag, which follows the format `CIT{example_flag}`.

## Initial Analysis
1. **Static Analysis**: Extracting strings from `coinjam.exe` revealed strings like `CIT{tamper_detected}` and `CIT{invalid_guard}`. This indicated that:
   - The actual flag was not stored in plaintext and was likely decrypted or generated dynamically in memory upon winning the game.
   - The binary had anti-tampering mechanisms to prevent simple memory manipulation or patching.

## Reverse Engineering
Using `capstone` and `pefile` in Python, we disassembled the `.text` section of the binary to locate the game logic.
1. **Finding the Score Variable**: We traced RIP-relative addressing and identified that the score (number of coins collected) was stored at `ImageBase + 0x1d01c`.
2. **Identifying the Anti-Tamper Guard**: By analyzing the instructions, we found a conditional jump at file offset `0x1dd9` (`83 f8 0a` -> `cmp eax, 0xa`) that acts as a guard/validation check for the score.

## Exploitation
To solve the challenge, we combined binary patching with dynamic memory manipulation.

1. **Bypassing the Guard**: We created a patched version of the binary (`coinjam_patched.exe`) by changing the byte at file offset `0x1ddb` to `0x00`. This successfully disabled the validation check that would otherwise trigger the `CIT{tamper_detected}` or `CIT{invalid_guard}` flags.
2. **Injecting the Winning Score**: With the patched game running, we executed `patch_score.py`. This script used the Windows API (`OpenProcess`, `WriteProcessMemory`) to directly write the winning score (`10`) into the running process's memory at `BaseAddress + 0x1d01c`.
3. **Extracting the Flag**: Trick the game into thinking we won caused it to decrypt the real flag in memory. We ran `dump_mem.py`, which used `ReadProcessMemory` to scan the live, committed memory pages of the process for the `CIT{` string.

## Result
The memory dump successfully captured the decrypted flag from RAM:
**`CIT{5x4W28cLIbUq}`**
