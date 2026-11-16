"""SLEEVE-SURFACE-20261031 blockers: feed must express every roster sleeve exactly once, grouped, with declared essentials."""
import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.terminal import build_feed, sleeve_family, cadence_label, declared_instrument

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _roll_and_meta():
    cfg = json.load(open(os.path.join(ROOT, "config/sleeves.json")))
    health_path = os.path.join(ROOT, "state/health.json")
    if not os.path.exists(health_path):
        # The census join is against LIVE health state (state/ is
        # not tracked), which a code-only export structurally cannot
        # carry. Skip by name there; on the live tree the join runs
        # at full strength. (Clean-export cure, 2026-11-08: this
        # absence previously surfaced as 5 errors.)
        raise unittest.SkipTest(
            "live health state absent (code-only export)")
    health = json.load(open(health_path))
    roll = {"generated_at": health.get("generated_at"), "cycle_id": "fixture",
            "snapshot_hash": "fixture", "producer_errors": health.get("producer_errors", {}),
            "sleeves": health["sleeves"]}
    meta = {}
    for r in cfg["sleeves"]:
        p = r.get("params") or {}
        meta[r["id"]] = {"slice_usd": float(r["slice"]["capital_usd"]),
                         "parked": bool(r.get("parked")), "cadence_s": r.get("cadence_s"),
                         "session": r.get("session"), "inputs": r.get("inputs") or [],
                         "symbol": p.get("symbol"), "declared_family": p.get("family"),
                         "parked_reason": p.get("parked_reason")}
    return cfg, health, roll, meta

