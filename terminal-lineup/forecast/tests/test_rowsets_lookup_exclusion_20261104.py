"""Regression blocker for ROWSETS-LOOKUP-EXCLUSION-20261104.

build_prior_rows extracted NEW-badge identities from every
data section its generic walk could reach, including the Dark
Prints page's per_name section: per-stock readings the page
holds as lookup data (one stock at a time, by typed ticker)
and renders none of as rows. The store therefore claimed 64
badgeable new identities for a page whose glass can never
show a badge, while the shared badge renderer (proven working
on the Board page, 22 badges) was blamed for a rendering
defect that did not exist. The walk now skips the per_name
subtree: identities are extracted only from data a page can
render as rows.

Fail direction on the pre-cure code: labels() returns the
per_name symbols, so test_lookup_symbols_not_extracted
fails; it passes on the cured code.
"""
import importlib.util
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "build_prior_rows", os.path.join(SITE, "build_prior_rows.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

DATA = {
    "session": "2026-11-03",
    "per_name": {
        "state": "collecting",
        "readings": [{"symbol": "AALG", "pct": 41.2,
                      "session": "2026-11-03"},
                     {"symbol": "AAPW", "pct": 12.0,
                      "session": "2026-11-03"}],
        "latest": {"AALG": 41.2, "AAPW": 12.0}},
    "history": [{"symbol": "SPY", "session": "2026-11-03"},
                {"symbol": "QQQ", "session": "2026-11-03"}],
}


def test_lookup_symbols_not_extracted():
    out = mod.labels(DATA)
    assert "AALG" not in out
    assert "AAPW" not in out


def test_rendered_rows_still_extracted():
    out = mod.labels(DATA)
    assert "SPY" in out
    assert "QQQ" in out
