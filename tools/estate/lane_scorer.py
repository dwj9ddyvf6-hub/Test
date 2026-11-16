#!/usr/bin/env python3
"""Local lane-scorer kit (A-23). The three pieces that only make sense
together, for scoring a proactive lane against labelled windows:
  1. Pilot window-labelling recipe: benefit credited ONCE per window on
     the first in-window fire; MUST dominates MAY (a fire inside both a
     MUST and a MAY window earns the MUST benefit only); cost charged
     PER FIRE independently; a violation (fire inside a MUST_NOT window)
     is charged even when the same fire earns a benefit; misses are
     priced only as lost benefit (lower recall), never as extra cost.
  2. PAUC timing shape for the timing half: per window, timing credit is
     the window benefit scaled by (1 - normalized delay of the first
     in-window fire); PAUC is total timing credit over the maximum
     possible. The cost half stays local (per-fire cost above).
  3. Gap-dependent trajectory cases: the same words at a different
     elapsed time require the opposite decision; cases are generated
     with explicit gap values.
Standing caution, enforced: every fire and window carries explicit
timestamps; a fire without "ts" raises ValueError. Elapsed time is
never inferred from conversation position.

Usage: lane_scorer.py selftest
Library: score_lane(fires, windows) -> dict; make_gap_cases(...) -> list
"""
import sys

BENEFIT = {"MUST": 4, "MAY": 2}
FIRE_COST = 1
VIOLATION_COST = 4

def score_lane(fires, windows):
    for f in fires:
        if "ts" not in f:
            raise ValueError("fire missing explicit ts: timestamps are never inferred")
    for w in windows:
        if "start" not in w or "end" not in w or w.get("kind") not in ("MUST", "MAY", "MUST_NOT"):
            raise ValueError(f"window malformed (needs start, end, kind in MUST/MAY/MUST_NOT): {w}")
    benefit = timing_credit = max_timing = 0.0
    fired_windows = 0
    per_fire_cost = FIRE_COST * len(fires)
    violations = 0
    for w in windows:
        if w["kind"] == "MUST_NOT":
            violations += sum(1 for f in fires if w["start"] <= f["ts"] <= w["end"])
            continue
        in_win = sorted((f for f in fires if w["start"] <= f["ts"] <= w["end"]),
                        key=lambda f: f["ts"])
        b = BENEFIT[w["kind"]]
        max_timing += b
        if in_win:
            fired_windows += 1
            benefit += b
            span = max(1e-9, w["end"] - w["start"])
            delay = (in_win[0]["ts"] - w["start"]) / span
            timing_credit += b * (1.0 - min(1.0, max(0.0, delay)))
    # MUST dominates MAY: a fire counted in an overlapping MAY window whose
    # first fire also sits inside a MUST window earns MUST only. Handled by
    # capping total benefit at the MUST-first accounting: recompute MAY
    # credit only for MAY windows with no MUST overlap on their first fire.
    musts = [w for w in windows if w["kind"] == "MUST"]
    for w in windows:
        if w["kind"] != "MAY":
            continue
        in_win = sorted((f for f in fires if w["start"] <= f["ts"] <= w["end"]),
                        key=lambda f: f["ts"])
        if in_win and any(m["start"] <= in_win[0]["ts"] <= m["end"] for m in musts):
            benefit -= BENEFIT["MAY"]
            timing_credit -= BENEFIT["MAY"] * (1.0 - min(1.0, max(0.0,
                (in_win[0]["ts"] - w["start"]) / max(1e-9, w["end"] - w["start"]))))
    total_windows = sum(1 for w in windows if w["kind"] in BENEFIT)
    return {
        "benefit": benefit,
        "cost": per_fire_cost + VIOLATION_COST * violations,
        "net": benefit - (per_fire_cost + VIOLATION_COST * violations),
        "violations": violations,
        "recall": (fired_windows / total_windows) if total_windows else 0.0,
        "pauc": (timing_credit / max_timing) if max_timing else 0.0,
        "fires": len(fires),
        "seed_note": "score with a fresh seed per policy when sampling; seed recorded by caller",
    }

def make_gap_cases(words, gap_threshold_s, gaps=(60, 3600, 86400)):
    """Same words, opposite correct decision across the gap threshold."""
    cases = []
    for g in gaps:
        cases.append({"words": words, "gap_s": g,
                      "expect": "fire" if g >= gap_threshold_s else "silent",
                      "note": "decision flips on explicit elapsed time, not wording"})
    return cases

def selftest():
    windows = [{"start": 0, "end": 100, "kind": "MUST"},
               {"start": 200, "end": 300, "kind": "MAY"},
               {"start": 400, "end": 500, "kind": "MUST_NOT"}]
    fires = [{"ts": 10}, {"ts": 20}, {"ts": 450}]
    r = score_lane(fires, windows)
    assert r["benefit"] == 4, r  # once per window despite two fires in MUST
    assert r["violations"] == 1 and r["cost"] == 3 + 4, r  # per-fire cost + violation even alongside benefit accounting
    assert 0 < r["pauc"] <= 1, r
    overlap = score_lane([{"ts": 50}],
                         [{"start": 0, "end": 100, "kind": "MUST"},
                          {"start": 0, "end": 100, "kind": "MAY"}])
    assert overlap["benefit"] == 4, overlap  # MUST dominates MAY
    try:
        score_lane([{"no_ts": 1}], windows)
        raise SystemExit("timestamp-less fire must raise")
    except ValueError:
        pass
    cases = make_gap_cases("any update?", 1800)
    assert {c["expect"] for c in cases} == {"fire", "silent"}, cases
    print("SELFTEST PASS lane_scorer: benefit once per window, MUST dominates MAY, per-fire cost, violation charged, PAUC in (0,1], missing ts rejected, gap cases flip decision")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
