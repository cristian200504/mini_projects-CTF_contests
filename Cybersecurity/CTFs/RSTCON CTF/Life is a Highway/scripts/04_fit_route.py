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
