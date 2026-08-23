# Hydra FC Offside 11mm - Solution

## Challenge Overview
The description mentions that "Shakes' equalizer at Hydra FC's Floating Stadium was ruled offside by eleven millimetres," and points to a web instance:
`https://offside-11mm-26cefb3f24f3.chals.z0d1ak.org`

In the challenge files, we have `hydra_var_telemetry_spec.v3.1.json`, which documents a telemetry API used by the VAR (Video Assistant Referee) system. The API allows interacting with match fixtures, retrieving summaries, fetching telemetry data streams (like raw tracking, IMU deck sensor data, calibration, and audit logs), and submitting appeals.

## Step 1: Enumerating the Matches
Our first goal is to find the match in question. Using the `GET /api/v1/fixtures` endpoint, we search for matches involving "Hydra":
```bash
curl "https://offside-11mm-26cefb3f24f3.chals.z0d1ak.org/api/v1/fixtures?team=Hydra"
```
The response reveals several matches. The relevant ones are:
1. `HYD-SS-FINAL`: "Hydra FC v Supa Strikas" (Shakes plays for Supa Strikas, so this is our target match).
2. `HYD-CAL-EAST-042`: "East Array Tide Calibration 042" (A calibration event).

## Step 2: Checking the Match Summary
Let's see what happened during the `HYD-SS-FINAL` match by fetching its summary:
```bash
curl "https://offside-11mm-26cefb3f24f3.chals.z0d1ak.org/api/v1/matches/HYD-SS-FINAL/summary"
```
The summary confirms that the disputed event was "Shakes equalizer," which was ruled **OFFSIDE** with a `reported_margin_mm` of 11mm.

## Step 3: Extracting Telemetry Data
We need to dive into the telemetry of this match to see if the system was manipulated. We make a POST request to `/api/v1/compare` to get all streams for the final match:
```json
{
  "match_ids": ["HYD-SS-FINAL"],
  "streams": ["raw_tracking", "deck_imu", "calibration", "audit"]
}
```

Analyzing the resulting JSON data provides the following key insights:
- **Audit Logs:** At match ms `5382110`, the `var-engine` evaluated frame `154828` and decided OFFSIDE. Right before this, an actor named `hydra-ops` activated a specific calibration profile `EAST-MATCH-043` for the `CAM-EAST` sensor.
- **Calibration Profiles:** The profile `EAST-MATCH-043` has a suspicious `longitudinal_offset_mm` of `48` applied to `CAM-EAST`. Other cameras have an offset of 0.

By requesting calibration data for the calibration match `HYD-CAL-EAST-042`, we find that the actual validated profile for `CAM-EAST` is `EAST-CAL-042`, which has a longitudinal offset of `0`.

## Step 4: Recomputing the Margin
According to the JSON specification provided, the position of a point is calculated as:
```
corrected_x_mm = raw_x_mm + longitudinal_offset_mm + round((deck_pitch_deg - reference_pitch_deg) * mm_per_degree)
```
If we use the bogus profile `EAST-MATCH-043` with a 48mm offset, the attacking line for Shakes becomes 1048mm, and the defender line is 1037mm. `1048 - 1037 = 11mm`, which perfectly matches the 11mm OFFSIDE ruling.

If we substitute the legitimate profile `EAST-CAL-042` with 0mm offset, Shakes's line is corrected to 1000mm. The new margin becomes `1000 - 1037 = -37mm`, meaning he was safely **ONSIDE**.

## Step 5: Submitting the Appeal
With the proof of manipulation, we must use the `/api/v1/appeal` endpoint to submit an appeal. The API expects a payload formatted as follows:

```json
{
  "match_id": "HYD-SS-FINAL",
  "kick_frame": 154828,
  "bad_sensor": "CAM-EAST",
  "correct_profile": "EAST-CAL-042",
  "corrected_margin_mm": -37
}
```

Submitting this request via curl:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"match_id":"HYD-SS-FINAL","kick_frame":154828,"bad_sensor":"CAM-EAST","correct_profile":"EAST-CAL-042","corrected_margin_mm":-37}' https://offside-11mm-26cefb3f24f3.chals.z0d1ak.org/api/v1/appeal
```
The server validates the appeal, overturns the decision to ONSIDE, and returns the flag:
`{"status":"accepted","decision":"ONSIDE","flag":"zdk{FeelING_bAD_fOR_CrOATiA}"}`
