"""Regression blockers for the terminal total audit round 1
pipelines cures (2026-10-31).

Covered cures:
- CHAIN-SPOT-ANCHOR-20261031: the chain collector's spot freshness
  gate anchors at the spot fetch moment, not the run start, and
  terminal_common.quote_freshness carries a named clock-skew
  tolerance for negative ages. Replays the 2026-10-30 manifest
  cases: a quote stamped 5 seconds after the run start must pass;
  a quote 11 minutes old must still fail.
- IV-LEDGER-LOSS-20261031: a failed chain capture records
  iv_ledger_rows_added 0 with the error name on its manifest line,
  so lost modelled IV accrual is a named event in one file.
- PANEL-THROUGH-EXPLICIT-20261031: refresh_engines.py passes an
  explicit --through (the freshest completed session) to both
  panel advance lanes, and after the evening chains have run
  neither panel's last SPY bar may trail that session.
- DAILY-STORES-SYNC-20261031: the Short Volume Ledger and State
  Analogue pages must agree with their stores once the daily
  stores lane has had its window (19:00 ET on a session day, any
  time on a non-session day). An out-of-band store advance that
  no consumer page reflects is a named failure here, not a
  silent one-advance lag until the next weekday run.
"""
import importlib.util
import json
import os
import sys
import time as time_mod
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
sys.path.insert(0, SITE)

import terminal_common as tc  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "collect_chains", os.path.join(SITE, "collect_chains.py"))
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

ET = ZoneInfo("America/New_York")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---- CHAIN-SPOT-ANCHOR: the 2026-10-30 manifest replay --------------

RUN_START = datetime(2026, 10, 30, 13, 57, 31, tzinfo=timezone.utc)


def test_quote_five_seconds_after_run_start_is_fresh():
    # Exact manifest case: run stamped 13:57:31Z, quote 13:57:36Z.
    out = tc.quote_freshness("2026-10-30T13:57:36+00:00", now=RUN_START)
    assert out["state"] == "fresh"
    assert out["age_seconds"] == -5.0


def test_quote_eleven_minutes_old_still_fails():
    old = datetime(2026, 10, 30, 13, 46, 31, tzinfo=timezone.utc)
    out = tc.quote_freshness(old.isoformat(), now=RUN_START)
    assert out["state"] == "stale"
    assert out["age_seconds"] == 660.0


def test_skew_tolerance_boundaries():
    at_edge = datetime(2026, 10, 30, 13, 58, 1, tzinfo=timezone.utc)
    assert tc.quote_freshness(at_edge.isoformat(),
                              now=RUN_START)["state"] == "fresh"
    past_edge = datetime(2026, 10, 30, 13, 58, 2, tzinfo=timezone.utc)
    assert tc.quote_freshness(past_edge.isoformat(),
                              now=RUN_START)["state"] == "stale"
    # The old positive boundary is unchanged: 90 fresh, 91 stale.
    q90 = datetime(2026, 10, 30, 13, 56, 1, tzinfo=timezone.utc)
    q91 = datetime(2026, 10, 30, 13, 56, 0, tzinfo=timezone.utc)
    assert tc.quote_freshness(q90.isoformat(),
                              now=RUN_START)["state"] == "fresh"
    assert tc.quote_freshness(q91.isoformat(),
                              now=RUN_START)["state"] == "stale"
    assert tc.quote_freshness(None, now=RUN_START)["state"] == "no_data"


def test_fetch_spot_anchors_at_fetch_moment(monkeypatch):
    # No now argument on the live path: a quote stamped at the
    # fetch moment is fresh even though no run-start time exists,
    # and a genuinely old quote still fails closed.
    now_ts = int(time_mod.time())
    doc = {"chart": {"result": [{"meta": {
        "regularMarketPrice": 100.0, "regularMarketTime": now_ts}}]}}
    monkeypatch.setattr(cc, "curl_json", lambda args, timeout=60: doc)
    _price, _src, _qts, state = cc.fetch_spot("SPY")
    assert state == "fresh"
    doc["chart"]["result"][0]["meta"]["regularMarketTime"] = now_ts - 660
    _price, _src, _qts, state = cc.fetch_spot("SPY")
    assert state == "stale"


def test_collector_main_does_not_pass_run_start_to_fetch_spot():
    src = _read(os.path.join(SITE, "collect_chains.py"))
    assert "fetch_spot(symbol)" in src
    assert "fetch_spot(\n                symbol, now=now_utc)" not in src
    assert "fetch_spot(symbol, now=now_utc)" not in src


# ---- IV-LEDGER-LOSS: failed captures name their zero accrual ---------

