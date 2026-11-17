"""Regression blocker for RECORD-STREAM-20261116.

Failure of record: refresh_record.py exited -9 inside the
session 2026-11-16 settle (and again on the rescue retry).
Its abstention_audit_block feeds Ledger.iter_rows() to
grading.abstention_coverage_audit, but the audit retained
every forecast row in per-engine taken_rows / refused_rows
lists before resolving any of them: the whole parsed ledger
(~480k rows) resident beside the price source on a 6 GB box.
On a quiet box the same code completed in 102 s; under the
full refresh's combined load it was SIGKILLed twice.

Cure pinned here: the audit resolves each row into a per-side
accumulator (_AuditSide) as it streams past and retains only
counts, reason tallies and the graded (realised, favourable)
pairs. The returned structure is unchanged, proven by the
equivalence test below and by the pre-existing
test_abstention_audit.py suite.

Fail direction: against the pre-cure grading.py the retention
test fails (every yielded row stays alive inside the audit)
and the source assertion fails (taken_rows present). Set
GRADING_MODULE_DIR to a directory holding a pre-cure
grading.py to watch them fail.
"""
import gc
import importlib.util
import inspect
import os
import sys
import weakref

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.environ.get("GRADING_MODULE_DIR",
                            os.path.join(HERE, ".."))
sys.path.insert(0, os.path.abspath(MODULE_DIR))


def _load_grading():
    path = os.path.join(MODULE_DIR, "grading.py")
    spec = importlib.util.spec_from_file_location(
        "grading_stream_blocker", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _load_grading()
BASE = "2026-10-20"
AT = "2026-10-27"


class AuditPrices:
    """Price stub mirroring the interface the grader uses."""

    def __init__(self, closes):
        self.bars = {}
        for (sym, date), close in closes.items():
            self.bars.setdefault(sym, {})[date] = (
                close, close, close, close)
        self.calendars = {s: sorted(t) for s, t in self.bars.items()}

    def has_session(self, s, d):
        return d in self.bars.get(s, {})

    def bar(self, s, d):
        return self.bars[s][d]

    def close(self, s, d):
        return self.bars[s][d][3]

    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s]
                if a <= d <= b]


class Row(dict):
    """A dict that supports weak references, so the retention
    test can watch whether the audit keeps rows alive."""


def _row(i, absence):
    sym = f"S{i:03d}"
    return Row({"type": "forecast", "engine_id": "engine_02",
                "subject": sym, "absence_state": absence,
                "horizon_open": BASE, "horizon_close": AT,
                "value": {"p": 0.5},
                "outcome": {"symbol": sym, "kind": "return",
                            "base_date": BASE, "at_date": AT}})


def test_audit_source_does_not_retain_row_lists():
    src = inspect.getsource(G.abstention_coverage_audit)
    assert "taken_rows" not in src
    assert "refused_rows" not in src


def test_audit_does_not_retain_streamed_rows():
    closes = {}
    for i in range(120):
        closes[(f"S{i:03d}", BASE)] = 100.0
        closes[(f"S{i:03d}", AT)] = 110.0
    refs = []
    peak_alive = [0]

    def gen():
        for i in range(120):
            r = _row(i, "present" if i % 2 == 0 else "no_data")
            refs.append(weakref.ref(r))
            yield r
            gc.collect()
            alive = sum(1 for w in refs if w() is not None)
            peak_alive[0] = max(peak_alive[0], alive)

    audit = G.abstention_coverage_audit(gen(), AuditPrices(closes))
    eng = audit["engines"]["engine_02"]
    assert eng["taken"] == 60 and eng["refused"] == 60
    assert eng["taken_graded"] == 60 and eng["refused_graded"] == 60
    # The row in flight plus at most a couple in transit; the
    # pre-cure audit keeps all 120 alive for the whole run.
    assert peak_alive[0] <= 5


def test_audit_results_unchanged_on_hand_computed_fixture():
    closes, rows = {}, []
    for i in range(30):
        sym = f"R{i:02d}"
        closes[(sym, BASE)] = 100.0
        closes[(sym, AT)] = 110.0 if i < 15 else 95.0
        rows.append({"type": "forecast", "engine_id": "engine_02",
                     "subject": sym, "absence_state": "no_data",
                     "horizon_open": BASE, "horizon_close": AT,
                     "value": {"p": None},
                     "outcome": {"symbol": sym, "kind": "return",
                                 "base_date": BASE, "at_date": AT}})
    audit = G.abstention_coverage_audit(iter(rows),
                                        AuditPrices(closes))
    eng = audit["engines"]["engine_02"]
    assert eng["refused"] == 30 and eng["refused_graded"] == 30
    assert eng["coverage_state"] == "covered"
    (cell,) = eng["refused_outcomes"]
    assert cell["mean"] == pytest.approx(0.025)
    assert cell["favourable_share"] == pytest.approx(0.5)


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
