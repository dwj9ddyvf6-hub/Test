"""Regression blockers for the terminal total audit round 1
engines-b cures (2026-10-31).

Covered cures:
- PANEL-THROUGH-20261031: panel advance defaults derive the
  freshest completed session, not yesterday, so a post-close run
  publishes the session that just closed.
- SESSION-PIN-FLOORS-20261031: rolling-source registers in
  living-router and half-life-clock are accrual floors, not
  exact pins that fail every scheduled run after a re-take.
- REFRESH-BUDGET-20261031: the daily refresh job budget covers
  the measured leg durations (asserted on the job definition
  copy the scheduler writes).
- ATTESTATION-REGEN-WIRED-20261031: the runner regenerates
  attestations from the ledger after grading (wired by the
  engines-a cure ATTESTATION-RECOUNT-20261031; asserted here so
  the wiring cannot silently drop out of this sector's runner).
"""
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
ROOT = os.path.dirname(SITE)
sys.path.insert(0, SITE)
ET = ZoneInfo("America/New_York")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_completed_session_post_close_same_day():
    from completed_session import freshest_completed_session as f
    assert f(datetime(2026, 10, 30, 17, 46, tzinfo=ET)) == "2026-10-30"
    assert f(datetime(2026, 11, 2, 17, 46, tzinfo=ET)) == "2026-11-02"


def test_completed_session_pre_close_and_weekend():
    from completed_session import freshest_completed_session as f
    assert f(datetime(2026, 10, 30, 15, 0, tzinfo=ET)) == "2026-10-29"
    assert f(datetime(2026, 10, 31, 1, 37, tzinfo=ET)) == "2026-10-30"
    assert f(datetime(2026, 11, 2, 8, 0, tzinfo=ET)) == "2026-10-30"


def test_completed_session_holiday():
    from completed_session import freshest_completed_session as f
    # Thanksgiving 2026 is a Thursday closure.
    assert f(datetime(2026, 11, 26, 17, 46, tzinfo=ET)) == "2026-11-25"


def test_panel_advance_defaults_use_completed_session():
    for name in ("advance_price_panel.py", "advance_deep_panel.py"):
        src = _read(os.path.join(SITE, name))
        assert "freshest_completed_session" in src, name
        # The old yesterday default must not survive as the
        # through derivation in either lane.
        assert "date()\n                   - timedelta(days=1)" not in src \
            and 'date()\n                   - timedelta(days=1)' not in src, name


def test_living_router_session_pins_are_floors():
    src = _read(os.path.join(SITE, "refresh_livingrouter.py"))
    assert 'tape["session"] != "2026-10-30"' not in src
    assert 'strat["session"] != "2026-10-29"' not in src
    assert 'tape["session"] < "2026-10-30"' in src
    assert 'strat["session"] < "2026-10-29"' in src
    # The finished-search grade-A counts stay exact.
    assert 'ga["grade_a"] != 63' in src


def test_living_router_zero_state_block_present():
    src = _read(os.path.join(SITE, "refresh_livingrouter.py"))
    assert '"zero_forecast_state"' in src
    assert '"first_possible": "2026-11-23"' in src


def test_halflife_registers_are_accrual_floors():
    src = _read(os.path.join(SITE, "refresh_halflifeclock.py"))
    assert 'sessions != ["2026-10-23"' not in src
    assert "sessions[:5] !=" in src
    assert 'graded_count"] < 88' in src
    assert 'tape["session"] != "2026-10-30"' not in src
    assert 'tape["session"] < "2026-10-30"' in src


def test_refresh_job_budget_covers_measured_legs():
    job = os.path.expanduser(
        "~/workspace/cron.d/weekly/"
        "forecast-engine-daily-refresh__weekly@"
        "Mon,Tue,Wed,Thu,Fri-17:46:00.md")
    src = _read(job)
    m = re.search(r"timeout_secs: (\d+)", src)
    assert m, "job carries no timeout"
    # Measured legs alone (proof log) sum past 10000s; the old
    # 3600s budget could never contain one full run.
    assert int(m.group(1)) >= 14400


def test_completion_reset_register_is_exact_per_day_not_a_count():
    src = _read(os.path.join(SITE, "refresh_completionclock.py"))
    assert 'len(reset_days) != 4' not in src
    assert "_REGISTERED_RESET" in src
    for day in ("2026-06-05", "2026-06-10", "2026-07-29",
                "2026-10-16"):
        assert day in src


def test_abstention_reissue_voids_and_valid_basis():
    src = _read(os.path.join(SITE, "refresh_abstentionsignal.py"))
    # Duplicate re-issues of an issued day are voided by
    # correction rows; the session's first issue stands.
    assert "append_correction" in src
    assert "frozen at first issue" in src
    # The ledger count check and the published count bind on
    # the valid basis, never the raw row count.
    assert 'mine.get("forecasts_valid"' in src
    assert '"forecasts_voided"' in src
    # The census pins stand at the re-taken 2026-10-30 session
    # for both rolling publishers.
    assert 'board.get("session") != "2026-10-30"' in src
    assert 'sop.get("session") != "2026-10-30"' in src


def test_runner_regenerates_attestations_after_grading():
    src = _read(os.path.join(SITE, "refresh_engines.py"))
    assert "refresh_attestations" in src
    grading_at = src.find("forecast-grading")
    regen_at = src.find("refresh_attestations")
    assert 0 < grading_at < regen_at
