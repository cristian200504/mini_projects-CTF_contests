import pyjls
import numpy as np

filename = "sleepy_cpu.jls"

with pyjls.Reader(filename) as r:
    sig_def = r.signals[2]
    data = r.fsr(2, 0, sig_def.length)
    
    print("Mean:", np.mean(data))
    print("Max:", np.max(data))
    print("Min:", np.min(data))

    threshold = 0.003
    
    # smooth the data to remove noise
    window = 50
    smoothed_data = np.convolve(data, np.ones(window)/window, mode='same')
    
    is_sleep = smoothed_data < threshold
    edges = np.diff(is_sleep.astype(int))
    
    sleep_starts = np.where(edges == 1)[0]
    sleep_ends = np.where(edges == -1)[0]
    
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

    # print("Raw durations:", durations)
    # print("Raw durations:", durations)
    chars = [int(round(d / 50.0)) - 1 for d in durations if d > 1000] # filter out short glitches
    # print("Chars:", chars)
    print("Flag:", "".join(chr(c) for c in chars if 32 <= c <= 126))
    print("Last raw duration:", durations[-1])
    print("All long durations:", [d for d in durations if d > 1000])
