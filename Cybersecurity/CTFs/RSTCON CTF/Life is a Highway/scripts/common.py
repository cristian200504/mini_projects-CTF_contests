"""Shared parsing and math for the documented reproduction.

These functions preserve the final session solver's calculations. They do not
read the user-confirmed answer. Paths are relative to this bundle, not cwd.
"""
from pathlib import Path
import gzip
import json
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "inputs"
REFERENCE = ROOT / "reference"
OUTPUT = ROOT / "output"
CAPTURE = INPUT / "candump-2026-08-22_185046.log.gz"
END_LAT = 38.9166896
END_LON = -77.2210292
METRES_PER_LAT_DEG = 111111.0
METRES_PER_LON_DEG = METRES_PER_LAT_DEG * np.cos(np.deg2rad(END_LAT))


def json_write(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def frames(path=CAPTURE):
    """Yield timestamp, interface, integer CAN ID, payload from candump lines."""
    with gzip.open(path, "rt", encoding="ascii") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                stamp, interface, message = line.split()
                identifier, payload = message.split("#", 1)
                yield float(stamp[1:-1]), interface, int(identifier, 16), bytes.fromhex(payload)
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Malformed candump line {line_number}") from exc


def ll_to_xy(ll):
    ll = np.asarray(ll)
    return np.column_stack(((ll[:, 1] - END_LON) * METRES_PER_LON_DEG,
                            (ll[:, 0] - END_LAT) * METRES_PER_LAT_DEG))


def xy_to_ll(xy):
    xy = np.asarray(xy)
    return np.column_stack((END_LAT + xy[:, 1] / METRES_PER_LAT_DEG,
                            END_LON + xy[:, 0] / METRES_PER_LON_DEG))


def integrate(values, times):
    return cumulative_trapezoid(values, times, initial=0)


class RouteModel:
    """Reproduce fit_analysis.py, with readable names and stable file paths."""

    def __init__(self):
        data = np.load(OUTPUT / "can_signals.npz")
        raw = data["024"]
        stamps = raw[:, 0]
        self.timestamps = np.arange(stamps[0], stamps[-1], 0.15)
        self.time = self.timestamps - self.timestamps[0]
        raw_yaw = (raw[:, 1].astype(int) & 3) * 256 + raw[:, 2]
        self.yaw_centered = np.interp(self.timestamps, stamps, (raw_yaw - 512) * 0.244)
        speed_rows = data["0B4"]
        speed_ms = (speed_rows[:, 6] * 256 + speed_rows[:, 7]) * 0.01 / 3.6
        self.speed = np.interp(self.timestamps, speed_rows[:, 0], speed_ms)
        self.moving = self.speed > 0.1
        gears = np.load(OUTPUT / "gears.npz")
        index = np.clip(np.searchsorted(gears["t"], self.timestamps, side="right") - 1,
                        0, len(gears["t"]) - 1)
        self.gear = gears["gear"][index]
        self.speed[self.gear == 16] *= -1
        self.yaw_integral = integrate(np.deg2rad(self.yaw_centered * self.moving), self.time)
        self.moving_integral = integrate(self.moving.astype(float), self.time)
        self.reference_index = np.abs(self.time - 1735).argmin()
        self.yaw_integral -= self.yaw_integral[self.reference_index]
        self.moving_integral -= self.moving_integral[self.reference_index]
        drift_time = (self.time - self.time.mean()) / self.time[-1]
        self.drift_integral = integrate(drift_time * self.moving, self.time)
        self.drift_integral -= self.drift_integral[self.reference_index]

        roads = json.loads((OUTPUT / "rt7_geometry.json").read_text())
        points = []
        for road in roads.values():
            xy = ll_to_xy(road["coords"])
            if xy[-1, 0] < xy[0, 0]:
                continue  # Regional eastbound heuristic, not a generic route matcher.
            for a, b in zip(xy[:-1], xy[1:]):
                points.extend(np.linspace(a, b, max(2, int(np.linalg.norm(b - a) / 15))))
        points = np.asarray(points)
        points = np.unique(np.rint(points / 5) * 5, axis=0)
        radius = np.linalg.norm(points, axis=1)
        self.road_points = points[(radius < 20000) & (radius > 800)]
        self.highway_mask = (self.time > 145) & (self.time < 1545)

    def trace(self, params, gain=1.0, drift=False):
        bias, heading, speed_scale = params[:3]
        angle = (gain * self.yaw_integral - np.deg2rad(bias) * self.moving_integral
                 + np.deg2rad(heading))
        if drift:
            angle -= np.deg2rad(params[3]) * self.drift_integral
        east = integrate(self.speed * speed_scale * np.cos(angle), self.time)
        north = integrate(self.speed * speed_scale * np.sin(angle), self.time)
        return np.column_stack((east - east[-1], north - north[-1]))

    def loss(self, params, gain=1.0, drift=False, clip=True):
        xy = self.trace(params, gain, drift)
        distance = cKDTree(xy[self.highway_mask]).query(self.road_points)[0]
        if clip:
            distance = np.minimum(distance, 3000)
        return float(np.mean(distance * distance))
