"""Regression blockers for the never-started daily stores cured
2026-10-29 (cure stream C: G8, G9, G12).

1. refresh_darkprints.py refused to publish at all once per-stock
   days were stored ("per-stock days have started being stored;
   this page's honest state has changed"). The cure publishes the
   store: the two state stamps must describe the store exactly
   (status ok, day count, first and last day), and the page data
   carries the store's real session count plus the freshest
   session's per-stock shares.
2. refresh_shortvol.py published every stored day for every stock;
   with the store live (a multi-year backfill) that is an unusable
   page file. The cure keeps the store whole and publishes each
   stock's freshest PAGE_DAYS days, stating both numbers.
3. refresh_analogue.py required every permanent-log state entry to
   equal the card (impossible once the count grows: yesterday's
   entry carries yesterday's count) and required the feed's
   board-session date to equal the card's run-day date (different
   date kinds, the sibling of the earnings-drift defect). The cure
   binds the freshest log entry to the card, requires earlier
   counts to sit at or below the card's, and binds the feed by
   generation order plus exact state-section agreement; the page
   publishes the real accrued count and the freshest day's
   readings.

Fixtures only; no live files are read or written.
"""

import gzip
import importlib.util
import json
import os
import sys

SITE = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "site"))
if SITE not in sys.path:
    sys.path.insert(0, SITE)
MORGUE = os.path.expanduser("~/workspace/morgue")


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rd = _load("refresh_darkprints")
rs = _load("refresh_shortvol")
ra = _load("refresh_analogue")

SESSION = "2026-10-28"
DAYS = ["2026-10-27", "2026-10-28"]


def _lane_stamp(days):
    if not days:
        return {"status": "no_data", "as_of": SESSION,
                "source": "FINRA", "delay": "after close",
                "source_family_id": "finra",
                "reason": "no FINRA day stored yet"}
    return {"status": "ok", "as_of": SESSION, "source": "FINRA",
            "delay": "after close", "source_family_id": "finra",
            "days": len(days), "first_date": days[0],
            "last_date": days[-1]}


def _store_day(dirpath, day, names):
    os.makedirs(dirpath, exist_ok=True)
    with gzip.open(os.path.join(dirpath, f"{day}.json.gz"),
                   "wt", encoding="utf-8") as fh:
        json.dump({"date": day, "names": names}, fh)


def _darkprints_fixture(tmp_path, stamp_days):
    morgue = tmp_path / "morgue"
    out = tmp_path / "out" / "data.json"
    stamp = _lane_stamp(stamp_days)
    lanes = {"lanes": {"short_volume": stamp}}
    dix_index = {"date": SESSION, "value": 0.5,
                 "constituents_used": 499, "constituents_total": 503,
                 "coverage": 0.992}
    cards = []
    for sym, ratio in (("SPY", 0.527), ("QQQ", 0.672),
                       ("IWM", 0.442)):
        cards.append({"underlying": sym, "dix_ratio": ratio,
                      "dix_date": SESSION,
                      "dix_index": dix_index if sym == "SPY" else None})
    (morgue / "output").mkdir(parents=True)
    (morgue / "state" / "morgue").mkdir(parents=True)
    with open(morgue / "output" / "map_card.json", "w") as fh:
        json.dump({"built_utc": "2026-10-29T00:00:00+00:00",
                   "cards": cards}, fh)
    feed_map = [{"symbol": sym, "dix_date": SESSION, "dix": ratio,
                 **({"dix_index": dix_index} if sym == "SPY" else {})}
                for sym, ratio in (("SPY", 0.527), ("QQQ", 0.672),
                                   ("IWM", 0.442))]
    with open(morgue / "output" / "morgue-feed.json", "w") as fh:
        json.dump({"as_of_session": SESSION,
                   "generated_at_utc": "2026-10-29T01:00:00+00:00",
                   "map": feed_map, "lanes": lanes}, fh)
    with open(morgue / "output" / "ledger.jsonl", "w") as fh:
        for sym, ratio in (("SPY", 0.527), ("QQQ", 0.672),
                           ("IWM", 0.442)):
            row = {"component": "gex_static_v1", "underlying": sym,
                   "dix_ratio": ratio, "dix_date": SESSION,
                   "ts_utc": "2026-10-29T00:00:00+00:00"}
            if sym == "SPY":
                row["dix_index"] = dix_index
            fh.write(json.dumps(row) + "\n")
    with open(morgue / "state" / "morgue" / "ext.json", "w") as fh:
        json.dump({"lanes": lanes}, fh)
    sv_dir = morgue / "state" / "morgue" / "shortvol"
    for day in DAYS:
        _store_day(str(sv_dir), day,
                   {"AAPL": [40.0, 100.0], "MSFT": [10.0, 50.0]})
    rd.CARD_PATH = str(morgue / "output" / "map_card.json")
    rd.FEED_PATH = str(morgue / "output" / "morgue-feed.json")
    rd.LEDGER_PATH = str(morgue / "output" / "ledger.jsonl")
    rd.EXT_PATH = str(morgue / "state" / "morgue" / "ext.json")
    rd.SHORTVOL_DIR = str(sv_dir)
    rd.OUT_PATH = str(out)
    return out


