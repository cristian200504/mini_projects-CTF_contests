"""
Step 1: pull the raw Plotly `data` (initial frame) and `frames` arrays out of the
handout HTML. The John Wick chat embeds a Plotly 3D voxel animation via
`Plotly.newPlot(...)` + `Plotly.addFrames(...)` calls on two very long lines.
This does simple bracket-matching JSON extraction (no JS engine needed).

Usage: run from this directory -> writes ./data/initial_data.json and ./data/frames.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(HERE, "..", "handout", "evilgram", "evilgram.html")
DATA_DIR = os.path.join(HERE, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def find_matching(s, start_idx, open_ch, close_ch):
    """Find the index of the char that closes the bracket at start_idx,
    respecting JSON string literals (so brackets inside strings don't count)."""
    assert s[start_idx] == open_ch
    depth = 0
    i = start_idx
    in_str = False
    esc = False
    while i < len(s):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("no matching bracket found")


def main():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # The two calls of interest live on the two longest lines of the file
    # (Plotly.newPlot(...) and Plotly.addFrames(...)). Find them by content
    # instead of hardcoding line numbers, in case the handout is re-rendered.
    newplot_line = next(l for l in lines if "Plotly.newPlot(" in l)
    addframes_line = next(l for l in lines if "Plotly.addFrames(" in l)

    # --- Plotly.newPlot("id", [data...], {layout...}, {config...})
    idx = newplot_line.index("Plotly.newPlot(")
    rest = newplot_line[idx:]
    data_start = rest.index("[")
    data_end = find_matching(rest, data_start, "[", "]")
    initial_data = json.loads(rest[data_start:data_end + 1])
    print("initial_data traces:", len(initial_data), "verts:", len(initial_data[0]["x"]))

    after_data = rest[data_end + 1:]
    layout_start = after_data.index("{")
    layout_end = find_matching(after_data, layout_start, "{", "}")
    layout = json.loads(after_data[layout_start:layout_end + 1])
    print("scene axis ranges:", {k: v.get("range") for k, v in layout.get("scene", {}).items() if isinstance(v, dict)})

    # --- Plotly.addFrames('id', [frames...])
    idx2 = addframes_line.index("Plotly.addFrames(")
    rest2 = addframes_line[idx2:]
    frames_start = rest2.index("[")
    frames_end = find_matching(rest2, frames_start, "[", "]")
    frames = json.loads(rest2[frames_start:frames_end + 1])
    frames.sort(key=lambda fr: int(fr["name"]))
    print("frames:", len(frames), "verts in frame 0:", len(frames[0]["data"][0]["x"]))

    with open(os.path.join(DATA_DIR, "initial_data.json"), "w") as f:
        json.dump(initial_data, f)
    with open(os.path.join(DATA_DIR, "frames.json"), "w") as f:
        json.dump(frames, f)

    print("wrote", DATA_DIR)


if __name__ == "__main__":
    main()
