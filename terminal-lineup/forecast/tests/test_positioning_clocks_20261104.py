"""Blockers for MAP-SESSION-DIX-20261104 and DARKPRINTS-FEED-CLOCK-20261104.

The positioning family carries two clocks: the Board/feed session
and the dark reading's own session (the FINRA file lags one session
by publication). Two gates compared them as if they were one clock
and refused every coherent evening:

- refresh_morning_map took the page session from the feed's
  as_of_session before the card's dix_date, so the Map claimed a
  session its card did not carry and Gamma Ladder and Agent Debate
  (gated on the card session) refused to publish.
- refresh_darkprints required the feed's as_of_session to equal
  the dark session exactly; same-day post-close Board publishing
  makes the feed exactly one session ahead every evening.

Fail direction: on the pre-cure tree, refresh_darkprints has no
_next_session helper (AttributeError) and the morning map source
carries the feed-first session line (assertion fails).
"""
import os
import sys

sys.path.insert(0, "site")
sys.path.insert(0, "forecast")
import refresh_darkprints as dp

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "site")


def test_next_session_weekday():
    assert dp._next_session("2026-11-02") == "2026-11-03"


def test_next_session_skips_weekend():
    # Friday 2026-10-30 -> Monday 2026-11-02
    assert dp._next_session("2026-10-30") == "2026-11-02"


def test_morning_map_session_comes_from_the_card():
    src = open(os.path.join(SITE, "refresh_morning_map.py"),
               encoding="utf-8").read()
    cured = 'session = card_doc.get("dix_date") or feed_doc.get("as_of_session")'
    assert cured in src
    broken = 'session = feed_doc.get("as_of_session") or card_doc.get("dix_date")'
    assert broken not in src


if __name__ == "__main__":
    test_next_session_weekday()
    test_next_session_skips_weekend()
    test_morning_map_session_comes_from_the_card()
    print("PASS")
