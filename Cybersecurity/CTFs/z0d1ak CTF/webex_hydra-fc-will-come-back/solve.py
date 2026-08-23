import requests
import json

BASE_URL = "https://offside-11mm-26cefb3f24f3.chals.z0d1ak.org/api/v1"

print("[*] Retrieving matches...")
fixtures = requests.get(f"{BASE_URL}/fixtures?team=Hydra").json().get("fixtures", [])
for f in fixtures:
    print(f"  - {f['id']}: {f['label']}")

print("\n[*] Fetching HYD-SS-FINAL match summary...")
summary = requests.get(f"{BASE_URL}/matches/HYD-SS-FINAL/summary").json()
print(f"  - Disputed Event: {summary['disputed_event']}")
print(f"  - Decision: {summary['decision']} (Margin: {summary['reported_margin_mm']}mm)")

print("\n[*] Sending appeal to fix manipulated calibration profile...")
appeal_payload = {
  "match_id": "HYD-SS-FINAL",
  "kick_frame": 154828,
  "bad_sensor": "CAM-EAST",
  "correct_profile": "EAST-CAL-042",
  "corrected_margin_mm": -37
}

res = requests.post(f"{BASE_URL}/appeal", json=appeal_payload)
print(f"  - Response: {res.text}")
