#!/usr/bin/env python3
"""Regression blocker: SIGNALFEED-GRADED-STATE-20261108.

The Signal Feed used to derive each Record map card's graded
state from grading-session arithmetic (graded when a card's
grading session is older than the freshest on record). The
premise failed on 2026-11-08: the 2026-11-05 group (grading
session 2026-11-06) still had no grade rows while a fresher
group existed, so the derivation counted 30 graded against
the Record's own 27 and the feed refused a sound record.

The cure moves the state to the producer: refresh_record.py
stamps each card's "graded" from the grading summary's own
grade rows and refuses at the producer when the stamped count
disagrees with the summary's count; refresh_signalfeed.py
reads the stamp and refuses a card that carries none.

Leg A pins the contract in both sources (a full producer
fixture harness is impractical: the Record build needs the
whole scorecard summary and ledger). Leg B pins the live
artifacts the cure produced: every published map card
carries a boolean stamp and the stamped count equals the
Record's own graded count.

Fail-first: on the pre-cure tree Leg A fails (no stamp in
the producer, the session derivation still in the consumer)
and Leg B fails (cards carry no graded key).

Run standalone or under pytest.
"""
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent


def test_producer_stamps_and_self_checks():
    src = (SITE / "refresh_record.py").read_text(encoding="utf-8")
    assert 'c["graded"] = c["published_at_utc"] in graded_ts' in src
    assert "n_stamped_graded != " in src
    assert "cards_graded" in src


def test_consumer_reads_the_stamp_not_sessions():
    src = (SITE / "refresh_signalfeed.py").read_text(
        encoding="utf-8")
    assert 'card.get("graded") is True' in src
    assert "carries no graded state" in src
    assert "freshest_grading" not in src


def test_published_record_carries_the_stamp():
    rec = json.load(open(SITE / "record" / "data.json",
                         encoding="utf-8"))
    map_part = rec.get("map") or {}
    cards = [c for g in map_part.get("groups") or []
             for c in g.get("cards") or []]
    assert cards, "no map cards on the published record"
    assert all(isinstance(c.get("graded"), bool) for c in cards)
    stamped = sum(1 for c in cards if c["graded"] is True)
    assert stamped == map_part.get("cards_graded")


def main() -> int:
    for t in (test_producer_stamps_and_self_checks,
              test_consumer_reads_the_stamp_not_sessions,
              test_published_record_carries_the_stamp):
        t()
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
