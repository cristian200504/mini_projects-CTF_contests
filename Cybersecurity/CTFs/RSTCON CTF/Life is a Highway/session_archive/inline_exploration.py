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
