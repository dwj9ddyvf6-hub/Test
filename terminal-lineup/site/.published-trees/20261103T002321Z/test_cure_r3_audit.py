#!/usr/bin/env python3
"""Regression blockers for the R3-AUDIT cures (2026-11-02).

Root causes proven by Chromium repro (R3-AUDIT rows 1, 2, 3):
- Master grammar() inserted the sentence with
  c.insertBefore(s, h.nextSibling) where h is often NESTED inside
  the card (read cards: h3.tk inside .top). insertBefore threw, the
  exception aborted the whole forEach, and every card after the
  first nested-heading card stayed unstamped (7 of 73; lookup read
  cards created later never stamped at all).
- Both layers stamped data-gb-full / data-gb-partial without
  removing the opposite attribute, so upgraded cards carried BOTH
  stamps and every census double-counted them as partial
  (replication-wire 30 full + 27 partial of 31 cards).
- subjectFirstR2 could pick the gb-comp subject card itself as the
  "proving card" when its rows carry proving-state words
  (proving-ground: chart and proving indices coincide).

Run: python3 site/test_cure_r3_audit.py  (exit 0 = PASS)
"""
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
fails = []

master = (SITE.parent.parent / ".scratch-femto-mirror" / "combined"
          / "grok-master.js").read_text()
for needle in ["grammarCardR3", "insertAfterChildR3",
               'removeAttribute("data-gb-partial")',
               'removeAttribute("data-gb-full")']:
    if needle not in master:
        fails.append(f"grok-master.js missing R3 cure: {needle}")
seg = master[master.find("function grammarCardR3"):]
seg = seg[:seg.find("/* C18 finder")]
if "insertBefore(s, h.nextSibling)" in seg or "insertBefore(he, se.nextSibling)" in seg:
    fails.append("grok-master grammar still inserts via a nested heading's nextSibling")
if ".tk" not in seg or ".tog" not in seg:
    fails.append("grok-master grammar has no title-element fallback for heading-less cards")
obs = master[master.find("new MutationObserver"):]
if "enhance()" not in obs:
    fails.append("Master MutationObserver does not re-run the full enhance()")

grok = (SITE / "grok.js").read_text()
enh = grok[grok.find("function enhanceCardsR2"):grok.find("function stripKickerDates")]
for needle in ["insertAfterChildR3", 'removeAttribute("data-gb-partial")',
               'removeAttribute("data-gb-full")']:
    if needle not in enh and needle not in grok:
        fails.append(f"grok.js enhanceCardsR2 missing R3 cure: {needle}")
if "c.insertBefore(se, hEl.nextSibling)" in enh:
    fails.append("enhanceCardsR2 still inserts via a possibly-nested heading's nextSibling")
sf = grok[grok.find("function subjectFirstR2"):grok.find("function badgeTargetsR3")]
if "provSkipR3" not in sf:
    fails.append("subjectFirstR2 does not skip the subject component card itself (proving-ground coincidence)")

if fails:
    print("FAIL")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("PASS")
