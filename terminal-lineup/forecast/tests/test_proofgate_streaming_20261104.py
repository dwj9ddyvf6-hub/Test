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
