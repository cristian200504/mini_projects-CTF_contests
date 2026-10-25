"""Inventory the gzip capture without assuming which CAN messages matter."""
from collections import Counter, defaultdict
import hashlib
import numpy as np
from common import CAPTURE, INPUT, OUTPUT, frames, json_write


def main():
    counts = Counter()
    minima, maxima, first_payloads = {}, {}, {}
    uniques = defaultdict(set)
    first_lines, last_lines = [], []
    begin = finish = None
    total = 0
    for stamp, interface, identifier, payload in frames():
        total += 1
        begin = stamp if begin is None else begin
        finish = stamp
        key = f"{identifier:03X}"
        counts[key] += 1
        uniques[key].add(payload)
        a = np.frombuffer(payload, dtype=np.uint8)
        if key not in minima:
            minima[key], maxima[key], first_payloads[key] = a.copy(), a.copy(), payload.hex().upper()
        else:
            minima[key] = np.minimum(minima[key], a)
            maxima[key] = np.maximum(maxima[key], a)
        line = f"({stamp:.6f}) {interface} {key}#{payload.hex().upper()}"
        if len(first_lines) < 15:
            first_lines.append(line)
        last_lines = (last_lines + [line])[-5:]
    result = {
        "capture": CAPTURE.name, "sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "compressed_bytes": CAPTURE.stat().st_size,
        "description_sha256": hashlib.sha256((INPUT / "description.txt").read_bytes()).hexdigest(),
        "frames": total, "unique_ids": len(counts), "first_timestamp": begin,
        "last_timestamp": finish, "duration_seconds": finish - begin,
        "first_lines": first_lines, "last_lines": last_lines,
        "messages": {key: {"frames": counts[key], "unique_payloads": len(uniques[key]),
                           "first_payload": first_payloads[key], "min_bytes": minima[key].tolist(),
                           "max_bytes": maxima[key].tolist()}
                     for key in sorted(counts, key=lambda value: int(value, 16))},
    }
    json_write(OUTPUT / "capture_inventory.json", result)
    print(f"Frames: {total:,}; IDs: {len(counts)}; duration: {finish-begin:.6f} s")
    print("Most frequent messages:", counts.most_common(10))


if __name__ == "__main__":
    main()
