# Time Lock - Solution

## Challenge Description
The challenge provides a Linux x86-64 executable that acts as a "time lock", sealing its contents unless the current date is exactly 1 January 9999. Since we cannot simply wait for the date or change our system clock (and because the flag is actually derived from the correct timestamp), we need to trick the program into thinking the date is correct by intercepting its calls to the C standard library.

## Methodology
The description mentions replacing library functions using the dynamic loader. On Linux, we can achieve this using the `LD_PRELOAD` environment variable, which forces the dynamic linker to load our custom shared library before any others (like `libc`).

1. **Find the targeted function**:
   By using `objdump -R ./time-lock` to view the dynamic relocation records, we can see that the binary imports the `time` function from `GLIBC`:
   ```
   0000000000404010 R_X86_64_JUMP_SLOT  time@GLIBC_2.2.5
   ```
   
2. **Calculate the target timestamp**:
   The `time` function returns a `time_t` representing the number of seconds since the Unix Epoch (January 1, 1970). We need the timestamp for 1 January 9999 at 00:00:00 UTC.
   Using a quick Python script:
   ```python
   import datetime
   print(int(datetime.datetime(9999, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp()))
   ```
   This gives us: `253370764800`.

3. **Write the wrapper library (`faketime.c`)**:
   We write a custom `time` function that always returns our calculated timestamp:
   ```c
   #include <time.h>

   time_t time(time_t *tloc) {
       time_t fake_time = 253370764800;
       if (tloc != NULL) {
           *tloc = fake_time;
       }
       return fake_time;
   }
   ```

4. **Compile and execute**:
   We compile the C code into a shared object (`.so`) file:
   ```bash
   gcc -shared -fPIC -o faketime.so faketime.c
   ```
   Then we run the executable with our library preloaded:
   ```bash
   LD_PRELOAD=./faketime.so ./time-lock
   ```

## Results
With `faketime.so` preloaded, the program asked for the current time, and our library handed it `253370764800`. Convinced that the year was 9999, it successfully derived and printed the flag!

## Flag
`NNS{y0u_c4n_l13_70_4_pr0gr4m_w17h_ld_pr3l04d}`
