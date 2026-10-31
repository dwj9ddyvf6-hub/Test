"""Regression blocker for the Squeeze Watch revisit (2026-10-29,
cure stream C): refresh_squeeze.py fail-closed on the
short-volume lane ever reporting stored days, so once the G9
store started the page could never publish again, and its
short-volume marker stayed not-available forever. The cure
publishes each name's short-volume share for the freshest
stored day beside its short interest. Fixtures only.
"""
import gzip
import importlib.util
import json
import os
import sys

SITE = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "site"))


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rsq = _load("refresh_squeeze")


def test_shortvol_shares_reads_the_stored_day(tmp_path):
    day = "2026-10-29"
    with gzip.open(tmp_path / f"{day}.json.gz", "wt",
                   encoding="utf-8") as fh:
        json.dump({"date": day, "names": {
            "AAPL": [40.0, 100.0], "MSFT": [10.0, 50.0],
            "ZERO": [0.0, 0.0]}}, fh)
    shares = rsq.shortvol_shares(str(tmp_path), day)
    assert shares == {"AAPL": 40.0, "MSFT": 20.0}


def test_shortvol_shares_refuses_a_mismatched_day(tmp_path):
    day = "2026-10-29"
    with gzip.open(tmp_path / f"{day}.json.gz", "wt",
                   encoding="utf-8") as fh:
        json.dump({"date": "2026-10-28", "names": {}}, fh)
    try:
        rsq.shortvol_shares(str(tmp_path), day)
    except ValueError:
        pass
    else:
        raise AssertionError("a mismatched stored day must refuse")


rsv = _load("refresh_shortvol")


def test_shortvol_zero_total_row_is_missing_not_a_refusal(tmp_path):
    # Live find: NJUN sits in the published FINRA file for
    # 2026-02-27 as (0, 0); the pre-cure refresh refused the
    # whole ledger on it. A zero-total row is no reading.
    morgue = tmp_path / "morgue"
    out = tmp_path / "out" / "data.json"
    days = ["2026-10-28", "2026-10-29"]
    stamp = {"status": "ok", "as_of": "2026-10-29",
             "source": "FINRA", "delay": "after close",
             "source_family_id": "finra", "days": 2,
             "first_date": days[0], "last_date": days[-1]}
    lanes = {"lanes": {"short_volume": stamp}}
    (morgue / "state" / "morgue").mkdir(parents=True)
    (morgue / "output").mkdir(parents=True)
    with open(morgue / "state" / "morgue" / "ext.json", "w") as fh:
        json.dump({"lanes": lanes}, fh)
    with open(morgue / "output" / "morgue-feed.json", "w") as fh:
        json.dump({"lanes": lanes}, fh)
    sv_dir = morgue / "state" / "morgue" / "shortvol"
    for day in days:
        os.makedirs(sv_dir, exist_ok=True)
        with gzip.open(sv_dir / f"{day}.json.gz", "wt",
                       encoding="utf-8") as fh:
            json.dump({"date": day, "names": {
                "AAPL": [40.0, 100.0], "NJUN": [0.0, 0.0]}}, fh)
    rsv.SHORTVOL_DIR = str(sv_dir)
    rsv.EXT_PATH = str(morgue / "state" / "morgue" / "ext.json")
    rsv.FEED_PATH = str(morgue / "output" / "morgue-feed.json")
    rsv.OUT_PATH = str(out)
    assert rsv.build() == 0
    data = json.loads(out.read_text())
    assert data["state"] == "collecting"
    assert data["days_on_record"] == 2
    syms = {t["symbol"] for t in data["tickers"]}
    assert syms == {"AAPL"}  # NJUN has no reading on any day


def test_the_old_lane_trip_is_gone():
    src = open(os.path.join(SITE, "refresh_squeeze.py"),
               encoding="utf-8").read()
    assert "no longer reports no" not in src
    assert "short_volume_share_pct" in src
    assert "sv_days" in src
