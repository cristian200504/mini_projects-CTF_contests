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
