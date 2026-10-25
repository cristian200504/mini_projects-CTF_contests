"""Run the complete offline reproduction from the bundled challenge inputs."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-inventory", action="store_true", help="Skip the full per-ID payload inventory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    jobs = ["00_inspect_capture.py", "01_extract_signals.py", "02_reconstruct_relative.py",
            "03_prepare_road_geometry.py", "04_fit_route.py", "05_check_calibration.py",
            "08_probe_wheel_model.py", "09_validate_confirmed_coordinate.py", "06_make_figures.py"]
    for name in jobs:
        if args.skip_inventory and name.startswith("00_"):
            continue
        print(f"\nRunning {name}", flush=True)
        subprocess.run([sys.executable, str(root/"scripts"/name)], check=True)
    print("\nCompleted. Results are in", root/"output")


if __name__ == "__main__":
    main()
