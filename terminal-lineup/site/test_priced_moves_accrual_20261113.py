#!/usr/bin/env python3
"""Regression blocker for PRICED-MOVES-ACCRUAL-20261113.

Defect (2026-11-12 tools run): refresh_earningsdistribution.py
failed closed with "a priced move appeared for ADIG in the
published calendar without a raw source". ADIG's move (27.6
percent for its 2026-11-12 report) had been priced by
priced_moves.py and published by the earnings calendar from
the priced move record, the estate's raw source; but the
record was rebuilt at 2026-11-13T00:14Z holding only the
forward 14-day window, so the moment ADIG reported, its raw
quotes rotated out of the record and the recount had no source
to recount from. The producer destroyed its own source.

Cures:
- priced_moves.merge_retained: entries accrue across runs. A
  past report's entry is carried forward (its raw quotes stay
  on record); a same-date entry whose re-pricing failed is
  carried; a superseded (re-dated) or window-expired future
  entry is dropped.
- refresh_earningsdistribution.published_move_verdict: a
  published move that recounts exactly stands; one whose raw
  entry rotated out before the accrual cure (report date
  before the record's rebuild date, no entry or only a later
  report's entry on record) is "rotated": refused honestly,
  named in the leg's output, never used, and the run does not
  fail; anything else is "unsourced" and still fails closed.

Fail direction: against the pre-cure modules both helpers are
absent (the record was a plain overwrite and the leg's only
verdict was fail), so these tests error there; they pass on
the cured code.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import priced_moves as pm
import refresh_earningsdistribution as ed


def entry(date, pct=10.0):
    return {"report_date": date, "priced_move_pct": pct}


class MergeRetainedTests(unittest.TestCase):
    def test_past_report_entry_is_retained(self):
        names, n = pm.merge_retained(
            {}, {"ADIG": entry("2026-11-12", 27.6)}, {},
            "2026-11-13")
        self.assertEqual(n, 1)
        self.assertEqual(names["ADIG"]["priced_move_pct"], 27.6)
        self.assertTrue(names["ADIG"]["retained_from_prior_run"])

    def test_same_date_failed_repricing_is_retained(self):
        names, n = pm.merge_retained(
            {}, {"XYZ": entry("2026-11-20")},
            {"XYZ": "2026-11-20"}, "2026-11-13")
        self.assertEqual(n, 1)
        self.assertIn("XYZ", names)

    def test_fresh_pricing_wins(self):
        fresh = {"XYZ": entry("2026-11-20", 9.0)}
        names, n = pm.merge_retained(
            dict(fresh), {"XYZ": entry("2026-11-20", 8.0)},
            {"XYZ": "2026-11-20"}, "2026-11-13")
        self.assertEqual(n, 0)
        self.assertEqual(names["XYZ"]["priced_move_pct"], 9.0)

    def test_redated_future_entry_is_dropped(self):
        names, n = pm.merge_retained(
            {}, {"XYZ": entry("2026-11-20")},
            {"XYZ": "2026-11-27"}, "2026-11-13")
        self.assertEqual(n, 0)
        self.assertNotIn("XYZ", names)

    def test_window_expired_future_entry_is_dropped(self):
        names, n = pm.merge_retained(
            {}, {"XYZ": entry("2026-12-20")}, {}, "2026-11-13")
        self.assertEqual(n, 0)
        self.assertNotIn("XYZ", names)


class PublishedMoveVerdictTests(unittest.TestCase):
    def test_exact_recount_matches(self):
        self.assertEqual(
            ed.published_move_verdict(
                "27.6%", entry("2026-11-12", 27.6),
                "2026-11-12", "2026-11-13"),
            "matches")

    def test_adig_case_is_rotated_not_unsourced(self):
        # Published 27.6% for 2026-11-12; the record rebuilt
        # 2026-11-13 carries no ADIG entry at all.
        self.assertEqual(
            ed.published_move_verdict(
                "27.6%", None, "2026-11-12", "2026-11-13"),
            "rotated")

    def test_later_report_entry_still_rotated(self):
        self.assertEqual(
            ed.published_move_verdict(
                "27.6%", entry("2027-02-11", 9.0),
                "2026-11-12", "2026-11-13"),
            "rotated")

    def test_upcoming_name_without_source_is_unsourced(self):
        self.assertEqual(
            ed.published_move_verdict(
                "5.0%", None, "2026-11-20", "2026-11-13"),
            "unsourced")

    def test_wrong_figure_is_unsourced(self):
        self.assertEqual(
            ed.published_move_verdict(
                "99.9%", entry("2026-11-12", 27.6),
                "2026-11-12", "2026-11-13"),
            "unsourced")


if __name__ == "__main__":
    unittest.main()
