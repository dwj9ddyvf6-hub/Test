"""Regression blockers for EARNINGS-RECORD-RETENTION-20261105
(loop row E-2).

fetch_earnings_calendar.py rebuilt its record from scratch on
every run over a forward-only window starting that day, so a
name's report date fell out of the record the first rebuild
after it reported (KDP reported 2026-11-03; the 2026-11-04
rebuild, window_start 2026-11-04, carried it null). The record
is the desk's dated memory of who reported when: its consumer
publishes past dates as past and builds realised moves from
them, and the trading-path blockers pin a just-reported name's
date on it.

The cure has two halves, both at the source:
- a trailing re-check: each rebuild also reads the last
  TRAILING_DAYS days of the same public calendar, so a name
  that reported inside that span is dated from the primary
  record itself at every rebuild (and a date lost before this
  cure existed is re-derived, never hand-restored);
- a retention merge: a dated entry on the previous record
  fills a fresh null when it stands inside the record's own
  trailing horizon (window_days behind the new window_start),
  so once dated, a report date stays readable across rebuilds
  for the horizon the record itself states. A fresh date
  always wins; a prior date ahead of the new window or older
  than the horizon is not resurrected.

Fail direction on the pre-cure code: merge_retained does not
exist and a seeded prior record is ignored by the rebuild, so
every test below fails.
"""
import importlib.util
import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.expanduser("~/workspace/terminal-lineup/site")

spec = importlib.util.spec_from_file_location(
    "fetch_earnings_calendar",
    os.path.join(SITE, "fetch_earnings_calendar.py"))
fec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fec)

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TODAY_ISO = TODAY.isoformat()


def test_retention_fills_null_inside_horizon():
    fresh = {"KDP": None, "CVX": "2026-12-01"}
    prior = {"KDP": YESTERDAY, "CVX": "2026-11-20"}
    merged, n = fec.merge_retained(fresh, prior, TODAY_ISO, 60)
    assert merged["KDP"] == YESTERDAY
    assert merged["CVX"] == "2026-12-01"  # the fresh date wins
    assert n == 1


def test_retention_respects_the_records_own_horizon():
    old = (TODAY - timedelta(days=61)).isoformat()
    fresh = {"KDP": None}
    merged, n = fec.merge_retained(fresh, {"KDP": old}, TODAY_ISO, 60)
    assert merged["KDP"] is None
    assert n == 0


def test_retention_never_imports_forward_or_foreign_dates():
    future = (TODAY + timedelta(days=10)).isoformat()
    fresh = {"KDP": None}
    merged, n = fec.merge_retained(
        fresh, {"KDP": future, "ZZZZ": YESTERDAY}, TODAY_ISO, 60)
    assert merged["KDP"] is None
    assert "ZZZZ" not in merged
    assert n == 0


def test_retention_without_prior_record_is_identity():
    fresh = {"KDP": None, "CVX": "2026-12-01"}
    merged, n = fec.merge_retained(fresh, None, TODAY_ISO, 60)
    assert merged == fresh
    assert n == 0


def test_rebuild_dates_just_reported_name_from_trailing_day(tmp_path):
    out = tmp_path / "record.json"
    prior = {"updated_ts": "2026-01-01T00:00:00Z",
             "entries": {"KDP": None, "CVX": None}}
    out.write_text(json.dumps(prior), encoding="utf-8")

    def fake_fetch(day_iso):
        if day_iso == YESTERDAY:
            return {"data": {"rows": [{"symbol": "KDP"}]}}
        return {"data": {"rows": []}}

    fec.fetch_day = fake_fetch
    fec.universe_symbols = lambda: ["CVX", "KDP"]
    fec.OUT_PATH = str(out)
    assert fec.main([]) == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["entries"]["KDP"] == YESTERDAY
    assert record["entries"]["CVX"] is None
    assert record["names_trailing"] >= 1
