"""Regression blocker for REPLICATION-CLAIM25-ASOF-20261107.

Claim 25 (golden sweeps) was verified by raw substring needles
pinned to the golden-sweep record's live totals
('"sessions_recorded": 8'). The tape accrues a session every
trading day by design, so the pin broke on schedule after every
hand re-take (2026-10-30, 2026-11-04, 2026-11-05) while the
record itself was never wrong; the needle also under-reported
the staleness, because a per-session entry still matched the
'"golden_prints": 2' needle after the aggregate reached 3.

The cure verifies the claim AS OF its census day (2026-11-05
recount: 8 sessions, freshest 2026-11-04, 2 prints inside):
prefix stability, an as-of recount of prints in the prefix, and
the live totals as floors. These tests pin that semantics
against the real, since-accrued record and against mutations.
Set LEG_MODULE_DIR to a directory holding a pre-cure copy of
the refresher to watch them fail.
"""
import copy
import importlib.util
import json
import os

import pytest

MODULE_DIR = os.environ.get(
    "LEG_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(MODULE_DIR, "refresh_replicationwire.py")
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "golden-sweep-wire", "data.json")

spec = importlib.util.spec_from_file_location("refresh_replicationwire", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def live_data():
    with open(DATA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_live_record_passes_asof_verification():
    # The exact case that failed four straight runs: the tape has
    # accrued past the census (10 sessions, 3 prints on disk).
    data = live_data()
    assert data["counts"]["sessions_recorded"] > 8
    assert mod.golden_claim_asof_ok(data) is True


def test_old_needle_is_absent_from_the_live_record_text():
    # Documents why the substring check failed on a healthy
    # record: the pinned literal no longer exists in the file.
    with open(DATA_PATH, encoding="utf-8") as fh:
        text = fh.read()
    assert '"sessions_recorded": 8' not in text


def test_accrual_after_the_census_still_passes():
    data = live_data()
    data["sessions"].append({"session": "2026-11-09"})
    data["prints"].append({"session": "2026-11-09"})
    data["counts"]["sessions_recorded"] += 1
    data["counts"]["golden_prints"] += 1
    assert mod.golden_claim_asof_ok(data) is True


def test_a_lost_prefix_session_fails():
    data = live_data()
    data["sessions"] = [s for s in data["sessions"]
                        if s["session"] != "2026-10-28"]
    assert mod.golden_claim_asof_ok(data) is False


def test_a_redated_prefix_fails():
    data = live_data()
    for s in data["sessions"]:
        if s["session"] == "2026-11-04":
            s["session"] = "2026-11-03"
    assert mod.golden_claim_asof_ok(data) is False


def test_an_extra_print_inside_the_prefix_fails():
    data = copy.deepcopy(live_data())
    data["prints"].append({"session": "2026-11-02"})
    assert mod.golden_claim_asof_ok(data) is False


def test_live_totals_below_the_census_fail():
    data = live_data()
    data["counts"]["sessions_recorded"] = 7
    assert mod.golden_claim_asof_ok(data) is False
    data = live_data()
    data["counts"]["golden_prints"] = 1
    assert mod.golden_claim_asof_ok(data) is False


def test_source_uses_asof_verification_not_count_needles():
    with open(PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert "check_golden_claim_asof" in src
    assert '"\\"sessions_recorded\\": 8"' not in src
    assert '"\\"golden_prints\\": 2"' not in src
    # The decision date is a fixed rule parameter and stays a
    # live needle by design.
    assert '\\"decision_date\\": \\"2026-12-08\\"' in src


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
