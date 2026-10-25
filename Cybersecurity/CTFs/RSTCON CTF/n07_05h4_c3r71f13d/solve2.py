import urllib.request
import urllib.error
import re
import json

HOST = 'http://18.215.143.250:8080'

# ── Node kinds (from JS) ──────────────────────────────────────────────────────
# q(tag)  = Mt("NO",  {tag}) → normally open contact
# qt(tag) = Mt("NC",  {tag}) → normally closed contact
# Y(tag)  = Mt("OTE", {tag}) → output coil
# TON     = Mt("TON", {tag, PRE?})
# OTU     = Mt("OTU", {tag}) → unlatch coil
# OTL     = Mt("OTL", {tag}) → latch coil
# F(nodes)= {id, nodes}      → rung
#
# CRITICAL: each rung must carry  "q": "<scenario_id>"
# so the server knows which puzzle it belongs to.
#
# Scenario 05 multi-rung: Ge() checks n===0 for the unlatch rung specially.
# Ge(t, e, n) where n is the rung index within that scenario.
#
# Scenario 06: 
#   Ge checks e.id==="06"&&n===0: runs I(r,{FLOW:1},600) then checks T_BW.DN
#   Two rungs: rung0=[FLOW→TON(T_BW,500)], rung1=[T_BW.DN→BLOWER]

_id = [0]
def nid():
    _id[0] += 1
    return f"x{_id[0]}"

def no(tag):   return {"id": nid(), "kind": "NO",  "tag": tag}
def nc(tag):   return {"id": nid(), "kind": "NC",  "tag": tag}
def ote(tag):  return {"id": nid(), "kind": "OTE", "tag": tag}
def otl(tag):  return {"id": nid(), "kind": "OTL", "tag": tag}
def otu(tag):  return {"id": nid(), "kind": "OTU", "tag": tag}
def ton(tag, pre=500): return {"id": nid(), "kind": "TON", "tag": tag, "PRE": pre}

def rung(q_id, nodes):
    return {"id": nid(), "q": q_id, "nodes": nodes}

# ── Scenario 01: ALARM = HI_LVL OR LEAK ──────────────────────────────────────
# F([q("HI_LVL"), q("LEAK"), Y("ALARM")])
# Branch: HI_LVL parallel with LEAK, then coil ALARM
# In the broken() code: q("HI_LVL") and q("LEAK") are SEPARATE nodes in a flat list
# meaning a ladder rung with a branch:
# The JS "branch" is represented as a node with an "or" array of parallel paths
# BUT looking at the broken() call: [q("HI_LVL"), q("LEAK"), Y("ALARM")]
# This is a flat 3-node rung: HI_LVL and LEAK in series? No, description says OR.
# The branch editor adds parallel nodes via "or" property.
# Let's try BOTH approaches:

# Approach A: flat series (what broken() literally says)
hi  = no("HI_LVL")
lk  = no("LEAK")
arm = ote("ALARM")
r01_flat = rung("01", [hi, lk, arm])

# Approach B: branched (HI_LVL with LEAK as parallel branch)
hi2  = no("HI_LVL")
lk2  = no("LEAK")
hi2["or"] = [[lk2]]
arm2 = ote("ALARM")
r01_branch = rung("01", [hi2, arm2])

# ── Scenario 02: INLET = START ────────────────────────────────────────────────
r02 = rung("02", [no("START"), ote("INLET")])

# ── Scenario 03: DOSE = AUTO AND NOT CL_FLT ──────────────────────────────────
# F([q("AUTO"), q("CL_FLT"), Y("DOSE")])  — wait, q() is NO not NC!
# But brief says NC on CL_FLT... The broken() uses q("CL_FLT") = NO contact??
# Let's look again: broken for 03 is: ()=>[F([q("AUTO"),q("CL_FLT"),Y("DOSE")])]
# q() = NO (normally open). But the brief says "when CL_FLT is OFF"...
# If CL_FLT is a "fault" flag, NC contact on it means: pass when CL_FLT=0.
# But the broken() reference solution uses q() = NO for CL_FLT?? 
# Maybe the test case has CL_FLT=0 in 'given', and NO(CL_FLT) would be OFF → DOSE OFF.
# The cases check: R({AUTO:1,CL_FLT:1},!1) must fail → need CL_FLT=0 to pass.
# So NC(CL_FLT) is correct. The broken() might actually use qt(). Let me recheck:
# From JS: j("03",...,()=>[F([q("AUTO"),q("CL_FLT"),Y("DOSE")])])
# Wait — actually looking at the raw M array string again:
# "()=>[F([q(\"AUTO\"),q(\"CL_FLT\"),Y(\"DOSE\")])]"
# That IS q() = NO for both. But with given {AUTO:1, CL_FLT:0},
# NO(AUTO)=1=pass, NO(CL_FLT)=0=FAIL → DOSE=OFF. That's wrong!
# Unless... the server evaluates differently. Let me just try qt() for CL_FLT.
r03_nc = rung("03", [no("AUTO"), nc("CL_FLT"), ote("DOSE")])
r03_no = rung("03", [no("AUTO"), no("CL_FLT"), ote("DOSE")])

