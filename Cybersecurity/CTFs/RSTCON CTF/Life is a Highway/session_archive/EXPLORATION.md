# Original solve sequence and exploratory scripts

## Provenance

`fit_analysis.py`, `fit_start.py`, and `check_variants.py` are the exact three
saved Python source files used during the live solve. Their SHA256 hashes are
recorded in `../output/verification.json`. They have not been reformatted or
silently corrected for the writeup.

The other analysis originally ran as short Python programs sent inline to the
shell. `inline_exploration.py` reorganizes that inline analysis into named
commands for replay. It was assembled after the solve and is explicitly not
an untouched shell-history export. The numbered scripts in `../scripts/` are
also a writeup-time packaging of the working method, with comments, stable
paths, offline data, and machine-readable outputs.

The original session updated several working files repeatedly. The final
`fitted.npz` and final `rt7_geometry.json` are preserved here. Historical figures
and `start_fitted.npz` can reflect earlier states. Do not interpret every saved
figure as a view of the same final parameter set.

## Actual sequence

| Step | Action | Finding or outcome |
| --- | --- | --- |
| 1 | Read `description.txt`; inspect gzip first and last lines | Known endpoint and 1 km tolerance; ordinary candump records |
| 2 | Count records and CAN IDs | 1,740,622 records across 91 IDs |
| 3 | Inspect unique payload counts and per-byte minima/maxima | Identify frequently changing candidate motion messages |
| 4 | Look up common Toyota DBC definitions | Match speed, wheel speed, yaw, steering and later gear layout |
| 5 | Extract selected timestamp-plus-byte arrays | `can_signals.npz` |
| 6 | Decode and integrate speed; inspect stops and yaw | About 22.04 km; realistic speed range; offset sensitivity |
| 7 | Plot three relative paths | Yaw bias changes the whole route geometry |
| 8 | Attempt reference fetch with `requests` | Import failed because the module was absent |
| 9 | Switch fetches to `urllib.request` | DBC and small OSM parking box succeeded |
| 10 | Try Overpass services | 406, 502 and timeout failures; not needed by final solution |
| 11 | Inventory parking geometry | Endpoint located at Tysons Corner Center Parking Garage C |
| 12 | Plot final turns and parking map | Repeated garage-like traverses; approximate orientation clue |
| 13 | Compare yaw with rear wheel differential | Strong-turn correlation 0.994585 |
| 14 | Try broad core OSM map bounding boxes | Exceeded the 50,000 node limit |
| 15 | Minimize final-approach distance to nearby roads | 245.02 degree rotation looked numerically good but was physically implausible; discarded |
| 16 | Decode gear changes | Brief reverse manoeuvre near the start; include signed speed |
| 17 | Download small regional map patches | Usable road fragments, but incomplete coverage |
| 18 | Fetch and stitch zoom 12 OSM tiles | Regional visual context for rotating and bias-correcting the trace |
| 19 | Regress lateral acceleration over speed against gyro | Unstable between speed ranges; not used as the final heading model |
| 20 | Plot six bias choices over regional map | Establish Cascades to Tysons along Route 7 |
| 21 | Correct initially misplaced patch boxes | Some earlier boxes contained Hunter Mill or Dranesville roads rather than Route 7 |
| 22 | Fit partial Route 7 geometry with `fit_analysis.py` | Initial start around 39.02835, -77.40565 |
| 23 | Add reference patches and rerun | Estimate around 39.02882, -77.40439 |
| 24 | Fit starting-area roads using `fit_start.py` | Different local result with rotation near a search boundary; not selected |
| 25 | Query membership of Route 7 way 227892589 | Identify Virginia Route 7 relation 176453 |
| 26 | Download relation 176453 in full | Continuous highway reference in a 1,672,729-byte response |
| 27 | Extract final regional geometry | 313 ways; 922 sampled optimizer reference points |
| 28 | Run final global fit | 39.0287198281, -77.4043081574; road-reference RMS 132.1097 m |
| 29 | Compare speed-zero and wheel-zero intervals | Check low-speed masking and the first manoeuvres |
| 30 | Run `check_variants.py` | Constant bias, alternate yaw scale and linear-drift fits remain near Cascades |
| 31 | Submit rounded estimate | 39.0287, -77.4043 |
| 32 | User confirms accepted coordinate | 39.0286785634, -77.4043945431; confirmation was after fitting |

## Exploratory replay commands

From `session_archive/`, run:

