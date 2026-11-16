#!/usr/bin/env python3
"""Regression blocker for BELIEF-LEGACY-KEY-20261109.

Failure of record: polymarket_daily and kalshi_daily failed
every live run from the engine's first week with the bare
pull-log note "FAILED 'key'", while their raw API responses
saved fine (live/raw/collect_belief/<date>/ holds a good
response for every failed night). Root cause, proven by
offline reproduction on the 2026-11-09 saved responses: the
stored snapshot series were first written with the columns
date, venue, event, probability, volume and no "key" column.
collect_belief merges those stored rows with new rows keyed
by "key" and hands the merged set to write_series, whose
natural-key span read does r[columns[0]] with columns[0] ==
"key": the legacy row raises KeyError('key') and the whole
night's snapshot is lost, every night.

Cure pinned here: the merge in collect_belief writes the
merge key back into every stored row ({**r, "key": k}), so
every row handed to write_series carries the natural key
the write contract requires, and the legacy history is
preserved under its synthesised date|event key.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import psychology_engine  # noqa: E402
import pipeline  # noqa: E402

HEADER = "".join(f"# {k}: x\n" for k in [
    "series", "source", "source_url_or_route", "retrieved",
    "last_pull", "revision_policy", "as_of_meaning",
    "archive_claim", "downloaded_span", "breaks", "transforms",
    "file_sha256"])

LEGACY_PM = (HEADER + "date,venue,event,probability,volume\n"
             "2026-10-30,polymarket,Legacy Event,0.5,100\n")
LEGACY_KA = (HEADER + "date,venue,event,probability,volume\n"
             "2026-10-30,kalshi,Legacy Market,0.4,200\n")

PM_JSON = json.dumps([
    {"title": "New Event A", "volume": 10,
     "markets": [{"outcomePrices": "[0.6, 0.4]"}]},
    {"title": "New Event B", "volume": 20,
     "markets": [{"outcomePrices": "[0.7, 0.3]"}]},
])
KA_JSON = json.dumps({"markets": [
    {"title": "New Market A", "yes_ask": 0.55, "volume": 30}]})


def _fake_fetch(url, timeout=60, binary=False):
    if "polymarket" in url:
        return PM_JSON
    if "kalshi" in url:
        return KA_JSON
    raise RuntimeError("curl exit 22 for " + url)


def test_belief_merge_survives_legacy_rows_without_key(
        tmp_path, monkeypatch):
    series = tmp_path / "series"
    series.mkdir()
    (series / "polymarket_daily.csv").write_text(LEGACY_PM)
    (series / "kalshi_daily.csv").write_text(LEGACY_KA)
    monkeypatch.setattr(psychology_engine, "SERIES", str(series))
    monkeypatch.setattr(psychology_engine, "PROV",
                        str(tmp_path / "PULL-LOG.md"))
    monkeypatch.setattr(pipeline, "TODAY", "2026-11-09")
    monkeypatch.setattr(pipeline, "fetch", _fake_fetch)

    out = pipeline.collect_belief()
    assert out["polymarket"] == 2, out
    assert out["kalshi"] == 1, out

    pm = psychology_engine.read_series("polymarket_daily.csv")
    assert len(pm) == 3, pm
    assert all(r.get("key") for r in pm), pm
    legacy = [r for r in pm if r["event"] == "Legacy Event"]
    assert legacy and legacy[0]["key"] == "2026-10-30|Legacy Event"

    ka = psychology_engine.read_series("kalshi_daily.csv")
    assert len(ka) == 2, ka
    assert all(r.get("key") for r in ka), ka
