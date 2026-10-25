# Full Python source for Life is a Highway

The numbered workflow was packaged for this writeup. The three files labeled original are unchanged from the live solve. The inline exploration replay was reorganized after the solve. The report-building utility is independent of the CTF calculation.

## run_all.py

```python
"""Run the complete offline reproduction from the bundled challenge inputs."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-inventory", action="store_true", help="Skip the full per-ID payload inventory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    jobs = ["00_inspect_capture.py", "01_extract_signals.py", "02_reconstruct_relative.py",
            "03_prepare_road_geometry.py", "04_fit_route.py", "05_check_calibration.py",
            "08_probe_wheel_model.py", "09_validate_confirmed_coordinate.py", "06_make_figures.py"]
    for name in jobs:
        if args.skip_inventory and name.startswith("00_"):
            continue
        print(f"\nRunning {name}", flush=True)
        subprocess.run([sys.executable, str(root/"scripts"/name)], check=True)
    print("\nCompleted. Results are in", root/"output")


if __name__ == "__main__":
    main()
```

## scripts/00_inspect_capture.py

```python
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
```

## scripts/01_extract_signals.py

```python
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
```

## scripts/02_reconstruct_relative.py

```python
"""Recreate the early no-map integration and its yaw-bias comparison plot."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from common import OUTPUT, integrate


def main():
    data = np.load(OUTPUT / "can_signals.npz")
    yaw_rows, speed_rows = data["024"], data["0B4"]
    time = yaw_rows[:, 0] - yaw_rows[0, 0]
    speed = np.interp(yaw_rows[:, 0], speed_rows[:, 0],
                      (speed_rows[:, 6] * 256 + speed_rows[:, 7]) * 0.01 / 3.6)
    raw_centered = (yaw_rows[:, 1].astype(int) & 3) * 256 + yaw_rows[:, 2] - 512
    plt.rcParams.update({"font.size": 10})
    fig, axes = plt.subplots(1, 3, figsize=(8, 4.2), constrained_layout=True)
    for ax, (gain, bias) in zip(axes, [(0.244, 0), (0.25, 0), (0.244, 0.06)]):
        yaw = raw_centered * gain - bias
        yaw[speed < 0.1] = 0
        angle = integrate(np.deg2rad(yaw), time)
        east = integrate(speed * np.cos(angle), time)
        north = integrate(speed * np.sin(angle), time)
        ax.scatter(east / 1000, north / 1000, c=time / 60, s=1, cmap="turbo")
        ax.plot(east[0]/1000, north[0]/1000, "go", label="Start")
        ax.plot(east[-1]/1000, north[-1]/1000, "rx", label="End")
        ax.set_title(f"Yaw scale {gain}\nBias {bias} deg/s")
        ax.set(xlabel="Relative x (km)", ylabel="Relative y (km)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(alpha=0.2)
    path = OUTPUT / "figures" / "relative_routes.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
    # Historical integration used the nominal DBC offset and unsigned speed.
    yaw = raw_centered * 0.244 - 0.072
    yaw[speed < 0.1] = 0
    angle = integrate(np.deg2rad(yaw), time)
    east = integrate(speed * np.cos(angle), time)
    north = integrate(speed * np.sin(angle), time)
    np.savez_compressed(OUTPUT / "integrated.npz", t=time, speed=speed, yr=yaw,
                        h=angle, x=east, z=north)
    print("Saved", path)


if __name__ == "__main__":
    main()
```

## scripts/03_prepare_road_geometry.py

```python
"""Extract the frozen Route 7 reference used by the final fit. Offline by default."""
import xml.etree.ElementTree as ET
import numpy as np
from common import REFERENCE, OUTPUT, json_write


def main():
    root = ET.parse(REFERENCE / "route7_full.osm").getroot()
    nodes = {int(node.get("id")): (float(node.get("lat")), float(node.get("lon")))
             for node in root.findall("node")}
    roads = {}
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        if tags.get("highway") not in ("primary", "trunk", "motorway"):
            continue
        coords = [nodes[int(node.get("ref"))] for node in way.findall("nd")]
        centre = np.mean(coords, axis=0)
        if 38.90 < centre[0] < 39.06 and -77.435 < centre[1] < -77.22:
            roads[way.get("id")] = {"coords": coords, "tags": tags}
    json_write(OUTPUT / "rt7_geometry.json", roads)
    print(f"Extracted {len(roads)} regional Route 7 ways")


if __name__ == "__main__":
    main()
```

## scripts/04_fit_route.py

```python
"""The decisive route fit. The accepted coordinate is NOT an input."""
import csv
import numpy as np
from scipy.optimize import differential_evolution
from common import RouteModel, OUTPUT, json_write, xy_to_ll


def main():
    model = RouteModel()
    fit = differential_evolution(model.loss,
        [(0.04, 0.14), (160, 185), (0.98, 1.02)],
        tol=0.00001, popsize=9, maxiter=100, seed=2, polish=True, workers=1)
    xy = model.trace(fit.x)
    ll = xy_to_ll(xy)
    np.savez_compressed(OUTPUT / "fitted.npz", params=fit.x, t=model.time,
                        xy=xy, ll=ll, P=model.road_points)
    result = {
        "estimated_start_latitude": float(ll[0, 0]),
        "estimated_start_longitude": float(ll[0, 1]),
        "bias_deg_per_second": float(fit.x[0]),
        "heading_at_1735s_ccw_from_east_degrees": float(fit.x[1]),
        "speed_scale": float(fit.x[2]),
        "road_point_to_trace_rms_metres": float(np.sqrt(fit.fun)),
        "reference_points": len(model.road_points),
        "success": bool(fit.success), "message": str(fit.message),
        "confirmed_answer_used_in_optimization": False,
    }
    json_write(OUTPUT / "fit_result.json", result)
    with (OUTPUT / "fitted_route.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_seconds_from_first_yaw_message", "latitude", "longitude"])
        writer.writerows(zip(model.time, ll[:, 0], ll[:, 1]))
    print(result)


if __name__ == "__main__":
    main()
```

