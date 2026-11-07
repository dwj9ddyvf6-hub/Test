"""Regression blocker for ABSTENTION-SESSION-PIN-20261107.

The abstention-signal guard pinned the Board's and Second
Opinion's freshest-day sessions to a hand-censused date constant
("2026-11-03"). Both pages advance by design, so the guard failed
closed on every run after the census day while the underlying
record stayed healthy (Board at 2026-11-06, counts and character
unchanged), four consecutive full refresh runs.

The cure computes the bindings: the Board's session must equal
the freshest session on the SPY panel the same record trusts;
Second Opinion's session must be a panel session at or after the
census floor. These tests pin the new semantics and the removal
of the date pins. Set LEG_MODULE_DIR to a directory holding a
pre-cure copy of the refresher to watch them fail.
"""
import importlib.util
import os

import pytest

MODULE_DIR = os.environ.get(
    "LEG_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(MODULE_DIR, "refresh_abstentionsignal.py")

spec = importlib.util.spec_from_file_location("refresh_abstentionsignal", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SESSIONS = ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05",
            "2026-11-06"]


def test_board_session_must_equal_panel_freshest():
    # The healthy live case that failed for four straight runs:
    # the Board advanced to the panel's freshest day.
    assert mod.board_session_ok("2026-11-06", SESSIONS) is True


def test_board_session_behind_panel_fails():
    assert mod.board_session_ok("2026-11-03", SESSIONS) is False
    assert mod.board_session_ok("2026-11-05", SESSIONS) is False


def test_board_session_with_no_panel_fails_closed():
    assert mod.board_session_ok("2026-11-06", []) is False


def test_sop_session_membership_and_floor():
    assert mod.sop_session_ok("2026-11-04", SESSIONS) is True
    assert mod.sop_session_ok("2026-11-03", SESSIONS) is True
    # A real session below the inspected census floor is a
    # regression of the record, not accrual.
    assert mod.sop_session_ok("2026-10-30",
                              ["2026-10-30"] + SESSIONS) is False
    # A date that is not a panel session at all cannot pass.
    assert mod.sop_session_ok("2026-11-07", SESSIONS) is False


def test_ib_history_is_prefix_verification_not_an_exact_list():
    carried = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
               "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04",
               "2026-11-05"]
    # Sessions accrued after the census are the record working.
    assert mod.ib_history_ok(carried) is True
    # Losing an inspected session is a real disagreement.
    assert mod.ib_history_ok([s for s in carried
                              if s != "2026-10-29"]) is False


def test_ib_live_counters_are_floors_not_pins():
    assert mod.ib_live_ok({"interaction_fires": 2,
                           "forecasts_recorded": 23}) is True
    assert mod.ib_live_ok({"interaction_fires": 1,
                           "forecasts_recorded": 16}) is True
    assert mod.ib_live_ok({"interaction_fires": 0,
                           "forecasts_recorded": 23}) is False
    assert mod.ib_live_ok({"interaction_fires": 2,
                           "forecasts_recorded": 9}) is False


def test_gradeable_excludes_voided_graded_and_absent_rows():
    # ABSTENTION-GRADE-VOIDED-20261107: the grading loop tried to
    # grade voided duplicate re-issues; the ledger refuses those
    # grades by design and the leg died with LedgerError.
    live = {"type": "forecast", "engine_id": mod.ENGINE_ID,
            "row_id": "a", "absence_state": None}
    assert mod.gradeable(live, set(), set()) is True
    assert mod.gradeable(live, set(), {"a"}) is False
    assert mod.gradeable(live, {"a"}, set()) is False
    assert mod.gradeable({**live, "row_id": "b",
                          "absence_state": "absent"},
                         set(), set()) is False
    assert mod.gradeable({**live, "row_id": "c", "type": "grade"},
                         set(), set()) is False


def test_dead_grading_guard_is_gone():
    # ABSTENTION-GRADE-GUARD-20261107: the grading loop's leftover
    # thr/fwd guard (names that exist only inside outcome_days)
    # crashed the leg with NameError on the first matured row.
    # Exactly one occurrence of the guard line may remain: the
    # legitimate one inside outcome_days, where thr/fwd are real.
    with open(PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert src.count("if thr is None or fwd is None:") == 1


def test_date_pins_are_gone_from_the_source():
    with open(PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert 'board.get("session") != "2026-11-03"' not in src
    assert 'sop.get("session") != "2026-11-03"' not in src
    assert 'ib_today.get("session") != "2026-11-03"' not in src
    assert 'ib["live"]["forecasts_recorded"] != 16' not in src
    assert "board_session_ok" in src and "sop_session_ok" in src
    assert "ib_history_ok" in src and "ib_live_ok" in src


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
