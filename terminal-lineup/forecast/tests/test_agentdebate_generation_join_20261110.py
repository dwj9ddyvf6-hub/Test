"""Regression blocker: AGENTDEBATE-GENERATION-JOIN-20261110.

Failure class (SYS-2, TOTAL APPLICATION census 2026-11-10):
refresh_agentdebate joined the Second Opinion's prints figures
against the Flow Board cell at the tape family's freshest
session. The tape family runs at 17:30 ET; the Second Opinion
refreshes in the 19:00 tools lane, so most evenings its prints
were built from the previous evening's tape card while the Flow
Board cell was the fresh card's: the parity check compared two
different generations and the consumer stopped nightly
("call-side net premium disagrees between records for SPY"),
although the estate's diagnoses of 2026-11-07, 2026-11-09 and
2026-11-10 each verified the figures match exactly at the
generation the Second Opinion was built from.

Cure pinned here: the consumer joins the Flow Board cell whose
published_at_utc equals the Second Opinion's
prints_published_at_utc (like for like by generation, the rule
the positioning gate already follows), fails closed when no
cell carries that generation, and stamps the page stale (never
current) when the joined generation is behind the freshest
tape session. The tools lane's existing tape family re-sync
(refresh_tools.py re-runs the family after the Second Opinion
advances) remains the ordered second run that lands the page
current the same evening; it is preserved, not replaced.

Fail direction: on the pre-cure code the disagreement fixture
below exits 1 at the parity check (it joins the freshest cell);
the source assertions name strings that exist only in the
cured sources.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
sys.path.insert(0, SITE)

import refresh_agentdebate as ad  # noqa: E402

GEN1 = "2026-11-09T21:51:45.802199+00:00"
GEN2 = "2026-11-10T21:47:10.090688+00:00"
MM_SESSION = "2026-11-09"
FUNDS = ["SPY", "QQQ", "IWM"]


def _records(so_session, prints_stamp, call, put, prints):
    so_names = []
    for sym in FUNDS:
        so_names.append({
            "symbol": sym,
            "directional": ["cautious", "cautious", "cautious"],
            "price": {"stance": "cautious", "score": 42.5,
                      "close": 100.0, "confirming": 0,
                      "checks_total": 8, "qualified": False},
            "prints": {"stance": "cautious", "prints": prints,
                       "call_net_premium": call,
                       "put_net_premium": put,
                       "net_premium": call + put},
            "positioning": {"stance": "cautious",
                            "dix_date": MM_SESSION, "spot": 99.0,
                            "call_wall": 110.0, "put_wall": 90.0,
                            "flip": 105.0, "below_flip": True},
        })
    so = {"session": so_session,
          "prints_published_at_utc": prints_stamp,
          "positioning_built_at_utc": "2026-11-10T00:00:00+00:00",
          "names": so_names}
    mm = {"session": MM_SESSION,
          "generated_at_utc": "2026-11-10T00:00:00+00:00",
          "indexes": [{"symbol": sym, "spot": 101.0,
                       "snapshot_spot": 99.0,
                       "call_wall": {"value": 110.0},
                       "put_wall": {"value": 90.0},
                       "flip": {"value": 105.0, "side": "above",
                                "distance_pct": 4.0}}
                      for sym in FUNDS]}
    fb = {"freshest_session": "2026-11-10",
          "published_at_utc": GEN2,
          "rows": [{"underlying": sym, "cells": [
              {"session": "2026-11-09", "published_at_utc": GEN1,
               "call_net_premium_usd": -100,
               "put_net_premium_usd": -200,
               "difference_usd": 100, "prints_examined": 1000},
              {"session": "2026-11-10", "published_at_utc": GEN2,
               "call_net_premium_usd": -999,
               "put_net_premium_usd": -888,
               "difference_usd": -111, "prints_examined": 2000},
          ]} for sym in FUNDS]}
    rd = {"reading": {"kind": "Range",
                      "sentence": "The market reading is range bound."},
          "checks": [{"id": "position",
                      "figure": "closed at 101 against a flip "
                                "level of 105"}]}
    pg = {"states": [{"key": "proving", "words": "Proving",
                      "definition": "Still proving."}]}
    return so, mm, fb, rd, pg


def _stage(tmp_path, monkeypatch, records):
    so, mm, fb, rd, pg = records
    paths = {}
    for key, doc in [("so", so), ("mm", mm), ("fb", fb),
                     ("rd", rd), ("pg", pg)]:
        p = os.path.join(str(tmp_path), key + ".json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        paths[key] = p
    out_dir = os.path.join(str(tmp_path), "agent-debate")
    monkeypatch.setattr(ad, "SO_PATH", paths["so"])
    monkeypatch.setattr(ad, "MM_PATH", paths["mm"])
    monkeypatch.setattr(ad, "FB_PATH", paths["fb"])
    monkeypatch.setattr(ad, "RD_PATH", paths["rd"])
    monkeypatch.setattr(ad, "PROVING_PATH", paths["pg"])
    monkeypatch.setattr(ad, "OUT_PATH",
                        os.path.join(out_dir, "data.json"))
    monkeypatch.setattr(ad, "HISTORY_PATH",
                        os.path.join(out_dir, "session-history.json"))
    return os.path.join(out_dir, "data.json")


def test_disagreement_case_completes_stamped_stale(tmp_path, monkeypatch):
    # Second Opinion one generation behind; its figures match
    # the GEN1 cell exactly and disagree with the freshest
    # (GEN2) cell on every figure. Pre-cure this exits 1.
    out_path = _stage(tmp_path, monkeypatch,
                      _records("2026-11-09", GEN1, -100, -200, 1000))
    ad.main()
    with open(out_path, encoding="utf-8") as fh:
        out = json.load(fh)
    assert out["session"] == "2026-11-09"
    assert out["tape_freshness"]["tape_session"] == "2026-11-10"
    assert out["tape_freshness"]["state"] == "stale"


def test_current_case_completes_stamped_current(tmp_path, monkeypatch):
    out_path = _stage(tmp_path, monkeypatch,
                      _records("2026-11-10", GEN2, -999, -888, 2000))
    ad.main()
    with open(out_path, encoding="utf-8") as fh:
        out = json.load(fh)
    assert out["session"] == "2026-11-10"
    assert out["tape_freshness"]["state"] == "current"


def test_unmatched_generation_still_fails_closed(tmp_path, monkeypatch):
    _stage(tmp_path, monkeypatch,
           _records("2026-11-09", "2026-11-08T00:00:00+00:00",
                    -100, -200, 1000))
    with pytest.raises(SystemExit):
        ad.main()


def test_sources_carry_the_generation_join():
    with open(os.path.join(SITE, "refresh_agentdebate.py"),
              encoding="utf-8") as fh:
        consumer = fh.read()
    assert 'so.get("prints_published_at_utc")' in consumer
    assert 'c.get("published_at_utc") == so_card' in consumer
    with open(os.path.join(SITE, "tape_family_run.py"),
              encoding="utf-8") as fh:
        family = fh.read()
    assert 'session == tape_session' in family
    with open(os.path.join(SITE, "refresh_tools.py"),
              encoding="utf-8") as fh:
        tools = fh.read()
    # The tools lane's tape family re-sync (the ordered second
    # run that brings the page current after the Second
    # Opinion advances) is preserved, not replaced.
    assert tools.index('"tape_family_run.py"') > \
        tools.index("refresh_second_opinion.py")
