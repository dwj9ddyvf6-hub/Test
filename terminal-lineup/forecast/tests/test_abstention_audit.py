"""Regression tests for the abstention coverage audit
(grading.abstention_coverage_audit, adopted from the abstention
audit design in analysis sections 6.5 and 8.2 item 1).

The audit grades what an engine refused, under a separate audit
role, and must reproduce hand-computed refused distributions.
It must never alter a grade, a ledger row, or a published figure.
"""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402

REG = R.load()
BASE = "2026-10-20"
AT = "2026-10-27"


class AuditPrices:
    """Price stub: closes keyed by (symbol, date); every listed date
    is a session. Mirrors the PriceSource interface the grader uses."""
    path = "audit-fixture-prices"

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


def row(engine, subject, outcome, absence="present", close=AT):
    return {"type": "forecast", "engine_id": engine,
            "subject": subject, "absence_state": absence,
            "horizon_open": BASE, "horizon_close": close,
            "value": {"p": None} if absence != "present" else {"p": 0.5},
            "outcome": outcome}


def return_outcome(sym):
    return {"symbol": sym, "kind": "return", "base_date": BASE,
            "at_date": AT}


def test_refused_distribution_reproduces_hand_computed_values():
    closes, rows = {}, []
    # 30 refused: 15 at +10% (close 110), 15 at -5% (close 95) on base 100.
    # Hand-computed: mean = (15*0.10 + 15*-0.05)/30 = 0.025;
    # median = (-0.05 + 0.10)/2 = 0.025; favourable share = 15/30 = 0.5.
    for i in range(30):
        sym = f"R{i:02d}"
        closes[(sym, BASE)] = 100.0
        closes[(sym, AT)] = 110.0 if i < 15 else 95.0
        rows.append(row("engine_02", sym, return_outcome(sym),
                        absence="no_data"))
    # 30 taken: 20 at +4% (104), 10 at -2% (98).
    # Hand-computed: mean = (20*0.04 + 10*-0.02)/30 = 0.02;
    # median = 0.04 (positions 15 and 16 of the sorted list are both
    # +0.04); favourable share = 20/30.
    for i in range(30):
        sym = f"T{i:02d}"
        closes[(sym, BASE)] = 100.0
        closes[(sym, AT)] = 104.0 if i < 20 else 98.0
        rows.append(row("engine_02", sym, return_outcome(sym)))
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_02"]
    assert eng["taken"] == 30 and eng["refused"] == 30
    assert eng["refused_by_absence_state"] == {"no_data": 30}
    assert eng["refused_graded"] == 30 and eng["taken_graded"] == 30
    assert eng["coverage_state"] == "covered"
    (cell,) = eng["refused_outcomes"]
    assert cell["kind"] == "return" and cell["thin_cell"] is False
    assert cell["mean"] == pytest.approx(0.025)
    assert cell["median"] == pytest.approx(0.025)
    assert cell["favourable_share"] == pytest.approx(0.5)
    (taken_cell,) = eng["taken_outcomes"]
    assert taken_cell["mean"] == pytest.approx(0.02)
    assert taken_cell["median"] == pytest.approx(0.04)
    assert taken_cell["favourable_share"] == pytest.approx(20 / 30)


def test_thin_cell_publishes_counts_only():
    closes, rows = {}, []
    for i in range(5):  # 5 graded refused outcomes: below the 30 floor
        sym = f"S{i}"
        closes[(sym, BASE)] = 100.0
        closes[(sym, AT)] = 110.0
        rows.append(row("engine_02", sym, return_outcome(sym),
                        absence="no_print"))
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_02"]
    assert eng["refused"] == 5 and eng["refused_graded"] == 5
    (cell,) = eng["refused_outcomes"]
    assert cell["graded"] == 5 and cell["thin_cell"] is True
    assert cell["mean"] is None and cell["median"] is None
    assert cell["favourable_share"] is None