```bash
python inline_exploration.py yaw-stops
python inline_exploration.py wheel-regression
python inline_exploration.py lateral-acceleration
python inline_exploration.py parking-inventory
python inline_exploration.py parking-orientation
python inline_exploration.py regional-bias-grid
python inline_exploration.py nearest-road-diagnostic
```

To optionally download the regional tiles again:

```bash
python inline_exploration.py fetch-region-tiles
```

This replay does not automatically make failed network requests. Their request
shapes and outcomes are recorded below. They were investigative attempts, not
dependencies of the accepted result.

## Network attempts

Overpass hosts tried included `overpass-api.de`, `overpass.kumi.systems`, and
`overpass.private.coffee`. One early status request returned 502. Interpreter
requests to the first host returned 406, including GET, a trailing-slash GET,
and POST variants. Other hosts timed out. These service responses are observations
from the session, not predictions of their present availability.

The large first query asked for major roads within 26 km of the endpoint:

```text
[out:json][timeout:60];
way(around:26000,38.9166896,-77.2210292)
  [highway~"^(primary|trunk|motorway|secondary|primary_link|trunk_link|motorway_link)$"];
out geom;
```

A smaller probe also failed through the first host:

```text
[out:json];way(38.91,-77.23,38.92,-77.22)[highway];out geom;
```

Core OSM `/api/0.6/map?bbox=...` calls failed with the node limit for these boxes:

```text
-77.46,38.98,-77.35,39.06
-77.35,38.90,-77.22,39.01
-77.30,38.91,-77.225,38.94
-77.36,38.94,-77.29,38.97
-77.42,38.975,-77.35,39.005
-77.45,39.005,-77.38,39.035
```

Successful map boxes, retained in `reference_patches/` or `../reference/`, were:

| Saved file | bbox in west south east north order |
| --- | --- |
| `parking_map.osm` | -77.225,38.914,-77.217,38.921 |
| `rt7_end.osm` | -77.25,38.91,-77.225,38.93 |
| `rt7_mid.osm` | -77.32,38.945,-77.295,38.965 |
| `rt7_west.osm` | -77.40,38.98,-77.375,39.0 |
| `rt7_mid2.osm` | -77.32,38.97,-77.295,38.99 |
| `rt7_west2.osm` | -77.40,39.0,-77.375,39.02 |
| `rt7_north.osm` | -77.425,39.02,-77.4,39.04 |
| `start_map.osm` | -77.415,39.02,-77.395,39.035 |
| `rt7_gap_a.osm` | -77.295,38.95,-77.275,38.977 |
| `rt7_gap_b.osm` | -77.35,38.985,-77.318,39.007 |

The unsuffixed mid and west boxes were useful demonstrations of why blindly
guessing a highway's latitude from memory was unreliable. They were not
the final highway reference. The final solve uses `../reference/route7_full.osm`.

The basemap used zoom 12, x tile indices 1166 through 1169, and y indices 1563
through 1567: 20 tiles stitched into 1024 by 1280 pixels. Its tiles came from
`https://tile.openstreetmap.org/12/{x}/{y}.png`. The canvas bounds were chosen
to cover longitude -77.49 to -77.20 and latitude 38.89 to 39.10.

## Intermediate numerical results

| Road data stage | Points | Start latitude | Start longitude | Road RMS m |
| --- | --- | --- | --- | --- |
| First useful partial reference | 307 | 39.02835327 | -77.40565304 | 108.97385 |
| Additional patches | 554 | 39.02882391 | -77.40439169 | 143.36426 |
| Full relation regional subset | 922 | 39.02871983 | -77.40430816 | 132.10971 |

Scores across these rows use different reference sets and cannot be ranked
as if they measured the same objective. Extra coverage can increase a score
while producing a better-supported route.

## Archive caveats

The final solver's saved source uses timestamp columns followed by payload bytes,
so column six of a saved speed array is payload byte five. Its comment about
keeping reference points between 1 km and 20 km is slightly inaccurate: the code
actually keeps radii greater than 800 m and less than 20 km.

`fit_start.py` was run before the full-relation final fit. Its historical output
was 39.03150144319316, -77.40657194842396, with translation approximately
(-188.19, 297.50) m and rotation -29.75 degrees. The final snapshot now in this
directory is a later input state. Replaying that exploratory script against
the final snapshot is useful for inspection but is not an exact replay of the
earlier local experiment.

The cleaned offline pipeline is the supported reproduction of the accepted
solution. Its outputs were checked against the final original arrays exactly.
