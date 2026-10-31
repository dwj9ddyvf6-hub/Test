"""Regression blocker for G3 cure stream E (DEEP panel expansion),
2026-10-29.

Pre-cure behaviour, two parts:
(1) The DEEP panel held only the 1,833 board names (base_coverage:
1,773 at or above 813 sessions); the rest of the current listed
universe (14,342 active Alpaca symbols) had no long history on disk.
(2) The first expansion attempt (deep_expansion/backfill_expansion.py)
died on batch 0: one invalid symbol (0029900E0) returned a 400 for
the whole 50-symbol request and the script exited (driver.log:
"batch 0 ERROR ... invalid symbol: 0029900E0", "backfill exited 3",
0 batches stored). The cure's fetcher bisects on invalid-symbol
errors, isolates the bad symbol, and completes the batch.

These tests fail on the pre-cure state and pass on the cured state.
The panel test reads the panel file itself, never a log.
"""
import json
import os
import sys

PANEL = os.path.expanduser("~/workspace/morgue/data_cache/deep_bars.json")
CURE_DIR = os.path.expanduser("~/workspace/morgue/data_cache/deep_cure_e")
MIN_SESSIONS = 813  # PCT_WINDOW + HIGH_WINDOW in refresh_ownnormdepth.py
BASE_NAMES = 1833
BASE_GE_813 = 1773


def test_fetcher_isolates_invalid_symbol_and_completes():
    sys.path.insert(0, CURE_DIR)
    import backfill_active as bf

    def fake_api(method, url, params=None, payload=None):
        syms = params["symbols"].split(",")
        if "BADXXX" in syms:
            raise RuntimeError(
                'Alpaca API error 400: {"message":"invalid symbol: BADXXX"}')
        bars = {s: [{"t": "2020-01-02T05:00:00Z", "o": 10.0, "h": 11.0,
                     "l": 9.0, "c": 10.5, "v": 100}] for s in syms}
        return {"bars": bars, "next_page_token": None}

    orig = bf.api_request
    bf.api_request = fake_api
    try:
        invalid = []
        out = bf.fetch(["AAA", "BADXXX", "ZZZ"], invalid)
    finally:
        bf.api_request = orig
    assert invalid == ["BADXXX"], invalid
    assert sorted(out) == ["AAA", "ZZZ"], sorted(out)
    assert out["AAA"][0] == ["2020-01-02", 10.0, 11.0, 9.0, 10.5, 100]


def test_panel_covers_beyond_board_universe():
    assert os.path.exists(PANEL), "DEEP panel missing: deep_bars.json"
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    assert len(panel) > BASE_NAMES, len(panel)
    ge = sum(1 for rows in panel.values() if len(rows) >= MIN_SESSIONS)
    assert ge > BASE_GE_813, ge
