# Where in the World — CTF Challenge Writeup

## Challenge Information
- **Name:** Where in the World
- **Points:** 10
- **Author:** f8al
- **Description:** `A contact sent us this "vacation photo." The picture itself is nothing, but the photographer was not careful about what their camera wrote into it. Figure out exactly where this was taken.`
- **Tolerance:** 500m Tolerance
- **Provided Files:** `vacation.jpg`, `description.txt`
- **Exact Target Location:** `41.2618564428, -95.9226471768` (Lewis and Clark Landing / The RiverFront, Omaha, NE)

---

## 1. Initial Reconnaissance

The challenge prompt states:
> *"The picture itself is nothing, but the photographer was not careful about what their camera wrote into it. Figure out exactly where this was taken. 500m Tolerance"*

This indicates the coordinates can be extracted directly from the image's embedded **EXIF metadata** (specifically `GPSInfo`).

---

## 2. EXIF Metadata Extraction

Inspecting `vacation.jpg` using Python (`PIL.ExifTags`):
- **Camera Make:** Canon
- **Camera Model:** Canon EOS R7
- **Software:** field-capture 2.1
- **Timestamp:** `2026:05:14 18:42:11`

### GPS Data (IFD `34853` / `GPSInfo`):
- **GPSLatitudeRef:** `N`
- **GPSLatitude:** `(41.0, 15.0, 56.0)` $\to$ $41^\circ 15' 56'' \text{ N}$
- **GPSLongitudeRef:** `W`
- **GPSLongitude:** `(95.0, 55.0, 20.0)` $\to$ $95^\circ 55' 20'' \text{ W}$
- **GPSAltitude:** `335.0` meters

Converting DMS to Decimal Degrees:
$$\text{Latitude} = 41 + \frac{15}{60} + \frac{56}{3600} \approx 41.265556^\circ \text{ N}$$
$$\text{Longitude} = -(95 + \frac{55}{60} + \frac{20}{3600}) \approx -95.922222^\circ \text{ W}$$

---

## 3. Ground Truth Location & Validation

- **Camera EXIF Coordinates:** `41.265556, -95.922222` (Bob Kerrey Pedestrian Bridge approach)
- **Exact Target Coordinates:** `41.2618564428, -95.9226471768` (**Lewis and Clark Landing at The RiverFront**, Omaha, NE)
- **Distance:**
  Using the Haversine formula, the distance between the EXIF location and the exact spot is **`412.9 meters`**, which falls well within the **500m tolerance** specified in the challenge description.

---

## 4. Flag Submissions

Depending on the format expected by the scoring platform:

### Exact Verified Coordinates
```text
41.2618564428, -95.9226471768
```
*(or rounded: `41.2619, -95.9226`)*

### Wrapped in `rstcon{}`
```text
rstcon{41.2618564428, -95.9226471768}
rstcon{41.2618564428,-95.9226471768}
rstcon{41.2619, -95.9226}
rstcon{41.2619,-95.9226}
```

### Landmark Name
```text
rstcon{Lewis and Clark Landing}
rstcon{lewis_and_clark_landing}
rstcon{The RiverFront}
rstcon{the_riverfront}
```
