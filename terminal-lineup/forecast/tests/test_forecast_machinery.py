"""Corruption tests for the forecast machinery. Each test names the
corruption it blocks; all must pass on the built machinery."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402

REG = R.load()
CLOCKS = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
LINEAGE = {"source_artifacts": [{"path": "fixture.json", "sha256": "ab" * 32}],
           "clocks": CLOCKS}


def make_ledger(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    return led


def forecast_kwargs(**over):
    kw = dict(engine_id="engine_01", issued_ts="2026-10-20T13:00:00Z",
              subject="SPY", quantity="close_band_5s",
              value={"lower": 100.0, "upper": 110.0, "stated_coverage": 0.68},
              horizon_open="2026-10-21", horizon_close="2026-10-27",
              lineage=LINEAGE, families=["distributional_volatility"],
              outcome={"symbol": "SPY", "kind": "close",
                       "at_date": "2026-10-27"})
    kw.update(over)
    return kw


class FakePrices:
    path = "fixture-prices"
    def __init__(self):
        self.bars = {"SPY": {"2026-10-21": (100.0, 101.0, 99.0, 100.5),
                             "2026-10-27": (104.0, 106.0, 103.0, 105.0)}}
        self.calendars = {"SPY": sorted(self.bars["SPY"])}
    def has_session(self, s, d): return d in self.bars.get(s, {})
    def bar(self, s, d): return self.bars[s][d]
    def close(self, s, d): return self.bars[s][d][3]
    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s] if a <= d <= b]


def test_rewrite_attempt_breaks_chain_and_blocks_append(tmp_path):
    led = make_ledger(tmp_path)
    led.append_forecast(**forecast_kwargs())
    # rewrite history: edit the forecast row in place
    lines = open(led.path).read().splitlines()
    row = json.loads(lines[1]); row["value"]["upper"] = 999.0
    lines[1] = json.dumps(row)
    open(led.path, "w").write("\n".join(lines) + "\n")
    assert led.verify_chain() is False
    with pytest.raises(L.LedgerError):
        led.append_forecast(**forecast_kwargs(subject="QQQ"))


def test_duplicate_forecast_counts_once(tmp_path):
    led = make_ledger(tmp_path)
    _r1, c1 = led.append_forecast(**forecast_kwargs())
    _r2, c2 = led.append_forecast(**forecast_kwargs())
    assert c1 is True and c2 is False
    forecasts = [r for r in led.rows() if r["type"] == "forecast"]
    assert len(forecasts) == 1
    figs = L.recompute_figures(led.rows())
    assert figs["engine_01"]["forecasts"] == 1


def test_grade_before_maturity_refused(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs(
        horizon_close="2026-12-31",
        outcome={"symbol": "SPY", "kind": "close", "at_date": "2026-12-31"}))
    with pytest.raises(G.GradingError):
        G.grade_forecast(led, row, FakePrices(), REG)


def test_unregistered_family_refused(tmp_path):
    led = make_ledger(tmp_path)
    with pytest.raises(R.RegistryError):
        led.append_forecast(**forecast_kwargs(families=["astrology"]))
    with pytest.raises(R.RegistryError):
        REG.validate_family("astrology")


def test_missing_clock_or_lineage_hash_refused(tmp_path):
    led = make_ledger(tmp_path)
    bad = {"source_artifacts": [{"path": "x.json", "sha256": "ab" * 32}],
           "clocks": {"event_time": "t"}}
    with pytest.raises(L.LedgerError):
        led.append_forecast(**forecast_kwargs(lineage=bad))


def test_grade_appends_and_figures_recompute_from_ledger_alone(tmp_path):
    led = make_ledger(tmp_path)
    # engine_01's registered rule is pinball; use a distribution value
    row, _ = led.append_forecast(**forecast_kwargs(
        quantity="close_distribution_5s",
        value={"quantiles": {"0.1": 100.0, "0.5": 105.0, "0.9": 110.0}}))
    grade = G.grade_forecast(led, row, FakePrices(), REG)
    assert grade["grade"]["realised"] == 105.0
    assert "crps_approx" in grade["grade"]["scores"]
    figs = L.recompute_figures(led.rows())  # ledger rows only, no cache
    assert figs["engine_01"]["graded"] == 1
    assert figs["engine_01"]["mean_scores"]["pinball@0.5"] == 0.0
    with pytest.raises(L.LedgerError):  # double grade refused
        led.append_grade(forecast_row=row, grade=grade["grade"])


def test_brier_rule_on_probability_engine(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs(
        engine_id="engine_02", quantity="touch_probability",
        value={"p": 0.8},
        families=["price"],
        outcome={"symbol": "SPY", "kind": "touch", "level": 105.5,
                 "window_open": "2026-10-21", "window_close": "2026-10-27",
                 "at_date": "2026-10-27"}))
    grade = G.grade_forecast(led, row, FakePrices(), REG)
    assert grade["grade"]["binary_outcome"] == 1.0  # high 106 touches 105.5
    assert grade["grade"]["scores"]["brier"] == pytest.approx(0.04)


def test_correction_is_new_row_not_rewrite(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs())
    before = len(led.rows())
    led.append_correction(corrects_row_id=row["row_id"], note="fixture")
    assert len(led.rows()) == before + 1
    assert led.verify_chain() is True


def test_registry_completeness():
    assert len(REG.engines) == 30
    assert len(REG.families) == 6
    assert len(REG.data["defect_sources"]) == 3
    assert all(s["state"] == "proving" for s in REG.engines.values())
    assert REG.validate() is True


def test_real_price_source_loads():
    prices = G.PriceSource()
    assert prices.has_session("SPY", "2026-10-23")
    assert prices.close("SPY", "2026-10-23") > 0
