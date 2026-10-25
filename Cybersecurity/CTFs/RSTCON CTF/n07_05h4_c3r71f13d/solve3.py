import urllib.request
import urllib.error
import json

HOST = 'http://18.215.143.250:8080'

_id = [0]
def nid():
    _id[0] += 1
    return f"x{_id[0]}"

def no(tag):   return {"id": nid(), "kind": "NO",  "tag": tag}
def nc(tag):   return {"id": nid(), "kind": "NC",  "tag": tag}
def ote(tag):  return {"id": nid(), "kind": "OTE", "tag": tag}
def otu(tag):  return {"id": nid(), "kind": "OTU", "tag": tag}
def ton(tag, pre=500): return {"id": nid(), "kind": "TON", "tag": tag, "PRE": pre}

def branch(*paths):
    # branch node: no "kind", has "or": [[path1 nodes], [path2 nodes], ...]
    return {"id": nid(), "or": list(paths)}

def rung(q_id, nodes):
    return {"id": nid(), "q": q_id, "nodes": nodes}

def post_solve(rungs_list):
    payload = json.dumps({"rungs": rungs_list}).encode()
    req = urllib.request.Request(
        HOST + "/api/solve",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}

# ── Scenario 01: ALARM = HI_LVL OR LEAK ──────────────────────────────────────
# Branch node with two parallel paths, then OTE(ALARM)
# branch_node = { id, or: [ [NO(HI_LVL)], [NO(LEAK)] ] }
r01 = rung("01", [
    branch([no("HI_LVL")], [no("LEAK")]),
    ote("ALARM")
])

# ── Scenario 02: INLET = START ────────────────────────────────────────────────
r02 = rung("02", [no("START"), ote("INLET")])

# ── Scenario 03: DOSE = AUTO AND NOT CL_FLT ──────────────────────────────────
r03 = rung("03", [no("AUTO"), nc("CL_FLT"), ote("DOSE")])

# ── Scenario 04: FILL = LVL_LO ────────────────────────────────────────────────
r04 = rung("04", [no("LVL_LO"), ote("FILL")])

# ── Scenario 05: WASTE = unlatch BW_PMP ──────────────────────────────────────
# Ge(05, n=0): A([rung0]), I({STOP:1,BW_PMP:1},50) → BW_PMP must be OFF
#              A([rung0]), I({STOP:0,BW_PMP:1},50) → BW_PMP must be ON (not unlatched)
# So: when STOP=1 → unlatch BW_PMP (OTU). When STOP=0 → BW_PMP stays latched.
# Ge(05, n=1): A([rung1]), I({BW_PMP:0},50) → WASTE=ON
#              A([rung1]), I({BW_PMP:1},50) → WASTE=OFF
# So: when BW_PMP=0 → WASTE=ON. NC(BW_PMP) → OTE(WASTE)
r05a = rung("05", [no("STOP"), otu("BW_PMP")])
r05b = rung("05", [nc("BW_PMP"), ote("WASTE")])

# ── Scenario 06: BLOWER = T_BW.DN (TON timer) ────────────────────────────────
# Ge(06, n=0): FLOW=1 for 600ms → T_BW.DN must be ON
#              FLOW=1 for 600ms then FLOW=0 50ms → T_BW.DN must be OFF
#              FLOW=1 for 100ms → T_BW.DN must be OFF (not done yet)
# So: rung0 = [NO(FLOW), TON(T_BW, PRE=500)]
# Ge(06, n=1): set T_BW.DN=1 manually, run → BLOWER must be ON
#              T_BW.DN=0 → BLOWER must be OFF
# So: rung1 = [NO(T_BW.DN), OTE(BLOWER)]
r06a = rung("06", [no("FLOW"), ton("T_BW", 500)])
r06b = rung("06", [no("T_BW.DN"), ote("BLOWER")])

all_rungs = [r01, r02, r03, r04, r05a, r05b, r06a, r06b]

print("=== POST /api/solve with correct branch structure ===")
result = post_solve(all_rungs)
print("Response:", result)

letters = result.get("letters", {})
print(f"\nLetters: {letters}")

if letters:
    # slots: 01=slot5, 02=slot4, 03=slot1, 04=slot2, 05=slot3, 06=slot0
    slot_map = {"01":5, "02":4, "03":1, "04":2, "05":3, "06":0}
    word = ['_'] * 6
    for scenario_id, letter in letters.items():
        slot = slot_map.get(scenario_id)
        if slot is not None:
            word[slot] = letter
    print(f"Word (by slot): {''.join(word)}")
    print(f"All letters collected: {sorted(letters.items())}")
