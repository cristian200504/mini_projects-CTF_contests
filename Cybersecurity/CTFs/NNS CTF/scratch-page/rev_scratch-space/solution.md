# Scratch Page - Solution

## Challenge Description
The challenge provides an x86-64 ELF Linux binary that asks for a passphrase to unlock it. The flag is constructed in memory but never passed to standard library functions (making `ltrace` useless) and doesn't invoke system calls to open files (making `strace` useless). Instead, it maps an anonymous "scratch page", dynamically builds the flag there, manually checks the user's input, and then zeroes out the page before unmapping it.

## Methodology
The key to solving this challenge is catching the flag in memory *after* it's been decrypted but *before* the program checks it against the user's input and zeroes the memory.

We can inspect the binary's behavior using `objdump`:
```bash
objdump -d -M intel ./scratch-space
```

Analyzing the `main` function reveals the program structure:
1. Prompts for input and reads a guess (`4011a9: call 401050 <read@plt>`).
2. Calls `mmap` to allocate a scratch page and stores the resulting pointer in local memory at `[rbp-0x8]` (`401215: mov QWORD PTR [rbp-0x8],rax`).
3. Decrypts the flag and places it into the mapped memory (Loop from `401222` to `401261`).
4. Prints "checking" and compares the guess with the flag.
5. Zeroes the mapped memory (Loop from `4012c9` to `4012de`).
6. Unmaps the scratch page (`4012ec: call 401060 <munmap@plt>`).

To extract the flag, we can use the GNU Debugger (`gdb`) to set a breakpoint immediately after the decryption loop finishes (at `0x40126e`) and read the string from the mapped memory pointer.

1. **Create a GDB script**:
   ```gdb
   break *0x40126e
   run < input.txt
   print (char*)*(void**)($rbp - 8)
   ```
   *(Note: The pointer to the mmap'd scratch space is stored on the stack at `$rbp - 8`)*

2. **Run GDB with the script**:
   ```bash
   gdb -x script.gdb -batch ./scratch-space
   ```

## Results
When the breakpoint is hit, GDB prints the string located at the address in `[rbp-0x8]`, which successfully reveals the flag!

```text
Breakpoint 1, 0x000000000040126e in main ()
$1 = 0x7ffff7fc1000 "NNS{s34rch3d_7h3_mm4p_b3f0r3_17_w4s_w1p3d}"
```

## Flag
`NNS{s34rch3d_7h3_mm4p_b3f0r3_17_w4s_w1p3d}`
