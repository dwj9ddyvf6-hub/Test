#!/usr/bin/env python3
"""Tests for api_spend.py (InfinityBlade proof for the nightly spend line).

(a) A synthetic usage log with known token counts produces the exact
    expected line figures.
(b) Re-recording the same day replaces the ledger row, never duplicates it.

Run: python3 ~/workspace/tools/test_api_spend.py
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "api_spend.py")
sys.path.insert(0, HERE)
import api_spend  # noqa: E402

# The host clock is UTC; "today" for this ledger is the America/New_York
# local day, the same day api_spend buckets by.
DAY = datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def _usage(inp, cached=0, cw=0):
    return {"input_tokens": inp,
            "input_tokens_details": {"cached_tokens": cached,
                                     "cache_write_tokens": cw},
            "output_tokens": 0, "total_tokens": inp}


def _make_root(tmp):
    pilot_dir = os.path.join(
        tmp, "research_notes", "decisions-trial-20261110")
    os.makedirs(pilot_dir)
    rows = [{"sym": "AAA", "usage": _usage(600_000, cached=100_000, cw=50_000)},
            {"sym": "BBB", "usage": _usage(400_000)}]
    with open(os.path.join(pilot_dir, "pilot_results.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    typed_dir = os.path.join(tmp, "midna-book", "typed-layer")
    os.makedirs(typed_dir)
    # Bank-v2 audit rows: one priced by the schedule from its usage
    # (100,000 plain input = $0.01), one carrying a recorded cost that
    # must REPLACE its schedule price (usage alone would be $0.02).
    typed_rows = [
        {"bank_id": "study-bank-v2", "usage": _usage(100_000)},
        {"bank_id": "study-bank-v2", "usage": _usage(200_000),
         "cost_usd": 0.005},
        {"bank_id": "study-bank-v1-pilot", "usage": _usage(999_999)},
    ]
    with open(os.path.join(typed_dir, "ledger.jsonl"), "w") as fh:
        for r in typed_rows:
            fh.write(json.dumps(r) + "\n")
    # Stamp every synthetic file at local noon today: mtime day-bucketing
    # must land on DAY in the local timezone regardless of when the test
    # runs (a bare time.time() stamp near local midnight would bucket
    # into the neighbouring day on the other side of the date line).
    noon = datetime.now(ZoneInfo("America/New_York")).replace(
        hour=12, minute=0, second=0, microsecond=0).timestamp()
    for base, _, files in os.walk(tmp):
        for f in files:
            os.utime(os.path.join(base, f), (noon, noon))


def test_line_figures():
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp)
        ledger = os.path.join(tmp, "ledger.jsonl")
        row = api_spend.build_row(tmp, DAY)
        assert row["requests"] == 4, row
        assert row["input_tokens"] == 1_300_000, row
        assert row["cached_tokens"] == 100_000, row
        # Pilot: (600k-100k cached-50k write) plain at $0.10 = $0.045,
        # 100k cached at $0.01 = $0.001, 50k cache write at $0.125 =
        # $0.00625, plus 400k plain = $0.04 -> $0.09225.
        # Typed bank v2: $0.01 computed + $0.005 recorded (replacing
        # the $0.02 its usage alone would price at) -> $0.015.
        # Total $0.10725, printed at cents as $0.11; the v1-pilot row
        # in the typed ledger must not be counted at all.
        assert row["est_cost_usd"] == 0.10725, row
        rows = api_spend.upsert_row(ledger, row)
        line = api_spend.format_line(row, rows)
        expected = ("API spend {}: 4 requests, 1,300,000 input tokens "
                    "(100,000 cached), est $0.11 today; month to date "
                    "est $0.11; ledger rows 1.").format(DAY)
        assert line == expected, line
        out = subprocess.run(
            [sys.executable, SCRIPT, "--day", DAY],
            env={**os.environ, "API_SPEND_ROOT": tmp,
                 "API_SPEND_LEDGER": ledger},
            capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        assert out.stdout.strip() == expected, out.stdout


def test_rerecord_no_duplicate():
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp)
        ledger = os.path.join(tmp, "ledger.jsonl")
        api_spend.upsert_row(ledger, api_spend.build_row(tmp, DAY))
        api_spend.upsert_row(ledger, api_spend.build_row(tmp, DAY))
        with open(ledger) as fh:
            lines = [l for l in fh if l.strip()]
        assert len(lines) == 1, lines
        other = dict(api_spend.build_row(tmp, DAY), date="2026-01-01")
        api_spend.upsert_row(ledger, other)
        with open(ledger) as fh:
            lines = [l for l in fh if l.strip()]
        assert len(lines) == 2, lines
        rows = api_spend.read_ledger(ledger)
        assert set(rows) == {DAY, "2026-01-01"}, rows


if __name__ == "__main__":
    test_line_figures()
    print("PASS test_line_figures")
    test_rerecord_no_duplicate()
    print("PASS test_rerecord_no_duplicate")
