"""Extract the frozen Route 7 reference used by the final fit. Offline by default."""
import xml.etree.ElementTree as ET
import numpy as np
from common import REFERENCE, OUTPUT, json_write


def main():
    root = ET.parse(REFERENCE / "route7_full.osm").getroot()
    nodes = {int(node.get("id")): (float(node.get("lat")), float(node.get("lon")))
             for node in root.findall("node")}
    roads = {}
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        if tags.get("highway") not in ("primary", "trunk", "motorway"):
            continue
        coords = [nodes[int(node.get("ref"))] for node in way.findall("nd")]
        centre = np.mean(coords, axis=0)
        if 38.90 < centre[0] < 39.06 and -77.435 < centre[1] < -77.22:
            roads[way.get("id")] = {"coords": coords, "tags": tags}
    json_write(OUTPUT / "rt7_geometry.json", roads)
    print(f"Extracted {len(roads)} regional Route 7 ways")


if __name__ == "__main__":
    main()