def test_unresolvable_kind_is_named_not_skipped():
    closes = {("SPY", AT): 105.0}
    rows = [row("engine_06", "SPY",
                {"symbol": "SPY", "kind": "max_drawdown", "at_date": AT},
                absence="no_data")]
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_06"]
    assert eng["refused_graded"] == 0 and eng["refused_unresolvable"] == 1
    assert eng["coverage_state"] == "unresolvable"
    assert "max_drawdown" in eng["coverage_reason"]
    assert eng["refused_outcomes"] == []


def test_binary_event_without_realised_has_no_price_route():
    # The live ledger's engine_12 abstention shape: a binary_event
    # outcome with no realised value recorded on the row.
    closes = {("AAPL", AT): 300.0}
    rows = [row("engine_12", "AAPL",
                {"symbol": "AAPL", "kind": "binary_event", "at_date": AT},
                absence="no_data")]
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_12"]
    assert eng["refused_unresolvable"] == 1 and eng["refused_graded"] == 0
    assert "no realised value" in eng["coverage_reason"]


def test_binary_event_with_realised_resolves_and_counts_favourable():
    closes, rows = {}, []
    for i in range(30):  # 30 refused events: 18 happened, 12 did not
        sym = f"B{i:02d}"
        closes[(sym, AT)] = 100.0
        rows.append(row("engine_30", sym,
                        {"symbol": sym, "kind": "binary_event",
                         "at_date": AT, "realised": 1 if i < 18 else 0},
                        absence="defect_abstention"))
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_30"]
    assert eng["refused_graded"] == 30
    (cell,) = eng["refused_outcomes"]
    assert cell["mean"] == pytest.approx(18 / 30)
    assert cell["favourable_share"] == pytest.approx(18 / 30)


def test_unmatured_refusals_are_pending_not_unresolvable():
    closes = {("SPY", BASE): 100.0}  # no session at horizon close
    rows = [row("engine_02", "SPY", return_outcome("SPY"),
                absence="not_yet_available")]
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_02"]
    assert eng["refused_not_yet_matured"] == 1
    assert eng["refused_unresolvable"] == 0 and eng["refused_graded"] == 0
    assert eng["coverage_state"] == "not_yet_matured"


def test_engine_without_abstentions_is_reported_as_such():
    closes = {("SPY", BASE): 100.0, ("SPY", AT): 101.0}
    rows = [row("engine_01", "SPY", return_outcome("SPY"))]
    audit = G.abstention_coverage_audit(rows, AuditPrices(closes))
    eng = audit["engines"]["engine_01"]
    assert eng["refused"] == 0
    assert eng["coverage_state"] == "no_abstentions"
    assert audit["totals"]["engines_with_abstentions"] == []


def test_audit_is_read_only_over_rows_and_figures(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("audit test")
    clocks = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
    lineage = {"source_artifacts": [{"path": "f.json",
                                     "sha256": "ab" * 32}],
               "clocks": clocks}
    common = dict(engine_id="engine_02", issued_ts="2026-10-20T13:00:00Z",
                  quantity="touch_probability", horizon_open=BASE,
                  horizon_close=AT, lineage=lineage, families=["price"])
    led.append_forecast(subject="SPY", value={"p": 0.8},
                        outcome={"symbol": "SPY", "kind": "touch",
                                 "level": 105.5, "window_open": BASE,
                                 "window_close": AT, "at_date": AT},
                        **common)
    led.append_forecast(subject="QQQ", value={"p": None},
                        outcome={"symbol": "QQQ", "kind": "touch",
                                 "level": 50.0, "window_open": BASE,
                                 "window_close": AT, "at_date": AT},
                        absence_state="no_data", **common)
    rows_before = copy.deepcopy(led.rows())
    figs_before = L.recompute_figures(rows_before)
    closes = {("SPY", BASE): 100.0, ("SPY", AT): 105.0,
              ("QQQ", BASE): 40.0, ("QQQ", AT): 45.0}
    prices = AuditPrices(closes)
    # touch needs window bars: give the stub full OHLC via closes map
    audit = G.abstention_coverage_audit(led.rows(), prices)
    assert led.rows() == rows_before            # ledger untouched
    assert L.recompute_figures(led.rows()) == figs_before  # grades untouched
    eng = audit["engines"]["engine_02"]
    assert eng["taken"] == 1 and eng["refused"] == 1
