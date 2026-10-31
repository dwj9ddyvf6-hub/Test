"""Regression blocker for G3 (DEEP panel not on disk), 2026-10-29.

Pre-cure behaviour: ~/workspace/morgue/data_cache/deep_bars.json did
not exist, Engine 3 (Own-Norm Depth) checked 1,832 names with 0
qualifying and fitted no curve, and Engine 15's 750-session class had
no long history anywhere on the box. These tests fail on that state
(the file is absent) and pass on the landed panel: they read the
panel file itself (never a log or a description of it) and assert the
contract refresh_ownnormdepth.py enforces: SPY present, SPY spanning
the fit era start (first date on or before 2016-01-01) through the
out-of-sample era (last date on or after 2023-01-01), rows in the
shipped [date, o, h, l, c, v] shape with strictly increasing dates,
and a counted population of names at or above the engine's
813-session floor (MIN_SESSIONS in refresh_ownnormdepth.py).
"""
import json
import os

PANEL = os.path.expanduser("~/workspace/morgue/data_cache/deep_bars.json")
MIN_SESSIONS = 813  # PCT_WINDOW + HIGH_WINDOW in refresh_ownnormdepth.py


def _load():
    assert os.path.exists(PANEL), "DEEP panel missing: deep_bars.json"
    with open(PANEL, encoding="utf-8") as fh:
        return json.load(fh)


def test_deep_panel_exists_and_spy_spans_both_eras():
    panel = _load()
    assert "SPY" in panel
    spy = panel["SPY"]
    assert spy[0][0] <= "2016-01-01", spy[0][0]
    assert spy[-1][0] >= "2023-01-01", spy[-1][0]
    assert len(spy) >= MIN_SESSIONS


def test_deep_panel_row_shape_and_clean_dates():
    panel = _load()
    for sym in ("SPY", "AAPL", "MSFT"):
        rows = panel[sym]
        assert len(rows) >= MIN_SESSIONS, sym
        dates = [r[0] for r in rows]
        assert dates == sorted(dates) and len(set(dates)) == len(dates)
        for r in rows[:5] + rows[-5:]:
            assert len(r) == 6
            assert all(isinstance(x, (int, float)) and x > 0
                       for x in r[1:5])


def test_deep_panel_has_qualifying_population():
    panel = _load()
    qualifying = sum(1 for rows in panel.values()
                     if len(rows) >= MIN_SESSIONS)
    # Pre-cure the count was 0 of 1,833 on every panel on disk. The
    # landed panel must carry a real population, not a token file.
    assert qualifying >= 1000, qualifying
    assert len(panel) >= 1500, len(panel)
