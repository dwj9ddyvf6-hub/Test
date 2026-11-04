"""Regression blockers for the 2026-10-31 FolioTend restyle + gap cures.
Fail on pre-cure state, pass on cured state (verified by construction:
each assertion targets text/geometry absent before the cure)."""
import pathlib, re
SITE = pathlib.Path(__file__).resolve().parents[2] / "site"
PIPE = pathlib.Path(__file__).resolve().parents[2] / "psychology-engine" / "pipeline.py"

def test_shared_tokens_are_foliotend():
    css = (SITE / "shared.css").read_text()
    for tok in ("--bg:#edf6f5", "--navy:#123247", "--accent:#098979", "--down:#b2595d"):
        assert tok in css, tok
    assert "--accent:#0b5fa5" not in css

def test_hub_has_102_cards_including_orphans():
    hub = (SITE / "index.html").read_text()
    assert hub.count('class="hubcard"') == 102
    assert 'href="market-mood/"' in hub and 'href="static-gex/"' in hub
    assert "102 tools in the lineup" in hub

def test_g3_count_agrees():
    hub = (SITE / "index.html").read_text()
    assert "2,232" not in hub and "2,238 graded study forecasts" in hub

def test_d3_no_stray_punctuation():
    hub = (SITE / "index.html").read_text()
    assert "today,." not in hub and "running today." in hub

def test_d1_pipeline_never_prints_none_percentile():
    src = PIPE.read_text()
    assert "no percentile yet, insufficient history" in src
    mm = (SITE / "market-mood" / "index.html").read_text()
    assert "percentile None" not in mm and "None" not in mm

def test_g2_market_mood_is_gauges_not_table_only():
    mm = (SITE / "market-mood" / "index.html").read_text()
    assert "gauge-band" in mm and "gauge-marker" in mm
    # Re-pinned 2026-11-04 (SUITE-TRIAGE-REPIN-20261104): the
    # cure-day literals were that day's gauge values (and the
    # composite, which the owner's later ruling removed from
    # the page entirely). The durable check is that every
    # gauge value the page's own data carries is printed on
    # the page.
    import json as _json
    _d = _json.loads((SITE / "market-mood" / "data.json").read_text())
    for _g in _d["state"]["gauges"].values():
        if _g.get("value") is not None:
            assert str(_g["value"]) in mm, _g["value"]
    # shared.css loads after inline style (standard order restored)
    assert mm.index("<style>") < mm.index("shared.css")

def test_d2_band_geometry_reserves_label_column():
    js = (SITE / "visual.js").read_text()
    # Re-pinned 2026-11-04 (SUITE-TRIAGE-REPIN-20261104): the
    # FolioTend label column (plotL = 185) was superseded by
    # the WEEK-READINESS-R2-20261102-F overlap cure, which
    # moved the row label onto its own line above the bar and
    # gave the bar the full plot width, so no bar can touch a
    # label. The pin now stands on that cure's geometry.
    assert "WEEK-READINESS-R2-20261102-F" in js
    assert "plotL = 0" in js and 'text-anchor="end"' in js