def test_manifest_error_line_carries_iv_loss_block():
    line = cc.manifest_line(
        "2026-10-30T13:57:31Z", "2026-10-30T09:57:31-0400", "SPY",
        "error", error="RuntimeError: spot quote stale",
        content={"iv_ledger_rows_added": 0,
                 "iv_ledger_error": "RuntimeError: spot quote stale"})
    assert line["status"] == "error"
    assert line["content"]["iv_ledger_rows_added"] == 0
    assert "RuntimeError" in line["content"]["iv_ledger_error"]


def test_collector_error_path_records_iv_loss():
    src = _read(os.path.join(SITE, "collect_chains.py"))
    exc_at = src.find("except Exception as exc")
    assert exc_at > 0
    block = src[exc_at:exc_at + 1600]
    assert '"iv_ledger_rows_added": 0' in block
    assert "iv_ledger_error" in block


# ---- PANEL-THROUGH-EXPLICIT: runner passes --through -----------------

def test_refresh_engines_passes_explicit_through_to_both_lanes():
    src = _read(os.path.join(SITE, "refresh_engines.py"))
    assert "freshest_completed_session" in src
    assert '"--through", panel_through' in src
    assert 'str(HERE / "advance_deep_panel.py"),\n         *through_args' \
        in src
    assert 'str(HERE / "advance_price_panel.py"),\n              *through_args' \
        in src


def test_panels_not_behind_completed_session_after_evening_chains():
    """Evening freshness blocker: once the evening chains have had
    their window (18:00 ET on a session day, or any time on a
    non-session day), both panels' last SPY bar must equal the
    freshest completed session. Before that window the check skips:
    the panels legitimately still hold the prior session."""
    from completed_session import freshest_completed_session
    target = freshest_completed_session()
    now_et = datetime.now(ET)
    if now_et.date().isoformat() == target \
            and now_et.time() < time(18, 0):
        pytest.skip("evening chains have not run yet today")
    board = json.load(open(os.path.expanduser(
        "~/workspace/morgue/data_cache/board_bt_bars.json"),
        encoding="utf-8"))
    assert board["SPY"][-1][0] == target, (
        f"board panel SPY last {board['SPY'][-1][0]} != {target}")
    sys.path.insert(0, SITE)
    import mmap
    import advance_deep_panel as adp
    with open(os.path.expanduser(
            "~/workspace/morgue/data_cache/deep_bars.json"),
            "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            scan = adp.scan_panel(mm)
        finally:
            mm.close()
    assert scan["SPY"][3] == target, (
        f"deep panel SPY last {scan['SPY'][3]} != {target}")


# ---- DAILY-STORES-SYNC: pages agree with their stores ---------------

def _stores_window_open():
    """True once the daily stores lane (weekdays 18:46 ET) has had
    its window for the freshest completed session. Before 19:00 ET
    on that session day the pages legitimately still hold the
    prior sync; after it, and on any non-session day, a page
    trailing its store is a failure."""
    from completed_session import freshest_completed_session
    target = freshest_completed_session()
    now_et = datetime.now(ET)
    if now_et.date().isoformat() == target \
            and now_et.time() < time(19, 0):
        pytest.skip("daily stores lane has not run yet today")
    return target


def test_short_volume_page_matches_finra_store():
    _stores_window_open()
    store_dir = os.path.expanduser(
        "~/workspace/morgue/state/morgue/shortvol")
    days = sorted(n[:-8] for n in os.listdir(store_dir)
                  if n.endswith(".json.gz"))
    assert days, "FINRA short volume store is empty"
    page = json.load(open(os.path.join(
        SITE, "short-volume", "data.json"), encoding="utf-8"))
    assert page["days_on_record"] == len(days), (
        f"short-volume page {page['days_on_record']} days != "
        f"store {len(days)} days")
    assert page["freshest_day"] == days[-1], (
        f"short-volume page freshest {page['freshest_day']} != "
        f"store {days[-1]}")


def test_state_analogue_page_matches_studies_card():
    _stores_window_open()
    card = json.load(open(os.path.expanduser(
        "~/workspace/morgue/output/studies_card.json"),
        encoding="utf-8"))
    state = card["state_vectors"]
    page = json.load(open(os.path.join(
        SITE, "state-analogue", "data.json"), encoding="utf-8"))
    assert page["counts"]["sessions_recorded"] == \
        state["history_sessions_accrued"], (
            f"state-analogue page "
            f"{page['counts']['sessions_recorded']} sessions != "
            f"card {state['history_sessions_accrued']}")
    assert page["as_of_session"] == state["latest"]["date"], (
        f"state-analogue page session {page['as_of_session']} "
        f"!= card latest {state['latest']['date']}")
