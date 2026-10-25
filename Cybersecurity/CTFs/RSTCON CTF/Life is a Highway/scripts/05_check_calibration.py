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
