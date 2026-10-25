# Life is a Highway CTF solution

The user-confirmed answer is **39.0286785634, -77.4043945431**.
The original submitted estimate was **39.0287, -77.4043**, about **8.51 metres** away.
The challenge accepts a point within 1 kilometre.

Read **WRITEUP.md** for the complete explanation and **SCRIPTS.md** for all
script source in one document. The PDF and editable Word copy contain the
technical writeup. Individual Python files are included for convenient execution.

## Run the solution

Use Python 3.12 or newer. From this folder:

```bash
python -m venv .venv
# Linux or macOS
source .venv/bin/activate
# Windows PowerShell instead
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_all.py
```

The workflow uses the included capture and frozen OpenStreetMap data. It does
not need network access and does not use the confirmed answer for fitting.
Results are written to `output/`. A normal run takes seconds to a few minutes,
depending on the machine.

Expected final fit, before the small local refinement in the sensitivity check:

```text
estimated_start_latitude       39.02871982814972
estimated_start_longitude     -77.40430815743889
bias_deg_per_second            0.07041628058182295
heading_at_1735s               180.4853612120586
speed_scale                   1.0151222330144072
road_point_to_trace_rms_m      132.10971255337884
reference_points              922
```

The heading above is a mathematical angle measured counterclockwise from east,
not a compass bearing. Small differences across dependency versions are normal.
The environment used for the documented run is saved in
`session_archive/environment.json`.

## What is included

| Location | Contents |
| --- | --- |
| `inputs/` | Original challenge description and unchanged gzip capture |
| `reference/` | Frozen Toyota DBC, Route 7 relation, parking/start maps, regional basemap |
| `scripts/` | Numbered, commented reproduction scripts and shared math |
| `output/` | Reproduced arrays, coordinates, route CSV, figures, metrics, validation |
| `session_archive/` | Three unchanged original programs, original results and exploratory figures |
| `session_archive/inline_exploration.py` | Organized replay of exploratory code originally run inline |
| `session_archive/EXPLORATION.md` | Actual solve sequence, failed requests, discarded approaches and caveats |
| `SCRIPTS.md` | All runnable Python source collected into one readable file |

To rerun the original final optimizer unchanged:

```bash
cd session_archive
python fit_analysis.py
python check_variants.py
```

The separate original `fit_start.py` is an exploratory local alignment, not the
final solver. Its saved result predates the final road-data snapshot; see the
archive notes before comparing a rerun with that older saved output.

## Reference data

Map data and tiles are from OpenStreetMap contributors:
https://www.openstreetmap.org/copyright

The Toyota signal definitions came from commaai opendbc:
https://github.com/commaai/opendbc

Network refresh is optional and writes to a separate folder:

```bash
python scripts/07_fetch_reference_data.py --discover-relation
```

Refreshing may change map geometry or DBC definitions. Keep the bundled snapshots
when reproducing the recorded numbers.
