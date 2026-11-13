#!/usr/bin/env python3
"""Regression blocker for TAPE-JOINED-STAMP-20261113.

Defect (2026-11-12, all session): the tape family run failed
whenever Agent Debate's headline session (the scored session it
debates, produced by the Second Opinion in the 19:00 tools lane)
stood behind the freshest tape session, which is its designed
state for the whole trading day and every early evening. The
intraday lane stamped FAILED every five minutes through the
2026-11-12 session (261 FAILED lines in lane_freshness.log for
the day) and the 17:30 tape run failed on the same row, though
the consumer had refreshed, joined its tape figures like for
like at its source's generation, and stamped itself stale
truthfully at write time; it read current only after the tools
lane's late re-run. The orchestrator judged a joined consumer
by a headline-session equality it recomputed, overwriting the
consumer's write-time stamp.

Cure: joined_verdict in tape_family_run.py. The family verdict
for a joined consumer is the consumer's own write-time
tape_freshness stamp: current stands; a first stale stamp for
the tape session is deferred to the tools lane re-run (page
stays stamped stale, deferral recorded on the stamp, run does
not fail); a spent deferral, a failed refresh, or a missing or
foreign stamp fails the run as before.

Fail direction: against the pre-cure module this test errors
(joined_verdict did not exist; the family's only joined rule
was headline equality, under which the deferred case below was
stamped stale and failed the run).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tape_family_run as tf


def stamp(state, tape="2026-11-12", deferred_for=None):
    doc = {"tape_session": tape, "consumer_session": "2026-11-11",
           "state": state, "note": "consumer's own write-time stamp"}
    if deferred_for:
        doc["family_deferred_for"] = deferred_for
    return doc


class JoinedVerdictTests(unittest.TestCase):
    def test_current_stamp_stands(self):
        self.assertEqual(
            tf.joined_verdict(0, stamp("current"), "2026-11-12"),
            "current")

    def test_first_stale_is_deferred_not_failed(self):
        # The 2026-11-12 evening case: refresh succeeded, joined
        # like for like, stamped stale at write time because its
        # cross-family producer had not run yet.
        self.assertEqual(
            tf.joined_verdict(0, stamp("stale"), "2026-11-12"),
            "deferred")

    def test_spent_deferral_fails(self):
        self.assertEqual(
            tf.joined_verdict(
                0, stamp("stale", deferred_for="2026-11-12"),
                "2026-11-12"),
            "stale_fail")

    def test_deferral_for_an_older_tape_session_does_not_block(self):
        self.assertEqual(
            tf.joined_verdict(
                0, stamp("stale", deferred_for="2026-11-11"),
                "2026-11-12"),
            "deferred")

    def test_failed_refresh_fails(self):
        self.assertEqual(
            tf.joined_verdict(1, stamp("current"), "2026-11-12"),
            "stale_fail")

    def test_missing_stamp_fails(self):
        self.assertEqual(
            tf.joined_verdict(0, None, "2026-11-12"), "stale_fail")

    def test_foreign_tape_session_fails(self):
        self.assertEqual(
            tf.joined_verdict(0, stamp("current", tape="2026-11-11"),
                              "2026-11-12"),
            "stale_fail")


if __name__ == "__main__":
    unittest.main()
