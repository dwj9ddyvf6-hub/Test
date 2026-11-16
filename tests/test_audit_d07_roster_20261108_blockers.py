"""AUDIT-D07 roster supersession blocker (cure 2026-11-08).

Defect: MONDAY-READINESS.md rows 7, 8, 16, 17 present a 312-sleeve
roster (63 FED / 226 UNFED / 23 PARKED) as PASS. That figure was true
on 2026-10-25; the roster has since grown (337 in config/sleeves.json
today) and the rows were never refreshed. Sole STILL-BROKEN row in
both the 2026-10-31 and 2026-11-08 weekly claims rechecks.

Cure: a dated ROSTER SUPERSESSION amendment (2026-11-08) appended to
MONDAY-READINESS.md in the file's own A9-amendment idiom (historical
rows preserved, status superseded by dated amendment), naming the
superseded rows and stating the live count. This blocker binds the
amendment's stated count to config/sleeves.json mechanically: any
future roster change turns the gate red until the amendment is
refreshed, so the stale-figure class cannot silently recur.

Fail direction proven 2026-11-08: against the pre-amendment file
(git HEAD copy in /tmp scratch) all three tests fail; against the
amended tree they pass.
"""
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _readiness():
    with open(os.path.join(HERE, "MONDAY-READINESS.md")) as fh:
        return fh.read()


def _config_count():
    with open(os.path.join(HERE, "config", "sleeves.json")) as fh:
        return len(json.load(fh)["sleeves"])


class TestAuditD07Roster(unittest.TestCase):
    def test_supersession_amendment_present(self):
        txt = _readiness()
        self.assertIn("ROSTER SUPERSESSION", txt)
        self.assertIn("AUDIT-D07", txt)

    def test_amendment_names_the_superseded_rows(self):
        txt = _readiness()
        m = re.search(r"ROSTER SUPERSESSION.*?(?=\n## |\Z)", txt, re.S)
        self.assertIsNotNone(m)
        body = m.group(0)
        for row in ("7", "8", "16", "17"):
            self.assertIn(row, body)
        self.assertIn("312", body)  # the stale figure, named as stale

    def test_amendment_count_matches_live_config(self):
        txt = _readiness()
        m = re.search(r"ROSTER SUPERSESSION.*?carries (\d+) sleeves",
                      txt, re.S)
        self.assertIsNotNone(
            m, "amendment does not state a roster count to bind")
        self.assertEqual(int(m.group(1)), _config_count(),
                         "readiness amendment roster figure is stale "
                         "against config/sleeves.json; refresh the "
                         "AUDIT-D07 amendment, never just the number")


if __name__ == "__main__":
    unittest.main()
