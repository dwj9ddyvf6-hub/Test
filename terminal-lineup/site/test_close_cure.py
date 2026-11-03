#!/usr/bin/env python3
"""CLOSE-CURE blockers (2026-11-02): hub orphans, hub refresh source,
correlation-web rendered pairs index.

Fail-first proven on the pre-cure tree: the hub orphaned how-it-works
(its refresh kept the section wrapper and dropped the anchor), and
correlation-web rendered 6 of its 7 new identities nowhere on load.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
fails = []


def check(name, ok, detail=""):
    if not ok:
        fails.append(f"{name}: {detail}")


# 1. No published lineup page is orphaned from the hub: every page
# directory with an index.html must be linked from the hub by its
# own slug href.
hub = (SITE / "index.html").read_text(encoding="utf-8")
pages = [d.name for d in sorted(SITE.iterdir())
         if d.is_dir() and (d / "index.html").exists()]
orphans = [s for s in pages if f'href="{s}/"' not in hub]
check("hub-no-orphans", not orphans, f"orphaned from hub: {orphans}")
check("hub-hiw-anchor", 'href="how-it-works/"' in hub,
      "hub carries no anchor to how-it-works/")

# 2. The cure is at the source in the hub refresh path: restructure()
# treats the how-it-works section as producer-owned (dropped before
# the section surgery, like needs-attention) and main() re-injects it
# guarded on the ANCHOR, not the section id (the id alone survived
# the regression as a dangling opening tag and defeated the old
# guard).
src = (SITE / "refresh_hub.py").read_text(encoding="utf-8")
check("refresh-strips-hiw",
      re.search(r"re\.sub\(r'<section id=\"how-it-works-link\">", src)
      is not None,
      "restructure() does not strip the producer-owned HIW section")
check("refresh-guard-on-anchor",
      'if \'href="how-it-works/"\' not in out:' in src,
      "main() guard is not keyed on the how-it-works anchor href")

# 3. Correlation Web renders a pairs index on load from its own
# data: every name on record, with its closest match, so every
# producer identity (latest_rows is drawn from this data) has a
# rendered surface a NEW badge can attach to.
cw = (SITE / "correlation-web" / "index.html").read_text(encoding="utf-8")
check("corrweb-pairs-index", 'id="pairsindex"' in cw
      and "function renderPairsIndex" in cw,
      "correlation-web has no on-load pairs index renderer")
check("corrweb-pairs-source", "DATA.symbols" in cw and "DATA.twins" in cw,
      "pairs index is not built from the page's own data")

if fails:
    print("FAIL test_close_cure:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print(f"PASS test_close_cure ({len(pages)} hub pages, 0 orphans)")
