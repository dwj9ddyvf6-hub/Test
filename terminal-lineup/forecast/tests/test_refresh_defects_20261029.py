"""Regression blockers for the two terminal refresh defects cured
2026-10-29:

1. refresh_chain.py refused to publish whenever the morgue Map
   stamps (Alpaca Map era, source alpaca-options) said no_data,
   even though the chain store now accrues under the TastyTrade
   collector (site/collect_chains.py) whose manifest is the store's
   own record. The cure checks the stored days against that
   manifest (latest ok line per file, sha256 of the bytes on disk)
   instead of the Map stamps, and accepts absent (null) open
   interest, the store contract's recorded state, while still
   refusing a present value that is not a number at or above zero.

2. refresh_earningsdrift.py required the feed's as_of_session (the
   board's last completed session, set by publish_feed from the
   board summary) to equal the study card's as_of (the ET calendar
   date the study ran). The daily rhythm runs the board preopen on
   the prior session and the studies postclose today, so the two
   dates differ by construction on every coherent cycle. The cure
   binds the feed's copy to the card by exact value equality (kept)
   plus generation order: the feed must have been generated at or
   after the card it copies.

Fixtures only; no live files are read or written.
"""

import gzip
import hashlib
import importlib.util
import json
import os
import sys

SITE = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "site"))
if SITE not in sys.path:
    sys.path.insert(0, SITE)


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rc = _load("refresh_chain")
red = _load("refresh_earningsdrift")

DAY = "2026-10-29"


def _stamp(status="no_data", as_of="2026-10-28", reason=None):
    st = {"status": status, "as_of": as_of,
          "source": "Alpaca options contracts and snapshots "
                    "(the Map's own reads)",
          "delay": "prior-close open interest; snapshots at the run",
          "source_family_id": "alpaca-options"}
    if reason:
        st["reason"] = reason
    return st


def _carrier_doc():
    cards = {und: _stamp(reason="no archived chain yet (the archive "
                                "starts with the first archived Map "
                                "chain)")
             for und in ("SPY", "QQQ", "IWM")}
    lane = _stamp(reason="no chain archived yet")
    return {"chain": {"cards": cards},
            "lanes": {"lanes": {"chain_archive": lane}}}


def _write_snapshot(chains_dir, und, rows):
    doc = {"underlying": und, "day": DAY, "spot": 500.0,
           "oi_date": None, "columns": ["occ", "oi", "volume", "iv"],
           "rows": rows}
    path = os.path.join(chains_dir, und, f"{DAY}.json.gz")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return path


def _rows(und, oi=None):
    return [[f"{und}261030C00500000", oi, None, None],
            [f"{und}261030P00500000", oi, None, None]]


def _manifest_line(chains_dir, und, path, sha=None):
    if sha is None:
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return {"ts_utc": f"{DAY}T22:39:41Z", "ts_et": f"{DAY}T18:39:41-0400",
            "symbol": und, "status": "ok", "path": path, "sha256": sha}


def _chain_env(tmp_path, tamper_sha_for=None, bad_oi_for=None):
    chains = tmp_path / "chains"
    lines = []
    for und in ("SPY", "QQQ", "IWM"):
        oi = -5 if und == bad_oi_for else None
        path = _write_snapshot(str(chains), und, _rows(und, oi=oi))
        sha = "0" * 64 if und == tamper_sha_for else None
        lines.append(_manifest_line(str(chains), und, path, sha=sha))
    with open(chains / "manifest.jsonl", "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")
    for name in ("ext.json", "ext_card.json", "morgue-feed.json"):
        with open(tmp_path / name, "w", encoding="utf-8") as fh:
            json.dump(_carrier_doc(), fh)
    rc.CHAINS_DIR = str(chains)
    rc.EXT_PATH = str(tmp_path / "ext.json")
    rc.CARD_PATH = str(tmp_path / "ext_card.json")
    rc.FEED_PATH = str(tmp_path / "morgue-feed.json")
    rc.OUT_PATH = str(tmp_path / "out" / "data.json")
    return tmp_path


