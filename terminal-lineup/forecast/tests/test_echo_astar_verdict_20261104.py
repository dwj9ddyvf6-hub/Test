"""Regression blocker for ECHO-ASTAR-VERDICT-20261104.

The Echo method's own algorithm (femto-lean/core/echo_lens.py
echo_read) grades its highest-conviction setups "A*", above
SETUP (line: out['verdict'] = 'A*' if astar else 'SETUP'). The
Echo Lens page's verdict vocabulary carried only the four lower
grades, so the first A* reading to reach the record (RNST, echo
panel session 2026-11-02, one name in 1,833) made the page refuse
every run: "a verdict this page cannot say (A*)". The page now
carries the method's full verdict set and tallies A* readings.

Fail direction on the pre-cure code: "A*" is not in VERDICT_WORDS
and the tally tuple has no A* slot, so the assertions fail.
"""
import importlib.util
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "refresh_echolens", os.path.join(SITE, "refresh_echolens.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_astar_is_a_sayable_verdict():
    assert "A*" in mod.VERDICT_WORDS
    for v in ("SETUP", "WATCH", "TRAP", "NO TRADE"):
        assert v in mod.VERDICT_WORDS


def test_astar_reading_renders_in_the_methods_words():
    r = {"verdict": "A*", "reason": "zone + confluence + reaction",
         "structure": "impulse forming", "zone": 38.08,
         "invalidation": 33.9,
         "targets": {"objective_1.618": 55.3}}
    words = mod.reading_words(r)
    assert "verdict: A*" in words
    assert "Zone at 38.08" in words
