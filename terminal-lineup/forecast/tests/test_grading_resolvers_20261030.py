"""Regression blockers for the 2026-10-30 grading cure (G1 remainder).

The live ledger grew outcome kinds after the 2026-10-29 resolver
pass: Engine 27's pin kinds (pin_breach_half_em,
pin_abs_distance_pct), Engine 19's provisional_proof_forward_check,
Engine 20's league_interval / league_ranking, and Engine 29's
cohort_barrier_race. Fail direction: on the pre-cure grading.py the
pin kinds and the four meta kinds all raise the generic
GradingError("unknown outcome kind ..."), and a taken binary_event
whose realised value has not been recorded yet raises a bare
KeyError instead of a named GradingError. Pin semantics are pinned
to Engine 27's own grade rows on the live ledger (IWM 2026-10-29:
close 284.01, pin 282.0, distance_pct 0.7128, em_pct 0.7627,
breached True).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402


class FakePrices:
    path = "fixture-prices"

    def __init__(self):
        self.bars = {"IWM": {"2026-10-29": (282.41, 285.0, 281.0, 284.01)}}
        self.volumes = {"IWM": {"2026-10-29": 1000}}
        self.calendars = {"IWM": ["2026-10-29"]}

    def has_session(self, s, d):
        return d in self.bars.get(s, {})

    def bar(self, s, d):
        return self.bars[s][d]

    def close(self, s, d):
        return self.bars[s][d][3]

    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s]
                if a <= d <= b]


P = FakePrices()


def test_pin_abs_distance_pct():
    out = {"symbol": "IWM", "kind": "pin_abs_distance_pct",
           "at_date": "2026-10-29", "pin": 282.0}
    realised, binary = G.resolve_outcome(out, P)
    assert realised == pytest.approx(0.7128, abs=1e-4)
    assert binary is None


def test_pin_breach_half_em():
    out = {"symbol": "IWM", "kind": "pin_breach_half_em",
           "at_date": "2026-10-29", "pin": 282.0, "em_pct": 0.7627}
    realised, binary = G.resolve_outcome(out, P)
    assert realised == pytest.approx(0.7128, abs=1e-4)
    # 0.7128 > half the expected move (0.38135): breached
    assert binary == 1.0
    far = dict(out, em_pct=2.0)  # half EM = 1.0 pct > distance
    assert G.resolve_outcome(far, P)[1] == 0.0


def test_meta_kinds_named_not_unknown():
    for kind in ("provisional_proof_forward_check", "league_interval",
                 "league_ranking", "cohort_barrier_race"):
        with pytest.raises(G.GradingError) as ei:
            G.resolve_outcome({"kind": kind, "symbol": "IWM"}, P)
        msg = str(ei.value)
        assert "not price-resolvable" in msg, (kind, msg)
        assert "unknown outcome kind" not in msg


def test_binary_event_without_realised_is_named():
    out = {"symbol": "IWM", "kind": "binary_event",
           "at_date": "2026-10-29"}
    with pytest.raises(G.GradingError) as ei:
        G.resolve_outcome(out, P)
    assert "realised" in str(ei.value)


def test_binary_event_with_realised_still_resolves():
    out = {"symbol": "IWM", "kind": "binary_event",
           "at_date": "2026-10-29", "realised": 1}
    assert G.resolve_outcome(out, P) == (1, 1.0)
