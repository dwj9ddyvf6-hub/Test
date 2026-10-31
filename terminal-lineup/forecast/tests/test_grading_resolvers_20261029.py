"""Regression blockers for the 2026-10-29 grading cure (G1/G2/G17).

Fail direction: on the pre-cure grading.py every new-kind test
raises GradingError("unknown outcome kind ..."), the abs_return
threshold test gets binary None (so its Brier scorer refuses), a
ledger row with no outcome symbol crashes is_matured with KeyError,
and run_grading aborts on the first unresolvable row. On the
pre-cure ledger.py, the cache test's second Ledger instance sees a
stale verified state (there is no cache at all: the property under
test is that appends stay fast AND external rewrites still refuse).
"""
import json
import math
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

# 12 sessions for TEST: closes rise then fall; volumes vary.
DAYS = [f"2026-10-{d:02d}" for d in range(5, 17)]
CLOSES = [100.0, 102.0, 101.0, 105.0, 103.0, 108.0,
          107.0, 106.0, 110.0, 109.0, 111.0, 112.0]


class FakePrices:
    path = "fixture-prices"

    def __init__(self):
        self.bars = {"TEST": {}, "SPY": {}}
        self.volumes = {"TEST": {}, "SPY": {}}
        for i, d in enumerate(DAYS):
            c = CLOSES[i]
            self.bars["TEST"][d] = (c - 1, c + 2, c - 3, c)
            self.volumes["TEST"][d] = 1000 + 100 * i
            self.bars["SPY"][d] = (200.0, 202.0, 198.0, 200.0 + i)
            self.volumes["SPY"][d] = 5000
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


P = FakePrices()


def test_abs_return_threshold_binary():
    out = {"symbol": "TEST", "kind": "abs_return",
           "base_date": DAYS[0], "at_date": DAYS[3],
           "threshold_fraction": 0.03}
    realised, binary = G.resolve_outcome(out, P)
    assert realised == pytest.approx(0.05)
    assert binary == 1.0


def test_max_drawdown():
    out = {"symbol": "TEST", "kind": "max_drawdown",
           "base_date": DAYS[0], "at_date": DAYS[-1],
           "window_open": DAYS[1], "window_close": DAYS[-1],
           "threshold_fraction": 0.04}
    realised, binary = G.resolve_outcome(out, P)
    # worst peak-to-trough: peak 105 at idx3, trough close 103 at
    # idx4: dd = 1-103/105
    assert realised == pytest.approx(1 - 103.0 / 105.0)
    assert binary == 0.0


def test_gap_fill_up_and_down():
    up = {"symbol": "TEST", "kind": "gap_fill", "at_date": DAYS[1],
          "prior_close": 100.0, "open": 103.0}
    # bar low = close-3 = 99 <= 100: filled
    assert G.resolve_outcome(up, P)[1] == 1.0
    down = {"symbol": "TEST", "kind": "gap_fill", "at_date": DAYS[1],
            "prior_close": 104.0, "open": 100.0}
    # bar high = close+2 = 104 >= 104: filled
    assert G.resolve_outcome(down, P)[1] == 1.0
    nofill = {"symbol": "TEST", "kind": "gap_fill", "at_date": DAYS[1],
              "prior_close": 110.0, "open": 100.0}
    assert G.resolve_outcome(nofill, P)[1] == 0.0


def test_close_vs_prior_close_sign():
    out = {"symbol": "TEST", "kind": "close_vs_prior_close_sign",
           "at_date": DAYS[1], "prior_close": 100.0}
    realised, binary = G.resolve_outcome(
        out, P, forecast_value={"predicted_close_sign": 1})
    assert realised == pytest.approx(0.02)
    assert binary == 1.0
    _r, binary2 = G.resolve_outcome(
        out, P, forecast_value={"predicted_close_sign": -1})
    assert binary2 == 0.0


def test_wall_and_flip_close_through():
    out = {"symbol": "TEST", "kind": "wall_break_close_through",
           "level": 104.0, "at_date": DAYS[3],
           "window_open": DAYS[1], "window_close": DAYS[3]}
    # reference close (day before window) = 100; level above;
    # close 105 on DAYS[3] closes through.
    assert G.resolve_outcome(out, P)[1] == 1.0
    far = dict(out, level=130.0)
    assert G.resolve_outcome(far, P)[1] == 0.0


def test_first_failure_side_with_context():
    ctx = [{"kind": "wall_break_close_through", "level": 104.0,
            "window_open": DAYS[1], "window_close": DAYS[1],
            "_cell": "call_wall_break_1s"},
           {"kind": "wall_break_close_through", "level": 90.0,
            "window_open": DAYS[1], "window_close": DAYS[1],
            "_cell": "put_wall_break_1s"}]
    out = {"symbol": "TEST", "kind": "first_failure_side",
           "at_date": DAYS[1]}
    realised, binary = G.resolve_outcome(out, P, context_outcomes=ctx)
    assert realised == 3.0  # close 102: neither wall closed through
    with pytest.raises(G.GradingError):
        G.resolve_outcome(out, P)


