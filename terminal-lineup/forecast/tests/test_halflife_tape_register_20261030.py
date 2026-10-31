"""Regression blocker for the 2026-10-30 Half-Life Clock cure (G17).

Fail direction: on the pre-cure refresh_halflifeclock.py the tape
register required Flow Tape's old ungraded note ("have not been
graded yet") and its published tape row claimed no grading existed,
so the refresh failed closed on every coherent cycle once tape
grading landed (live error: "tape record moved from 75 ungraded
alerts"). The cure re-registers the tape leg against the graded
state counted from flow-tape/grades.json (216 of 300 graded).
"""
import os

SRC = os.path.expanduser(
    "~/workspace/terminal-lineup/site/refresh_halflifeclock.py")


def _src():
    with open(SRC, encoding="utf-8") as fh:
        return fh.read()


def test_old_ungraded_register_is_gone():
    src = _src()
    assert '"have not been graded yet" not in tape["grading_note"]' \
        not in src
    assert 'fail("tape record moved from 75 ungraded alerts")' \
        not in src


def test_graded_register_is_pinned():
    src = _src()
    assert "216 of 300 logged alerts graded" in src


def test_tape_row_no_longer_claims_no_grading():
    src = _src()
    assert "Missing: any grading at all" not in src
    assert "nothing has ever " not in src
