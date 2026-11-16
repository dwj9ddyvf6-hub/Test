#!/usr/bin/env python3
"""Replay fixture for research_filter.py (adoption A-27 regression blocker).

Recorded chunk set with expected keep/drop. Fails if the filter's threshold
or rubric handling changes silently.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from research_filter import filter_chunks

FIXTURE = [
    {"id": "c1", "sub_question": "q", "text": "direct answer", "score": 3},
    {"id": "c2", "sub_question": "q", "text": "partial evidence", "score": 2},
    {"id": "c3", "sub_question": "q", "text": "background pointer", "score": 1},
    {"id": "c4", "sub_question": "q", "text": "off topic", "score": 0},
    {"id": "c5", "sub_question": "q", "text": "weak, below threshold", "score": 0.5},
]
EXPECTED_KEPT = ["c1", "c2", "c3"]
EXPECTED_DROPPED = ["c4", "c5"]

def main():
    out = filter_chunks(FIXTURE)
    kept = [c["id"] for c in out["kept"]]
    dropped = [c["id"] for c in out["dropped"]]
    assert kept == EXPECTED_KEPT, f"kept {kept} != {EXPECTED_KEPT}"
    assert dropped == EXPECTED_DROPPED, f"dropped {dropped} != {EXPECTED_DROPPED}"
    try:
        filter_chunks([{"id": "bad", "score": 9}])
        raise AssertionError("out-of-range score must raise")
    except ValueError:
        pass
    print("test_research_filter OK: replay fixture keep/drop match")

if __name__ == "__main__":
    main()