## scripts/05_check_calibration.py

```python
"""Repeat the three sensitivity checks run before the original answer."""
import numpy as np
from scipy.optimize import minimize
from common import RouteModel, OUTPUT, json_write, xy_to_ll


def main():
    model = RouteModel()
    base = np.load(OUTPUT / "fitted.npz")["params"]
    rows = []
    for gain, drift in [(1.0, False), (0.25/0.244, False), (1.0, True)]:
        initial = list(base) + ([0] if drift else [])
        bounds = [(0.04, 0.14), (155, 190), (0.97, 1.03)]
        if drift:
            bounds += [(-0.15, 0.15)]
        loss = lambda params: model.loss(params, gain, drift, clip=False)
        fit = minimize(loss, initial, bounds=bounds, method="Nelder-Mead",
                       options={"maxiter": 1500, "xatol": 1e-7, "fatol": 1e-4})
        xy = model.trace(fit.x, gain, drift)
        ll = xy_to_ll(xy)
        name = f"variant_{gain}_{drift}"
        np.savez_compressed(OUTPUT / f"{name}.npz", params=fit.x, xy=xy, ll=ll, t=model.time)
        row = {"gain": gain, "linear_drift": drift, "parameters": fit.x.tolist(),
               "rms_metres": float(np.sqrt(fit.fun)), "start_latitude": float(ll[0, 0]),
               "start_longitude": float(ll[0, 1]), "success": bool(fit.success),
               "heading_on_upper_bound": bool(abs(fit.x[1]-190) < 0.001)}
        rows.append(row)
        print(row)
    json_write(OUTPUT / "calibration_variants.json", rows)


if __name__ == "__main__":
    main()
```

## scripts/06_make_figures.py

```python
"""Make the report figures from reproduced data and frozen map images."""
import json
import os
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from common import OUTPUT, REFERENCE, END_LAT, END_LON, ll_to_xy

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
FIGURES = OUTPUT / "figures"


def save_figure(figure, destination, **kwargs):
    """Publish only a complete PNG, avoiding partially visible image files."""
    temporary = destination.with_name(destination.stem + ".pending.png")
    figure.savefig(temporary, **kwargs)
    with Image.open(temporary) as candidate:
        candidate.verify()
    os.replace(temporary, destination)


def regional_map():
    data = np.load(OUTPUT / "fitted.npz")
    zoom, tile_x, tile_y = map(int, (REFERENCE/"basemap_info.txt").read_text().split())
    base = Image.open(REFERENCE/"regional_basemap.png")
    lat, lon = data["ll"].T
    tiles = 2**zoom
    px = (lon+180)/360*tiles*256-tile_x*256
    py = (1-np.arcsinh(np.tan(np.deg2rad(lat)))/np.pi)/2*tiles*256-tile_y*256
    fig, ax = plt.subplots(figsize=(11, 8), constrained_layout=True)
    ax.imshow(base)
    ax.plot(px, py, color="#17598c", linewidth=2.8, label="CAN route fitted to Route 7")
    ax.plot(px[0], py[0], "o", color="#146c43", markersize=9)
    ax.plot(px[-1], py[-1], "s", color="#a83131", markersize=8)
    ax.annotate("Estimated start\nCascades, Sterling", (px[0], py[0]),
                xytext=(12, 25), textcoords="offset points", fontsize=14,
                fontweight="bold", bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})
    ax.annotate("Known end\nTysons Corner Center", (px[-1], py[-1]),
                xytext=(-255, -18), textcoords="offset points", fontsize=14,
                fontweight="bold", bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})
    for minute in [10, 15]:
        index = np.abs(data["t"]-minute*60).argmin()
        ax.plot(px[index], py[index], "o", color="#17598c", ms=4)
        ax.annotate(f"{minute} min", (px[index], py[index]), xytext=(6, 5), textcoords="offset points",
                    fontsize=9, color="#123751", bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    ax.set_xlim(px.min()-55, px.max()+55)
    ax.set_ylim(py.max()+65, py.min()-65)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Reconstructed drive from Cascades to Tysons", fontsize=15, loc="left", pad=14)
    fig.text(0.12, -0.02, "Map data and tiles: OpenStreetMap contributors | openstreetmap.org/copyright", fontsize=8)
    save_figure(fig, FIGURES/"route_map.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def signal_dashboard():
    data = np.load(OUTPUT/"can_signals.npz")
    yaw, speed_rows = data["024"], data["0B4"]
    start = yaw[0, 0]
    yaw_time = (yaw[:, 0]-start)/60
    speed_time = (speed_rows[:, 0]-start)/60
    speed = (speed_rows[:, 6]*256+speed_rows[:, 7])*0.01
    yr = ((yaw[:, 1].astype(int)&3)*256+yaw[:, 2]-512)*0.244
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True, constrained_layout=True)
    axes[0].plot(speed_time[::8], speed[::8], color="#17598c", lw=1)
    axes[0].set(ylabel="Speed (km/h)", title="Decoded speed and centered yaw rate")
    axes[1].plot(yaw_time[::10], yr[::10], color="#a26019", lw=0.8)
    axes[1].set(xlabel="Minutes after the first yaw message", ylabel="Centered yaw (deg/s)")
    for ax in axes:
        ax.axvspan(145/60, 1545/60, color="#17598c", alpha=0.05)
        ax.grid(alpha=0.18)
        ax.set_xlim(0, 30)
    save_figure(fig, FIGURES/"decoded_signals.png", dpi=180)
    plt.close(fig)


def parking_shape():
    data = np.load(OUTPUT/"fitted.npz")
    root = ET.parse(REFERENCE/"parking_map.osm").getroot()
    nodes = {int(node.get("id")): (float(node.get("lat")), float(node.get("lon"))) for node in root.findall("node")}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        if "highway" not in tags and tags.get("building") != "parking":
            continue
        xy = ll_to_xy([nodes[int(node.get("ref"))] for node in way.findall("nd")])
        if tags.get("building") == "parking":
            axes[0].plot(xy[:, 0], xy[:, 1], color="#555555", lw=1.2)
            if "name" in tags:
                axes[0].text(*xy.mean(0), tags["name"], fontsize=7)
        elif tags["highway"] not in ("footway", "path", "steps", "elevator"):
            axes[0].plot(xy[:, 0], xy[:, 1], color="#b7b7b7", lw=0.7)
    axes[0].plot(0, 0, "rx", ms=9, mew=2)
    axes[0].set(xlim=(-420, 350), ylim=(-400, 350), title="Known endpoint at Garage C",
                xlabel="Metres east of known endpoint", ylabel="Metres north")
    selected = data["t"] > 1640
    xy = data["xy"][selected]
    axes[1].scatter(xy[:, 0], xy[:, 1], c=data["t"][selected], s=3, cmap="viridis")
    axes[1].plot(0, 0, "rx", ms=9, mew=2)
    axes[1].set(title="Final manoeuvres in the fitted trace", xlabel="Metres east", ylabel="Metres north")
    for ax in axes:
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.18)
    fig.text(0.01, -0.04, "Geometry: OpenStreetMap contributors. Garage motions give orientation clues, not exact indoor positions.", fontsize=8)
    save_figure(fig, FIGURES/"parking_and_turns.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def calibration_plot():
    variants = json.loads((OUTPUT/"calibration_variants.json").read_text())
    confirmed = np.array([39.0286785634, -77.4043945431])
    my = 111111
    mx = my*np.cos(np.deg2rad(confirmed[0]))
    fig, ax = plt.subplots(figsize=(7.8, 4.8), constrained_layout=True)
    names = ["Constant bias", "Yaw scale 0.25 / 0.244", "Linear bias drift"]
    colours = ["#17598c", "#a26019", "#6f4796"]
    for row, label, colour in zip(variants, names, colours):
        x = (row["start_longitude"]-confirmed[1])*mx
        y = (row["start_latitude"]-confirmed[0])*my
        ax.scatter(x, y, s=70, color=colour, label=label)
    ax.scatter(0, 0, marker="*", s=160, color="#146c43", label="User-confirmed coordinate", zorder=5)
    ax.axhline(0, color="#cccccc", lw=0.8)
    ax.axvline(0, color="#cccccc", lw=0.8)
    ax.set(xlabel="Metres east of the confirmed coordinate", ylabel="Metres north",
           title="Post-solve comparison of calibration variants", xlim=(-60, 90), ylim=(-230, 80))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)
    ax.legend(loc="lower left", bbox_to_anchor=(1.02, 0.1), frameon=False, fontsize=9)
    save_figure(fig, FIGURES/"calibration_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    regional_map()
    signal_dashboard()
    parking_shape()
    calibration_plot()
    print("Wrote report figures to", FIGURES)


if __name__ == "__main__":
    main()
```

