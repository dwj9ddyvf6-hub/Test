"""Regression blocker for SECOND-OPINION-NULL-DIX-20261104.

On 2026-11-04 the positioning card's FINRA leg went missing
(the postclose FNQC download truncated; see the morgue cure
FINRA-TRUNCATED-READ-RETRY-20261104), so the card carried
dix_ratio/dix_date null. Every sibling cross-check in
refresh_second_opinion.py refuses cleanly by name on bad
input, but the dark-pool comparison computed
round(c["dix_ratio"], 3) on the null and died with a raw
TypeError traceback (the tools refresh failure of record,
2026-11-04 19:00 ET run). The cure is a fail-closed guard in
the lane's own fail() style, placed before the first use of
the card's dix fields: a card with no dark pool reading is
refused by name, never crashed on.

Fail direction on the pre-cure code: the guard text does not
exist in the source, so the presence assertion fails. (The
guard is inline in build(), whose full harness is the whole
terminal feed; per the bug law this blocker is a
source-assertion where a full harness is impractical, and it
also pins the guard's position ahead of the dix use.)
"""
import os

LIVE = os.path.expanduser(
    "~/workspace/terminal-lineup/site/refresh_second_opinion.py")
SRC_PATH = os.environ.get("SECOND_OPINION_SRC", LIVE)

GUARD_MARK = "carries no dark"
DIX_USE = 'round(c["dix_ratio"]'


def _src():
    with open(SRC_PATH, encoding="utf-8") as fh:
        return fh.read()


def test_null_dix_guard_present():
    src = _src()
    assert GUARD_MARK in src, (
        "no null-DIX refusal guard in refresh_second_opinion.py; "
        "a positioning card with a missing FINRA leg crashes "
        "the dark-pool comparison instead of refusing by name")
    assert "its FINRA leg" in src


def test_guard_refuses_through_the_lane_fail_helper():
    src = _src()
    i = src.index(GUARD_MARK)
    window = src[max(0, i - 400):i]
    assert "return fail(" in window, (
        "the null-DIX guard must refuse through the lane's "
        "fail() helper, not raise or print-and-continue")


def test_guard_precedes_the_first_dix_use():
    src = _src()
    assert src.index(GUARD_MARK) < src.index(DIX_USE), (
        "the guard must sit before the first round() over the "
        "card's dix_ratio, or the crash it prevents still fires")
