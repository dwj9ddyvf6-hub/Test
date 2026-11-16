"""UNJOURNALED-WRITER guard blockers (NO-PARTIALS DRIVE
2026-11-11): the 2026-11-02 flatten burst (19 broker orders,
coid family v3-aster_etf_drift1_m150-2026-10-1436-<n>-<SYMBOL>-
sell) has no generating code path in this tree, proven by
repeated census (2026-11-08 and this drive's forensic re-grep):
exactly one production .submit_order( call site exists, inside
the journaled dispatcher; PaperDoor.cancel_order has zero
production callers; no /v2/orders literal exists outside
broker.py. The historical writer is therefore out-of-tree
(evidence-bounded: an interactive or one-off route over the
shared paper credential; v2's AlpacaDoor is the reachable
alternate door).

The remaining cure is a gate guard, so a future direct writer
fails the gate the day it lands instead of being discovered by
reconcile: this blocker walks desk3 production sources and holds
the census as an invariant.

Fail direction: if any new production call site appears, the
counts below break and the gate goes red.
"""
import os, re, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "desk3")


def _sources():
    for dirpath, _dirs, files in os.walk(ROOT):
        if "__pycache__" in dirpath:
            continue
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


class TestSingleJournaledWriter(unittest.TestCase):

    def test_exactly_one_submit_site_outside_broker(self):
        sites = []
        for path in _sources():
            if os.path.basename(path) == "broker.py":
                continue
            text = open(path, encoding="utf-8").read()
            for m in re.finditer(r"\.submit_order\s*\(", text):
                sites.append((os.path.relpath(path, ROOT),
                              text[:m.start()].count("\n") + 1))
        self.assertEqual(len(sites), 1, sites)
        self.assertEqual(sites[0][0], "dispatcher.py")

    def test_no_cancel_order_callers_in_production(self):
        offenders = []
        for path in _sources():
            if os.path.basename(path) == "broker.py":
                continue
            text = open(path, encoding="utf-8").read()
            if re.search(r"\.cancel_order\s*\(", text):
                offenders.append(os.path.relpath(path, ROOT))
        self.assertEqual(offenders, [])

    def test_no_orders_endpoint_literal_outside_broker(self):
        offenders = []
        for path in _sources():
            if os.path.basename(path) == "broker.py":
                continue
            if "/v2/orders" in open(path, encoding="utf-8").read():
                offenders.append(os.path.relpath(path, ROOT))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