## scripts/07_fetch_reference_data.py

```python
"""Optional network reference refresh; not called by the offline reproduction.

The solve used urllib after an initial 'requests' import failed. It tried
Overpass and broad map bboxes before using the core OSM relation/full endpoint.
Frozen successful responses are bundled so service changes do not block replay.
"""
import argparse
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from common import REFERENCE

URLS = {
    "toyota_2017.dbc": "https://raw.githubusercontent.com/commaai/opendbc/master/opendbc/dbc/generator/toyota/_toyota_2017.dbc",
    "route7_full.osm": "https://www.openstreetmap.org/api/0.6/relation/176453/full",
    "parking_map.osm": "https://www.openstreetmap.org/api/0.6/map?bbox=-77.225,38.914,-77.217,38.921",
    "start_map.osm": "https://www.openstreetmap.org/api/0.6/map?bbox=-77.415,39.02,-77.395,39.035",
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "LifeIsAHighwayCTFWriteup/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def discover_relation(way_id="227892589"):
    response = fetch(f"https://www.openstreetmap.org/api/0.6/way/{way_id}/relations")
    root = ET.fromstring(response)
    for relation in root.findall("relation"):
        tags = {tag.get("k"): tag.get("v") for tag in relation.findall("tag")}
        if tags.get("network") == "US:VA" and tags.get("ref") == "7":
            return relation.get("id")
    raise RuntimeError("No Virginia Route 7 relation found")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=REFERENCE / "refreshed")
    parser.add_argument("--discover-relation", action="store_true")
    args = parser.parse_args()
    if args.discover_relation:
        print("Route 7 relation:", discover_relation())
    args.destination.mkdir(parents=True, exist_ok=True)
    for name, url in URLS.items():
        payload = fetch(url)
        (args.destination / name).write_bytes(payload)
        print(name, len(payload))


if __name__ == "__main__":
    main()
```

## scripts/08_probe_wheel_model.py

