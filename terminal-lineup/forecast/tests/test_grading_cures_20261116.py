"""Regression blockers for the 2026-11-16 grading contract cures
(FORECAST-GRADING-CONTRACT-20261116 / FORECAST-REPORTS-OOM-20261116).

Fail direction, on the pre-cure tree:
- earnings_ratio (Engine 11) raises GradingError("unknown outcome
  kind 'earnings_ratio'") in resolve_outcome, so 2,914 matured
  rows skip every grading run and Engine 11 has 0 graded rows.
- pin_event_passed (Engine 27's FE26 scored-zero rows) raises the
  same unknown-kind error instead of the named not-price-resolvable
  reason its record-resolved sibling kinds carry.
- first_failure_side (Engine 8) can never resolve in the streaming
  grading path: ledger.GRADING_CONTEXT_KINDS omits
  "wall_break_close_through", so the stream state's context rows
  never contain the wall siblings the resolver scans for.
- Engine 4 stage_3 rows (value {"medians_pct": ...}, no
  "resolved_by") crash the survival_brier scorer with
  KeyError('resolved_by'): 3,616 rows.
- forecast.run_grading_reports loaded the whole parsed ledger
  with Ledger.rows() (435,910 rows, measured peak RSS 3.31 GB)
  and was OOM-killed (exit -9), which run_grading turned into
  the forecast-grading leg's exit 1. That cure (streaming
  compaction) landed in run_grading_reports.compact_rows with
  its own blocker, forecast/tests/
  test_grading_reports_stream_20261116.py; this file blocks the
  four grading-contract breaks.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402

REG = R.load()
CLOCKS = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
LINEAGE = {"source_artifacts": [{"path": "f.json", "sha256": "ab" * 32}],
           "clocks": CLOCKS}

DAYS = [f"2026-10-{d:02d}" for d in range(5, 31)] + \
       [f"2026-11-{d:02d}" for d in range(2, 10)]


class FakePrices:
    path = "fixture-prices"

    def __init__(self, closes):
        # closes: {symbol: {date: close}}
        self.bars = {}
        self.volumes = {}
        for sym, by_date in closes.items():
            self.bars[sym] = {d: (c, c, c, c)
                              for d, c in by_date.items()}
            self.volumes[sym] = {d: 1000 for d in by_date}
        self.calendars = {s: sorted(t) for s, t in self.bars.items()}

    def has_session(self, s, d):
        return d in self.bars.get(s, {})

    def bar(self, s, d):
        try:
            return self.bars[s][d]
        except KeyError:
            raise G.GradingError(f"no bar for {s} on {d}")

    def close(self, s, d):
        return self.bar(s, d)[3]

    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s]
                if a <= d <= b]


def _ledger(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    return led


# ---- Engine 11: earnings_ratio ------------------------------------

def test_earnings_ratio_resolves_with_engine_arithmetic():
    # The engine's own worked numbers (refresh_gammaearningstrap
    # self_test): prev 200 -> close 210 on a 4.0% priced move is
    # ratio 1.25 and an exceedance; 100 -> 96 on 5.0% is 0.80.
    prices = FakePrices({"TEST": {DAYS[0]: 200.0, DAYS[1]: 210.0,
                                  DAYS[2]: 100.0, DAYS[3]: 96.0}})
    out = {"symbol": "TEST", "kind": "earnings_ratio",
           "report_date": DAYS[1], "priced_move_pct": 4.0,
           "arm": "main_negative_positioning"}
    realised, binary = G.resolve_outcome(out, prices)
    assert realised == pytest.approx(1.25)
    assert binary == 1.0
    out2 = dict(out, report_date=DAYS[3], priced_move_pct=5.0)
    realised2, binary2 = G.resolve_outcome(out2, prices)
    assert realised2 == pytest.approx(0.80)
    assert binary2 == 0.0
    # The live ledgered form: the engine carries the earnings
    # feed's expected-move field verbatim, a percent string.
    out3 = dict(out, priced_move_pct="4.0%")
    realised3, binary3 = G.resolve_outcome(out3, prices)
    assert realised3 == pytest.approx(1.25)
    assert binary3 == 1.0


def test_earnings_ratio_grades_end_to_end(tmp_path):
    prices = FakePrices({"TEST": {DAYS[0]: 200.0, DAYS[1]: 210.0}})
    led = _ledger(tmp_path)
    led.append_forecast_declared(
        engine_id="engine_11", issued_ts="2026-10-20T13:00:00Z",
        subject="TEST", quantity="earnings move size ratio",
        value={"arm": "main_negative_positioning",
               "priced_move_pct": 4.0, "claim_share_at_least": 0.55,
               "claim_median_ratio_at_least": 1.10},
        horizon_open=DAYS[1], horizon_close=DAYS[1],
        lineage=LINEAGE, families=["events_calendar"],
        outcome={"symbol": "TEST", "kind": "earnings_ratio",
                 "report_date": DAYS[1], "priced_move_pct": 4.0,
                 "arm": "main_negative_positioning"})
    row = [r for r in led.iter_rows() if r.get("type") == "forecast"][0]
    grade_row = G.grade_forecast(led, row, prices, REG)
    grade = grade_row["grade"]
    assert grade["realised"] == pytest.approx(1.25)
    assert grade["binary_outcome"] == 1.0
    assert grade["scores"]["exceedance"] == 1.0
    assert grade["arm"] == "main_negative_positioning"


# ---- Engine 27: pin_event_passed -----------------------------------

def test_pin_event_passed_is_named_not_unknown():
    assert "pin_event_passed" in G.NON_PRICE_RESOLVABLE_KINDS
    prices = FakePrices({"SPY": {DAYS[0]: 100.0}})
    out = {"kind": "pin_event_passed", "symbol": "SPY",
           "at_date": DAYS[0]}
    with pytest.raises(G.GradingError) as ei:
        G.resolve_outcome(out, prices)
    msg = str(ei.value)
    assert "unknown outcome kind" not in msg
    assert "scored zero" in msg


# ---- Engine 8: first_failure_side in the streaming path ------------

def test_first_failure_side_grades_in_streaming_path(tmp_path):
    day = DAYS[5]
    closes = {day: 105.0, DAYS[4]: 100.0}
    prices = FakePrices({"SPY": closes})
    led = _ledger(tmp_path)
    base = dict(engine_id="engine_08",
                issued_ts="2026-10-20T13:00:00Z", subject="SPY",
                horizon_open=day, horizon_close=day,
                lineage=LINEAGE, families=["modelled_inventory"])
    led.append_forecast_declared(
        quantity="call wall break", value={"p": 0.1,
                                          "cell": "call_wall_break_1s"},
        outcome={"symbol": "SPY", "kind": "wall_break_close_through",
                 "level": 110.0, "window_open": day,
                 "window_close": day, "at_date": day}, **base)
    led.append_forecast_declared(
        quantity="put wall break", value={"p": 0.3,
                                          "cell": "put_wall_break_1s"},
        outcome={"symbol": "SPY", "kind": "wall_break_close_through",
                 "level": 90.0, "window_open": day,
                 "window_close": day, "at_date": day}, **base)
    led.append_forecast_declared(
        quantity="first failure side",
        value={"bins": [0.1, 0.3, 0.6], "cell": "first_failure_1s"},
        outcome={"symbol": "SPY", "kind": "first_failure_side",
                 "at_date": day}, **base)
    state = led.grading_stream_state()
    skipped = []
    grades = G.run_grading_streaming(led, prices, REG, state,
                                     skipped=skipped)
    ffs = [g for g in grades
           if (g["grade"] or {}).get("realised") == 3.0]
    assert len(ffs) == 1, (
        f"first_failure_side did not grade in the streaming path; "
        f"skipped: {skipped}")
    assert not any(s["kind"] == "first_failure_side" for s in skipped)


# ---- Engine 4: stage_3 medians_pct ---------------------------------

def test_engine04_stage3_medians_grade_as_point_estimate(tmp_path):
    by_date = {d: 100.0 for d in DAYS}
    by_date[DAYS[0]] = 100.0
    by_date[DAYS[5]] = 101.0  # +1.00% over the +5 window
    prices = FakePrices({"TEST": by_date})
    led = _ledger(tmp_path)
    led.append_forecast_declared(
        engine_id="engine_04", issued_ts="2026-10-20T13:00:00Z",
        subject="TEST", quantity="stage_3_median_cumulative_return",
        value={"medians_pct": {"plus_1": 0.221, "plus_3": 0.528,
                               "plus_5": 2.5},
               "stage": "stage_3"},
        horizon_open=DAYS[1], horizon_close=DAYS[5],
        lineage=LINEAGE, families=["price"],
        outcome={"symbol": "TEST", "kind": "return",
                 "base_date": DAYS[0], "at_date": DAYS[5]})
    row = [r for r in led.iter_rows() if r.get("type") == "forecast"][0]
    grade_row = G.grade_forecast(led, row, prices, REG)
    grade = grade_row["grade"]
    assert grade["realised"] == pytest.approx(0.01)
    # estimate is the +5 median on the realised (fraction) scale
    assert grade["scores"]["abs_error"] == pytest.approx(
        abs(0.025 - 0.01))
    assert grade["scores"]["signed_error"] == pytest.approx(
        0.025 - 0.01)

