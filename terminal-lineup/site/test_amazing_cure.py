#!/usr/bin/env python3
"""Regression blockers: AMAZING-CURE (2026-11-02 night, Phase Cure).

Three defects from AMAZING-AUDIT.md, each fail-first proven:

1. DEFECT-VIXRING-NOINSERT: grok.js vixRingCard() built the VIX ring
   card with compCard(), appended the SVG and footnote to it, but never
   inserted the card into the document, so the ring never rendered
   (live vix-ring.json was correct; the rendered page had no
   .gb-vixring element and no "21.15" text). Cure: placeComp(card).

2. DEFECT-C15-CARD-TARGETS: badgeTargetsR3 selected only .gb-rkrow .id
   labels and table first cells. The changed pages render their row
   identities in other shapes the producer extraction matches:
   .vk-rname native ranked rows (reversal-wire, portfolio-builder,
   board, holly-ideas, tape-heatmap), .sym/.symbol native name spans
   (board, portfolio-builder, holly-ideas), .entry strong/.lab native
   entries (reversal-wire), chart-title headings whose rendered text
   extends the producer title after a colon (morning-map,
   strat-combos), and SVG text labels that lead with the identity
   (correlation-web). Cure: those shapes are targets, with
   first-occurrence-per-identity dedupe so a name rendered in two
   components badges once, and prefix matching only for heading/SVG
   shapes. The latest-set containment rule from
   AMAZING-C15-IDENTITY-20261102 is unchanged.

3. PARTIAL-CARDS verdict chips: .verdict elements nested in .group
   rows are status chips ("Did not hold up"), not cards; the grammar
   pass stamped them data-gb-partial and appended a footnote into the
   chip (26 on replication-wire, 10 on survivors-wire, 8 on
   odds-cards). Cure: chip-shaped verdicts (no heading/table/chart of
   their own, short text) are skipped by the grammar pass and carry
   no stamp. Also: heroFromCardR3's last-resort integer scan could
   return a bare year (a date fragment) as a card's hero figure;
   bare years are excluded there.
"""
import re
from pathlib import Path

GROK = Path(__file__).with_name("grok.js")


def main():
    src = GROK.read_text()
    fails = []

    # 1. VIX ring card must be inserted into the document.
    vix = src[src.index("function vixRingCard"):src.index("function moodStripR2")]
    if "placeComp(card)" not in vix:
        fails.append("vixRingCard never inserts its card (no placeComp(card))")
    if vix and "placeComp(card)" in vix and vix.index("placeComp(card)") < vix.index('card.appendChild(el("p", "gb-foot"'):
        fails.append("vixRingCard inserts the card before its footnote is appended")

    # 2. C15 targets must cover the native shapes, with dedupe.
    bt = src[src.index("function badgeTargetsR3"):src.index("function newBadgesR2")]
    for needle in (".vk-rname", ".sym", ".symbol", ".entry", "h2", "h3", "svg"):
        if needle not in bt:
            fails.append(f"badgeTargetsR3 missing target shape: {needle}")
    nb = src[src.index("function newBadgesR2"):src.index("function moodBandR3")]
    if "badged" not in nb:
        fails.append("newBadgesR2 has no first-occurrence-per-identity dedupe")
    if "latest[lab]" not in nb:
        fails.append("newBadgesR2 lost the latest-set containment rule")

    # 3. Verdict chips skipped by the grammar pass; no bare-year heroes.
    ec = src[src.index("function enhanceCardsR2"):src.index("function stripKickerDates")]
    if "verdict" not in ec or "gb-chip-skip" not in ec:
        fails.append("enhanceCardsR2 does not skip verdict chips")
    hero = src[src.index("function heroFromCardR3"):src.index("function insertAfterChildR3")]
    if "19|20" not in hero and "(?:19|20)" not in hero and "20\\\\d\\\\d" not in hero:
        fails.append("heroFromCardR3 does not exclude bare years")

    if fails:
        print("FAIL test_amazing_cure:")
        for f in fails:
            print(" -", f)
        return 1
    print("PASS test_amazing_cure: vix ring inserted, C15 native targets + dedupe, verdict chips skipped, no bare-year heroes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
