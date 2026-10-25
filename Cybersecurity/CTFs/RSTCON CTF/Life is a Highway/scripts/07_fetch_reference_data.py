"""Optional network reference refresh; not called by the offline reproduction.

The solve used urllib after an initial 'requests' import failed. It tried
Overpass and broad map bboxes before using the core OSM relation/full endpoint.
Frozen successful responses are bundled so service changes do not block replay.
"""
import argparse
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from common import REFERENCE

URLS = {
    "toyota_2017.dbc": "https://raw.githubusercontent.com/commaai/opendbc/master/opendbc/dbc/generator/toyota/_toyota_2017.dbc",
    "route7_full.osm": "https://www.openstreetmap.org/api/0.6/relation/176453/full",
    "parking_map.osm": "https://www.openstreetmap.org/api/0.6/map?bbox=-77.225,38.914,-77.217,38.921",
    "start_map.osm": "https://www.openstreetmap.org/api/0.6/map?bbox=-77.415,39.02,-77.395,39.035",
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "LifeIsAHighwayCTFWriteup/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def discover_relation(way_id="227892589"):
    response = fetch(f"https://www.openstreetmap.org/api/0.6/way/{way_id}/relations")
    root = ET.fromstring(response)
    for relation in root.findall("relation"):
        tags = {tag.get("k"): tag.get("v") for tag in relation.findall("tag")}
        if tags.get("network") == "US:VA" and tags.get("ref") == "7":
            return relation.get("id")
    raise RuntimeError("No Virginia Route 7 relation found")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=REFERENCE / "refreshed")
    parser.add_argument("--discover-relation", action="store_true")
    args = parser.parse_args()
    if args.discover_relation:
        print("Route 7 relation:", discover_relation())
    args.destination.mkdir(parents=True, exist_ok=True)
    for name, url in URLS.items():
        payload = fetch(url)
        (args.destination / name).write_bytes(payload)
        print(name, len(payload))


if __name__ == "__main__":
    main()
