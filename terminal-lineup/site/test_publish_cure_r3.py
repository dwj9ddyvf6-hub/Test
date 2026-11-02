#!/usr/bin/env python3
"""Regression blockers for the R3 publish cures (2026-11-02).

Rows covered:
- The eight data.json files that never published (seven over the old
  5 MB data cap, insider-wire blocked by a first_name false positive
  on third-party SEC Form 4 data) are now in the sync's included set
  and pass candidate_for, while the gate's other patterns and a
  standalone first-name reference still block.
- The Market Mood ruling (owner, 2026-11-02): no composite hero
  gauge, no labelled median line, and no 'Current: X' endpoint label
  in the render layer or the page generator.

Run: python3 site/test_publish_cure_r3.py  (exit 0 = PASS)
"""
import sys
import re
from unittest.mock import patch
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))
import sync_to_test as sync  # noqa: E402

fails = []

EIGHT = ["ai-chart-read", "breakout-scanner", "chain-explorer",
         "insider-wire", "momentum-clock", "one-page-report",
         "pattern-draw", "short-volume"]

# 1) All eight data.json files are in the included set and under cap.
included = set(sync.included_files())
for slug in EIGHT:
    rel = f"site/{slug}/data.json"
    if rel not in included:
        fails.append(f"{rel} not in sync included set")
    size = (SITE / slug / "data.json").stat().st_size
    if size > sync.DATA_JSON_CAP:
        fails.append(f"{rel} over DATA_JSON_CAP ({size})")

# 2) candidate_for passes the real insider-wire data unchanged, and
#    passes a synthetic third-party full name.
raw = (SITE / "insider-wire" / "data.json").read_bytes()
cand, reason = sync.candidate_for("site/insider-wire/data.json", raw)
if cand != raw:
    fails.append(f"insider-wire data blocked: {reason}")
# Synthetic privacy cases use neutral fixtures, never the owner's identifiers.
# Restore both the pattern source and cached matcher after these cases.
_fixture_patterns = [
    ("first_name", re.compile(r"\bAlex\b", re.I)),
    ("surname", re.compile(r"\bBennett\b", re.I)),
    ("codename", re.compile(r"\bprivate-codename\b", re.I)),
]
with patch.object(sync.pii_gate, "PATTERNS", _fixture_patterns), \
        patch.object(sync, "_FIRST_NAME_RX", dict(_fixture_patterns)["first_name"]):
    synthetic = b'{"rows": [{"insider": "Walsh Alex F", "shares": 10}]}'
    cand, reason = sync.candidate_for("site/insider-wire/data.json", synthetic)
    if cand != synthetic:
        fails.append(f"third-party full name blocked: {reason}")

    # 3) Every other pattern and a standalone first name still block.
    for label, payload in (
            ("surname", b'{"insider": "Doe Bennett"}'),
            ("codename", b'{"note": "private-codename"}'),
            ("standalone first name", b'{"insider": "Alex"}'),
            ("first name + surname", b'{"insider": "Alex Bennett"}')):
        cand, reason = sync.candidate_for("site/insider-wire/data.json", payload)
        if cand is not None:
            fails.append(f"insider-wire {label} NOT blocked")
    cand, reason = sync.candidate_for("site/other-page/data.json", synthetic)
    if cand is not None:
        fails.append("third-party name waiver leaked to another file")

# 4) Market Mood ruling needles in the render layer and generator.
grok = (SITE / "grok.js").read_text()
strip_fn = grok[grok.find("function moodStripR2"):grok.find("function morningMapR2")]
if "Current:" in strip_fn:
    fails.append("moodStripR2 still labels a Current: composite endpoint")
if "gb-gaugewrap" not in grok:
    fails.append("mood recipe wrap missing from grok.js")
mood_fn = grok[grok.find("function moodRecipe"):grok.find("function rotationScatter")]
if "gb-big" in mood_fn or "composite_percentile" in mood_fn:
    fails.append("moodRecipe still renders the composite hero value")
pipeline = (SITE.parent / "psychology-engine" / "pipeline.py").read_text()
if "{comp_bar}" in pipeline or "Composite percentile {comp" in pipeline:
    fails.append("pipeline.py still renders the composite headline")
if "no single composite headline" not in pipeline:
    fails.append("pipeline.py ruling note missing")
mood_html = (SITE / "market-mood" / "index.html").read_text()
if "Headline reading" in mood_html or "Composite percentile" in mood_html:
    fails.append("rendered market-mood page still carries the headline")

if fails:
    print("FAIL")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("PASS")
