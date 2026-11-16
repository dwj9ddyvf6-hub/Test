"""A9-DOCS-20261026 blocker (cure landed b3253e1; blocker wired
2026-11-08 by the weekly-recheck cure lane).

Defect: MONDAY-READINESS.md and V3-REPORT.md presented A9 as OPEN
after the live fill had already closed it
(state/a9_first_fill.json, FILLED_READ_BACK 2026-10-26T15:39:25Z).
Cure: dated STATUS AMENDMENT appended to both docs recording A9
CLOSED with the full proof citation; historical narrative preserved.

This blocker is the regression guard the docs cure never had: if
either amendment is lost (bad merge, doc rewrite), the gate goes
red. Source-assertion by design: the cure is documentary, so the
assertion is over the documents themselves, including the exact
client_order_id the amendment cites.

Fail direction proven 2026-11-08: against the pre-cure docs
(git show b3253e1^:MONDAY-READINESS.md / V3-REPORT.md in /tmp
scratch) the tests fail; against HEAD they pass.
"""
import os
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COID = ("v3-aster_etf_leader1_m150-aster_etf_leader1_m150-"
        "20261026T151808-4")


class TestA9DocsAmendments(unittest.TestCase):
    def _doc(self, name):
        with open(os.path.join(HERE, name)) as fh:
            return fh.read()

    def test_monday_readiness_amendment(self):
        txt = self._doc("MONDAY-READINESS.md")
        self.assertIn("STATUS AMENDMENT", txt)
        self.assertIn("A9 is CLOSED", txt)
        self.assertIn(COID, txt)
        self.assertIn("FILLED_READ_BACK", txt)

    def test_v3_report_amendment(self):
        txt = self._doc("V3-REPORT.md")
        self.assertIn("STATUS AMENDMENT", txt)
        self.assertIn("A9 is CLOSED", txt)
        self.assertIn(COID, txt)


if __name__ == "__main__":
    unittest.main()
