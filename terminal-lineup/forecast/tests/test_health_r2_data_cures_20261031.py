"""Regression blocker: HEALTH-R2-RECORD-STRIP-20261031
(engine/data correctness + ledger/integrity class, cure round 2).

Three engine refreshers (engine_12 earnings-distribution,
engine_20 calibration-league, engine_19 in-regime-oracle) wrote
their page data.json with no self-enrich tail, so any bare run
(a standalone recheck, the refresh_tools panel re-sync) stripped
the record_surface and explanation blocks the lanes add, and the
pages published with no record until the next full lane close.
Proven on the final R2 tree: test_record_surface_20261031 and
test_explanation_20261031 both failed naming exactly these three
pages, last written bare at 2026-11-01T01:24-01:28Z after the
01:22Z hourly enrich.

Cure: each refresher carries the self-enrich tail its siblings
already carry (refresh_earningscal.py pattern): after writing
its data.json it calls record_surface.enrich_slug then
explanation.enrich_slug for its own slug.

Fail direction: the source assertions fail on the pre-cure
refreshers (no enrich_slug call anywhere in them, verified
against the HEAD copies) and the live-state assertions fail on
the pre-cure tree (both parent suites red, above). Gate wiring:
run_suite.py discovers every test_*.py under forecast/tests.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
sys.path.insert(0, str(SITE))

CASES = {
    "refresh_earningsdistribution.py": "earnings-distribution",
    "refresh_calibrationleague.py": "calibration-league",
    "refresh_inregimeoracle.py": "in-regime-oracle",
}
FIELDS = ("current_reading", "study_record", "calibration_record",
          "live_accrual", "missing")


def test_refreshers_carry_self_enrich_tail():
    for script, slug in CASES.items():
        src = (SITE / script).read_text()
        rs_at = src.find(f'_rs.enrich_slug("{slug}")')
        ex_at = src.find(f'_ex.enrich_slug("{slug}")')
        assert rs_at != -1, f"{script}: no record-surface self-enrich tail"
        assert ex_at != -1, f"{script}: no explanation self-enrich tail"
        assert rs_at < ex_at, (
            f"{script}: enrich order must be record surface first, "
            "explanation second (the explanation reads the record)")


def test_pages_carry_full_record_and_explanation():
    for slug in CASES.values():
        data = json.loads((SITE / slug / "data.json").read_text())
        rs = data.get("record_surface")
        assert rs and all(f in rs for f in FIELDS), (
            f"{slug}: record_surface missing or incomplete")
        assert rs["missing"]["what_and_when"], (
            f"{slug}: record_surface missing line is empty")
        assert data.get("explanation"), f"{slug}: no explanation block"


def test_enrich_tail_preserves_engine_values():
    import record_surface
    path = SITE / "calibration-league" / "data.json"
    before = json.loads(path.read_text())
    digest_before = hashlib.sha256(json.dumps(
        {k: v for k, v in before.items()
         if k not in ("record_surface", "explanation",
                      "reading_history", "subject_chart")},
        sort_keys=True).encode()).hexdigest()
    record_surface.enrich_file(path)
    after = json.loads(path.read_text())
    digest_after = hashlib.sha256(json.dumps(
        {k: v for k, v in after.items()
         if k not in ("record_surface", "explanation",
                      "reading_history", "subject_chart")},
        sort_keys=True).encode()).hexdigest()
    assert digest_before == digest_after
