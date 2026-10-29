"""event_research: the one computation the source implemented for its earnings candidates — the surprise
normalisation of r4_candidate_evidence.R4CandidateEvidence.normalize_earnings (agentic-trading-desk main @4c8c179c,
run unmodified in a scratch copy of its tree: GRIFFITH_SRC) — vs the port's surprise_fraction
(desk/sleeves/families/event_research.py) on randomized earnings rows (actual / estimate present, missing, zero,
string-typed, negative; event and known times in order and reversed). Compared: READY rows' surpriseFraction exactly,
and that every QUARANTINED row (missing or zero estimate, missing actual) is one the port refuses (None) or one
quarantined for its timestamps only. The momentum half of MOMENTUM_PEAD is the vendored evaluate_daily_candidate
(receipt griffith_factor); the rest of the three rules has no source implementation to compare against.

    GRIFFITH_SRC=/path/to/scratch/agentic_src python3 -m tools.parity.event_research [n]"""
import json
import os
import random
import sys

from desk.sleeves.families import event_research as E

from . import write_receipt
from .griffith import run_source

SRC = r'''
import sys, json, tempfile, pathlib, sqlite3
sys.dont_write_bytecode = True
from r4_candidate_evidence import R4CandidateEvidence
tmp = pathlib.Path(tempfile.mkdtemp(prefix="case_")) / "d.db"            # inside PAYLOAD["tmp"]
ev = R4CandidateEvidence(tmp)
db = sqlite3.connect(tmp)
db.execute("""CREATE TABLE m8_research_evidence(sequence_id INTEGER PRIMARY KEY AUTOINCREMENT, evidence_id TEXT,
  symbols_json TEXT, published_at TEXT, effective_at TEXT, availability_state TEXT, raw_metadata_json TEXT,
  evidence_kind TEXT)""")
for i, r in enumerate(PAYLOAD["rows"]):
    db.execute("INSERT INTO m8_research_evidence(evidence_id,symbols_json,published_at,effective_at,availability_state,"
               "raw_metadata_json,evidence_kind) VALUES(?,?,?,?,?,?,?)",
               ("e%d" % i, json.dumps(r["symbols"]), r["known"], r["event"], r["state"],
                json.dumps({"provider_metadata": {"eps_estimate": r["est"], "eps_actual": r["act"]}}), "EARNINGS"))
db.commit()
for _ in range(20):
    if not ev.normalize_earnings(200)["inserted"]:
        break
out = {}
for sid, sf, state, reasons in db.execute(
        "SELECT source_evidence_id,surprise_fraction,state,reasons FROM r4_earnings_surprises"):
    out[sid] = [sf, state, json.loads(reasons)]
db.close()
import shutil
shutil.rmtree(tmp.parent, ignore_errors=True)
print(json.dumps(out))
'''


def make_rows(n, seed=31337):
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        est = rnd.choice([None, 0, 0.0, "0", "", rnd.uniform(-3, 5), round(rnd.uniform(-1, 3), 2), str(round(rnd.uniform(0.01, 4), 2))])
        act = rnd.choice([None, "", rnd.uniform(-3, 5), round(rnd.uniform(-1, 3), 2), str(round(rnd.uniform(-1, 4), 2))])
        known = f"2026-0{rnd.randint(1, 9)}-1{rnd.randint(0, 9)}T1{rnd.randint(0, 9)}:00:00+00:00"
        event = known if rnd.random() < 0.85 else f"2026-12-2{rnd.randint(0, 9)}T10:00:00+00:00"
        rows.append({"symbols": ["X%d" % i] if rnd.random() < 0.95 else ["A", "B"], "est": est, "act": act,
                     "known": known, "event": event, "state": "AVAILABLE" if rnd.random() < 0.95 else "STALE"})
    return rows


def _f(v):
    try:
        return float(v) if v not in (None, "", "None", "null") else None
    except (TypeError, ValueError):
        return None


def main(argv):
    tree = os.environ.get("GRIFFITH_SRC")
    if not tree or not os.path.isdir(tree):
        raise SystemExit("set GRIFFITH_SRC to a scratch copy of agentic-trading-desk@4c8c179")
    n = int(argv[0]) if argv else 2000
    rows = make_rows(n)
    src = run_source(SRC, {"rows": rows}, tree, 1800, "event_research_parity_")
    diffs, ready = [], 0
    for i, r in enumerate(rows):
        sf, state, reasons = src["e%d" % i]
        mine = E.surprise_fraction({"consensus": _f(r["est"]), "eps": _f(r["act"])})
        value_reasons = {"EPS_ESTIMATE_REQUIRED", "EPS_ACTUAL_REQUIRED", "NONZERO_EPS_ESTIMATE_REQUIRED"}
        if state == "READY":
            ready += 1
            if mine != sf:
                diffs.append({"row": i, "source": sf, "port": mine})
        elif set(reasons) & value_reasons:
            if mine is not None:
                diffs.append({"row": i, "source": [state, reasons], "port": mine})
    path_ = write_receipt("event_research", {
        "family": "event_research", "sleeves": list(E.SPECS), "cases": n, "identical": n - len(diffs),
        "n_diffs": len(diffs), "diffs": diffs[:30], "coverage": {"ready": ready, "quarantined": n - ready},
        "source": {"repo": "agentic-trading-desk", "commit": E.SOURCE["commit"],
                   "run": "R4CandidateEvidence.normalize_earnings"},
        "not_comparable": "the PEAD / SUE / momentum-PEAD selection, timing and sizing: registered rules the source "
                          "never implemented (tests/test_event_research.py checks them against the registry)"})
    print(json.dumps({"cases": n, "diffs": len(diffs), "ready": ready, "receipt": path_}))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
