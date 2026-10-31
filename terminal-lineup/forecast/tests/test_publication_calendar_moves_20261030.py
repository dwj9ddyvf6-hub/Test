"""Regression blockers for the Earnings Calendar priced move cure
(2026-10-30, FIX STREAM 2 remainder of R-15).

Before the cure, refresh_earningscal.py published expected_move
null for every name and its note claimed no priced move record
existed, even after priced_moves.py landed a per name record;
refresh_earningsdistribution.py fail closed on ANY published
calendar move. These tests fail on that tree: the join helper did
not exist and the published calendar carried zero moves.
"""
import importlib.util
import json
import os

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "site")
SITE = os.path.normpath(SITE)


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_priced_move_join_requires_date_agreement():
    cal = _load("refresh_earningscal")
    priced = {"AAPL": {"report_date": "2026-11-02",
                       "priced_move_pct": 3.9552}}
    assert cal.priced_move_for(priced, "AAPL", "2026-11-02") == "4.0%"
    assert cal.priced_move_for(priced, "AAPL", "2026-11-03") is None
    assert cal.priced_move_for(priced, "MSFT", "2026-11-02") is None
    assert cal.priced_move_for(
        {"X": {"report_date": "2026-11-02", "priced_move_pct": None}},
        "X", "2026-11-02") is None


def test_published_calendar_moves_recount_from_priced_record():
    with open(os.path.join(SITE, "earnings-calendar", "data.json"),
              encoding="utf-8") as fh:
        cal = json.load(fh)
    with open(os.path.join(SITE, "earnings-record",
                           "priced_moves.json"),
              encoding="utf-8") as fh:
        priced = json.load(fh)["names"]
    published = {n["symbol"]: n for n in cal["names"]}
    with_move = {s: n for s, n in published.items()
                 if n.get("expected_move") is not None}
    assert with_move, "calendar still publishes no priced moves"
    for sym, n in with_move.items():
        entry = priced[sym]
        assert entry["report_date"] == n["date"]
        assert n["expected_move"] == f"{entry['priced_move_pct']:.1f}%"
    expect = {s for s, e in priced.items()
              if s in published
              and e.get("report_date") == published[s]["date"]}
    assert set(with_move) == expect
    assert cal["priced_moves_on_record"] == len(with_move)