```python
"""Document the wheel differential cross-check and why it was not the solver."""
import numpy as np
from common import OUTPUT, json_write


def main():
    data = np.load(OUTPUT / "can_signals.npz")
    yaw, wheels = data["024"], data["0AA"]
    yr = ((yaw[:, 1].astype(int) & 3)*256 + yaw[:, 2] - 512)*0.244
    wheel_speed = (wheels[:, 1:9:2]*256 + wheels[:, 2:9:2] - 6767)*0.01/3.6
    rr = np.interp(yaw[:, 0], wheels[:, 0], wheel_speed[:, 2])
    rl = np.interp(yaw[:, 0], wheels[:, 0], wheel_speed[:, 3])
    difference = rr-rl
    selected = (np.abs(yr) > 3) & ((rr+rl) > 3)
    regression = np.column_stack((difference[selected], (rr[selected]+rl[selected])/2,
                                  np.ones(selected.sum())))
    coefficients = np.linalg.lstsq(regression, yr[selected], rcond=None)[0]
    result = {"strong_turn_yaw_to_rear_difference_correlation":
              float(np.corrcoef(yr[selected], difference[selected])[0, 1]),
              "fit_yaw_equals_a_diff_plus_b_speed_plus_c": coefficients.tolist(),
              "used_for_final_coordinate": False}
    json_write(OUTPUT / "wheel_crosscheck.json", result)
    print(result)


if __name__ == "__main__":
    main()
```

## scripts/09_validate_confirmed_coordinate.py

```python
"""Post-solve validation only. The confirmed answer never enters the fit."""
import json
import math
from common import OUTPUT, json_write

CONFIRMED = (39.0286785634, -77.4043945431)
SUBMITTED = (39.0287, -77.4043)


def haversine(a, b):
    lat1, lat2 = map(math.radians, (a[0], b[0]))
    dlat, dlon = math.radians(b[0]-a[0]), math.radians(b[1]-a[1])
    q = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371008.8 * 2 * math.asin(math.sqrt(q))


def main():
    fit = json.loads((OUTPUT / "fit_result.json").read_text())
    estimate = (fit["estimated_start_latitude"], fit["estimated_start_longitude"])
    result = {"confirmed_coordinate_source": "User confirmation after the solution was submitted",
              "confirmed_latitude_longitude": list(CONFIRMED),
              "submitted_latitude_longitude": list(SUBMITTED),
              "submitted_to_confirmed_metres": haversine(SUBMITTED, CONFIRMED),
              "reproduced_to_confirmed_metres": haversine(estimate, CONFIRMED),
              "challenge_tolerance_metres": 1000,
              "confirmed_answer_used_in_optimization": False}
    json_write(OUTPUT / "postsolve_validation.json", result)
    print(result)


if __name__ == "__main__":
    main()
```

## scripts/common.py

```python
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
```

## session_archive/fit_analysis.py original unchanged

```python
import numpy as np,json
from scipy.integrate import cumulative_trapezoid as cint
from scipy.spatial import cKDTree
from scipy.optimize import differential_evolution,minimize
from pathlib import Path
D=np.load('can_signals.npz');raw=D['024'];ts=raw[:,0];t=np.arange(ts[0],ts[-1],.15);tr=t-t[0]
yr=np.interp(t,ts,((raw[:,1].astype(int)&3)*256+raw[:,2]-512)*.244)
v=D['0B4'];v=np.interp(t,v[:,0],(v[:,6]*256+v[:,7])*.01/3.6);moving=v>.1
g=np.load('gears.npz');gear=g['gear'][np.clip(np.searchsorted(g['t'],t,side='right')-1,0,len(g['t'])-1)];v[gear==16]*=-1
Y=cint(np.deg2rad(yr*moving),tr,initial=0);M=cint(moving.astype(float),tr,initial=0);ref=abs(tr-1735).argmin();Y-=Y[ref];M-=M[ref]
lat0,lon0=38.9166896,-77.2210292;my=111111.;mx=my*np.cos(np.deg2rad(lat0));roads=json.load(open('rt7_geometry.json'));points=[]
for road in roads.values():
 ll=np.array(road['coords']);p=np.column_stack([(ll[:,1]-lon0)*mx,(ll[:,0]-lat0)*my]);
 if p[-1,0]<p[0,0]:continue
 for a,b in zip(p[:-1],p[1:]):points.extend(np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/15))))
P=np.array(points);P=np.unique(np.rint(P/5)*5,axis=0);mask=(tr>145)&(tr<1545)
# Keep road reference points only between 1 km and 20 km from endpoint.
P=P[(np.linalg.norm(P,axis=1)<20000)&(np.linalg.norm(P,axis=1)>800)]

def trace(params):
 bias,heading,scale=params;h=Y-np.deg2rad(bias)*M+np.deg2rad(heading);x=cint(v*scale*np.cos(h),tr,initial=0);y=cint(v*scale*np.sin(h),tr,initial=0);return np.column_stack([x-x[-1],y-y[-1]])
def loss(params):
 p=trace(params);tree=cKDTree(p[mask]);d=tree.query(P)[0];return np.mean(np.minimum(d,3000)**2)
if __name__=='__main__':
 print('Reference points',P.shape,flush=True)
 fit=differential_evolution(loss,[(.04,.14),(160,185),(.98,1.02)],tol=.00001,popsize=9,maxiter=100,seed=2,polish=True,workers=1)
 print('fit',fit.x,'rms',np.sqrt(fit.fun),fit.message,flush=True)
 xy=trace(fit.x);ll=np.column_stack([lat0+xy[:,1]/my,lon0+xy[:,0]/mx]);print('start',ll[0],flush=True)
 for tm in range(0,1800,120):
  i=abs(tr-tm).argmin();print(tm,ll[i],flush=True)
 np.savez_compressed('fitted.npz',params=fit.x,t=tr,xy=xy,ll=ll,P=P)
```

