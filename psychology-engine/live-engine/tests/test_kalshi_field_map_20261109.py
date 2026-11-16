#!/usr/bin/env python3
"""Regression blocker for KALSHI-FIELD-MAP-20261109.

The Kalshi branch of collect_belief built its snapshot rows
from m.get("yes_ask") and m.get("volume"). The Kalshi trade
API's current payload (saved raw responses under
live/raw/collect_belief/, probed 2026-11-09/10) carries no
such keys: prices are last_price_dollars / yes_ask_dollars /
yes_bid_dollars and volume is volume_fp. Every Kalshi
snapshot therefore stored empty probability and volume
alongside the events. The fetches were fine; the mapping
was written against a retired field shape.

Cure pinned here: probability comes from
last_price_dollars (the last traded price, the probability
analogue the Polymarket branch stores), falling back to
yes_ask_dollars and then the legacy keys; volume comes
from volume_fp, falling back to the legacy key.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import psychology_engine  # noqa: E402
import pipeline  # noqa: E402

MARKET = {
    "title": "Will the Federal Reserve Cut rates by 25bps at "
             "their December 2027 meeting?",
    "last_price_dollars": "0.0300",
    "yes_ask_dollars": "0.0400",
    "yes_bid_dollars": "0.0200",
    "volume_fp": "2825.65",
}


def _fake_fetch(url, timeout=60, binary=False):
    if "kalshi" in url:
        return json.dumps({"markets": [MARKET]})
    raise RuntimeError("no route in this fixture for " + url)


def test_kalshi_snapshot_maps_the_current_payload_fields(
        tmp_path, monkeypatch):
    monkeypatch.setattr(psychology_engine, "SERIES",
                        str(tmp_path / "series"))
    monkeypatch.setattr(psychology_engine, "PROV",
                        str(tmp_path / "PULL-LOG.md"))
    monkeypatch.setattr(psychology_engine, "RAW",
                        str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "TODAY", "2026-11-09")
    monkeypatch.setattr(pipeline, "fetch", _fake_fetch)

    pipeline.collect_belief()
    rows = psychology_engine.read_series("kalshi_daily.csv")
    assert len(rows) == 1, rows
    assert rows[0]["probability"] == "0.0300", rows
    assert rows[0]["volume"] == "2825.65", rows
