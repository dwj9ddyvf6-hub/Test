"""Regression blockers for the FE17 dispersion ruling
(2026-10-30, RC-07): the FE17 centre's registered dispersion
input is the forecast error dispersion on record, adopted
under its own true name by registry amendment, under the
owner's decision delegated to Midna on 2026-10-30. It is not
cross analyst estimate dispersion, which no free source
carries, and nothing may name it as such.

Fail direction: on the pre-ruling tree the refresher passes
None for the dispersion input on every name, the adaptation
names the missing input estimate_dispersion_z, the page block
stands at inputs_partial_dispersion_ruling_open, and the
registry carries no fe17_centre amendment, so every test
below fails there.
"""

import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
FORECAST = os.path.normpath(os.path.join(HERE, ".."))
for p in (SITE, FORECAST):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ad = _load("engine_adaptations_ruling",
           os.path.join(SITE, "engine_adaptations.py"))
e12 = _load("refresh_earningsdistribution_ruling",
            os.path.join(SITE, "refresh_earningsdistribution.py"))

RECORD_FIXTURE = {
    "names": {
        "TEST": {
            "timing_quality": 0.9,
            "forecast_error_dispersion": {
                "state": "recorded",
                "cross_section_z": 0.5,
                "sd": 0.05,
                "definition": ("forecast error dispersion: sd of "
                               "the name's own prior forecast "
                               "errors, z scored across reporting "
                               "names. Not cross analyst "
                               "dispersion."),
            },
        },
        "NOTIMING": {
            "timing_quality": None,
            "forecast_error_dispersion": {
                "state": "recorded",
                "cross_section_z": -0.25,
                "sd": 0.04,
                "definition": ("forecast error dispersion: sd of "
                               "the name's own prior forecast "
                               "errors, z scored across reporting "
                               "names. Not cross analyst "
                               "dispersion."),
            },
        },
    },
    "names_with_timing": 46,
}


def test_missing_dispersion_named_by_its_true_name():
    out = ad.fe17_centre(None, 2.0, None, None)
    assert out["state"] == "not_recorded"
    assert "forecast_error_dispersion_z" in out["missing"]
    assert "estimate_dispersion_z" not in out["missing"]


def test_recorded_centre_names_its_dispersion_input():
    out = ad.fe17_centre(4.0, 2.0, 0.5, 1.0)
    assert out["state"] == "recorded"
    # (0.6*4 + 0.4*2) * (1 + 0.08*0.5) * 1.0 = 3.2 * 1.04
    assert out["centre_pct"] == pytest.approx(3.328)
    assert out["dispersion_input"] == "forecast_error_dispersion"
    assert out["dispersion_z"] == pytest.approx(0.5)


def test_fe17_for_view_consumes_the_record_dispersion(
        monkeypatch):
    monkeypatch.setattr(e12, "earnings_record",
                        lambda: RECORD_FIXTURE)
    view = {"state": "recorded", "typical_pct": 2.0}
    out = e12.fe17_for_view(view, 4.0, "TEST")
    assert out["state"] == "recorded"
    # (0.6*4 + 0.4*2) * (1 + 0.08*0.5) * 0.9 = 3.2 * 1.04 * 0.9
    assert out["centre_pct"] == pytest.approx(2.9952)
    assert out["dispersion_input"] == "forecast_error_dispersion"


def test_fe17_for_view_still_names_each_missing_input(
        monkeypatch):
    monkeypatch.setattr(e12, "earnings_record",
                        lambda: RECORD_FIXTURE)
    view = {"state": "recorded", "typical_pct": 2.0}
    out = e12.fe17_for_view(view, 4.0, "NOTIMING")
    assert out["state"] == "not_recorded"
    assert out["missing"] == ["timing_quality"]
    out = e12.fe17_for_view(view, 4.0, "UNRECORDED")
    assert out["state"] == "not_recorded"
    assert "forecast_error_dispersion_z" in out["missing"]
    assert "timing_quality" in out["missing"]


def test_page_block_records_all_three_inputs(monkeypatch):
    monkeypatch.setattr(e12, "earnings_record",
                        lambda: RECORD_FIXTURE)
    monkeypatch.setattr(
        e12, "priced_moves",
        lambda: {"priced_moves_on_record": 30, "names": {}})
    block = e12._fe17_page_block()
    assert block["state"] == "inputs_recorded"
    assert block["missing"] == []
    assert block["dispersion_input"] == "forecast_error_dispersion"
    assert block["names_with_dispersion_on_record"] == 2
    assert block["priced_moves_on_record"] == 30
    assert block["names_with_timing"] == 46
    detail = block["detail"].lower()
    assert "forecast error dispersion" in detail
    assert "2026-10-30" in block["detail"]


def test_registry_carries_the_ruling():
    with open(os.path.join(FORECAST, "registry.json"),
              encoding="utf-8") as fh:
        reg = json.load(fh)
    eng = {e["id"]: e for e in reg["engines"]}["engine_12"]
    centre = eng.get("fe17_centre")
    assert centre is not None
    amendment = centre["amendment"]
    assert amendment["date"] == "2026-10-30"
    assert amendment["adopted_input"] == "forecast_error_dispersion"
    assert amendment["superseded_input"] == \
        "estimate_dispersion_z_cross_analyst"
    inputs = {i["name"]: i for i in centre["inputs"]}
    disp = inputs["dispersion"]
    assert "forecast error dispersion" in disp["definition"]
    assert "none on disk today" not in eng["notes"]
