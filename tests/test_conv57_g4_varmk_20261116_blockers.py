"""CONV57-G4-VARIATION-20261116 regression blockers.

The Tensor G4 variation aster_tensor_g4_varmk (Form C of
pass2/CONV57-G4-VARIATION-PROPOSAL.md) is rostered live beside
its parents under the variation doctrine: own id, own falsifier,
parents byte-untouched, Tensor engine untouched. These tests pin
the registration, the gate's exact semantics (including the
registration recount on the held stream: 3 of 428, not the
proposal's printed 2 — the divergence is named in the config
entry and in desk3/aster_g4_varmk.py), and the parent/engine
integrity hashes.

Fail direction: on the pre-cure tree the module, adapter, config
entry and roster row do not exist, so the registration, gate and
drive tests fail/error; the integrity pins pass both ways by
design (they pin what must NOT change).
"""
import hashlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

STREAM = os.path.join(
    os.path.expanduser("~"),
    "workspace/research_notes/alpha-hunt-chaos-20261115/pass2/"
    "firestream_work/tensor_stream.jsonl")

# Pre-cure pins (computed on HEAD 95a5326, the tree this landing
# branches from): the G4 parent engine and the Tensor native
# bridge must remain byte-identical after registration.
PARENT_SHA256 = {
    "desk3/aster_batch14.py":
        "c449c1e9af6e2cb4e53d116f29330dad874d68d6b343268ad2857"
        "09c77f1fdec",
    "desk3/tensor_native.py":
        "2906c0c3808c32e951d29235059a4fe39a6d1787011e724f91a2350"
        "519f7b7c1",
    "sleeves/saty_sol.py":
        "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416"
        "cc08962bdc",
}


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _core_row(**kw):
    row = {"native_close": 5.0, "depth60": 80.0, "ret60": 10.0,
           "vol20": 0.15, "dv20": 5_000_000.0, "atr_ratio": 1.4,
           "primaryMarkers": [], "bullishVotes": 6,
           "bearishVotes": 1}
    row.update(kw)
    return row


class TestRegistration(unittest.TestCase):
    def test_config_entry_exact(self):
        cfg = json.load(open(os.path.join(
            ROOT, "config/conversion_variations_20261115.json")))
        hits = [v for v in cfg["variations"]
                if v.get("id") == "aster_tensor_g4_varmk"]
        self.assertEqual(len(hits), 1)
        v = hits[0]
        self.assertEqual(v["conv"], "CONV-57")
        self.assertEqual(v["module"],
                         "adapters3.aster_tensor_g4_varmk")
        self.assertIn("20 resolved forward fires", v["falsifier"])
        self.assertIn("full quarter", v["falsifier"])
        self.assertIn("3 of 428", v["replay_counts"])
        self.assertIn("SATL", v["replay_counts"])

    def test_roster_row_is_live_clone_of_chassis(self):
        cfg = json.load(open(os.path.join(
            ROOT, "config/sleeves.json")))
        rows = cfg["sleeves"]
        # TOTAL-AUDIT-PIN-REBASE-20261116: struck at 388 on the
        # lane tree (387 + this registration); on main the same
        # registration lands on the 398 roster, so the pin is 399;
        # CONV123-REVIVAL-20261116 then raised it to 400.
        self.assertEqual(len(rows), 400)
        hits = [r for r in rows
                if r["id"] == "aster_tensor_g4_varmk"]
        self.assertEqual(len(hits), 1)
        row = hits[0]
        self.assertFalse(row["parked"])
        self.assertEqual(row["slice"]["capital_usd"], 10000.0)
        self.assertEqual(row["inputs"],
                         ["tensor", "bars", "positions"])
        parent = [r for r in rows
                  if r["id"] == "aster_tensor_g4_cash_all_25"][0]
        clone = dict(row)
        clone["id"] = parent["id"]
        clone["module"] = parent["module"]
        self.assertEqual(clone, parent)


