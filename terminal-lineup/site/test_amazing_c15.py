#!/usr/bin/env python3
"""Regression blocker: DEFECT-C15-IDENTITY (AMAZING Build, 2026-11-02).

The R3 badge renderer diffed EVERY rendered table first cell and ranker
label against baseline_rows only. The producer (build_prior_rows.py)
extracts identities from data.json with a different walk, so stat, date
and prose labels that were never producer identities got NEW badges
(false positives: desk account labels, market-mood gauge labels,
fear-day historical dates), and a removal-only page (pin-or-escape)
badged rows that were not new.

Cure: a rendered label may badge only when it is a producer identity
of the CURRENT session (present in latest_rows) AND absent from the
prior-session baseline (baseline_rows). This test fails on the old
renderer (no latest-set containment check) and passes on the cured one.
It also simulates the cured rule against the recon cases.
"""
import re
from pathlib import Path

GROK = Path(__file__).with_name("grok.js")


def badge_rule(lab, prior, latest):
    """Mirror of the cured renderer rule."""
    return bool(lab) and lab in latest and lab not in prior


def main():
    src = GROK.read_text()
    fn = src[src.index("function newBadgesR2"):src.index("function newBadgesR2") + 1600]
    assert "latest_rows" in fn, "renderer never consults latest_rows: identity match unproven"
    assert re.search(r"latest\[lab\]", fn), "renderer does not require latest-set containment"
    # Recon false positives: labels never extracted by the producer.
    prior = {"AAPL", "MSFT"}
    latest = {"AAPL", "MSFT", "NVDA"}
    for lab in ("buying power", "equity", "2026-10-30", "Total entries"):
        assert not badge_rule(lab, prior, latest), lab
    # Removal-only page: a rendered row absent from latest must not badge.
    assert not badge_rule("OLDROW", prior, latest)
    # True positive: a producer identity new this session badges.
    assert badge_rule("NVDA", prior, latest)
    # Continuing row does not badge.
    assert not badge_rule("AAPL", prior, latest)
    print("PASS test_amazing_c15: badge rule requires latest-set containment and baseline absence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
