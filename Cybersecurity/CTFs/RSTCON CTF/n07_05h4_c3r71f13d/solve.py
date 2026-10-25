import urllib.request
import urllib.error
import re
import json

HOST = 'http://18.215.143.250:8080'

# ── Understand the node builder functions from the JS ────────────────────────
# From the JS bundle:
#   q(name)   = normally open contact (NO)  -> {kind:"XIC", tag: name}
#   qt(name)  = normally closed contact (NC) -> {kind:"XIO", tag: name}
#   Y(name)   = output coil                 -> {kind:"OTE", tag: name}
#   F(nodes)  = rung                        -> {id:uuid, nodes: [...]}
#
# The server receives:  POST /api/solve  { "rungs": [ rung, ... ] }
# Each rung = { "id": str, "nodes": [ node, ... ] }
# Each node = { "id": str, "kind": "XIC"|"XIO"|"OTE"|"OTL"|"OTU"|"TON", ... }
#
# For branched rungs (parallel contacts), nodes have an "or" array:
#   { id, kind:"XIC", tag:"HI_LVL", or:[[{...LEAK node...}]] }
#
# Let's reconstruct each scenario's correct solution rungs.

def uid(n):
    # simple deterministic IDs; server doesn't care about exact UUID format
    return f"node-{n:04d}"

rung_counter = [0]
node_counter = [0]

def new_id(prefix="n"):
    node_counter[0] += 1
    return f"{prefix}{node_counter[0]:04d}"

def make_xic(tag):
    return {"id": new_id(), "kind": "XIC", "tag": tag}

def make_xio(tag):
    return {"id": new_id(), "kind": "XIO", "tag": tag}

def make_ote(tag):
    return {"id": new_id(), "kind": "OTE", "tag": tag}

def make_otl(tag):
    return {"id": new_id(), "kind": "OTL", "tag": tag}

def make_otu(tag):
    return {"id": new_id(), "kind": "OTU", "tag": tag}

def make_ton(tag, preset_ms=500):
    return {"id": new_id(), "kind": "TON", "tag": tag, "PRE": preset_ms}

def make_rung(nodes):
    return {"id": new_id("r"), "nodes": nodes}

# ── Build the correct solution for ALL 6 scenarios ──────────────────────────
# The server checks ALL rungs against ALL scenarios simultaneously.
# Each scenario's solution rungs contribute one letter when correct.
#
# Scenario 01: ALARM = HI_LVL OR LEAK → branched rung
#   [HI_LVL ─┬─ ALARM]      (parallel branch: LEAK)
#              └─ LEAK ──┘
# In JSON: node XIC(HI_LVL) with or:[[XIC(LEAK)]], then OTE(ALARM)
hi_lvl = make_xic("HI_LVL")
leak   = make_xic("LEAK")
hi_lvl["or"] = [[leak]]          # parallel branch
alarm  = make_ote("ALARM")
rung01 = make_rung([hi_lvl, alarm])

# Scenario 02: INLET = START (normally open)
#   [START ── INLET]
rung02 = make_rung([make_xic("START"), make_ote("INLET")])

# Scenario 03: DOSE = AUTO AND NOT CL_FLT (NC contact for CL_FLT)
#   [AUTO ── /CL_FLT ── DOSE]
rung03 = make_rung([make_xic("AUTO"), make_xio("CL_FLT"), make_ote("DOSE")])

# Scenario 04: FILL = LVL_LO (just a coil)
#   [LVL_LO ── FILL]    (the brief says "add a coil", implying LVL_LO contact + FILL coil)
rung04 = make_rung([make_xic("LVL_LO"), make_ote("FILL")])

# Scenario 05: WASTE = unlatch BW_PMP when STOP is on
#   Two rungs:
#   Rung A: [STOP]  (just the contact, to make rung active)
#   Rung B: [/BW_PMP ── WASTE]  (NC on latched coil to energise WASTE)
#   Actually from the JS broken solution: F([q("STOP")]), F([qt("BW_PMP"),Y("WASTE")])
#   So:
#   Rung A: [START]  -- just STOP contact, drives OTU
#   Rung B: [/BW_PMP ── WASTE]
# Wait, the JS says: F([q("STOP")]), F([qt("BW_PMP"),Y("WASTE")])
# F([q("STOP")]) = rung with just XIC(STOP) and no coil?
# That seems like it's just a contact rung (maybe to unlatch BW_PMP?)
# The brief says "Use an unlatch". OTU = unlatch coil.
# Correct interpretation:
#   Rung A: [STOP ── (OTU BW_PMP)]  → unlatch BW_PMP when STOP is on
#   Rung B: [/BW_PMP ── WASTE]      → WASTE on when BW_PMP is off (unlatched)
rung05a = make_rung([make_xic("STOP"), make_otu("BW_PMP")])
rung05b = make_rung([make_xio("BW_PMP"), make_ote("WASTE")])

# Scenario 06: BLOWER = T_BW.DN (TON timer done bit)
#   Rung A: [FLOW ── TON(T_BW, 500ms)]
#   Rung B: [T_BW.DN ── BLOWER]
rung06a = make_rung([make_xic("FLOW"), make_ton("T_BW", 500)])
rung06b = make_rung([make_xic("T_BW.DN"), make_ote("BLOWER")])

# ── Assemble all rungs and POST ───────────────────────────────────────────────
all_rungs = [rung01, rung02, rung03, rung04, rung05a, rung05b, rung06a, rung06b]

payload = json.dumps({"rungs": all_rungs}, indent=2)
print("=== Payload ===")
print(payload[:2000])

req = urllib.request.Request(
    HOST + "/api/solve",
    data=payload.encode(),
    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    method="POST"
)

print("\n=== POST /api/solve ===")
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode()
        print(f"Status: {r.status}")
        print(f"Response: {body}")
        data = json.loads(body)
        letters = data.get("letters", {})
        print(f"\nLetters received: {letters}")
        if letters:
            # Reconstruct word by sorting by slot
            print(f"Word (sorted by key): {''.join(v for k,v in sorted(letters.items()))}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
