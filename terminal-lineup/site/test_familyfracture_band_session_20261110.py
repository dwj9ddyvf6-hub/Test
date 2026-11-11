"""Regression blocker for FAMILYFRACTURE-BAND-SESSION-20261110.

Defect: refresh_familyfracture.py compared its panel-based
expected-move recomputation against Engine 1's published band
figure without checking that the band record was dated for the
panel's freshest session. When the panel advanced to 2026-11-10
while corrected-band/data.json still stood at as_of_session
2026-11-09, the refresh refused with a figure-disagreement
message ("recomputed 3.1342 disagrees with published 5.0932")
even though the two figures agree exactly within either session
(4.0876 x guard 1.246 = 5.0932 through 2026-11-09): a stale
record misreported as a figure disagreement.

Cure: band_session_check() fails closed naming both sessions
when the band record's as_of_session differs from the panel's
last session; within a matched session the exact figure
comparison decides as before. No tolerance was widened and the
refusal itself is unchanged in strength.

Fail-first: on the pre-cure module this test fails because
band_session_check does not exist (AttributeError). Point
FF_MODULE_PATH at a pre-cure copy to re-verify the direction.
"""

import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.environ.get(
    "FF_MODULE_PATH", os.path.join(HERE, "refresh_familyfracture.py"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "refresh_familyfracture_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_matching_session_passes_the_check():
    mod = _load()
    bands = {"as_of_session": "2026-11-10"}
    assert mod.band_session_check(bands, "2026-11-10") is None


def test_stale_band_record_fails_closed_naming_both_sessions():
    mod = _load()
    bands = {"as_of_session": "2026-11-09"}
    message = mod.band_session_check(bands, "2026-11-10")
    assert message is not None
    assert "2026-11-09" in message
    assert "2026-11-10" in message
    assert "stale" in message


def test_missing_band_session_fails_closed():
    mod = _load()
    message = mod.band_session_check({}, "2026-11-10")
    assert message is not None
    assert "2026-11-10" in message


def test_band_newer_than_panel_also_fails_closed():
    mod = _load()
    bands = {"as_of_session": "2026-11-11"}
    message = mod.band_session_check(bands, "2026-11-10")
    assert message is not None
    assert "2026-11-11" in message


def test_session_check_runs_before_the_figure_comparison():
    with open(MODULE_PATH, encoding="utf-8") as fh:
        src = fh.read()
    check_at = src.index("band_session_check(bands, panel_last)")
    figure_at = src.index("the recomputed expected move for")
    assert check_at < figure_at
