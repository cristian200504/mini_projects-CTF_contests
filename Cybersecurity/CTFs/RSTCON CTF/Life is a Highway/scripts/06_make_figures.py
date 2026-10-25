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
