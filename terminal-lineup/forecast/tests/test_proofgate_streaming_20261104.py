"""Regression blockers for PROOFGATE-STREAM-20261104.

The proof gate lane (refresh_proofgate.py) was OOM-killed
(exit -9) three times. Two of its reads were unbounded: the
DEEP panel loader held the whole 1.14 GB panel as one text
while slicing symbol arrays out of it, and the pre-append
chain verification parsed the whole forecast ledger into
memory. The cures: the panel is read as a chunked stream, one
symbol's segment at a time (a memory map does not bound a
full-universe scan, which faults every page in), and the lane
verifies the chain with Ledger.verify_chain_streaming, which
holds one parsed row at a time.

Fail directions on the pre-cure code: verify_chain_streaming
does not exist (AttributeError), and the panel load's peak
memory on the fixture below exceeds the stated bound (the
whole text plus the decoded row lists), where the cured
loader stays under it.

Retention half (added the same day, after a live run exposed
it): the first streaming form still loaded every symbol's
closes into one retained map for the scan to consume, and a
measured live run held the same 2.45 GB plateau the
whole-text loader died at. The lane now computes each name
as its segment streams past (build_from_panel). The last two
tests pin that: the streamed scan's results equal the
in-memory scan's on the same fixture, and the streamed
scan's peak memory stays bounded where the retained-map
scan's does not (the per-name proof computation is stubbed
in the memory test: the defect class under test is
retention, and the equivalence test covers the math).
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
FORECAST = os.path.expanduser("~/workspace/terminal-lineup/forecast")
sys.path.insert(0, FORECAST)
sys.path.insert(0, SITE)

from ledger import Ledger  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "refresh_proofgate", os.path.join(SITE, "refresh_proofgate.py"))
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)


def _small_ledger(tmp_path, n=40):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    for i in range(n):
        led._append({"type": "note", "n": i})
    return path


def test_streaming_verify_matches_verify_chain(tmp_path):
    path = _small_ledger(tmp_path)
    led = Ledger(path)
    assert led.verify_chain() is True
    assert led.verify_chain_streaming() is True


def test_streaming_verify_detects_a_broken_link(tmp_path):
    path = _small_ledger(tmp_path)
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    row = json.loads(lines[10])
    row["n"] = 99999  # rewrite a body without fixing its hash
    lines[10] = json.dumps(row)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    led = Ledger(path)
    assert led.verify_chain() is False
    assert led.verify_chain_streaming() is False


def test_streaming_verify_missing_file_is_empty(tmp_path):
    led = Ledger(str(tmp_path / "absent.jsonl"))
    assert led.verify_chain_streaming() is True


_CHILD = r"""
import importlib.util, json, resource, sys
spec = importlib.util.spec_from_file_location(
    "refresh_proofgate", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
closes, freshest = mod.load_panel_closes(sys.argv[2])
assert len(closes) == 800, len(closes)
assert freshest == "2026-11-03", freshest
assert closes["SYM000"][0] == 100.0
assert len(closes["SYM799"]) == 10000
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
"""


def _write_fixture_panel(path, symbols=800, bars=10000):
    """A panel of ~400 MB of JSON: the whole file as one text
    plus the closes map peaks at roughly 650 MB, while the
    closes the scan keeps are ~260 MB of floats. One segment
    template is written for every symbol to keep the build
    fast."""
    bar = json.dumps(["2026-11-02", 100.0, 101.0, 99.0, 100.0,
                      123456])
    last = json.dumps(["2026-11-03", 100.0, 101.0, 99.0, 106.0,
                       123456])
    segment = "[" + ", ".join(
        [json.dumps(["2026-11-02", 100.0, 101.0, 99.0,
                     100.0 + (b % 7), 123456])
         for b in range(bars - 1)] + [last]) + "]"
    assert bar  # the plain bar template documents the row shape
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{")
        for s in range(symbols):
            if s:
                fh.write(", ")
            fh.write(json.dumps(f"SYM{s:03d}") + ": " + segment)
        fh.write("}")


def test_panel_load_is_memory_bounded(tmp_path):
    panel = tmp_path / "panel.json"
    _write_fixture_panel(str(panel))
    module = os.path.join(SITE, "refresh_proofgate.py")
    out = subprocess.run(
        [sys.executable, "-c", _CHILD, module, str(panel)],
        capture_output=True, text=True, timeout=900)
    assert out.returncode == 0, out.stderr[-2000:]
    peak_kb = int(out.stdout.strip().splitlines()[-1])
    # Stated bound: the load must peak under 450 MB on this
    # ~400 MB fixture. The whole-text loader peaks around
    # 650 MB on the same file (the resident text on top of the
    # closes map); the streaming loader holds one chunk and
    # one symbol's rows beside the closes.
    assert peak_kb < 450 * 1024, peak_kb


def _write_walk_panel(path, symbols=6, bars=400):
    """A small panel of deterministic price walks, long enough
    for the frozen rule's indicators and episodes."""
    import math
    import random
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{")
        for s in range(symbols):
            rng = random.Random(1000 + s)
            price = 100.0
            rows = []
            for b in range(bars):
                price *= 1.0 + rng.uniform(-0.02, 0.021)
                rows.append([f"2025-{(b // 28) % 12 + 1:02d}-"
                             f"{b % 28 + 1:02d}", price, price,
                             price, price, 1000])
            if s:
                fh.write(", ")
            fh.write(json.dumps(f"WALK{s}") + ": " +
                     json.dumps(rows))
        fh.write("}")


def test_streamed_scan_matches_in_memory_scan(tmp_path):
    panel = str(tmp_path / "walk.json")
    _write_walk_panel(panel)
    _reg, rule = pg.load_rule()
    closes, freshest = pg.load_panel_closes(panel)
    expected = pg.build(closes, rule)
    got, got_freshest = pg.build_from_panel(panel, rule)
    assert got_freshest == freshest
    assert set(got) == set(expected)
    for sym in expected:
        e, g = expected[sym], got[sym]
        assert g["proof_state"] == e["proof_state"], sym
        assert g["episodes"] == e["episodes"], sym
        assert g["hits"] == e["hits"], sym
        assert g["p_value"] == e["p_value"], sym
        assert g["bh_q_value"] == e["bh_q_value"], sym


_CHILD_STREAM = r"""
import importlib.util, resource, sys
spec = importlib.util.spec_from_file_location(
    "refresh_proofgate", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.PG.compute_name_proof = lambda sym, closes, rule: {
    "symbol": sym, "proof_state": "OBSERVING", "p_value": 1.0}
RULE = {"multiple_testing": {"alpha": 0.05}}
results, freshest = mod.build_from_panel(sys.argv[2], RULE)
assert len(results) == 250, len(results)
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
"""

_CHILD_RETAIN = r"""
import importlib.util, resource, sys
spec = importlib.util.spec_from_file_location(
    "refresh_proofgate", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.PG.compute_name_proof = lambda sym, closes, rule: {
    "symbol": sym, "proof_state": "OBSERVING", "p_value": 1.0}
RULE = {"multiple_testing": {"alpha": 0.05}}
closes, freshest = mod.load_panel_closes(sys.argv[2])
assert len(closes) == 250, len(closes)
results = mod.build(closes, RULE)
assert len(results) == 250, len(results)
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
"""


def test_streamed_scan_does_not_retain_the_panel():
    # The fixture is ~380 MB of JSON, too big for the pytest
    # tmp dir on this host (a 512 MB tmpfs): it is written to
    # a scratch dir beside this test and removed afterwards.
    scratch = os.path.join(HERE, ".tmp_fixtures")
    os.makedirs(scratch, exist_ok=True)
    panel = os.path.join(scratch, "big_panel.json")
    try:
        _write_fixture_panel(panel, symbols=250, bars=24000)
        module = os.path.join(SITE, "refresh_proofgate.py")
        peaks = {}
        for name, child in (("stream", _CHILD_STREAM),
                            ("retain", _CHILD_RETAIN)):
            out = subprocess.run(
                [sys.executable, "-c", child, module, panel],
                capture_output=True, text=True, timeout=900)
            assert out.returncode == 0, (name, out.stderr[-2000:])
            peaks[name] = int(out.stdout.strip().splitlines()[-1])
        # Stated bound: the streamed scan peaks under 200 MB on
        # a fixture whose closes map alone is roughly 190 MB of
        # Python floats; the retained-map scan must exceed the
        # streamed peak by at least 100 MB, proving the fixture
        # discriminates the two forms.
        assert peaks["stream"] < 200 * 1024, peaks
        assert peaks["retain"] > peaks["stream"] + 100 * 1024, peaks
    finally:
        if os.path.exists(panel):
            os.remove(panel)