def test_chain_publishes_collector_store_despite_map_no_data_stamps(
        tmp_path):
    _chain_env(tmp_path)
    assert rc.build() == 0
    data = json.load(open(rc.OUT_PATH))
    assert data["state"] == "snapshots_on_record"
    assert data["snapshots_on_record"] == 3
    assert data["freshest_snapshot"] == DAY
    spy = [u for u in data["underlyings"]
           if u["underlying"] == "SPY"][0]
    snap = spy["snapshots"][0]
    assert snap["contracts"] == 2
    strike = snap["expiries"][0]["strikes"][0]
    # Absent open interest stays absent, never invented as zero.
    assert strike["call"]["oi"] is None


def test_chain_refuses_when_manifest_hash_disagrees(tmp_path):
    _chain_env(tmp_path, tamper_sha_for="QQQ")
    assert rc.build() == 1
    assert not os.path.exists(rc.OUT_PATH)


def test_chain_refuses_present_negative_open_interest(tmp_path):
    _chain_env(tmp_path, bad_oi_for="SPY")
    assert rc.build() == 1
    assert not os.path.exists(rc.OUT_PATH)


# ---- earnings drift ----------------------------------------------------

EARN_MEAN = -0.0012
EARN_STD = 0.0144


def _earn():
    return {"state": "graded", "n": 36, "mean": EARN_MEAN,
            "median": -0.0018, "std": EARN_STD,
            "share_positive": 15 / 36,
            "sharpe": EARN_MEAN / EARN_STD,
            "label": "fixture", "symbols": ["AAPL", "MSFT", "NVDA"]}


def _earn_env(tmp_path, feed_generated="2026-10-29T20:51:17+00:00",
              feed_earn=None):
    earn = _earn()
    card = {"generated_at": "2026-10-29T20:51:16+00:00",
            "as_of": "2026-10-29", "earnings_dist": earn}
    feed = {"as_of_session": "2026-10-28",
            "generated_at_utc": feed_generated,
            "studies": {"earnings_dist":
                        earn if feed_earn is None else feed_earn}}
    with open(tmp_path / "studies_card.json", "w",
              encoding="utf-8") as fh:
        json.dump(card, fh)
    with open(tmp_path / "morgue-feed.json", "w",
              encoding="utf-8") as fh:
        json.dump(feed, fh)
    with open(tmp_path / "ledger.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"component": "study-earnings-dist",
                             "value": earn}) + "\n")
    with open(tmp_path / "studies_card.py", "w",
              encoding="utf-8") as fh:
        fh.write('EARNINGS_SYMBOLS = ("AAPL", "MSFT", "NVDA")\n'
                 'EARNINGS_LOOKBACK_DAYS = 1095\n')
    with open(tmp_path / "studies.py", "w", encoding="utf-8") as fh:
        fh.write("def earnings_moves(dates, closes, cap: int = 20):\n"
                 "    pass\n")
    red.CARD_PATH = str(tmp_path / "studies_card.json")
    red.FEED_PATH = str(tmp_path / "morgue-feed.json")
    red.LOG_PATH = str(tmp_path / "ledger.jsonl")
    red.ENGINE_PATH = str(tmp_path / "studies_card.py")
    red.STUDY_PATH = str(tmp_path / "studies.py")
    red.OUT_PATH = str(tmp_path / "out" / "data.json")
    return tmp_path


def test_earnings_publishes_when_feed_session_predates_run_date(
        tmp_path):
    # The coherent daily rhythm: board session 2026-10-28, study
    # run 2026-10-29, feed generated just after the card.
    _earn_env(tmp_path)
    assert red.build() == 0
    data = json.load(open(red.OUT_PATH))
    assert data["events"] == 36
    assert data["positive"] == 15
    assert data["as_of"] == "2026-10-29"


def test_earnings_refuses_feed_generated_before_the_card(tmp_path):
    _earn_env(tmp_path, feed_generated="2026-10-29T20:51:10+00:00")
    assert red.build() == 1
    assert not os.path.exists(red.OUT_PATH)


def test_earnings_refuses_feed_copy_that_differs_from_card(tmp_path):
    other = _earn()
    other["n"] = 35
    _earn_env(tmp_path, feed_earn=other)
    assert red.build() == 1
    assert not os.path.exists(red.OUT_PATH)