def test_darkprints_publishes_the_live_per_name_store(tmp_path):
    out = _darkprints_fixture(tmp_path, DAYS)
    assert rd.build() == 0
    data = json.loads(out.read_text())
    assert data["state"] == "index_and_per_name"
    pn = data["per_name"]
    assert pn["state"] == "collecting"
    assert pn["sessions_on_record"] == 2
    assert pn["names_on_record"] == 2
    assert pn["latest"]["AAPL"] == 40.0
    assert pn["latest_session"] == "2026-10-28"
    # Engine 26's dark leg reads the readings list shape.
    readings = {(r["session"], r["symbol"]): r["pct"]
                for r in pn["readings"]}
    assert readings[("2026-10-28", "AAPL")] == 40.0
    assert readings[("2026-10-28", "MSFT")] == 20.0


def test_darkprints_refuses_a_stamp_that_misdescribes_the_store(
        tmp_path):
    out = _darkprints_fixture(tmp_path, ["2026-10-27"])  # stamp: 1 day
    assert rd.build() == 1
    assert not out.exists()


def _shortvol_fixture(tmp_path, n_days=25):
    morgue = tmp_path / "morgue"
    out = tmp_path / "out" / "data.json"
    days = [f"2026-09-{d:02d}" for d in range(1, 26)][:n_days]
    stamp = _lane_stamp(days)
    lanes = {"lanes": {"short_volume": stamp}}
    (morgue / "state" / "morgue").mkdir(parents=True)
    (morgue / "output").mkdir(parents=True)
    with open(morgue / "state" / "morgue" / "ext.json", "w") as fh:
        json.dump({"lanes": lanes}, fh)
    with open(morgue / "output" / "morgue-feed.json", "w") as fh:
        json.dump({"lanes": lanes}, fh)
    sv_dir = morgue / "state" / "morgue" / "shortvol"
    for day in days:
        _store_day(str(sv_dir), day, {"AAPL": [40.0, 100.0]})
    rs.SHORTVOL_DIR = str(sv_dir)
    rs.EXT_PATH = str(morgue / "state" / "morgue" / "ext.json")
    rs.FEED_PATH = str(morgue / "output" / "morgue-feed.json")
    rs.OUT_PATH = str(out)
    return out, days


def test_shortvol_publishes_store_count_with_a_bounded_page_window(
        tmp_path):
    out, days = _shortvol_fixture(tmp_path)
    assert rs.build() == 0
    data = json.loads(out.read_text())
    assert data["state"] == "collecting"
    assert data["days_on_record"] == 25
    assert data["freshest_day"] == days[-1]
    assert data["page_days_shown"] == rs.PAGE_DAYS
    rows = data["tickers"][0]["days"]
    assert len(rows) == rs.PAGE_DAYS
    assert rows[-1]["date"] == days[-1]
    assert rows[-1]["short_share_pct"] == 40.0


STATE_NOW = {"state": "insufficient_history",
             "history_sessions_accrued": 1,
             "p_nn": None,
             "reason": "P_NN needs >=126 accrued state sessions",
             "latest": {"date": "2026-10-29",
                        "vector": [0.01, 0.02, None, 0.45, 0.009]}}
STATE_BEFORE = {"state": "insufficient_history",
                "history_sessions_accrued": 0,
                "reason": "no accrued state history on disk yet"}


def _analogue_fixture(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out" / "data.json"
    card = {"as_of": "2026-10-29",
            "generated_at": "2026-10-29T21:00:00+00:00",
            "state_vectors": STATE_NOW}
    feed = {"as_of_session": "2026-10-28",
            "generated_at_utc": "2026-10-29T21:05:00+00:00",
            "studies": {"state_vectors": STATE_NOW}}
    with open(src / "studies_card.json", "w") as fh:
        json.dump(card, fh)
    with open(src / "morgue-feed.json", "w") as fh:
        json.dump(feed, fh)
    with open(src / "ledger.jsonl", "w") as fh:
        fh.write(json.dumps(
            {"component": "state-vectors", "value": STATE_BEFORE,
             "ts_utc": "2026-10-27T21:00:00+00:00"}) + "\n")
        fh.write(json.dumps(
            {"component": "state-vectors", "value": STATE_NOW,
             "ts_utc": "2026-10-29T21:00:00+00:00"}) + "\n")
    ra.CARD_PATH = str(src / "studies_card.json")
    ra.FEED_PATH = str(src / "morgue-feed.json")
    ra.LOG_PATH = str(src / "ledger.jsonl")
    ra.ENGINE_PATH = os.path.join(MORGUE, "studies.py")
    ra.OUT_PATH = str(out)
    return out


def test_analogue_publishes_the_growing_count(tmp_path):
    out = _analogue_fixture(tmp_path)
    assert ra.build() == 0
    data = json.loads(out.read_text())
    assert data["counts"]["sessions_recorded"] == 1
    assert data["counts"]["sessions_remaining"] == 125
    assert data["as_of_session"] == "2026-10-29"
    assert data["today"]["values"][0] == 0.01
    assert data["today"]["values"][2] is None
