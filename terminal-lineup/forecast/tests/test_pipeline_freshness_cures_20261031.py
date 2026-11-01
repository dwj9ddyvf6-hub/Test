"""Regression blockers for the terminal health loop cure round 1
(pipeline / freshness / automation class), 2026-10-31:

- D-R1-01: ledger appends from ANY path carry run provenance.
  The Ledger choke point (_append) writes one sidecar line per
  append to ledger_provenance.log beside the ledger. Pre-cure no
  sidecar existed, so the ~19,700 rows appended outside the
  refresh runner had no provenance.
- D-R1-02: mortality-curve's as_of is its registered issuance
  date (ISSUE), a single-issuance engine: the refresher's ISSUE
  constant and the published page agree, so the freshness census
  must not read it as a lagging session date.
- D-R1-03: refresh_chain binds a populated store by its
  collector manifest, not the lane stamp: the lane last_date
  check lives inside the empty-store branch, after the
  total_days == 0 gate and before the manifest check.
- D-R1-21: the canonical suite gate is the memory-bounded
  per-file runner (run_suite.py at the terminal root): it exists,
  discovers test files, and reports a per-file verdict with a
  gate exit code.
"""
import json
import os
import subprocess
import sys

LINEUP = os.path.expanduser("~/workspace/terminal-lineup")
FORECAST = os.path.join(LINEUP, "forecast")
SITE = os.path.join(LINEUP, "site")
sys.path.insert(0, FORECAST)


def test_ledger_append_writes_provenance_sidecar(tmp_path):
    from ledger import Ledger
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    row = led.append_genesis("blocker fixture")
    prov_path = tmp_path / "ledger_provenance.log"
    assert prov_path.exists()
    lines = [json.loads(l) for l in
             prov_path.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    assert len(lines) == 1
    assert lines[0]["row_id"] == row["row_id"]
    assert lines[0]["type"] == "genesis"
    assert lines[0]["ts_utc"].endswith("Z")
    # The sidecar is not part of the chain: the chain still verifies.
    assert led.verify_chain()


def test_mortality_as_of_is_its_registered_issuance():
    src = open(os.path.join(SITE, "refresh_mortalitycurve.py"),
               encoding="utf-8").read()
    assert 'ISSUE = "2026-10-29"' in src
    data = json.load(open(os.path.join(
        SITE, "mortality-curve", "data.json"), encoding="utf-8"))
    assert data["as_of"] == "2026-10-29"


def test_chain_lane_date_check_binds_empty_store_only():
    src = open(os.path.join(SITE, "refresh_chain.py"),
               encoding="utf-8").read()
    gate = src.index('if total_days == 0:')
    lane_check = src.index('lane.get("last_date")')
    manifest = src.index("err = manifest_check(days_by_und)")
    assert gate < lane_check < manifest


def test_suite_runner_is_the_canonical_gate(tmp_path):
    runner = os.path.join(LINEUP, "run_suite.py")
    assert os.path.exists(runner)
    out = tmp_path / "suite_summary.json"
    r = subprocess.run(
        [sys.executable, runner, "--out", str(out),
         os.path.join(FORECAST, "tests",
                      "test_refresh_defects_20261029.py")],
        capture_output=True, text=True, timeout=600)
    # Gate exit must be 0 and the summary must carry a per-file
    # PASS verdict for the target file.
    assert r.returncode == 0, r.stdout + r.stderr
    summary = json.loads(out.read_text(encoding="utf-8"))
    assert summary["gate_exit"] == 0
    assert summary["counts"].get("PASS") == 1
