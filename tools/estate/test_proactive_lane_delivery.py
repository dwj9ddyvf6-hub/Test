#!/usr/bin/env python3
"""Blocker for the proactive lane's stage-2 delivery grading (discipline 1,
wired 2026-11-03): the delivery grade is computed inside the send path,
recorded on every fire, and metadata leakage blocks the fire. Uses temp
ledger/outbox; never touches live lane state."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proactive_lane as pl

def _run(pl_mod, cand, now):
    return pl_mod.run_candidate(cand, now=now)

def main():
    with tempfile.TemporaryDirectory() as d:
        pl.LEDGER = os.path.join(d, "ledger.jsonl")
        pl.OUTBOX = os.path.join(d, "outbox.jsonl")
        good = {"text": "Tools gate GREEN: unique-candidate cover complete",
                "purpose": "result", "origin_event": "tools-gate-test-1",
                "recipient": "principal", "p_accept": 0.9, "p_need": 1.0,
                "ask": "review tools gate", "class": "vertical"}
        r1 = _run(pl, good, now=1_800_000_000)
        assert r1["verdict"] == "fire", r1
        assert "delivery_score" in r1, "stage-2 grade must be recorded on the fire record"
        out = [json.loads(l) for l in open(pl.OUTBOX)]
        assert len(out) == 1 and out[0]["fire_id"] == r1["fire_id"], out
        leaky = dict(good)
        leaky["text"] = 'lane: tools-gate-digest verdict fire tau=0.20 origin_event evt-9 {"a": 1} ' + "word " * 60
        leaky["origin_event"] = "tools-gate-test-2"
        r2 = _run(pl, leaky, now=1_800_000_000 + 7200)
        assert r2["verdict"] == "blocked" and "metadata leakage" in r2["reason"], r2
        out = [json.loads(l) for l in open(pl.OUTBOX)]
        assert len(out) == 1, "the leaky draft must not reach the outbox"
    print("test_proactive_lane_delivery OK: grade recorded on fire, leakage blocked before outbox")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
