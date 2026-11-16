#!/usr/bin/env python3
"""Blocker for proactive_lane A-20 additions: silent-verdict audit and the
one-reformulation cap. Uses a temp ledger; never touches the live lane state.
"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proactive_lane as pl

def main():
    with tempfile.TemporaryDirectory() as d:
        led = os.path.join(d, "ledger.jsonl")
        rows = [
            {"ts": 1, "verdict": "fire", "origin_event": "e1"},
            {"ts": 2, "verdict": "silent", "origin_event": "e2"},
            {"ts": 3, "verdict": "slow", "origin_event": "e3"},
            {"ts": 4, "verdict": "silent", "origin_event": "e4"},
        ]
        with open(led, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        out = pl.audit_silent_verdicts(led, sample_n=2)
        assert out["counts"] == {"fire": 1, "silent": 2, "slow": 1}, out["counts"]
        assert out["silent_total"] == 3, out["silent_total"]
        assert [r["origin_event"] for r in out["silent_sample"]] == ["e3", "e4"]
        pl.record_reformulation(led, "e2", "narrowed recipient scope")
        try:
            pl.record_reformulation(led, "e2", "second try")
            raise AssertionError("second reformulation must raise")
        except ValueError:
            pass
        try:
            pl.record_reformulation(led, "e9", "")
            raise AssertionError("unnamed reformulation must raise")
        except ValueError:
            pass
    print("test_proactive_lane_audit OK: silent audit counts/sample and reformulation cap hold")

if __name__ == "__main__":
    main()
