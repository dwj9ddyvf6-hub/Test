"""Regression blocker for the G3/G17 joint remainder, 2026-10-30:
Engines 3 and 15 could not run against the landed DEEP panel at
all. Both refreshers loaded the panel whole with json.load; the
2026-10-30 refresh proof run OOM killed both (exit -9,
self-analogue at 404s) on the 413 MB panel, and the landed panel
is 1,046 MB. Cure: a StreamedPanel lazy per-symbol view in both
refreshers (the pattern refresh_proofgate.py proved on this
panel): file text plus a symbol offset index, one symbol's rows
parsed per access, nothing cached.

Fail direction: pre-cure neither refresher defines StreamedPanel,
so this file fails at the attribute assertions. The end-to-end
build tests run each refresher's build() against a fixture
deep-format panel in a temp dir (live ledger for Engine 15 is a
temp ledger; Engine 3 appends nothing because its fixture live
panel has no qualifying names, by design) and assert the outputs
that were impossible pre-panel: Engine 15 ledgers real forecasts
for qualifying names; Engine 3 fits its curve and computes the
out-of-sample evaluation.
"""
import json
import math
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "site"))
sys.path.insert(0, os.path.expanduser("~/workspace/morgue"))

import refresh_ownnormdepth as e3  # noqa: E402
import refresh_selfanalogue as e15  # noqa: E402
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402


def _weekdays(start_iso, count):
    d = date.fromisoformat(start_iso)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _walk_rows(days, seed, start_price=100.0):
    rng = random.Random(seed)
    rows = []
    price = start_price
    for i, d in enumerate(days):
        drift = 0.0004 + 0.004 * math.sin(i / 40.0)
        close = price * math.exp(drift + rng.gauss(0.0, 0.011))
        open_ = price * (1.0 + rng.gauss(0.0, 0.002))
        high = max(open_, close) * (1.0 + abs(rng.gauss(0.0, 0.004)))
        low = min(open_, close) * (1.0 - abs(rng.gauss(0.0, 0.004)))
        vol = 1000000 * (1.0 + 0.3 * math.sin(i / 25.0)
                         + abs(rng.gauss(0.0, 0.1)))
        rows.append([d, round(open_, 4), round(high, 4),
                     round(low, 4), round(close, 4), int(vol)])
        price = close
    return rows


def _write_panel(path, panel):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(panel, fh)


def test_streamed_panel_matches_json_load(tmp_path):
    days = _weekdays("2020-01-02", 30)
    panel = {"SPY": _walk_rows(days, 1), "BRK.B": _walk_rows(days, 2),
             "AAA": _walk_rows(days[:5], 3)}
    path = str(tmp_path / "panel.json")
    _write_panel(path, panel)
    for mod in (e3, e15):
        view = mod.StreamedPanel(path)
        assert len(view) == 3
        assert set(view.keys()) == {"SPY", "BRK.B", "AAA"}
        assert "SPY" in view and "ZZZ" not in view
        for sym, rows in panel.items():
            assert view[sym] == rows, (mod.__name__, sym)
        assert {s: len(r) for s, r in view.items()} == {
            s: len(r) for s, r in panel.items()}
        # residency contract: no attribute holds parsed rows for
        # the universe (that is the OOM being cured)
        for attr in vars(view).values():
            assert not (isinstance(attr, dict)
                        and attr and all(
                            isinstance(v, list) for v in attr.values()))


def test_selfanalogue_build_ledgers_from_deep_fixture(tmp_path,
                                                      monkeypatch):
    days = _weekdays("2023-01-02", 800)
    panel = {"SPY": _walk_rows(days, 11)}
    for i, sym in enumerate(("AAA", "BBB", "CCC")):
        panel[sym] = _walk_rows(days, 20 + i)
    panel_path = str(tmp_path / "deep_bars.json")
    _write_panel(panel_path, panel)
    ledger_path = str(tmp_path / "ledger.jsonl")
    reg = registry_mod.load()
    led = ledger_mod.Ledger(ledger_path, registry=reg)
    led.append_genesis("streaming fixture")
    out_path = str(tmp_path / "data.json")
    monkeypatch.setattr(e15, "DEEP_PANEL_PATH", panel_path)
    monkeypatch.setattr(e15, "PANEL_PATH", panel_path)
    monkeypatch.setattr(e15, "LEDGER_PATH", ledger_path)
    monkeypatch.setattr(e15, "OUT_PATH", out_path)
    assert e15.build() == 0
    data = json.load(open(out_path))
    assert data["waiting"]["names_checked"] == 4
    assert data["waiting"]["names_qualifying"] >= 3
    assert data["live"]["forecasts_recorded"] >= 3
    rows = ledger_mod.Ledger(ledger_path, registry=reg).rows()
    mine = [r for r in rows if r.get("engine_id") == "engine_15"
            and r.get("type") == "forecast"]
    assert len(mine) >= 3


def test_ownnormdepth_build_fits_curve_from_deep_fixture(tmp_path,
                                                         monkeypatch):
    deep_days = _weekdays("2016-01-01", 2300)
    deep = {"SPY": _walk_rows(deep_days, 31)}
    for i, sym in enumerate(("AAA", "BBB", "CCC", "DDD")):
        deep[sym] = _walk_rows(deep_days, 40 + i)
    deep_path = str(tmp_path / "deep_bars.json")
    _write_panel(deep_path, deep)
    live_days = _weekdays("2026-03-02", 120)
    live = {"SPY": _walk_rows(live_days, 51),
            "AAA": _walk_rows(live_days, 52)}
    live_path = str(tmp_path / "board_bt_bars.json")
    _write_panel(live_path, live)
    out_path = str(tmp_path / "data.json")
    monkeypatch.setattr(e3, "DEEP_PANEL_PATH", deep_path)
    monkeypatch.setattr(e3, "LIVE_PANEL_PATH", live_path)
    monkeypatch.setattr(e3, "OUT_PATH", out_path)
    assert e3.build() == 0
    data = json.load(open(out_path))
    assert data["curve"]["state"] == "fitted_frozen"
    assert data["curve"]["fit_events"] > 0
    assert data["history"]["out_of_sample"]["state"] == "computed"
    assert data["history"]["out_of_sample"]["graded"] > 0
