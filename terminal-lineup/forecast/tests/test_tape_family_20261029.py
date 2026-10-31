"""Regression blockers for the tape family cure (G6/G7, 2026-10-29).

Fail direction: every module/function asserted here was absent
before the cure (tape_family_run, collect_pername_tape,
grade_tape_alerts did not exist), and the two source assertions
fail on the pre-cure refreshers (the feed-session equality that
refused every coherent cycle, and Flow Engine's colliding picks).
"""
import importlib.util
import json
import os
import sys

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")


def load_module(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_orchestrator_stamp_current_and_stale(tmp_path):
    fam = load_module("tape_family_run")
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"session": "2026-10-29"}))
    doc = json.loads(p.read_text())
    assert fam.stamp(str(p), doc, "2026-10-29", "2026-10-29") == "current"
    doc = json.loads(p.read_text())
    assert doc["tape_freshness"]["state"] == "current"
    assert fam.stamp(str(p), doc, "2026-10-29", "2026-10-27") == "stale"
    doc = json.loads(p.read_text())
    assert doc["tape_freshness"]["consumer_session"] == "2026-10-27"
    # every consumer is in the dependency-ordered run list
    scripts = [c[0] for c in fam.CONSUMERS]
    assert scripts[0] == "refresh_flow_tape.py"
    assert scripts.index("refresh_flowboard.py") < \
        scripts.index("refresh_agentdebate.py")
    assert len(scripts) == 9


def test_feed_session_equality_removed_from_tape_consumers():
    for name in ("refresh_activity", "refresh_premiummeter"):
        src = open(os.path.join(SITE, name + ".py")).read()
        assert 'feed.get("as_of_session") != card_session' not in src
        assert "generation order" in src  # the replacement binding


def test_flowengine_picks_are_distinct_by_construction():
    src = open(os.path.join(SITE, "refresh_flowengine.py")).read()
    assert "def pick(key, exclude=())" in src
    assert "pick(key, exclude=seen)" in src


def test_collector_universe_is_bounded_and_direction_unjudged():
    col = load_module("collect_pername_tape")
    uni = col.bounded_universe()
    assert set(["SPY", "QQQ", "IWM"]).issubset(set(uni))
    assert 50 <= len(uni) <= 60  # tracked 50 + ETFs, bounded
    assert col.DIRECTION_BASIS == "unjudged_no_print_time_quote"
    store = os.path.expanduser(
        "~/workspace/morgue/state/morgue/pername_tape/2026-10-29.json")
    if not os.path.exists(store):
        import pytest
        pytest.skip("per-name store for 2026-10-29 not present")
    doc = json.load(open(store))
    assert doc["direction_basis"] == "unjudged_no_print_time_quote"
    for name in doc["names"].values():
        assert name["net_premium"] is None
        for a in name["alerts"]:
            assert a["direction"] == "unjudged"
            assert a["side"] == "unknown"


def test_flow_tape_self_stamps_freshness():
    # Residual drift found 2026-10-30: a standalone
    # refresh_flow_tape.py run overwrote the orchestrator's stamp,
    # leaving flow-tape/data.json with tape_freshness absent while
    # every consumer carried one. The source itself must self-stamp.
    src = open(os.path.join(SITE, "refresh_flow_tape.py")).read()
    assert '"tape_freshness"' in src
    assert '"tape_session": session' in src
    doc = json.load(open(os.path.join(SITE, "flow-tape", "data.json")))
    assert doc["tape_freshness"]["state"] == "current"
    assert doc["tape_freshness"]["tape_session"] == doc["session"]
    assert doc["tape_freshness"]["consumer_session"] == doc["session"]


def test_flowengine_grading_check_matches_grading_record():
    # Found live 2026-10-30: Flow Engine demanded the tape's
    # not-yet-graded wording forever, so once grading landed its
    # refresh refused every session. The check must verify the
    # note against the grading record's true counts instead.
    src = open(os.path.join(SITE, "refresh_flowengine.py")).read()
    assert '"not been graded yet" not in grading_note' not in src
    fe = load_module("refresh_flowengine")
    graded, total, hits = fe.grading_totals()
    assert graded > 0  # grading has landed on the final record
    note = json.load(open(os.path.join(
        SITE, "flow-tape", "data.json")))["grading_note"]
    assert fe.grading_note_matches(note)
    assert not fe.grading_note_matches(
        "they have not been graded yet")
    assert not fe.grading_note_matches(
        f"{graded + 1} of {total} logged alerts graded so far, "
        f"{hits} of them in the direction the alert pointed.")


def test_grade_move_rule():
    g = load_module("grade_tape_alerts")
    assert g.grade_move("bullish", 0.01) is True
    assert g.grade_move("bullish", -0.01) is False
    assert g.grade_move("bearish", -0.01) is True
    assert g.grade_move("bearish", 0.01) is False
    assert g.grade_move("neutral", 0.01) is None
    grades_path = os.path.join(SITE, "flow-tape", "grades.json")
    if os.path.exists(grades_path):
        doc = json.load(open(grades_path))
        assert doc["totals"]["graded"] > 0
        assert doc["sessions"]["2026-10-29"]["ungraded_by_reason"] == {
            "next_session_close_not_yet_available": 75}