## session_archive/fit_start.py original unchanged

```python
import xml.etree.ElementTree as E,numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import differential_evolution,minimize
D=np.load('fitted.npz');t=D['t'];lat0,lon0=D['ll'][0];my=111111.;mx=my*np.cos(np.deg2rad(lat0));root=E.parse('start_map.osm').getroot();nodes={int(n.get('id')):((float(n.get('lon'))-lon0)*mx,(float(n.get('lat'))-lat0)*my) for n in root.findall('node')};points=[];fast=[];rt=[]
for w in root.findall('way'):
 tag={v.get('k'):v.get('v') for v in w.findall('tag')}
 if tag.get('highway') not in ('service','unclassified','residential','tertiary','secondary','primary','trunk','motorway','primary_link','secondary_link','trunk_link','motorway_link'):continue
 p=np.array([nodes[int(n.get('ref'))] for n in w.findall('nd')]);P=[]
 for a,b in zip(p[:-1],p[1:]):P.extend(np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/2))))
 points.extend(P)
 if tag.get('highway') in ('secondary','primary','trunk','motorway','primary_link','secondary_link','trunk_link','motorway_link'):fast.extend(P)
 if 'VA 7' in tag.get('ref','') and p[-1,0]>p[0,0]:rt.extend(P)
T=cKDTree(points);F=cKDTree(fast);R=cKDTree(rt)
sel=(t>22)&(t<200);P=np.column_stack([(D['ll'][:,1]-lon0)*mx,(D['ll'][:,0]-lat0)*my])[sel][::5];ts=t[sel][::5];mask1=ts<85;mask2=(ts>=85)&(ts<140);mask3=ts>=140

def transform(params,p=P):
 x,y,theta=params;a=np.deg2rad(theta);rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);return p@rot.T+np.array([x,y])
def loss(params):
 q=transform(params);d=np.r_[T.query(q[mask1])[0],F.query(q[mask2])[0],R.query(q[mask3])[0]];return np.mean(d**2)
if __name__=='__main__':
 fit=differential_evolution(loss,[(-800,800),(-800,800),(-30,30)],tol=1e-6,popsize=12,maxiter=180,seed=4,polish=True)
 print('fit',fit.x,'rms',np.sqrt(fit.fun),'start latlon',lat0+fit.x[1]/my,lon0+fit.x[0]/mx,flush=True);np.savez_compressed('start_fitted.npz',params=fit.x,start=np.array([lat0+fit.x[1]/my,lon0+fit.x[0]/mx]),P=transform(fit.x),t=ts,origin=np.array([lat0,lon0]))
```

## session_archive/check_variants.py original unchanged

```python
import fit_analysis as f,numpy as np
from scipy.integrate import cumulative_trapezoid as cint
from scipy.spatial import cKDTree
from scipy.optimize import minimize
D=np.load('fitted.npz');base=D['params'];time=(f.tr-f.tr.mean())/f.tr[-1];B=cint(time*f.moving,f.tr,initial=0);B-=B[f.ref]

def trace(params,gain=1,drift=False):
 bias,heading,scale=params[:3];h=gain*f.Y-np.deg2rad(bias)*f.M+np.deg2rad(heading)
 if drift:h-=np.deg2rad(params[3])*B
 x=cint(f.v*scale*np.cos(h),f.tr,initial=0);y=cint(f.v*scale*np.sin(h),f.tr,initial=0);return np.column_stack([x-x[-1],y-y[-1]])
def loss(p,gain,drift):
 xy=trace(p,gain,drift);d=cKDTree(xy[f.mask]).query(f.P)[0];return np.mean(d*d)
for gain,drift in [(1.0,False),(.25/.244,False),(1.0,True)]:
 ini=list(base)+([0] if drift else []);bounds=[(.04,.14),(155,190),(.97,1.03)]+([(-.15,.15)] if drift else []);res=minimize(loss,ini,args=(gain,drift),bounds=bounds,method='Nelder-Mead',options={'maxiter':1500,'xatol':1e-7,'fatol':1e-4});xy=trace(res.x,gain,drift);lat=f.lat0+xy[0,1]/f.my;lon=f.lon0+xy[0,0]/f.mx;print('gain',gain,'linear drift',drift,'rms',res.fun**.5,'parameters',res.x,'start',lat,lon,flush=True)
 np.savez_compressed('variant_'+str(gain)+'_'+str(drift)+'.npz',params=res.x,xy=xy,ll=np.column_stack([f.lat0+xy[:,1]/f.my,f.lon0+xy[:,0]/f.mx]),t=f.tr)
```

## session_archive/inline_exploration.py