# ── Scenario 04: FILL = LVL_LO ───────────────────────────────────────────────
# broken: ()=>[F([q("LVL_LO")])]  — just a contact, no coil??
# But we need FILL energised. Maybe the coil is implicit from the scenario definition.
# Let's try with coil and without.
r04_with = rung("04", [no("LVL_LO"), ote("FILL")])
r04_nocoil = rung("04", [no("LVL_LO")])

# ── Scenario 05: WASTE = unlatch BW_PMP ──────────────────────────────────────
# broken: ()=>[F([q("STOP")]), F([qt("BW_PMP"),Y("WASTE")])]
# Rung 0 (q=05): STOP contact — but what's the coil? unlatch BW_PMP?
# From Ge() for 05: checks n===0, runs I(r,{STOP:1,BW_PMP:1},50) → !y(r,"BW_PMP")
# So rung0 must unlatch BW_PMP when STOP=1. Needs OTU(BW_PMP).
# Rung 1 (q=05): NC(BW_PMP) → OTE(WASTE)
r05a = rung("05", [no("STOP"), otu("BW_PMP")])
r05b = rung("05", [nc("BW_PMP"), ote("WASTE")])

# But broken() says F([q("STOP")]) with no coil node — maybe rung0 just has STOP
# and the test only checks rung1 for WASTE? Let's also try:
r05a_nocoil = rung("05", [no("STOP")])

# ── Scenario 06: BLOWER = T_BW.DN (TON) ─────────────────────────────────────
# broken: ()=>[F([q("FLOW")]), F([q("T_BW.DN"),Y("BLOWER")])]
# Rung 0 (q=06): FLOW → TON(T_BW, 500ms)
# Rung 1 (q=06): T_BW.DN → BLOWER
r06a = rung("06", [no("FLOW"), ton("T_BW", 500)])
r06b = rung("06", [no("T_BW.DN"), ote("BLOWER")])

# ── Try multiple combinations ─────────────────────────────────────────────────
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

# Test 1: branch for 01, NC for 03, with coil for 04, with coil for 05a
print("=== Test 1: branch+NC+coils ===")
rungs1 = [r01_branch, r02, r03_nc, r04_with, r05a, r05b, r06a, r06b]
r = post_solve(rungs1)
print(r)

_id[0] = 100  # reset IDs

print("\n=== Test 2: flat for 01, NC for 03, with coil for 04, no coil for 05a ===")
rungs2 = [rung("01",[no("HI_LVL"),no("LEAK"),ote("ALARM")]),
          rung("02",[no("START"),ote("INLET")]),
          rung("03",[no("AUTO"),nc("CL_FLT"),ote("DOSE")]),
          rung("04",[no("LVL_LO"),ote("FILL")]),
          rung("05",[no("STOP")]),
          rung("05",[nc("BW_PMP"),ote("WASTE")]),
          rung("06",[no("FLOW"),ton("T_BW",500)]),
          rung("06",[no("T_BW.DN"),ote("BLOWER")])]
r2 = post_solve(rungs2)
print(r2)

_id[0] = 200

print("\n=== Test 3: branch for 01, NO for 03 (as in broken()), rest same ===")
h = no("HI_LVL"); l = no("LEAK"); h["or"] = [[l]]
rungs3 = [rung("01",[h,ote("ALARM")]),
          rung("02",[no("START"),ote("INLET")]),
          rung("03",[no("AUTO"),no("CL_FLT"),ote("DOSE")]),
          rung("04",[no("LVL_LO"),ote("FILL")]),
          rung("05",[no("STOP")]),
          rung("05",[nc("BW_PMP"),ote("WASTE")]),
          rung("06",[no("FLOW"),ton("T_BW",500)]),
          rung("06",[no("T_BW.DN"),ote("BLOWER")])]
r3 = post_solve(rungs3)
print(r3)
