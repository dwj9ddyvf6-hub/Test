#!/usr/bin/env python3
"""Tests for claim_ledger.py (ADOPT A5)."""
import os, sys, unittest
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_ledger

REF = date(2026, 11, 2)


def src(sid, key, authority="primary"):
    return {"source_id": sid, "authority": authority, "independence_key": key}


def entry(**kw):
    base = {"claim_id": "c1", "statement": "X holds.", "locations": ["p.md"],
            "supporting": [], "contradicting": [], "risk": "ordinary",
            "assessment": "provisional", "refresh_due": "2027-01-01"}
    base.update(kw)
    return base


class ClaimLedgerTest(unittest.TestCase):
    def test_syndicated_copies_share_key_fail_high_risk(self):
        e = entry(risk="high", assessment="accepted",
                  supporting=[src("a", "wire"), src("b", "wire"), src("c", "wire")])
        errors, _ = claim_ledger.validate_ledger({"entries": [e]}, reference=REF)
        self.assertTrue(any("independence_keys" in x for x in errors))

    def test_high_risk_two_independent_keys_passes(self):
        e = entry(risk="high", assessment="accepted",
                  supporting=[src("a", "wire"), src("b", "filing")])
        errors, _ = claim_ledger.validate_ledger({"entries": [e]}, reference=REF)
        self.assertEqual(errors, [])

    def test_past_refresh_due_reported_stale_by_computation(self):
        e = entry(refresh_due="2026-01-01")
        errors, warnings = claim_ledger.validate_ledger({"entries": [e]}, reference=REF)
        self.assertEqual(errors, [])
        self.assertTrue(any("STALE" in w for w in warnings))
        self.assertNotIn("stale", e)  # staleness is computed, never stored

    def test_unsupported_entry_validates_clean(self):
        e = entry(assessment="unsupported")
        errors, warnings = claim_ledger.validate_ledger({"entries": [e]}, reference=REF)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_accepted_without_fresh_source_fails(self):
        e = entry(assessment="accepted",
                  supporting=[src("a", "k", authority="synthetic")])
        errors, _ = claim_ledger.validate_ledger({"entries": [e]}, reference=REF)
        self.assertTrue(any("fresh, active, non-synthetic" in x for x in errors))

    def test_contradiction_must_be_contested(self):
        e = entry(assessment="accepted", supporting=[src("a", "k1")],
                  contradicting=[src("b", "k2")])
        errors, _ = claim_ledger.validate_ledger({"entries": [e]}, reference=REF)
        self.assertTrue(any("contested" in x for x in errors))


if __name__ == "__main__":
    unittest.main()