```python
"""Organized replay of the exploratory Python that originally ran inline.

This file was assembled for the writeup; it is NOT an unchanged original file.
The unchanged saved session programs are fit_analysis.py, fit_start.py, and
check_variants.py alongside it. See EXPLORATION.md for order and failed probes.

Run from this directory, e.g. python inline_exploration.py yaw-stops.
Network commands are optional. Successful snapshots are already bundled.
"""
import argparse
from collections import Counter
from pathlib import Path
import json
import math
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import numpy as np
from scipy.integrate import cumulative_trapezoid as cint
from scipy.spatial import cKDTree
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REFERENCE = ROOT / "reference"


def yaw_stops():
    data = np.load(HERE/"can_signals.npz")
    yaw, speed_rows, wheels = data["024"], data["0B4"], data["0AA"]
    time = yaw[:, 0]-yaw[0, 0]
    speed = np.interp(yaw[:, 0], speed_rows[:, 0],
                      (speed_rows[:, 6]*256+speed_rows[:, 7])/360)
    rear = np.interp(yaw[:, 0], wheels[:, 0],
                     ((wheels[:, 5]*256+wheels[:, 6]+wheels[:, 7]*256+wheels[:, 8])/2-6767)/360)
    yr = ((yaw[:, 1].astype(int)&3)*256+yaw[:, 2]-512)*0.244
    print("Stationary centered yaw counts:", Counter(yr[speed<0.05]).most_common(12))
    masked = cint(np.where(speed>0.1, yr-0.072, 0), time, initial=0)
    unmasked = cint(yr-0.072, time, initial=0)
    for second in range(0, 180, 5):
        mask = (time>=second)&(time<second+5)
        index = abs(time-second-5).argmin()
        print(second, "speed", speed[mask].mean(), "rear", rear[mask].mean(),
              "yaw", yr[mask].mean(), "discarded angle", (unmasked-masked)[index])


def wheel_regression():
    data = np.load(HERE/"can_signals.npz")
    yaw, wheels = data["024"], data["0AA"]
    speed = (wheels[:, 1:9:2]*256+wheels[:, 2:9:2]-6767)*0.01/3.6
    yr = np.interp(wheels[:, 0], yaw[:, 0],
                    ((yaw[:, 1].astype(int)&3)*256+yaw[:, 2]-512)*0.244)
    velocity = speed[:, 2:4].mean(axis=1)
    difference = speed[:, 2]-speed[:, 3]
    for low in [0, 5, 10, 15]:
        mask = velocity>low
        design = np.column_stack((difference[mask], velocity[mask], np.ones(mask.sum())))
        fit = np.linalg.lstsq(design, yr[mask], rcond=None)[0]
        print("minimum speed", low, "coefficients", fit,
              "apparent track", 180/np.pi/fit[0], "radius correction", -fit[1]/fit[0])
    time = wheels[:, 0]-wheels[0, 0]
    for second in range(100, 1600, 100):
        mask = (time>=second)&(time<second+100)&(velocity>5)
        ratio = np.mean((difference[mask]-(yr[mask]-0.072)*np.pi/180*1.53)/velocity[mask])
        print(second, "mean speed", velocity[mask].mean(), "ratio correction", ratio)


def lateral_acceleration():
    data = np.load(HERE/"can_signals.npz")
    yaw, speed_rows = data["024"], data["0B4"]
    raw = (yaw[:, 1].astype(int)&3)*256+yaw[:, 2]
    speed = np.interp(yaw[:, 0], speed_rows[:, 0], (speed_rows[:, 6]*256+speed_rows[:, 7])/360)
    acceleration = ((yaw[:, 5].astype(int)&3)*256+yaw[:, 6])*0.03589-18.375
    for low, high in [(5, 15), (15, 30)]:
        mask = (speed>low)&(speed<high)
        design = np.column_stack((raw[mask]-512, np.ones(mask.sum()), 1/speed[mask]))
        fit = np.linalg.lstsq(design, acceleration[mask]/speed[mask], rcond=None)[0]
        print(low, high, "coefficients", fit, "first two in degrees", fit[:2]*180/np.pi)


def parking_inventory():
    root = ET.parse(REFERENCE/"parking_map.osm").getroot()
    nodes = {int(node.get("id")): (float(node.get("lat")), float(node.get("lon"))) for node in root.findall("node")}
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        coords = np.array([nodes[int(node.get("ref"))] for node in way.findall("nd")])
        centre = coords.mean(0)
        if abs(centre[0]-38.9166896)<0.002 and abs(centre[1]+77.2210292)<0.003:
            if any(key in tags for key in ["highway", "parking", "building"]):
                print(way.get("id"), centre, tags)


def parking_orientation():
    """The distance-only local experiment that returned an implausible 245 deg."""
    signals = np.load(HERE/"can_signals.npz")
    yaw, speed_rows = signals["024"], signals["0B4"]
    time = yaw[:, 0]-yaw[0, 0]
    speed = np.interp(yaw[:, 0], speed_rows[:, 0],
                      (speed_rows[:, 6]*256+speed_rows[:, 7])*0.01/3.6)
    yr = ((yaw[:, 1].astype(int)&3)*256+yaw[:, 2])*0.244-125
    yr[speed<0.1] = 0
    angle = cint(np.deg2rad(yr), time, initial=0)
    x = cint(speed*np.cos(angle), time, initial=0)
    y = cint(speed*np.sin(angle), time, initial=0)
    x, y = x-x[-1], y-y[-1]
    lat0, lon0 = 38.9166896, -77.2210292
    my, mx = 111111, 111111*np.cos(np.deg2rad(lat0))
    root = ET.parse(REFERENCE/"parking_map.osm").getroot()
    nodes = {int(node.get("id")): ((float(node.get("lon"))-lon0)*mx,
                                  (float(node.get("lat"))-lat0)*my) for node in root.findall("node")}
    points = []
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        if "highway" not in tags or tags["highway"] in ["footway", "steps", "cycleway", "elevator", "path", "pedestrian"]:
            continue
        coords = np.array([nodes[int(node.get("ref"))] for node in way.findall("nd")])
        for a, b in zip(coords[:-1], coords[1:]):
            points.extend(np.linspace(a, b, max(2, int(np.linalg.norm(b-a)/2))))
    tree = cKDTree(points)
    selected = np.where((time>1555)&(time<1650)&(speed>1))[0][::20]
    path = np.column_stack((x[selected], y[selected]))

    def loss(degrees):
        a = np.deg2rad(degrees)
        rotation = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        return np.mean(tree.query(path@rotation.T)[0]**2)

    best = min(range(360), key=loss)
    optimum = minimize_scalar(loss, bounds=(best-3, best+3), method="bounded")
    print("Local-only orientation", optimum.x, "RMS", optimum.fun**0.5)
    print("Discarded: a small road-distance score did not establish a plausible garage route.")


def regional_bias_grid():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    data = np.load(HERE/"can_signals.npz")
    yaw, speed_rows = data["024"], data["0B4"]
    time = yaw[:, 0]-yaw[0, 0]
    speed = np.interp(yaw[:, 0], speed_rows[:, 0], (speed_rows[:, 6]*256+speed_rows[:, 7])/360)
    yr = ((yaw[:, 1].astype(int)&3)*256+yaw[:, 2]-512)*0.244
    zoom, x0, y0 = map(int, (REFERENCE/"basemap_info.txt").read_text().split())
    base = Image.open(REFERENCE/"regional_basemap.png")
    lat0, lon0 = 38.9166896, -77.2210292
    my, mx = 111111, 111111*np.cos(np.deg2rad(lat0))
    fig, axes = plt.subplots(2, 3, figsize=(15, 15), constrained_layout=True)
    for ax, bias in zip(axes.ravel(), [0, 0.05, 0.072, 0.085, 0.1, 0.12]):
        rate = yr-bias
        rate[speed<0.1] = 0
        angle = cint(np.deg2rad(rate), time, initial=0)
        angle += np.deg2rad(172)-angle[(time>1730)&(time<1740)].mean()
        x, y = cint(speed*np.cos(angle), time, initial=0), cint(speed*np.sin(angle), time, initial=0)
        lat, lon = lat0+(y-y[-1])/my, lon0+(x-x[-1])/mx
        px = (lon+180)/360*2**zoom*256-x0*256
        py = (1-np.arcsinh(np.tan(np.deg2rad(lat)))/np.pi)/2*2**zoom*256-y0*256
        ax.imshow(base)
        ax.plot(px, py, "b-", lw=1.5)
        ax.plot(px[0], py[0], "go")
        ax.set_title(f"bias {bias}; start {lat[0]:.5f}, {lon[0]:.5f}")
        ax.set_xticks([])
        ax.set_yticks([])
        print(bias, lat[0], lon[0])
    fig.savefig(HERE/"replayed_regional_bias_grid.png", dpi=150)
    plt.close(fig)


def nearest_road_diagnostic():
    import fit_analysis as solver
    fitted = np.load(HERE/"fitted.npz")
    tree = cKDTree(solver.P)
    for second in list(range(100, 400, 20))+[500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1500]:
        index = abs(fitted["t"]-second).argmin()
        distance, nearest = tree.query(fitted["xy"][index])
        print(second, distance, fitted["ll"][index], "nearest reference xy", solver.P[nearest])
    print("Near excluded map regions, distance to the retained reference set is not a road error.")


def fetch_region_tiles():
    """Recreate the 20-tile OSM basemap. Optional network access."""
    from PIL import Image
    zoom = 12
    n = 2**zoom
    xt = lambda lon: (lon+180)/360*n
    yt = lambda lat: (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
    west, south, east, north = -77.49, 38.89, -77.20, 39.10
    x0, x1, y0, y1 = int(xt(west)), int(xt(east)), int(yt(north)), int(yt(south))
    destination = REFERENCE/"refreshed_tiles"
    destination.mkdir(exist_ok=True)
    image = Image.new("RGB", ((x1-x0+1)*256, (y1-y0+1)*256), "white")
    for x in range(x0, x1+1):
        for y in range(y0, y1+1):
            path = destination/f"{zoom}_{x}_{y}.png"
            if not path.exists():
                request = urllib.request.Request(f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png",
                                                  headers={"User-Agent": "CTF-CAN-writeup/1.0"})
                path.write_bytes(urllib.request.urlopen(request, timeout=20).read())
            image.paste(Image.open(path), ((x-x0)*256, (y-y0)*256))
    image.save(destination/"regional_basemap.png")
    (destination/"basemap_info.txt").write_text(f"{zoom} {x0} {y0}\n")


def main():
    commands = {"yaw-stops": yaw_stops, "wheel-regression": wheel_regression,
                "lateral-acceleration": lateral_acceleration, "parking-inventory": parking_inventory,
                "parking-orientation": parking_orientation, "regional-bias-grid": regional_bias_grid,
                "nearest-road-diagnostic": nearest_road_diagnostic, "fetch-region-tiles": fetch_region_tiles}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=commands)
    args = parser.parse_args()
    commands[args.command]()


if __name__ == "__main__":
    main()
```

