"""Regression blockers for the terminal total audit engines-b
cure pass, second round (2026-10-31).

Covered cures:
- FAMILY-CARD-SESSION-20261031: the Family Fracture positioning
  card agreement is session based. A card built on a later
  calendar day for the session it represents passes when its
  readings match that session's permanent log run; a card whose
  readings match no run, or whose session predates the freshest
  tape aligned run, still fails closed.
- SPONSORED-WAIT-STATE-20261031: sponsored-reset renders its
  pre-fire wait text only while no cohort has formed; once a
  cohort forms the field names the formed cohort, so the wait
  text and the live counts never claim opposite states.
- ORACLE-COUNT-BASIS-20261031: engine_19's calibration
  attestation and its page live record count on one basis, the
  engine's own weekly window forecasts; the Aperture proof-gate
  provisional rows hosted under engine_19 are counted in the
  proof_gate block. The publisher (refresh_attestations) and the
  independent verifier (verify_grade_rows) declare the same
  exclusion.
- GAP-REGISTER-WINDOW-20261031: gap-destiny's settled count
  register binds exactly on its registered window (panel
  sessions through 2026-10-29); sessions after the window are
  new settled history, so a panel advance no longer fails the
  refresher, and the published page carries the freshest
  completed session.
- REFRESH-PROOF-LOG-20261031 (asserted here at the runner
  contract level): every refresh_engines.py run files its own
  proof log under a dated header naming the exit code.
- ORACLE-REGISTER-FLOORS-20261031: the In-Regime Oracle census
  binds the Horizon Grades and Record counts as registered
  floors with internal consistency (qualified a subset of
  graded, graded monotone in the horizon, the Record graded
  total at least the 1-day horizon graded total), never as
  exact equalities. A republication with grown graded counts
  passes; a count moving backward, a qualified count exceeding
  its graded count, a broken monotone order, or a Record total
  below what it contains still fails closed.
"""
import importlib.util
import json
import os
import sys

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
ROOT = os.path.dirname(SITE)
sys.path.insert(0, SITE)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _page(slug):
    with open(os.path.join(SITE, slug, "data.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _ff_runs():
    return {
        "2026-10-30": {
            "SPY": ("t", {"spot": 1, "zero_gamma": 2,
                          "net_gex_usd_per_1pct": 3}),
            "QQQ": ("t", {"spot": 4, "zero_gamma": 5,
                          "net_gex_usd_per_1pct": 6})},
        "2026-10-31": {
            "SPY": ("t", {"spot": 7, "zero_gamma": 8,
                          "net_gex_usd_per_1pct": 9}),
            "QQQ": ("t", {"spot": 10, "zero_gamma": 11,
                          "net_gex_usd_per_1pct": 12})}}


def _ff_card(spot_spy=7, built="2026-10-31T06:07:55Z"):
    return {"built_utc": built, "cards": [
        {"underlying": "SPY", "spot": spot_spy, "zero_gamma": 8,
         "net_gex_usd_per_1pct": 9},
        {"underlying": "QQQ", "spot": 10, "zero_gamma": 11,
         "net_gex_usd_per_1pct": 12}]}


def test_family_card_rebuild_after_tape_day_passes():
    ff = _load("ff_cure", os.path.join(SITE,
                                       "refresh_familyfracture.py"))
    # The audit replay: tape freshest day 2026-10-30, positioning
    # card rebuilt 2026-10-31 for its own session. The old build
    # date equality check failed this; the session check passes.
    assert ff.positioning_card_session(
        _ff_card(), _ff_runs(), ["SPY", "QQQ"]) == "2026-10-31"


def test_family_card_mismatched_readings_rejected():
    ff = _load("ff_cure2", os.path.join(SITE,
                                        "refresh_familyfracture.py"))
    assert ff.positioning_card_session(
        _ff_card(spot_spy=999), _ff_runs(),
        ["SPY", "QQQ"]) is None


def test_family_card_stale_session_still_fails_closed():
    src = _read(os.path.join(SITE, "refresh_familyfracture.py"))
    # The build floors the card session at the freshest tape
    # aligned positioning run, and the old date equality pin is
    # gone.
    assert "card_day < map_day_fresh" in src
    assert 'map_card["built_utc"][:10] != map_day_fresh' not in src


def test_family_fracture_page_reproduced():
    data = _page("family-fracture")
    assert data["decision_date"] == "2026-11-02"


def test_sponsored_wait_text_never_contradicts_counts():
    data = _page("sponsored-reset")
    live = data["live"]
    wait = live["wait"]
    if live["cohorts_formed"] == 0:
        assert wait.startswith("No group has started yet")
    else:
        assert "No group has started yet" not in wait
        # The formed cohort's session is named in the text.
        assert live["freshest_session"] in wait


def test_sponsored_wait_is_computed_not_a_template():
    src = _read(os.path.join(SITE, "refresh_sponsoredreset.py"))
    assert '"wait": wait_text' in src
    assert "formed_cohorts" in src


def test_oracle_one_counting_basis_on_page():
    data = _page("in-regime-oracle")
    att = data["calibration_attestation"]["attestation"]
    live = data["live_record"]
    assert att["forecasts_recorded"] == live["forecasts_recorded"]
    assert att["graded_forecasts"] == live["windows_graded"]
    assert "counting_basis" in att
    assert "counting_basis" in live
    # The hosted proof-gate rows are counted exactly once, in
    # the proof_gate block.
    assert data["proof_gate"]["ledger_rows_total"] > 0


def test_oracle_exclusion_declared_by_publisher_and_verifier():
    pub = _read(os.path.join(ROOT, "forecast",
                             "refresh_attestations.py"))
    ver = _read(os.path.join(ROOT, "forecast",
                             "verify_grade_rows.py"))
    for src in (pub, ver):
        assert "FOREIGN_OUTCOME_KINDS" in src
        assert "provisional_proof_forward_check" in src
        assert "engine_19" in src


def test_gap_register_binds_on_registered_window():
    src = _read(os.path.join(SITE, "refresh_gapdestiny.py"))
    assert 'EXPECT_THROUGH = "2026-10-29"' in src
    assert "fear_days_registered" in src
    assert "reg_band_n" in src
    # The whole panel exact pins that failed on every advance
    # are gone.
    assert 'if fear_days != EXPECT["fear_days"]' not in src


def test_gap_page_carries_freshest_completed_session():
    from completed_session import freshest_completed_session
    data = _page("gap-destiny")
    assert data["as_of_session"] == freshest_completed_session()


def _hz(days, graded, qualified):
    return {"days": days, "graded_count": graded,
            "qualified": {"graded_count": qualified}}


def _oracle_pair(g1=110, q1=63, g5=22, q5=12, g21=0, q21=0,
                 record_graded=125):
    horizon = {"horizons": [_hz(1, g1, q1), _hz(5, g5, q5),
                            _hz(21, g21, q21)]}
    record = {"totals": {"calls_graded_so_far": record_graded}}
    return horizon, record


def _oracle_check(horizon, record):
    mod = _load("oracle_register",
                os.path.join(SITE, "refresh_inregimeoracle.py"))
    return mod.check_horizon_record_register(horizon, record)


def _assert_fails_closed(horizon, record):
    try:
        _oracle_check(horizon, record)
    except SystemExit as exc:
        assert "FAILED CLOSED" in str(exc)
        return
    raise AssertionError("register check passed a broken pair")


def test_oracle_register_accepts_live_and_grown_counts():
    # The live published pair (the 2026-10-31 republication state
    # that the exact pins refused) passes.
    horizon = _page("horizon-grades")
    record = _page("record")
    assert _oracle_check(horizon, record) is True
    # A further republication with grown graded counts at every
    # horizon and a grown Record total still passes: growth is
    # the sources advancing on their own cadence, not drift.
    horizon, record = _oracle_pair(g1=160, q1=90, g5=60, q5=30,
                                   g21=25, q21=10, record_graded=200)
    assert _oracle_check(horizon, record) is True


def test_oracle_register_fails_closed_on_backward_counts():
    # 1-day graded moving backward below the registered floor.
    horizon, record = _oracle_pair(g1=87)
    _assert_fails_closed(horizon, record)
    # 1-day qualified moving backward below its floor.
    horizon, record = _oracle_pair(q1=46)
    _assert_fails_closed(horizon, record)
    # The Record graded total moving backward below its floor.
    horizon, record = _oracle_pair(record_graded=99)
    _assert_fails_closed(horizon, record)


def test_oracle_register_fails_closed_on_inconsistent_counts():
    # A qualified count exceeding its own graded count.
    horizon, record = _oracle_pair(q1=111)
    _assert_fails_closed(horizon, record)
    # Graded counts not monotone in the horizon.
    horizon, record = _oracle_pair(g5=111)
    _assert_fails_closed(horizon, record)
    # The Record total below the 1-day graded total it contains.
    horizon, record = _oracle_pair(record_graded=105)
    _assert_fails_closed(horizon, record)


def test_oracle_register_exact_pins_are_gone():
    src = _read(os.path.join(SITE, "refresh_inregimeoracle.py"))
    assert "check_horizon_record_register" in src
    assert 'hz[1]["graded_count"] != 88' not in src
    assert 'calls_graded_so_far"] != 100' not in src


def test_runner_files_proof_log_with_exit_header():
    src = _read(os.path.join(SITE, "refresh_engines.py"))
    assert "def write_proof_log" in src
    assert "exit {exit_code}" in src
    assert "refresh_proof.log" in src
