"""Save timestamp-plus-byte arrays and decode the signals used in the solve."""
from collections import defaultdict
import numpy as np
from common import OUTPUT, frames, json_write


def main():
    wanted = {0x024, 0x025, 0x0AA, 0x0B4, 0x3D0, 0x610, 0x1D0}
    rows, gears = defaultdict(list), []
    for stamp, _, identifier, payload in frames():
        if identifier in wanted:
            rows[f"{identifier:03X}"].append([stamp, *payload])
        if identifier == 0x3BC:
            gears.append((stamp, payload[1] & 0x3F))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    arrays = {key: np.asarray(value) for key, value in rows.items()}
    np.savez_compressed(OUTPUT / "can_signals.npz", **arrays)
    gear_array = np.asarray(gears)
    np.savez_compressed(OUTPUT / "gears.npz", t=gear_array[:, 0], gear=gear_array[:, 1].astype(int))
    speed_rows = arrays["0B4"]
    speed = (speed_rows[:, 6] * 256 + speed_rows[:, 7]) * 0.01 / 3.6
    wheel_rows = arrays["0AA"]
    wheel_speed = ((wheel_rows[:, 1:9:2].astype(int) * 256
                    + wheel_rows[:, 2:9:2].astype(int)) & 0x7FFF)
    wheel_speed = (wheel_speed * 0.01 - 67.67) / 3.6
    yaw_rows = arrays["024"]
    yaw_raw = (yaw_rows[:, 1].astype(int) & 3) * 256 + yaw_rows[:, 2]
    summary = {
        "speed_message_duration_s": float(speed_rows[-1, 0] - speed_rows[0, 0]),
        "max_speed_kph": float(speed.max() * 3.6),
        "unsigned_speed_distance_km": float(np.trapezoid(speed, speed_rows[:, 0]) / 1000),
        "wheel_distances_km_FR_FL_RR_RL": (np.trapezoid(wheel_speed, wheel_rows[:, 0], axis=0) / 1000).tolist(),
        "yaw_raw_range": [int(yaw_raw.min()), int(yaw_raw.max())],
        "yaw_centered_range_deg_per_s": [float(((yaw_raw-512)*0.244).min()),
                                         float(((yaw_raw-512)*0.244).max())],
        "array_counts": {key: len(value) for key, value in arrays.items()},
        "gear_frames": len(gears),
    }
    json_write(OUTPUT / "signal_summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