## tools/build_documents.py

```python
"""Convert the Markdown technical report to an editable, styled Word document.

This is a report-production utility, not a component of the CTF calculation.
Run with python-docx installed, then render the DOCX using a Word/PDF renderer.
"""
from pathlib import Path
import re
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path(__file__).resolve().parents[1]


def font(run, name, size=None, bold=False):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size:
        run.font.size = Pt(size)
    run.bold = bold


def inline(paragraph, text, table=False):
    for token in re.split(r"(\*\*.*?\*\*|`[^`]+`)", text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            paragraph.add_run(token[2:-2]).bold = True
        elif token.startswith("`") and token.endswith("`"):
            value = token[1:-1]
            if table and re.fullmatch(r"[0-9a-f]{64}", value):
                value = value[:32]+"\n"+value[32:]
            run = paragraph.add_run(value)
            font(run, "DejaVu Sans Mono", 8.7 if table else 9.4)
        else:
            paragraph.add_run(token)


def table_borders(table):
    props = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        element = OxmlElement("w:"+name)
        for key, value in [("val", "single"), ("sz", "4"), ("color", "D9D9D9")]:
            element.set(qn("w:"+key), value)
        borders.append(element)
    props.append(borders)


def add_table(document, rows):
    rows = [[cell.strip() for cell in row] for row in rows]
    count = len(rows[0])
    if count == 2:
        widths = [2.15, 4.75]
    elif count == 4:
        widths = [1.75, 1.65, 1.65, 1.85]
    elif count == 5:
        widths = [0.7, 0.8, 2.2, 2.0, 1.2]
    else:
        widths = [6.9/count]*count
    if rows[0][0] == "Hex ID":
        widths = [0.8, 0.8, 2.25, 3.05]
    if rows[0][0] == "Parameter":
        widths = [1.65, 1.75, 3.5]
    if count == 3 and rows[0][0] != "Parameter":
        widths = [2.3]*3
    table = document.add_table(rows=1, cols=count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for column, width in zip(table.columns, widths):
        column.width = Inches(width)
    for index, values in enumerate(rows):
        cells = table.rows[0].cells if index == 0 else table.add_row().cells
        for cell, width, value in zip(cells, widths, values):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props = cell._tc.get_or_add_tcPr()
            margins = OxmlElement("w:tcMar")
            for side in ["top", "left", "bottom", "right"]:
                margin = OxmlElement("w:"+side)
                margin.set(qn("w:w"), "85")
                margin.set(qn("w:type"), "dxa")
                margins.append(margin)
            props.append(margins)
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "E8EEF2" if index == 0 else ("F8FAFB" if index % 2 == 0 else "FFFFFF"))
            props.append(shading)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.line_spacing = 1.03
            inline(p, value.strip(), table=True)
            for run in p.runs:
                if run.font.size is None:
                    run.font.size = Pt(9.6)
                if index == 0:
                    run.bold = True
            if count >= 4 and index > 0 and len(value) < 18:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        row_props = table.rows[index]._tr.get_or_add_trPr()
        no_split = OxmlElement("w:cantSplit")
        row_props.append(no_split)
        if index == 0:
            repeat = OxmlElement("w:tblHeader")
            row_props.append(repeat)
    table_borders(table)
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 0.4
    p.add_run().font.size = Pt(3)


