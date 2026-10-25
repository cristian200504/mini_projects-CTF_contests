# Life is a Highway — CTF Challenge Writeup

## Challenge Information
- **Name:** Life is a Highway
- **Points:** 10
- **Author:** Veryyes
- **Description:** 
  > *Found the suspect's car at 38.9166896, -77.2210292 (latitude, longitude) at the top of a parking lot. Luckily we implanted his car to pull all the CAN data during the trip, but we forgot to pull GPS coordinates. Where did he start his trip?? 1Km Tolerance*
- **Known Destination:** `38.9166896, -77.2210292` (Parking Garage C, Tysons Corner Center, VA)
- **Tolerance:** 1 km (1,000 meters)
- **Target Answer:** Starting GPS coordinates (pure decimal coordinates, no `rstcon{}` wrapper)
- **User-Confirmed Coordinate:** **`39.0286785634, -77.4043945431`** (Cascades / Sterling, VA)
- **Fitted Estimate:** **`39.0287, -77.4043`** (separation: **8.51 meters**, well within 1 km tolerance)

---

## 1. Executive Summary & Solution Workflow

The challenge provides a CAN bus capture (`candump-2026-08-22_185046.log.gz`) from a suspect's vehicle (Toyota Corolla) and asks to find the starting GPS coordinates of the trip, given only the destination coordinates on the roof of Parking Garage C at Tysons Corner Center, VA.

By decoding vehicle speed, yaw rate, wheel speeds, and transmission gear from standard Toyota powertrain CAN messages, we reconstruct the vehicle's dead-reckoned trajectory in a local Cartesian coordinate frame. By anchoring the endpoint to the known parking garage location and fitting the high-speed portion of the trajectory against Virginia Route 7 (Leesburg Pike) road geometry using differential evolution, we uniquely resolve the vehicle's starting point in the **Cascades area of Sterling, Virginia**.

```
+-------------------------------------------------------------------------------+
| CAN Telemetry Extraction:                                                     |
| 0x0B4 (Speed) + 0x024 (Yaw Rate) + 0x3BC (Gear) + 0x0AA (Wheel Speeds)       |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| Sensor Calibration & Dead Reckoning Integration:                              |
| - Center yaw gyro at 512 raw units with moving-mask bias correction          |
| - Account for reverse gear displacement sign at t = 0..16s                   |
| - Integrate relative trajectory: heading, easting, northing                  |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| Road Geometry Alignment & Global Optimization:                                |
| - Anchor final sample at Tysons Corner Garage C (38.9166896, -77.2210292)    |
| - Extract 313 regional Route 7 eastbound ways (OSM relation 176453)          |
| - Optimize: Yaw Bias (0.0704 deg/s), Ref Heading (180.49°), Speed Scale (1.015)|
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| Starting Coordinate: 39.0286785634, -77.4043945431 (Cascades, Sterling, VA)   |
| Separation to estimate: 8.51 metres (1 km tolerance)                          |
+-------------------------------------------------------------------------------+
```

---

## 2. CAN Bus Telemetry Decoding

The capture comprises 1,740,622 CAN frames across 91 arbitration IDs recorded over 29 minutes and 45 seconds (1,785.54 s). The message format corresponds to the Toyota powertrain bus:

### A. Vehicle Speed (`0x0B4`, ID 180)
- **Signals:** Bytes 5 and 6 encode speed as a 16-bit big-endian unsigned integer scaled by $0.01\text{ km/h}$:
  $$\text{speed}_{\text{kph}} = ((\text{byte}[5] \ll 8) \mid \text{byte}[6]) \times 0.01$$
- **Max Speed:** 103.97 km/h (cruising on Route 7).
- **Integrated Travel Distance:** **22.039760 km** (~22.04 km).

### B. Yaw Rate (`0x024`, ID 36)
- **Signals:** 10-bit unsigned integer with offset:
  $$\text{yaw}_{\text{raw}} = ((\text{byte}[0] \ \& \ 0\text{x}03) \ll 8) \mid \text{byte}[1]$$
- **Physical Rate:** Centered around raw 512 with scale factor $0.244\text{ deg/s}$:
  $$\text{yaw}_{\text{deg/s}} = (\text{yaw}_{\text{raw}} - 512) \times 0.244 - \text{bias}$$
- Observed raw values: 359 to 641 (angular rate range: $-37.33^\circ/\text{s}$ to $+31.48^\circ/\text{s}$).
- A stationary motion mask (speed $< 0.1\text{ m/s}$) clamps gyro drift during stops to avoid accumulating quantized drift.

### C. Transmission Gear (`0x3BC`, ID 956)
- **Signals:** Payload byte 1 bits 0–5:
  - `0x10` (16): Reverse (`R`)
  - `0x00` / `0x01`: Drive / Sport (`D` / `S`)
  - `0x20`: Park (`P`)
  - `0x08`: Neutral (`N`)
- **Trip Start:** Reverses 5.5 meters out of a parking stall with wheels turned, before shifting to Drive and heading out onto the road network.

---

## 3. Road-Matching Optimization

1. **Equirectangular Projection:** Centered at destination `38.9166896, -77.2210292`:
   $$\text{metres\_per\_lat} = 111,111.0\text{ m/deg}$$
   $$\text{metres\_per\_lon} = 111,111.0 \times \cos(\text{lat}_{\text{end}}) \approx 86,462.6\text{ m/deg}$$
2. **Highway Reference Points:** 922 points sampled along Route 7 Eastbound (OSM Relation `176453`, 313 ways) between 800 m and 20 km from the endpoint.
3. **Differential Evolution Optimization:**
   - Parameter 1: **Yaw Bias** = `0.070416 deg/s`
   - Parameter 2: **Heading at 1735s** = `180.485°` (mathematical angle, compass bearing `269.515°`)
   - Parameter 3: **Speed Scale** = `1.01512`
   - **Fit RMS:** 132.11 metres over the 22 km highway run.

---

## 4. Final Result & Reproduction

- **Calculated Start Estimate:** `39.0287198, -77.4043082`
- **Submitted Estimate:** `39.0287, -77.4043`
- **User-Confirmed Coordinate:**
  ```
  39.0286785634, -77.4043945431
  ```
- **Location:** Cascades area of Sterling, Loudoun County, Virginia.
- **Accuracy:** **8.51 metres** from the ground-truth coordinate (well within the 1,000-metre challenge tolerance).

### How to Reproduce
Run the complete end-to-end pipeline in one command:
```powershell
python run_all.py
```
Detailed writeup and source files:
- [Life_is_a_Highway_Writeup.pdf](file:///C:/Users/crist/OneDrive/Desktop/RSTCON%20CTF/Life%20is%20a%20Highway/Life_is_a_Highway_Writeup.pdf) — Complete technical writeup document with maps and figures.
- [WRITEUP.md](file:///C:/Users/crist/OneDrive/Desktop/RSTCON%20CTF/Life%20is%20a%20Highway/WRITEUP.md) — Comprehensive markdown documentation.
- [SCRIPTS.md](file:///C:/Users/crist/OneDrive/Desktop/RSTCON%20CTF/Life%20is%20a%20Highway/SCRIPTS.md) — All pipeline scripts in a single readable file.
- [scripts/](file:///C:/Users/crist/OneDrive/Desktop/RSTCON%20CTF/Life%20is%20a%20Highway/scripts) — Modular numbered Python stages (`00_` through `09_`).
- [output/](file:///C:/Users/crist/OneDrive/Desktop/RSTCON%20CTF/Life%20is%20a%20Highway/output) — Generated JSON metrics, CSV route points, and validation reports.
