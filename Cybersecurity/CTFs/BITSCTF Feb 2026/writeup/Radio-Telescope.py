import numpy as np

def rolling_var(x: np.ndarray, w: int) -> np.ndarray:
    """Fast rolling variance using cumulative sums."""
    cs = np.cumsum(np.insert(x, 0, 0.0))
    cs2 = np.cumsum(np.insert(x * x, 0, 0.0))
    s = cs[w:] - cs[:-w]
    s2 = cs2[w:] - cs2[:-w]
    mean = s / w
    return (s2 / w) - (mean * mean)

def group_contiguous(idxs):
    """Group sorted indices into contiguous runs."""
    groups = []
    if len(idxs) == 0:
        return groups
    start = prev = idxs[0]
    for i in idxs[1:]:
        if i == prev + 1:
            prev = i
        else:
            groups.append((start, prev))
            start = prev = i
    groups.append((start, prev))
    return groups

def decode_from_quiet_windows(signal: np.ndarray, window: int = 20) -> str:
    rv = rolling_var(signal, window)

    # Adaptive threshold: "way quieter than typical"
    med = np.median(rv)
    thr = med * 0.001  # works on this challenge; adaptive vs hard-coded absolute numbers

    quiet_starts = np.where(rv < thr)[0]
    groups = group_contiguous(quiet_starts)

    chars = []
    for (gstart, _) in groups:
        seg = signal[gstart:gstart + window]
        ch = chr(int(round(seg.mean())))
        chars.append(ch)

    return "".join(chars)

def main():
    path = "rt7-log.txt"
    signal = np.loadtxt(path)

    msg = decode_from_quiet_windows(signal, window=20)
    print("Recovered message:", msg)

    # Fix expected CTF prefix format
    if msg.startswith("CTF{") and msg.endswith("}"):
        flag = "BITS" + msg  # CTF{...} -> BITSCTF{...}
    elif "CTF{" in msg:
        flag = msg.replace("CTF{", "BITSCTF{", 1)
    else:
        # If message already correct or different, just show it
        flag = msg

    print("Flag:", flag)

if __name__ == "__main__":
    main()