def main():
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    styles = document.styles
    for name, size, bold in [("Normal", 11, False), ("Title", 25, False),
                              ("Heading 1", 15, True), ("Heading 2", 12, True),
                              ("Caption", 9.2, False)]:
        style = styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = RGBColor(0, 0, 0)
    styles["Normal"].paragraph_format.line_spacing = 1.08
    styles["Normal"].paragraph_format.space_after = Pt(6)
    styles["Title"].paragraph_format.space_after = Pt(12)
    styles["Heading 1"].paragraph_format.space_before = Pt(14)
    styles["Heading 1"].paragraph_format.space_after = Pt(7)
    styles["Heading 2"].paragraph_format.space_before = Pt(10)
    styles["Heading 2"].paragraph_format.space_after = Pt(5)
    styles["Caption"].paragraph_format.space_after = Pt(9)
    code = styles.add_style("CTF Code", WD_STYLE_TYPE.PARAGRAPH)
    code.font.name, code.font.size = "DejaVu Sans Mono", Pt(8.8)
    code.paragraph_format.line_spacing = 1.0
    code.paragraph_format.space_after = Pt(7)
    code.paragraph_format.space_before = Pt(3)
    code.paragraph_format.left_indent = Inches(0.1)
    code.paragraph_format.right_indent = Inches(0.03)
    document.core_properties.title = "Life is a Highway CTF writeup"
    document.core_properties.subject = "CAN decoding and route reconstruction"
    document.core_properties.author = "ChatGPT"
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = footer.add_run("Life is a Highway CTF writeup  |  ")
    run.font.size = Pt(8)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    lines = (ROOT/"WRITEUP.md").read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("```"):
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code_lines.append(lines[index])
                index += 1
            p = document.add_paragraph(style="CTF Code")
            p.paragraph_format.keep_together = len(code_lines) < 12
            run = p.add_run("\n".join(code_lines))
            font(run, "DejaVu Sans Mono", 8.8)
            index += 1
            continue
        if line.startswith("#"):
            level = len(line)-len(line.lstrip("#"))
            text = line[level:].strip()
            if level == 1:
                document.add_paragraph(text, style="Title")
            else:
                document.add_paragraph(text, style=f"Heading {min(level-1, 2)}")
            index += 1
            continue
        if line.startswith("| "):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = lines[index].strip().strip("|").split("|")
                if not all(re.fullmatch(r"\s*:?-+:?\s*", cell) for cell in cells):
                    rows.append(cells)
                index += 1
            add_table(document, rows)
            continue
        match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if match:
            label, filename = match.groups()
            width = 6.2 if "route_map" in filename else (6.6 if "calibration" not in filename else 5.7)
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            image = p.add_run().add_picture(str(ROOT/filename), width=Inches(width))
            image._inline.docPr.set("descr", label)
            index += 1
            continue
        text_lines = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and not lines[index].startswith(("#", "```", "|", "![")):
            text_lines.append(lines[index])
            index += 1
        text = " ".join(text_lines)
        p = document.add_paragraph(style="Caption" if text.startswith("Figure ") else "Normal")
        inline(p, text)
        if text.endswith(":"):
            p.paragraph_format.keep_with_next = True
    # The default Word template can carry a blue paragraph border in Title.
    # Remove inherited and direct paragraph borders, retaining table borders.
    for border in list(document.styles.element.xpath(".//w:pBdr")):
        border.getparent().remove(border)
    for border in list(document._element.xpath(".//w:pBdr")):
        border.getparent().remove(border)
    output = ROOT/"Life_is_a_Highway_Writeup.docx"
    document.save(output)
    print(output)


if __name__ == "__main__":
    main()
```
