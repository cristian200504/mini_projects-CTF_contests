# Open Secret - Solution

## Challenge Description
The challenge provides an x86-64 Linux ELF binary that requires a license file to unlock. However, the path to the license file is not hardcoded in the binary as a plain string, so running `strings` on it yields no useful information. The program dynamically builds the file path in memory and then invokes a system call to open it.

## Methodology
The description suggests using a system call tracer like `strace`. Alternatively, since the program directly invokes system calls to interact with the kernel, we can use the GNU Debugger (`gdb`) to catch the specific syscall responsible for opening files.

Modern Linux systems typically use the `openat` system call (syscall number 257) or `open` (syscall number 2). In the x86-64 syscall convention, the path name string is passed via the `$rsi` register for `openat` (where `$rdi` is the directory file descriptor), and `$rdi` for `open`.

Here are the steps to intercept it:

1. **Create a GDB script** to automatically break on the relevant system calls, run the program, and print the arguments.
   ```gdb
   catch syscall openat
   catch syscall open
   run
   x/s $rsi
   ```

2. **Run GDB with the script**:
   ```bash
   gdb -x script.gdb -batch ./open-secret
   ```

3. **Inspect the output**:
   When the program executed, GDB caught the `openat` syscall. Examining the memory at the `$rsi` register revealed the target path:
   ```text
   Catchpoint 1 (call to syscall openat), 0x0000000000401026 in sys ()
   0x403060 <full>: "/home/santey22/.config/nns/key"
   ```
   The program is looking for a file at `~/.config/nns/key`. (It constructs the path dynamically using the `HOME` environment variable).

4. **Create the dummy license file**:
   ```bash
   mkdir -p ~/.config/nns
   touch ~/.config/nns/key
   ```

5. **Run the program again**:
   ```bash
   ./open-secret
   ```

## Results
Once the file `~/.config/nns/key` was present on the filesystem, running `./open-secret` resulted in the program successfully opening the file and outputting the flag!

## Flag
`NNS{7h3_p47h_w4s_h1dd3n_bu7_s7r4c3_s4w_7h3_0p3n}`
