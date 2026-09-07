# Sleepy CPU - CTF Challenge Solution

## Overview
This challenge involves a side-channel power analysis attack. We are provided with a Joulescope trace file (`sleepy_cpu.jls`) that recorded the current consumption of a microcontroller, along with its firmware source code.

## Analysis of the Firmware
Looking at the provided firmware source code in `main.c`:

```c
for (char* c = flag; *c; c++)
{
    for (int i = 0; i < 100000; i++)
    {
        __asm volatile ("nop");
    }

    k_sleep(K_MSEC(*c));
}
```

The code iterates over each character of the hidden `flag` string. For each character, it does two things:
1. Executes a busy loop (100,000 `nop` instructions). This results in a spike of active CPU time and high power consumption.
2. Calls `k_sleep(K_MSEC(*c))`, which puts the microcontroller to sleep for exactly `*c` milliseconds, where `*c` is the ASCII integer value of the character. This results in an extended period of minimal power consumption.

This means we can deduce the ASCII value of each flag character simply by measuring the duration (in milliseconds) of each low-power sleep period between the high-power spikes.

## Extracting the Flag
To extract the flag, we can write a Python script utilizing the `pyjls` library to parse the Joulescope file and measure the duration of these sleep cycles.

The sample rate of the capture is 50,000 Hz, meaning there are 50 samples per millisecond. 
By applying a threshold, we can filter the signal into binary states: `active` vs `sleep`. We then count the number of samples in each sleep period and divide by 50 to get the duration in milliseconds, which directly corresponds to the ASCII character value.

### Solution Script (`solve.py`)
```python
import pyjls
import numpy as np

filename = "sleepy_cpu.jls"

with pyjls.Reader(filename) as r:
    # Read the current signal (Signal ID 2)
    sig_def = r.signals[2]
    data = r.fsr(2, 0, sig_def.length)
    
    # 0.003 A is a good threshold to separate active spikes from sleep
    threshold = 0.003
    
    # Smooth the data to remove noise
    window = 50
    smoothed_data = np.convolve(data, np.ones(window)/window, mode='same')
    
    # Binarize into sleep vs active
    is_sleep = smoothed_data < threshold
    edges = np.diff(is_sleep.astype(int))
    
    # Find edges
    durations = []
    current_start = None
    for i, e in enumerate(edges):
        if e == 1:
            current_start = i
        elif e == -1 and current_start is not None:
            durations.append(i - current_start)
            current_start = None

    if current_start is not None:
        durations.append(len(edges) - current_start)

    # Convert samples to ms (50 samples = 1 ms). 
    # We subtract 1 to account for the overhead delay in the sleep function.
    chars = [int(round(d / 50.0)) - 1 for d in durations if d > 1000]
    
    # Convert ASCII integers back to characters
    flag = "".join(chr(c) for c in chars if 32 <= c <= 126)
    
    # The final closing brace gets merged with the idle sleep in the capture,
    # so we append it to complete the CTF flag format.
    print("Flag:", flag + "}")
```

Running the script gives us the hidden flag:
**`NNS{pow3r_4n4lys15_c4n_rev3al_what_th3_cpu_i5_w0rk1ng_on}`**
