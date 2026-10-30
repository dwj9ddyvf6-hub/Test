#!/usr/bin/env python3
"""Psychology Engine v1 acceptance tests (design Section 7, fail-able)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from psychology_engine import check_header, expanding_percentiles, SERIES
from pipeline import compile_state, GAUGE_FILES

def test_header_checker_passes_on_store():
    bad = []
    for f in sorted(os.listdir(SERIES)):
        if f.endswith(".csv"):
            probs = check_header(os.path.join(SERIES, f))
            if probs: bad.append((f, probs))
    assert not bad, bad

def test_header_checker_fails_on_missing_field(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("# series: x\n# source: y\ndate,value\n2020-01-01,1\n")
    probs = check_header(str(p))
    assert any("missing provenance field" in x for x in probs), probs

def test_header_checker_fails_on_duplicate_key(tmp_path):
    p = tmp_path / "dup.csv"
    head = "".join(f"# {k}: x\n" for k in
                   ["series", "source", "source_url_or_route", "retrieved", "last_pull",
                    "revision_policy", "as_of_meaning", "archive_claim", "downloaded_span",
                    "breaks", "transforms", "file_sha256"])
    p.write_text(head + "date,value\n2020-01-01,1\n2020-01-01,2\n")
    probs = check_header(str(p))
    assert any("duplicate natural key" in x for x in probs), probs

def test_percentile_no_future():
    vals = [10, 20, 30, 40, 50]
    full = expanding_percentiles(vals)
    trunc = expanding_percentiles(vals[:3])
    assert full[:3] == trunc, "later data changed an earlier percentile: no-future rule broken"

def _synth(pcts):
    """300 observations per gauge; the last value sits at the target percentile
    of its own history (values 0..299 with the last replaced by the quantile)."""
    def mk(p):
        k = max(0, min(299, round(p / 100 * 299)))
        vals = [float(i) for i in range(300)]
        vals[-1] = float(k)
        return [{"date": "2026-10-30", "value": v, "pct": None, "kind": "live"} for v in vals]
    rows = {g: [] for g in GAUGE_FILES}
    core = ["G1", "G2", "G3", "G5", "G6", "G7"]
    for g, p in zip(core, pcts):
        rows[g] = mk(p)
    rows["G4"] = mk(50)
    rows["G9"] = mk(50)
    return rows

def test_contested_synthetic():
    rows = _synth([5, 50, 95, 50, 50, 50])
    s = compile_state(gauge_rows=rows, publish=False)
    assert s["contested"] and s["regime"].startswith("Contested:"), s["regime"]
    assert "G1" in s["disagreement"] and "G3" in s["disagreement"]

def test_insufficient_data_synthetic():
    rows = _synth([50, 50, 50, 50, 50, 50])
    for g in ["G3", "G5", "G6", "G7"]:
        rows[g] = []
    s = compile_state(gauge_rows=rows, publish=False)
    assert s["regime"] == "Insufficient data" and s["composite_percentile"] is None

def test_synthetic_compile_never_publishes():
    """Regression blocker for the build-day defect: a synthetic compile
    overwrote the real state and consumer files. publish=False must write
    nothing."""
    import hashlib
    state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "output", "state-latest.json")
    if not os.path.exists(state_path):
        return
    before = hashlib.sha256(open(state_path, "rb").read()).hexdigest()
    rows = _synth([5, 50, 95, 50, 50, 50])
    compile_state(gauge_rows=rows, publish=False)
    after = hashlib.sha256(open(state_path, "rb").read()).hexdigest()
    assert before == after, "synthetic compile changed the published state"

def _hdr():
    return {"series": "demo", "source": "x", "source_url_or_route": "y",
            "retrieved": "2026-10-30", "last_pull": "2026-10-30",
            "revision_policy": "r", "as_of_meaning": "a", "archive_claim": "c",
            "breaks": "none", "transforms": "none", "file_sha256": ""}

def test_failed_pull_never_destroys_stored_series(tmp_path, monkeypatch):
    """Regression blocker for the 2026-10-30 GDELT loss: bf_gdelt landed 71
    rows, a later re-pull failed (curl exit 22), and its exception handler
    called write_absent, overwriting the good series with an empty absent
    file. Every failure path (write_absent, preserve_series, and a direct
    empty write_series) must preserve stored rows."""
    import psychology_engine as pe
    monkeypatch.setattr(pe, "SERIES", str(tmp_path))
    rows = [{"date": "2026-08-02", "tone": -0.579}, {"date": "2026-08-03", "tone": -0.346}]
    pe.write_series("demo.csv", _hdr(), ["date", "tone"], rows)
    assert len(pe.read_series("demo.csv")) == 2
    pe.write_absent("demo.csv", _hdr())
    assert len(pe.read_series("demo.csv")) == 2, "write_absent erased stored data"
    pe.preserve_series("demo.csv", _hdr())
    assert len(pe.read_series("demo.csv")) == 2, "preserve_series erased stored data"
    pe.write_series("demo.csv", _hdr(), ["date", "tone"], [])
    assert len(pe.read_series("demo.csv")) == 2, "empty write_series erased stored data"

def test_absent_written_only_where_no_data_stored(tmp_path, monkeypatch):
    import psychology_engine as pe
    monkeypatch.setattr(pe, "SERIES", str(tmp_path))
    pe.preserve_series("never.csv", _hdr())
    assert pe.read_series("never.csv") == []
    assert os.path.exists(os.path.join(str(tmp_path), "never.csv"))

def test_g7_recomputable_from_stored_gdelt_series():
    """Check 3 blocker: G7's stored gauge values must be recomputable from
    the stored GDELT history series (expanding percentile of tone), with
    identical dates and count. Fails while the series file is empty."""
    from psychology_engine import read_series, expanding_percentiles, GAUGES
    tone = [(r["date"], float(r["tone"])) for r in read_series("gdelt_gkg_tone_daily.csv")]
    assert tone, "gdelt_gkg_tone_daily.csv holds no rows: G7 cannot be recomputed"
    expect = expanding_percentiles([v for _, v in tone])
    with open(os.path.join(GAUGES, "g7_attention_narrative.csv")) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    import csv as _csv
    gauge = list(_csv.DictReader(lines))
    assert len(gauge) == len(tone), (len(gauge), len(tone))
    for (d, _), exp, g in zip(tone, expect, gauge):
        assert g["date"] == d
        assert abs(float(g["value"]) - round(exp, 4)) < 0.01, (d, g["value"], exp)

def test_no_band_under_minimum_history():
    rows = _synth([50, 50, 50, 50, 50, 50])
    rows["G7"] = [{"date": "2026-10-30", "value": 50.0, "pct": 50.0, "kind": "live"} for _ in range(10)]
    s = compile_state(gauge_rows=rows, publish=False)
    assert s["gauges"]["G7"]["percentile"] is None
    assert any("no band" in f for f in s["gauges"]["G7"]["flags"])
