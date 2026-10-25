# n07_05h4_c3r71f13d — Solve Writeup

**Category:** ICS / PLC / Web  
**Points:** 10  
**Flag:** `rstcon{LD_better_than_ST}`

---

## Challenge Description

> Production is down. The PLC battery was a dud, so the program is gone. It was a vendor's equipment, and they never told us it was there, so nobody knew the battery had failed.
>
> Fix the logic and get the line running again.

- Mirror 1: `http://18.215.143.250:8080`
- Mirror 2: `http://18.145.136.91:8080`

---

## Reconnaissance

The service serves a browser-based PLC simulator called **open-plcIOsim**. Fetching and grepping the JS bundle (`/assets/index-CnN86lsh.js`) immediately reveals two API endpoints:

```
/api/solve   POST — submit ladder rungs, receive letters
/api/flag    POST — submit assembled word, receive flag
```

### Puzzle structure

The JS defines 6 ladder logic scenarios in an array `M`, each with:

| Field | Meaning |
|-------|---------|
| `id` | Scenario ID (`"01"` – `"06"`) |
| `coil` | Target output coil name |
| `brief` | Human-readable task description |
| `slot` | Position of this letter in the final word |
| `bools` | Input tag names |
| `given` | Default input values shown to the user |
| `cases` | Test vectors `{steps, on}` used to verify correctness |
| `broken` | Factory function returning the correct reference rungs |

Solving all 6 puzzles yields 6 letters. Unscrambling them by `slot` spells the answer word.

---

## Node and Rung Format

From the JS evaluation engine:

```js
// Node kinds
q(tag)   → { id, kind: "NO",  tag }   // Normally Open contact
qt(tag)  → { id, kind: "NC",  tag }   // Normally Closed contact
Y(tag)   → { id, kind: "OTE", tag }   // Output coil (energise)
           { id, kind: "OTU", tag }   // Unlatch coil
           { id, kind: "TON", tag, PRE: ms }  // Timer On Delay

// Branch node (parallel paths) — no "kind" property
branch   → { id, or: [ [path1_nodes], [path2_nodes], ... ] }

// Rung
F(nodes) → { id, q: "<scenario_id>", nodes: [...] }
```

The `q` field on each rung is critical — it links the rung to its scenario. Without it the server returns `{"letters": {}}`.

---

## Scenario Solutions

### 01 — ALARM (slot 5 → letter Y)
> Energize ALARM when HI_LVL **or** LEAK is on. Use a branch.

```
─┬─[HI_LVL]─┬─(ALARM)
 └─[LEAK  ]─┘
```

Branch node with two parallel NO contacts, followed by OTE coil.

### 02 — INLET (slot 4 → letter T)
> Energize INLET when START is on. Normally open contact.

```
─[START]─(INLET)
```

### 03 — DOSE (slot 1 → letter A)
> Energize DOSE when AUTO is on and CL_FLT is off. Normally closed contact.

```
─[AUTO]─[/CL_FLT]─(DOSE)
```

NC contact on CL_FLT passes when CL_FLT = 0.

### 04 — FILL (slot 2 → letter F)
> LVL_LO is on. Add a coil so FILL turns on.

```
─[LVL_LO]─(FILL)
```

### 05 — WASTE (slot 3 → letter E)
> STOP is on and BW_PMP is latched on. Unlatch BW_PMP so WASTE turns on.

Two rungs (both tagged `q: "05"`):

```
Rung 0: ─[STOP]─(U BW_PMP)   ← unlatch when STOP=1
Rung 1: ─[/BW_PMP]─(WASTE)   ← WASTE on when BW_PMP unlatched
```

### 06 — BLOWER (slot 0 → letter S)
> Energize BLOWER when T_BW is done. FLOW is on. Preset 500 ms.

Two rungs (both tagged `q: "06"`):

```
Rung 0: ─[FLOW]─[TON T_BW PRE=500]
Rung 1: ─[T_BW.DN]─(BLOWER)
```

---

## Solve Script

```python
import urllib.request, json

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
def branch(*paths): return {"id": nid(), "or": list(paths)}
def rung(q_id, nodes): return {"id": nid(), "q": q_id, "nodes": nodes}

def post(path, body):
    req = urllib.request.Request(
        HOST + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

rungs = [
    # 01: ALARM = HI_LVL OR LEAK
    rung("01", [branch([no("HI_LVL")], [no("LEAK")]), ote("ALARM")]),
    # 02: INLET = START
    rung("02", [no("START"), ote("INLET")]),
    # 03: DOSE = AUTO AND NOT CL_FLT
    rung("03", [no("AUTO"), nc("CL_FLT"), ote("DOSE")]),
    # 04: FILL = LVL_LO
    rung("04", [no("LVL_LO"), ote("FILL")]),
    # 05: WASTE — unlatch BW_PMP on STOP
    rung("05", [no("STOP"), otu("BW_PMP")]),
    rung("05", [nc("BW_PMP"), ote("WASTE")]),
    # 06: BLOWER — TON timer
    rung("06", [no("FLOW"), ton("T_BW", 500)]),
    rung("06", [no("T_BW.DN"), ote("BLOWER")]),
]

letters = post("/api/solve", {"rungs": rungs})["letters"]
print("Letters:", letters)

# Slot map from JS: 01→5, 02→4, 03→1, 04→2, 05→3, 06→0
slot_map = {"01":5, "02":4, "03":1, "04":2, "05":3, "06":0}
word = ['_'] * 6
for sid, letter in letters.items():
    word[slot_map[sid]] = letter
word = ''.join(word)
print("Word:", word)  # SAFETY

flag = post("/api/flag", {"word": word})
print("Flag:", flag)  # rstcon{LD_better_than_ST}
```

### Output

```
Letters: {'01': 'Y', '02': 'T', '03': 'A', '04': 'F', '05': 'E', '06': 'S'}
Word: SAFETY
Flag: rstcon{LD_better_than_ST}
```

---

## Key Takeaways

1. **JS bundle is the manual.** The minified bundle contained the full scenario definitions, node type names, evaluation logic, and even the reference (broken) solutions. One grep for `/api/` revealed the entire attack surface.

2. **Branch nodes have no `kind` property.** Parallel contacts are represented as `{id, or: [[...], [...]]}` — a node whose type is inferred from the absence of `kind`. Using `kind:"XIC"` (common in other Modbus/ladder tools) would silently fail.

3. **The `q` field is the scenario linker.** Without tagging each rung with its scenario ID via `"q": "01"` etc., the server can't attribute the correct logic to the correct puzzle and returns empty letters.

4. **Multi-rung scenarios (05, 06) need both rungs tagged.** The server groups rungs by `q` value and evaluates them as a set — sending only one rung for a two-rung scenario fails the check.

5. **The flag is the word unscrambled by slot index.** Letters `Y T A F E S` at slots `5 4 1 2 3 0` → position order gives **S A F E T Y** → `SAFETY`.
