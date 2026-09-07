# Flag Pointer Register - Solution

## Challenge Description
The challenge provides a Windows x86-64 executable that decodes a flag correctly in memory but prints the wrong message due to a mix-up in register assignments right before the `WriteFile` API call. The goal is to either fix the register during debugging or extract the decoded flag manually.

## Methodology
In the x64 Windows calling convention, the first four integer/pointer arguments are passed in the `RCX`, `RDX`, `R8`, and `R9` registers. 
The signature for `WriteFile` is:
```c
BOOL WriteFile(
  HANDLE       hFile,                  // RCX
  LPCVOID      lpBuffer,               // RDX
  DWORD        nNumberOfBytesToWrite,  // R8
  LPDWORD      lpNumberOfBytesWritten, // R9
  LPOVERLAPPED lpOverlapped            // Stack
);
```

By disassembling the binary, we can see the flow before `WriteFile` is called:
```assembly
   1400010b8:	e8 43 ff ff ff       	call   0x140001000       ; Decoder function
   ...
   1400010cd:	48 8d 15 6c 0f 00 00 	lea    0xf6c(%rip),%rdx  ; RDX points to 0x140002040 (Wrong buffer)
   ...
   1400010dd:	ff d3                	call   *%rbx             ; Call WriteFile
```

The decoder function (`0x140001000`) returns the pointer to the decoded flag in `RAX` (`0x140003000`). However, instead of moving `RAX` to `RDX` for the `WriteFile` buffer argument, the program loads a hardcoded pointer to an error message ("Access denied: RDX points to the wrong output buffer.").

To solve this, we can either:
1. Break before the `WriteFile` call in a debugger (like x64dbg) and change `RDX` to equal `RAX`.
2. Extract the static XOR key and encrypted buffer from the binary and decode it ourselves.

Using `objdump`, the key at `0x140002000` is:
`31 72 a9 4c e3 16 85 5b`

And the encrypted flag at `0x140003000` is:
`7f 3c fa 37 91 22 fd 04 59 46 cd 13 d4 7e b6 04 57 1e 9d 2b bc 74 f0 6c 6e 00 cd 34 bc 66 b5 6a 5f 45 9a 28 bc 21 b5 04 06 1a 9a 13 94 64 b5 35 56 2d cb 39 85 70 b6 29 4c`

Writing a simple Python script to XOR the two gives us the plaintext flag.

## Flag
`NNS{r4x_h4d_7h3_fl4g_bu7_rdx_p01n73d_70_7h3_wr0ng_buff3r}`
