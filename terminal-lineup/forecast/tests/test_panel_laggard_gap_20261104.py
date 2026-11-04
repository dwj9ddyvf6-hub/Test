"""Blocker for PANEL-LAGGARD-GAP-20261104.

advance() must insert a fetched session a symbol is missing inside
its stored run (a halted day whose zero bar was published late),
in date order, not only append sessions after the symbol's last
date. On the pre-cure code the interior session was dropped
(it filtered to dates strictly after the last stored date), the
hole stayed, and continuity-gated consumers (Momentum Clock)
refused to publish.
"""
import sys

sys.path.insert(0, "site")
sys.path.insert(0, "forecast")
import advance_price_panel as app


def _row(d, c=10.0, v=100):
    return [d, c, c, c, c, v]


def test_interior_gap_is_inserted_in_order():
    panel = {"SUPN": [_row("2026-10-29"), _row("2026-10-30"),
                      _row("2026-11-03", 7.0, 900)]}
    fetched = {"SUPN": {"2026-11-02": _row("2026-11-02", 10.0, 0),
                        "2026-11-03": _row("2026-11-03", 7.0, 900)}}
    appended, missing = app.advance(panel, fetched)
    dates = [r[0] for r in panel["SUPN"]]
    assert dates == ["2026-10-29", "2026-10-30", "2026-11-02",
                     "2026-11-03"], dates
    assert appended == {"SUPN": ["2026-11-02"]}, appended
    assert missing == [], missing


def test_append_after_last_still_works():
    panel = {"SPY": [_row("2026-11-02")]}
    fetched = {"SPY": {"2026-11-03": _row("2026-11-03", 11.0, 5)}}
    appended, missing = app.advance(panel, fetched)
    assert [r[0] for r in panel["SPY"]] == ["2026-11-02", "2026-11-03"]
    assert appended == {"SPY": ["2026-11-03"]}
    assert missing == []


def test_no_new_bars_reports_missing():
    panel = {"OLD": [_row("2026-10-01")]}
    appended, missing = app.advance(panel, {})
    assert appended == {}
    assert missing == ["OLD"]


def test_existing_dates_are_not_duplicated():
    panel = {"SPY": [_row("2026-11-02"), _row("2026-11-03")]}
    fetched = {"SPY": {"2026-11-03": _row("2026-11-03", 99.0, 1)}}
    appended, missing = app.advance(panel, fetched)
    assert [r[0] for r in panel["SPY"]] == ["2026-11-02", "2026-11-03"]
    assert panel["SPY"][1][4] == 10.0  # stored bar untouched
    assert appended == {}


if __name__ == "__main__":
    test_interior_gap_is_inserted_in_order()
    test_append_after_last_still_works()
    test_no_new_bars_reports_missing()
    test_existing_dates_are_not_duplicated()
    print("PASS")
