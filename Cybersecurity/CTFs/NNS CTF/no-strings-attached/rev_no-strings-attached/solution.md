# No Strings Attached - Solution

## Challenge Description
The challenge provided an x86-64 ELF executable and a description stating that the binary requires a passphrase to unlock. Running `strings` on the binary doesn't reveal the passphrase because the program dynamically constructs it in memory. Only after building the passphrase does it hand it over to a C standard library function (`strcmp`) to compare against the user's input.

## Methodology
The description hinted at using `ltrace` to intercept library calls, but we can effectively achieve the same result using the GNU Debugger (`gdb`). 

By setting a breakpoint on the `strcmp` function, we can inspect the arguments being passed to it right before the comparison happens. In the x86-64 calling convention, the first two arguments to a function are passed in the `$rdi` and `$rsi` registers. 

Here are the steps taken:

1. **Load the binary in GDB**:
   ```bash
   gdb ./no-strings-attached
   ```

2. **Set a breakpoint on `strcmp`**:
   ```gdb
   break strcmp
   ```

3. **Run the program and provide dummy input**:
   ```gdb
   run
   ```
   (We provided the string `"hello"` as input).

4. **Inspect the registers when the breakpoint is hit**:
   When GDB stops at `strcmp`, we can examine the strings pointed to by the `$rdi` and `$rsi` registers.
   ```gdb
   x/s $rdi
   x/s $rsi
   ```

## Results
Upon examining the memory addresses stored in the registers, GDB printed the two strings:
- `$rdi`: `"hello\r"` (Our dummy input)
- `$rsi`: `"NNS{n0_str1ngs_1n_7h3_b1n4ry_bu7_ltr4c3_s4w_7h3_c0mp4r3}"` (The dynamically constructed flag)

## Flag
`NNS{n0_str1ngs_1n_7h3_b1n4ry_bu7_ltr4c3_s4w_7h3_c0mp4r3}`
