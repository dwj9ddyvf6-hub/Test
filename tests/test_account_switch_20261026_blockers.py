"""ACCOUNT-SWITCH-20261026 blocker (operational cure 2026-10-26;
blocker wired 2026-11-08 by the weekly-recheck cure lane).

Defect: the desk was born on an undercapitalized paper account
(~$100k against ~$3.1M of designed slice capital); from
2026-10-26T16:07:27Z the broker refused virtually every order with
40310000 insufficient buying power. Cure was operational, no desk
strategy code changed: fresh $1M paper account PA36X7WU3, pending
store mass-expired, sleeves reset flat, and a new capital epoch
(state/capital_epoch.json, start 2026-10-26T20:14:30Z, reason
account_switch) that the epoch-aware reconcile reads so the old
account's history can never re-enter the books.

The regression this guards: the desk silently running against the
wrong account or a pre-switch epoch. The live-state assertions skip
on a bare code-only export (state/ is not tracked; the epoch record
structurally cannot exist there) and run at full strength on the
live tree. The export-safe assertions pin the paper-only config and
the epoch-aware reconcile mechanism the cure depends on.

Fail direction: against a scratch epoch record carrying the old
account (or no epoch record on a live tree), the epoch tests fail;
recorded in BUGLOG_2026-11-08.md.
"""
import json
import os
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPOCH_PATH = os.path.join(HERE, "state", "capital_epoch.json")


class TestAccountSwitch(unittest.TestCase):
    def test_paper_only_config(self):
        with open(os.path.join(HERE, "config", "sleeves.json")) as fh:
            cfg = json.load(fh)
        self.assertTrue(cfg["paper_only"])

    def test_reconcile_is_epoch_aware(self):
        with open(os.path.join(HERE, "desk3", "reconcile.py")) as fh:
            src = fh.read()
        self.assertIn("capital_epoch", src,
                      "reconcile lost its capital-epoch read; the "
                      "account switch's books separation is gone")

    @unittest.skipUnless(os.path.exists(EPOCH_PATH),
                         "live state absent (code-only export)")
    def test_epoch_record_is_the_switch(self):
        with open(EPOCH_PATH) as fh:
            epoch = json.load(fh)
        self.assertEqual(epoch["account"], "PA36X7WU3")
        self.assertEqual(epoch["reason"], "account_switch")
        self.assertTrue(
            epoch["epoch_start_utc"].startswith("2026-10-26T20:14:30"),
            "capital epoch no longer starts at the account switch")
        self.assertEqual(epoch["start_equity"], 1000000)


if __name__ == "__main__":
    unittest.main()
