"""Regression blockers for DEEP-PASS 3.2 items 13 and 15
(2026-10-29): the static GEX single convention cross check
(site/static_gex.py, site/refresh_staticgex.py, site/static-gex/)
and the new territory FE research questions as registry entries
(forecast/registry.json research_questions, validated by
forecast/registry.py).

Fail direction: the GEX tests fail if the module is removed or
its convention changes (signs, walls, grid flip, IV band); the
registry tests fail on the pre-item registry, which carried no
research_questions at all.
"""

import importlib.util
import json
import math
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "..", "site")
sys.path.insert(0, os.path.abspath(SITE))


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sg = _load("static_gex")

from forecast.registry import Registry, RegistryError, load as load_registry  # noqa: E402


def fixture_rows():
    """A small chain around spot 100: heavy call OI above spot,
    heavy put OI below spot, every contract carrying OI and IV."""
    rows = []
    for strike, coi, poi in ((90.0, 100, 3000), (95.0, 200, 500),
                             (100.0, 800, 800), (105.0, 500, 200),
                             (110.0, 2000, 100)):
        rows.append([f"SPY270115C{int(strike * 1000):08d}", coi, 0, 0.20])
        rows.append([f"SPY270115P{int(strike * 1000):08d}", poi, 0, 0.20])
    return rows


def test_bs_gamma_known_value():
    # Textbook gamma at the money, one year, 20 percent vol.
    g = sg.bs_gamma(100.0, 100.0, 1.0, 0.20, 0.0)
    d1 = (math.log(1.0) + (0.045 + 0.5 * 0.04) * 1.0) / 0.20
    expected = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) \
        / (100.0 * 0.20)
    assert g == pytest.approx(expected, rel=1e-12)
    assert 0.018 < g < 0.020


def test_sign_convention_and_walls():
    out = sg.static_gex_snapshot(fixture_rows(), 100.0, "2026-10-29", "SPY")
    by_strike = {s["strike"]: s for s in out["per_strike"]}
    assert all(s["call_gex"] >= 0 for s in by_strike.values())
    assert all(s["put_gex"] <= 0 for s in by_strike.values())
    # Largest call figure sits at 110 (OI 2000 outweighs the at the
    # money gamma edge of the 100 strike's 800); largest put figure
    # by size at 90 (OI 3000).
    assert out["call_wall"] == 110.0
    assert out["put_wall"] == 90.0
    assert out["net_gex"] == pytest.approx(
        sum(s["net_gex"] for s in by_strike.values()), abs=0.05)


def test_flip_and_iv_sensitivity_band():
    out = sg.static_gex_snapshot(fixture_rows(), 100.0, "2026-10-29", "SPY")
    band = out["flip_iv_band"]
    assert out["flip"] is not None
    assert band["legs"]["central"] == out["flip"]
    assert band["low"] <= out["flip"] <= band["high"]
    assert band["low"] < band["high"]  # IV actually moves the flip
    assert set(band["legs"]) == {"central", "iv_x0.80", "iv_x1.25"}


def test_no_crossing_means_no_flip_not_extrapolation():
    rows = [[f"SPY270115C{int(k * 1000):08d}", 500, 0, 0.20]
            for k in (90.0, 100.0, 110.0)]  # calls only: never crosses
    out = sg.static_gex_snapshot(rows, 100.0, "2026-10-29", "SPY")
    assert out["net_gex"] > 0
    assert out["flip"] is None
    assert out["flip_iv_band"]["low"] is None


def test_missing_oi_or_iv_excluded_never_filled():
    rows = fixture_rows()
    rows.append(["SPY270115C00115000", None, 0, 0.20])   # no OI
    rows.append(["SPY270115P00085000", 700, 0, None])    # no IV
    out = sg.static_gex_snapshot(rows, 100.0, "2026-10-29", "SPY")
    cov = out["coverage"]
    assert cov["contracts"] == 12 and cov["counted"] == 10
    assert cov["excluded_no_oi"] == 1 and cov["excluded_no_iv"] == 1
    strikes = {s["strike"] for s in out["per_strike"]}
    assert 115.0 not in strikes and 85.0 not in strikes


def test_nothing_countable_publishes_nulls():
    out = sg.static_gex_snapshot([["SPY270115C00100000", None, None, None]],
                                 100.0, "2026-10-29", "SPY")
    assert out["net_gex"] is None and out["flip"] is None
    assert out["per_strike"] == []


def test_refresh_and_page_carry_the_convention():
    refresh = os.path.join(SITE, "refresh_staticgex.py")
    page = os.path.join(SITE, "static-gex", "index.html")
    with open(refresh) as fh:
        src = fh.read()
    assert "static_gex_snapshot" in src and "gamma-ladder" in src
    with open(page) as fh:
        html = fh.read()
    assert "data.json" in html and "flip_iv_band" in html


# ---- item 15: registry research questions ------------------------------

def test_research_questions_in_first_pass_order():
    reg = load_registry()
    rq = reg.data["research_questions"]
    questions = [r["id"] for r in rq if r["kind"] == "research_question"]
    assert questions == ["fe01", "fe05", "fe21", "fe25", "fe19", "fe07"]
    for r in rq:
        assert r["decision_rule"] and r["statement"]
        assert r["data_routes"], r["id"]
        for rt in r["data_routes"]:
            assert rt["status"] in ("existing", "partial", "absent")
            reg.validate_family(rt["family"])


def test_conditioners_are_conditioners_only():
    reg = load_registry()
    rq = reg.research_questions()
    hurst = rq["fe02_hurst_gate"]
    assert hurst["kind"] == "conditioner"
    assert hurst["target_engine_ids"] == ["engine_03", "engine_09"]
    assert "not wired" in reg.engines["engine_03"]["notes"]
    diffusion = rq["fe06_sector_diffusion"]
    assert diffusion["kind"] == "conditioner"
    assert diffusion["target_engine_ids"] == ["engine_17", "engine_18"]
    # No conditioner may be graded as an engine.
    for entry in (hurst, diffusion):
        assert entry["state"] == "conditioner_candidate"
        assert "grading_rule_id" not in entry


def test_fe27_form_adopted_without_fe27():
    reg = load_registry()
    form = reg.research_questions()["fe27_reaction_sign_form"]
    assert form["kind"] == "input_form"
    assert form["applies_to_engine_id"] == "engine_24"
    fields = {f["name"] for f in form["form_fields"]}
    assert fields == {"cycle_reaction_sign", "regime_confidence"}
    assert "not adopted" in form["statement"]
    assert "fe27_reaction_sign_form" in reg.engines["engine_24"]["notes"]
    # FE27 is nowhere registered as an engine or a research question.
    assert all(r["source_fe"] != "FE27" or r["kind"] == "input_form"
               for r in reg.data["research_questions"])


def test_registry_rejects_conditioner_without_targets(tmp_path):
    reg = load_registry()
    bad = json.loads(json.dumps(reg.data))
    for r in bad["research_questions"]:
        if r["id"] == "fe02_hurst_gate":
            r["target_engine_ids"] = []
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(RegistryError):
        Registry(str(path))


def test_registry_still_validates_30_engines():
    reg = load_registry()
    assert len(reg.engines) == 30 and reg.validate()
