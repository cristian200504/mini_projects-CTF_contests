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