class TestGate(unittest.TestCase):
    def test_proposal_qualifiers(self):
        from desk3.aster_g4_varmk import qualifies
        skyq = _core_row(native_close=3.11, ret60=161.3,
                         bullishVotes=6, bearishVotes=1,
                         atr_ratio=1.69)
        crml = _core_row(native_close=7.16, ret60=9.3,
                         bullishVotes=6, bearishVotes=1,
                         atr_ratio=1.035)
        satl = _core_row(native_close=5.73, ret60=24.3,
                         bullishVotes=7, bearishVotes=0,
                         atr_ratio=1.394)
        self.assertTrue(qualifies(skyq))
        self.assertTrue(qualifies(crml))
        self.assertTrue(qualifies(satl))

    def test_marker_forms(self):
        from desk3.aster_g4_varmk import qualifies
        # buy-green satisfies the marker element even with no
        # vote signature, and COOL does not apply (atr hot).
        self.assertTrue(qualifies(_core_row(
            primaryMarkers=["buy-green"], bullishVotes=0,
            bearishVotes=7, atr_ratio=1.72)))
        # a buy-cyan row is a buy-marker row: adjacency does not
        # apply and it is not green.
        self.assertFalse(qualifies(_core_row(
            primaryMarkers=["buy-cyan"])))
        # signature below threshold / bearish above threshold.
        self.assertFalse(qualifies(_core_row(bullishVotes=5)))
        self.assertFalse(qualifies(_core_row(bearishVotes=2)))
        # missing votes fail closed.
        self.assertFalse(qualifies(_core_row(bullishVotes=None)))

    def test_core_conjuncts_exact(self):
        from desk3.aster_g4_varmk import qualifies
        self.assertFalse(qualifies(_core_row(native_close=10.01)))
        self.assertFalse(qualifies(_core_row(depth60=69.9)))
        self.assertFalse(qualifies(_core_row(ret60=-0.1)))
        self.assertFalse(qualifies(_core_row(vol20=0.089)))
        self.assertFalse(qualifies(_core_row(dv20=1_999_999.0)))
        self.assertFalse(qualifies(_core_row(depth60=None)))

    def test_held_stream_recount(self):
        if not os.path.exists(STREAM):
            self.skipTest("held stream not on this box")
        from desk3.aster_g4_varmk import qualifies
        rows = [json.loads(l) for l in open(STREAM) if l.strip()]
        self.assertEqual(len(rows), 428)
        got = {(r["symbol"], r["week_end"])
               for r in rows if qualifies(r)}
        self.assertEqual(got, {("SKYQ", "2026-09-11"),
                               ("SATL", "2026-10-02"),
                               ("CRML", "2026-10-30")})


def _bundle(sym="SKYQ", signal_end="2026-11-13T16:00:00-05:00",
            **feat):
    f = {"native_close": 3.11, "depth60": 98.9, "ret60": 161.3,
         "vol20": 0.283, "dv20": 6_975_552.0, "atr_ratio": 1.69}
    f.update(feat)
    return {"tensor": {"tensor_analysis": {sym: {
        "features": f,
        "rep_g": {"last": {"primaryMarkers": [],
                           "bullishVotes": 6, "bearishVotes": 1}},
        "signal_end": signal_end}}}}


class TestDrive(unittest.TestCase):
    def test_entry_first_session_after_signal_week(self):
        from adapters3.aster_tensor_g4_varmk import evaluate
        view = _bundle()
        view["positions"] = []
        view["bars"] = {}
        out = evaluate(view, {"session": "2026-11-16",
                              "now": "2026-11-16T15:00:00"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["symbol"], "SKYQ")
        self.assertEqual(out[0]["qty"], int(400 // 3.11))

    def test_no_entry_on_signal_week_session_itself(self):
        from adapters3.aster_tensor_g4_varmk import evaluate
        view = _bundle()
        view["positions"] = []
        view["bars"] = {}
        out = evaluate(view, {"session": "2026-11-13",
                              "now": "2026-11-13T15:00:00"})
        self.assertEqual(out, [])

    def test_no_bundle_rows_fail_closed(self):
        from adapters3.aster_tensor_g4_varmk import evaluate
        self.assertEqual(evaluate({"positions": [], "bars": {}},
                                  {"session": "2026-11-16"}), [])
        self.assertEqual(evaluate(
            {"tensor": {}, "positions": [], "bars": {}},
            {"session": "2026-11-16"}), [])

    def test_week52_exit(self):
        from adapters3.aster_tensor_g4_varmk import evaluate
        view = {"tensor": {}, "bars": {},
                "positions": [{"symbol": "SKYQ", "qty": 10.0,
                               "avg_price": 3.0,
                               "exit_at": "2026-11-01"}]}
        out = evaluate(view, {"session": "2026-11-16",
                              "now": "2026-11-16T15:00:00"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")


class TestIntegrity(unittest.TestCase):
    def test_parent_and_pinned_files_byte_identical(self):
        for rel, pin in PARENT_SHA256.items():
            self.assertEqual(_sha(os.path.join(ROOT, rel)), pin,
                             rel)

    def test_tensor_engine_hashes_pass(self):
        sys.path.insert(0, os.path.join(ROOT, "vendor"))
        import tensor_exact
        tensor_exact.verify_engine_hashes()
        self.assertEqual(tensor_exact.ENGINE_VERSION_PINNED,
                         "v698")


if __name__ == "__main__":
    unittest.main()
