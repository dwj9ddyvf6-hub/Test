"""Regression blocker for the Self-Analogue checkpoint cache
(cure G17 remainder, 2026-10-30).

Fail direction: on the pre-cure refresh_selfanalogue.py none of
these helpers exist (the build recomputed every qualifying name
from scratch on every run, so a killed multi-hour run lost all
progress and a same-panel daily re-run cost the same hours,
which is why the daily refresh could not go green with the DEEP
legs cured). The cache stores only deterministic recompute
results keyed by the panel fingerprint; these tests pin the
round-trip, the fingerprint refusal, and the torn-line tolerance.
"""
import importlib.util
import json
import os
import sys

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
sys.path.insert(0, SITE)
sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "refresh_selfanalogue_cache_test",
        os.path.join(SITE, "refresh_selfanalogue.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fingerprint_changes_with_size(tmp_path):
    mod = _load()
    p = tmp_path / "panel.json"
    p.write_text("{}")
    fp1 = mod.panel_fingerprint(str(p))
    p.write_text('{"A": []}')
    fp2 = mod.panel_fingerprint(str(p))
    assert fp1 != fp2
    assert fp1.startswith("panel.json:")


def test_lengths_cache_roundtrip_and_fingerprint_refusal(tmp_path):
    mod = _load()
    path = str(tmp_path / "lengths.json")
    lengths = {"AAPL": 2973, "SPY": 2973}
    mod.write_lengths_cache(path, "panel.json:10:20", lengths)
    assert mod.read_lengths_cache(path, "panel.json:10:20") == lengths
    assert mod.read_lengths_cache(path, "panel.json:99:20") is None
    assert mod.read_lengths_cache(
        str(tmp_path / "missing.json"), "panel.json:10:20") is None


def test_fc_cache_roundtrip_none_and_torn_line(tmp_path):
    mod = _load()
    path = str(tmp_path / "results.jsonl")
    fc = {"usable_states": 2764, "matched": 461,
          "p10": -6.88, "p50": 3.11, "p90": 11.04}
    mod.append_fc_cache(path, "AAPL", fc)
    mod.append_fc_cache(path, "ZZZZ", None)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write('{"symbol": "TORN", "fc": {"usable_')  # killed mid-append
    out = mod.read_fc_cache(path)
    assert out["AAPL"] == fc
    assert out["ZZZZ"] is None
    assert "TORN" not in out


def test_build_consults_cache_before_computing():
    with open(os.path.join(SITE, "refresh_selfanalogue.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert "cached_fc = read_fc_cache(fc_path)" in src
    assert "fc = self_analogue_forecast_fast(panel[sym])" in src
    assert "append_fc_cache(fc_path, sym, fc)" in src
    assert "read_lengths_cache(lengths_path, fingerprint)" in src