def test_realised_vol_and_shape():
    out = {"symbol": "TEST", "kind": "realised_vol",
           "base_date": DAYS[0], "sessions": 5}
    rv, binary = G.resolve_outcome(out, P)
    sq = [math.log(CLOSES[i + 1] / CLOSES[i]) ** 2 for i in range(5)]
    assert rv == pytest.approx(math.sqrt(252.0 * sum(sq) / 5))
    assert binary is None
    shape = {"symbol": "TEST", "kind": "vol_shape",
             "base_date": DAYS[0], "sessions": 21}
    # only 12 sessions on the fixture: window incomplete refuses
    with pytest.raises(G.GradingError):
        G.resolve_outcome(shape, P)


def test_realised_range_and_cohort_excess():
    out = {"symbol": "TEST", "kind": "realised_range_5s",
           "base_date": DAYS[0], "at_date": DAYS[4],
           "window_open": DAYS[1], "window_close": DAYS[4]}
    realised, _b = G.resolve_outcome(out, P)
    assert realised == pytest.approx((107.0 - 98.0) / 100.0 * 100.0)
    cohort = {"symbol": "TEST", "kind": "cohort_excess_5s",
              "base_date": DAYS[0], "at_date": DAYS[3],
              "benchmark": "SPY", "members": ["TEST"]}
    realised, _b = G.resolve_outcome(cohort, P)
    bench = 203.0 / 200.0 - 1.0
    assert realised == pytest.approx((0.05 - bench) * 100.0)


def test_volume_below_frozen_median():
    out = {"symbol": "TEST", "kind": "volume_below_frozen_median",
           "base_date": DAYS[0], "at_date": DAYS[5],
           "frozen_median_volume": 1150.0}
    # volumes 1100..1500 in window: 1100 < 1150 -> 1
    assert G.resolve_outcome(out, P)[1] == 1.0
    out2 = dict(out, frozen_median_volume=1000.0)
    assert G.resolve_outcome(out2, P)[1] == 0.0


def test_non_price_kinds_named_not_unknown():
    for kind in ("young_figure", "recheck_replication"):
        with pytest.raises(G.GradingError) as ei:
            G.resolve_outcome({"kind": kind}, P)
        assert "not price-resolvable" in str(ei.value)


def test_is_matured_without_symbol_does_not_crash():
    row = {"outcome": {"kind": "young_figure"},
           "horizon_close": "2027-10-29"}
    assert G.is_matured(row, P) is False


def test_run_grading_skips_unresolvable_and_grades_rest(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    kw = dict(engine_id="engine_02", issued_ts="2026-10-20T13:00:00Z",
              subject="TEST", quantity="touch_probability",
              value={"p": 0.8}, horizon_open=DAYS[1],
              horizon_close=DAYS[3], lineage=LINEAGE,
              families=["price"],
              outcome={"symbol": "TEST", "kind": "touch",
                       "level": 106.0, "window_open": DAYS[1],
                       "window_close": DAYS[3], "at_date": DAYS[3]})
    led.append_forecast(**kw)
    kw2 = dict(kw, subject="TEST2", quantity="bad_probability",
               outcome={"symbol": "TEST", "kind": "young_figure",
                        "at_date": DAYS[3]})
    # young_figure has no symbol: is_matured is False, so it is
    # simply not graded yet; use a matured-but-broken row instead:
    kw2["outcome"] = {"symbol": "TEST", "kind": "gap_fill",
                      "at_date": DAYS[3]}  # no prior_close -> raises
    led.append_forecast(**kw2)
    skipped = []
    grades = G.run_grading(led, P, REG, skipped=skipped)
    assert len(grades) == 1
    assert len(skipped) == 1 and skipped[0]["kind"] == "gap_fill"


def test_ledger_append_cache_still_refuses_external_rewrite(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = L.Ledger(path, registry=REG)
    led.append_genesis("test")
    for i in range(5):
        led.append_correction(corrects_row_id=led.rows()[0]["row_id"],
                              note=f"n{i}")
    assert led.verify_chain()
    # external rewrite (same length class) must be detected on the
    # next append even though this instance has a warm cache
    lines = open(path).read().splitlines()
    row = json.loads(lines[1])
    row["note"] = "tampered"
    lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
    open(path, "w").write("\n".join(lines) + "\n")
    with pytest.raises(L.LedgerError):
        led.append_correction(corrects_row_id=led.rows()[0]["row_id"],
                              note="after-tamper")
