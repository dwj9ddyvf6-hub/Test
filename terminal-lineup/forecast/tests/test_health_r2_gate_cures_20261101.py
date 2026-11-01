"""Regression blockers for the terminal health loop cure round 2
(pipeline / freshness / automation class), 2026-11-01:

- D-R2-01 root cause (found in this cure pass, after AUDIT-R2):
  the canonical suite gate could not produce a green record
  because test_shipyard_adoptions.py::test_real_tree_matches_
  committed_manifest failed intermittently inside full gate
  runs while passing standalone. Proven chain (per-file desk
  hash tracking across the suite order, then a full-order
  reproduction capturing the assertion): test_charts_ia runs
  site/publish_desk.py as a bare subprocess to prove the desk
  producer; publish_desk.py was the one served-tree writer
  that never imported terminal_common, so the shared manifest
  sync (MANIFEST-SHARED-WRITE-20261031, an atexit rebuild in
  terminal_common) never registered in that process. Whenever
  the desk feed had advanced since the last manifest build,
  the publish rewrote desk/data.json and left asset-manifest
  .json stale; shipyard (and smoke_check) then failed on
  desk/data.json until an unrelated terminal_common process
  exited and synced. Cure: publish_desk.py imports
  terminal_common on the refresh_hub pattern, putting it on
  the same shared write path as every other refresh script.
  A/B spot-check on the live tree, 2026-11-01: from a stale-
  manifest state, publish with TERMINAL_NO_MANIFEST_SYNC=1
  (the pre-cure behaviour) left SMOKE FAIL MISMATCH
  desk/data.json; publish with the cure active left SMOKE
  PASS (207 files) with desk/data.json byte-identical.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

LINEUP = Path(__file__).resolve().parents[2]
SITE = LINEUP / "site"
sys.path.insert(0, str(SITE))


def test_publish_desk_imports_terminal_common_manifest_sync():
    src = (SITE / "publish_desk.py").read_text(encoding="utf-8")
    assert "import terminal_common" in src, (
        "publish_desk.py writes served files without the shared "
        "manifest-sync write path (terminal_common)")


def test_standalone_publish_desk_leaves_manifest_matching():
    # The exact exercise that proved the defect: a bare
    # publish_desk.py run (as test_charts_ia performs it) must
    # leave the committed manifest matching the served tree.
    out = subprocess.run(
        [sys.executable, str(SITE / "publish_desk.py")],
        capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stdout + out.stderr
    import importlib
    sc = importlib.import_module("smoke_check")
    manifest = sc.load_manifest()
    assert sc.verify_tree(str(SITE), manifest) == []
