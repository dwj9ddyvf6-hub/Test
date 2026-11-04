"""Regression blocker for WALL-LIFETIME-SESSION-DATES-20261104.

Wall Lifetime re-checks every map grade against the imported
grading-date rule. It built the rule's session list as grade
sessions union card publish dates, which put Saturday 2026-10-31
(a post-close publish date) into the list as if it were a trading
session. The rule's same-date branch then mapped that morning's
three cards (SPY, QQQ, IWM, published 2026-10-31T06:07Z) to
2026-10-31, while the morgue grader, which passes each symbol's
true bar dates, graded them against Monday 2026-11-02. The
re-check refused every run. Session dates now come from the
panel's SPY bars, the same true-session source the grader uses.

On the pre-cure code these tests fail: session_dates_from does not
exist (ImportError), which is the fail direction.
"""
import importlib.util
import os
import sys

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
MORGUE = os.path.expanduser("~/workspace/morgue")
sys.path.insert(0, MORGUE)
from scorecards import map_grading_date  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "refresh_walllifetime", os.path.join(SITE, "refresh_walllifetime.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

PANEL = {"SPY": [["2026-10-29"], ["2026-10-30"], ["2026-11-02"],
                 ["2026-11-03"]]}


def test_session_dates_are_true_sessions_only():
    assert mod.session_dates_from(PANEL) == [
        "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03"]


def test_saturday_card_grades_against_monday():
    dates = mod.session_dates_from(PANEL)
    assert map_grading_date("2026-10-31T06:07:55.999806+00:00",
                            dates) == "2026-11-02"


def test_weekday_morning_card_still_grades_same_day():
    dates = mod.session_dates_from(PANEL)
    assert map_grading_date("2026-11-03T13:51:16+00:00",
                            dates) == "2026-11-03"


def test_evening_card_grades_next_session():
    dates = mod.session_dates_from(PANEL)
    assert map_grading_date("2026-10-30T21:58:11+00:00",
                            dates) == "2026-11-02"
