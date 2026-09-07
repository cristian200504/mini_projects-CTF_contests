# Patch Tuesday - Solution

## Challenge Description
The challenge provides a Windows x86-64 executable that promises a free flag but does not deliver it out of the box. The objective is to use a debugger or a patching tool to change a conditional jump so that the program follows the path that reveals the flag.

## Methodology
Using `objdump` on the binary to disassemble the `.text` section, we can locate the logic that decides whether to print the flag or reject the user:
```bash
objdump -d ./free-flag.exe
```

Looking at offset `0x140001079`, the program checks a condition and branches:
```assembly
   140001082:	85 c0                	test   %eax,%eax
   140001084:	74 02                	je     0x140001088
   140001086:	eb 05                	jmp    0x14000108d
   140001088:	e9 9a 00 00 00       	jmp    0x140001127
```

If `%eax` is 0 (which it is, since we don't provide a correct magic value), the zero flag is set, and the `je` (Jump if Equal) instruction at `140001084` is taken. This routes execution to `140001088`, which unconditionally jumps to `140001127`—the "failure" path that avoids decrypting the flag. 

If we can stop the `je` instruction from being taken, execution will fall through to `140001086`, which jumps to `14000108d`—the start of the flag decryption loop.

To fix this, we can patch the binary directly:
1. Identify the file offset for virtual address `0x140001084`. The `.text` section starts at `0x140001000` with a file offset of `0x400`. So, the address `0x140001084` is located at file offset `0x484`.
2. The `je` instruction at this offset translates to the bytes `74 02`. 
3. We can overwrite these two bytes with `90 90` (two `NOP` / No Operation instructions).

I wrote a small Python script to patch the executable:
```python
data = bytearray(open('free-flag.exe', 'rb').read())
data[0x484] = 0x90
data[0x485] = 0x90
open('patched.exe', 'wb').write(data)
```

## Results
When running the newly created `patched.exe`, the program successfully fell through the previously blocked path, decrypted the payload, and printed out the correct flag!

## Flag
`NNS{1_h0p3_y0u_p47ch3d_7h3_0pc0d3_dur1ng_run71m3_jnz_15_much_b3773r_7h4n_jz}`