class TestSleeveSurface(unittest.TestCase):
    def test_count_equals_roster_and_names_exactly_once(self):
        cfg, health, roll, meta = _roll_and_meta()
        feed = build_feed(roll, meta)
        names = [r["name"] for r in feed["strategies"]]
        roster = [r["id"] for r in cfg["sleeves"]]
        self.assertEqual(len(names), len(roster))
        self.assertEqual(sorted(names), sorted(roster))
        self.assertEqual(len(names), len(set(names)), "duplicate sleeve on surface")
        self.assertEqual(feed["summary"]["strategies_total"], len(roster))

    def test_census_matches_health_join(self):
        cfg, health, roll, meta = _roll_and_meta()
        feed = build_feed(roll, meta)
        from collections import Counter
        c = Counter(v["state"] for v in health["sleeves"].values())
        # CENSUS-TAXONOMY-20261116: health state is the data axis
        # (FED / UNFED / PARKED, registry-fed or not); feed status is
        # the evaluation axis. A FED sleeve is Ready only when its
        # last evaluation was ok: a FED sleeve whose evaluation
        # errored or wedged is Needs attention, by name (terminal
        # _status_for; cycle.py writes state and status as separate
        # fields, verdict wedged on a pool timeout). The 2026-10-31
        # form of this test equated ready with the FED census and
        # failed whenever a FED sleeve wedged (gate receipts
        # 20261116T121856Z-11661 and 20261116T123838Z-16361: ready
        # 375 vs FED 376, saty_gpt_v02 FED with status wedged).
        # The census join stays at full strength below: every FED
        # sleeve is accounted for exactly once, as Ready or as
        # Needs attention, and no sleeve is lost or double-counted.
        def expected_status(sid, entry):
            if meta[sid]["parked"]:
                return "Paused"
            if entry.get("state") == "UNFED":
                return "Waiting for data"
            if entry.get("status") in ("error", "wedged") or \
                    entry.get("verdict") == "wedged":
                return "Needs attention"
            return "Ready"
        by = {r["name"]: r for r in feed["strategies"]}
        self.assertEqual(sorted(by), sorted(health["sleeves"]),
                         "join lost or invented a sleeve")
        self.assertEqual(len(by), len(feed["strategies"]),
                         "join double-counted a sleeve")
        expected = Counter(expected_status(sid, entry)
                           for sid, entry in health["sleeves"].items())
        for sid, entry in health["sleeves"].items():
            self.assertEqual(by[sid]["status"], expected_status(sid, entry),
                             f"{sid}: FED-and-wedged must never read Ready")
        self.assertEqual(feed["summary"]["ready"], expected["Ready"])
        self.assertEqual(feed["summary"]["needs_attention"],
                         expected["Needs attention"])
        self.assertEqual(feed["summary"]["ready"] +
                         feed["summary"]["needs_attention"], c["FED"])
        self.assertEqual(feed["summary"]["waiting_for_data"], c["UNFED"])
        self.assertEqual(feed["summary"]["waiting_for_data"],
                         expected["Waiting for data"])
        self.assertEqual(feed["summary"]["paused"], c["PARKED"])
        self.assertEqual(feed["summary"]["paused"], expected["Paused"])
        self.assertEqual(feed["summary"]["ready"] +
                         feed["summary"]["needs_attention"] +
                         feed["summary"]["waiting_for_data"] +
                         feed["summary"]["paused"],
                         feed["summary"]["strategies_total"])
        self.assertEqual(feed["summary"]["strategies_total"],
                         len(health["sleeves"]))
        plain = {"FED": "Data arriving", "UNFED": "Data missing", "PARKED": "Paused"}
        for r in feed["strategies"]:
            self.assertEqual(r["feed_state"], plain[health["sleeves"][r["name"]]["state"]])

    def test_wedged_fed_sleeve_is_needs_attention_by_name(self):
        # CENSUS-TAXONOMY-20261116: deterministic form of the census
        # pin, so it bites even on a live health roll where no sleeve
        # happens to be wedged at gate time. Fixture copies only:
        # saty_gpt_v02 (the sleeve that wedged in the 2026-11-16
        # receipts, error timeout>30.0s, orders_placed 0) is first
        # set FED-and-ok, then FED-and-wedged, in copied rolls.
        cfg, health, roll, meta = _roll_and_meta()
        sid = "saty_gpt_v02"
        self.assertIn(sid, roll["sleeves"])
        roll["sleeves"][sid] = {"state": "FED", "status": "ok",
                                "orders_placed": 0}
        base = build_feed(roll, meta)
        base_row = [r for r in base["strategies"] if r["name"] == sid][0]
        self.assertEqual(base_row["status"], "Ready")
        roll["sleeves"][sid] = {"state": "FED", "status": "wedged",
                                "verdict": "wedged",
                                "error": "timeout>30.0s",
                                "orders_placed": 0}
        feed = build_feed(roll, meta)
        row = [r for r in feed["strategies"] if r["name"] == sid][0]
        self.assertEqual(row["status"], "Needs attention")
        self.assertEqual(row["feed_state"], "Data arriving")
        self.assertEqual(feed["summary"]["ready"],
                         base["summary"]["ready"] - 1)
        self.assertEqual(feed["summary"]["needs_attention"],
                         base["summary"]["needs_attention"] + 1)
        from collections import Counter
        c = Counter(v["state"] for v in roll["sleeves"].values())
        self.assertEqual(feed["summary"]["ready"] +
                         feed["summary"]["needs_attention"], c["FED"])
        self.assertEqual(feed["summary"]["strategies_total"],
                         base["summary"]["strategies_total"])
        self.assertEqual(len(feed["strategies"]), len(base["strategies"]))

    def test_groups_sum_to_roster_and_family_derived(self):
        cfg, health, roll, meta = _roll_and_meta()
        feed = build_feed(roll, meta)
        self.assertEqual(sum(g["total"] for g in feed["sleeve_groups"]), len(cfg["sleeves"]))
        for r in feed["strategies"]:
            self.assertEqual(r["family"], sleeve_family(r["name"]))
            self.assertEqual(r["family_source"], "derived_from_id")

    def test_declared_essentials_present_sparse_omitted(self):
        cfg, health, roll, meta = _roll_and_meta()
        feed = build_feed(roll, meta)
        by = {r["name"]: r for r in feed["strategies"]}
        for row in cfg["sleeves"]:
            r = by[row["id"]]
            self.assertEqual(r["cadence_s"], row["cadence_s"])
            self.assertEqual(r["session"], row["session"])
            self.assertEqual(r["inputs"], row["inputs"])
        # sparse: instrument only where declared
        self.assertEqual(by["em_1587"]["instrument"], "VIX (1Day)")
        self.assertNotIn("instrument", by["1d"])
        enj = [r for r in feed["strategies"] if r.get("declared_family")]
        self.assertTrue(enj and all(r["instrument"] == "ENJUSDT" for r in enj))

    def test_helpers(self):
        self.assertEqual(cadence_label(300), "every 5 minutes")
        self.assertEqual(cadence_label(86400), "daily")
        self.assertIsNone(declared_instrument(["bars:*:1Day"]))
        self.assertEqual(declared_instrument(["bars:QQQ:1Hour"]), "QQQ (1Hour)")

    def test_page_renders_grouped_foliotend_surface(self):
        html = open(os.path.join(ROOT, "terminal/index.html")).read()
        for token in ("#123247", "#0e3e52", "#edf6f5", "#098979", "#b2595d", "20px"):
            self.assertIn(token, html)
        self.assertIn("sleeve_groups", html + open(os.path.join(ROOT, "desk3/terminal.py")).read())
        self.assertIn('id="groups"', html)

    def test_status_flip_flows_through_regeneration(self):
        # Fixture copy only: flip one FED sleeve to UNFED in a copied roll.
        cfg, health, roll, meta = _roll_and_meta()
        sid = sorted(k for k, v in roll["sleeves"].items() if v["state"] == "FED")[0]
        roll["sleeves"][sid] = {"state": "UNFED", "missing": ["bars"], "stale": []}
        feed = build_feed(roll, meta)
        row = [r for r in feed["strategies"] if r["name"] == sid][0]
        self.assertEqual(row["status"], "Waiting for data")
        self.assertEqual(row["feed_state"], "Data missing")
        self.assertEqual(row["missing"], ["bars"])

if __name__ == "__main__":
    unittest.main()
