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
