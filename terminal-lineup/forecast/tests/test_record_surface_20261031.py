"""Regression blocker: RECORD-SURFACE-20261031.

Every hub page's data.json must carry a complete record_surface block
(study record labelled, calibration record key, live accrual key,
current reading, missing line), and enrichment must never change any
pre-existing value. Fails on the pre-cure tree (no record_surface
anywhere) and passes after the producer cure.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
sys.path.insert(0, str(SITE))

FIELDS = ("current_reading", "study_record", "calibration_record",
          "live_accrual", "missing")


def hub_slugs():
    hub = (SITE / "index.html").read_text()
    return sorted(set(re.findall(r'href="([a-z0-9\-]+)/"', hub)))


def test_every_hub_page_carries_record_surface():
    missing = []
    for slug in hub_slugs():
        path = SITE / slug / "data.json"
        if not path.exists():
            continue  # interactive calculators, named in CHANGES.md
        data = json.loads(path.read_text())
        rs = data.get("record_surface")
        if not rs or any(f not in rs for f in FIELDS):
            missing.append(slug)
        elif not rs["missing"]["what_and_when"]:
            missing.append(slug + " (empty missing line)")
    assert not missing, f"pages without a full record_surface: {missing}"


def test_enrichment_preserves_existing_values():
    import record_surface
    for slug in ("corrected-band", "market-mood", "regime-dial"):
        path = SITE / slug / "data.json"
        before = json.loads(path.read_text())
        digest_before = hashlib.sha256(json.dumps(
            {k: v for k, v in before.items()
             if k not in ("record_surface", "reading_history")},
            sort_keys=True).encode()).hexdigest()
        record_surface.enrich_file(path)
        after = json.loads(path.read_text())
        digest_after = hashlib.sha256(json.dumps(
            {k: v for k, v in after.items()
             if k not in ("record_surface", "reading_history")},
            sort_keys=True).encode()).hexdigest()
        assert digest_before == digest_after, slug


def test_specific_stranded_records_surfaced():
    mood = json.loads((SITE / "market-mood" / "data.json").read_text())
    assert mood["record_surface"]["gauge_history"]["files"]
    horizon = json.loads((SITE / "horizon-grades" / "data.json").read_text())
    assert "record_on_the_record_page" in str(
        horizon["record_surface"]["surfaced_from_other_files"])
    flow = json.loads((SITE / "flow-engine" / "data.json").read_text())
    assert "record_on_the_flow_tape_page" in str(
        flow["record_surface"]["surfaced_from_other_files"])
    regime = json.loads((SITE / "regime-dial" / "data.json").read_text())
    assert regime["reading_history"], "regime reading history must accrue"
