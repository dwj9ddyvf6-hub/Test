"""Blockers REBALANCE-POLICY-20261031 + REBALANCE-ENFORCE-20261031:
rebalance policy as a first-class object, enforced for exactly the
dimensions that declare concrete values.

Audit (research_notes/quants-mechanisms-steal-20261031/AUDIT.md
item 6): no RebalancePolicy object existed; grep for
drift_threshold / partial_rebalance / tracking_error / turnover
budget across desk code returned no hits. The steal pass landed
the descriptive object with enforcement pinned to
"declared_not_enforced" (ESCALATED for an owner ruling).

Owner ruling 2026-10-31 authorized enforcing the values ALREADY
DECLARED. Census at enforcement time: drift_threshold,
tracking_error_threshold and max_annual_turnover are None on
336/336 config rows and on all three book declarations, so those
dimensions have NO declared value and stay declared_not_enforced
by name; inventing one is not authorized and the contract object
refuses to claim them enforced. Concrete declared values, and
what enforces them:

  - frequency: aster_etf per-spec MONTHLY / BUY_HOLD, enforced
    in desk3/aster_etf.evaluate (BUY_HOLD with holdings returns
    no intents; MONTHLY holdings that entered in the current
    month return no intents); momentum_rotation weekly, enforced
    by the delegated strategy's rebalance_due (REBALANCE_DAYS=7)
    in its signal path; ts_momentum_decile monthly, enforced by
    the monthly gate at its loaded wrapper
    (adapters3/ts_momentum_decile._monthly_rebalance_suppressed,
    aster MONTHLY semantics: initial allocation and a new entry
    month allowed, same-month suppressed).
  - partial_rebalance (aster only, True): delta-only trading in
    evaluate (buy target-held, sell held-target), never a full
    re-buy of the target.
  - signal_change_rebalance: False on aster/ts (an intra-period
    signal change cannot rebalance: the same frequency gates
    suppress it), True on momentum (when the weekly gate is due,
    the book rebalances on its rank change).

These tests fail on the descriptive-only tree (enforcement pinned
declared_not_enforced, no enforced_dimensions, no ts monthly gate)
and pass on the enforced tree.
"""
import hashlib
import importlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DEFAULT_BLOCK = {
    "frequency": "signal_driven",
    "drift_threshold": None,
    "drift_type": None,
    "partial_rebalance": False,
    "tracking_error_threshold": None,
    "tracking_error_window_days": None,
    "max_annual_turnover": None,
    "signal_change_rebalance": True,
    "execution_timing": "on_evaluation",
    "enforcement": "declared_not_enforced",
    "status": "ESCALATED_FOR_RULING",
    "enforced_dimensions": [],
}

ASTER_DIMS = ["frequency", "partial_rebalance", "signal_change_rebalance"]
BOOK_DIMS = ["frequency", "signal_change_rebalance"]
DECLARED_ONLY = ["drift_threshold", "tracking_error_threshold",
                 "max_annual_turnover"]
ENFORCED_IDS = {
    "aster_etf_leader1_m150", "aster_etf_qld_buy_hold",
    "aster_etf_qld_monthly", "aster_etf_qqq_buy_hold",
    "aster_etf_qqq_monthly_c098", "aster_etf_qqq_monthly_m150",
    "aster_etf_qqq_qld_buy_hold", "aster_etf_qqq_qld_monthly",
    "aster_etf_smh_hold_c098", "aster_etf_smh_hold_m150",
    "momentum_rotation", "ts_momentum_decile",
}


class TestRebalancePolicyContract(unittest.TestCase):
    def test_default_object_is_explicit_and_declares_absence(self):
        from desk3.contract import RebalancePolicy
        p = RebalancePolicy()
        self.assertEqual(p.frequency, "signal_driven")
        self.assertIsNone(p.drift_threshold)
        self.assertIsNone(p.drift_type)
        self.assertIs(p.partial_rebalance, False)
        self.assertIsNone(p.tracking_error_threshold)
        self.assertIsNone(p.tracking_error_window_days)
        self.assertIsNone(p.max_annual_turnover)
        self.assertEqual(p.enforcement, "declared_not_enforced")
        self.assertEqual(p.status, "ESCALATED_FOR_RULING")
        self.assertEqual(p.enforced_dimensions, ())
        self.assertEqual(p.to_dict(), DEFAULT_BLOCK)

    def test_pinned_port_copies_stay_untouched(self):
        digests = set()
        for rel in ("core/sleeve.py", "desk3/vendor/core/sleeve.py"):
            with open(os.path.join(ROOT, rel), "rb") as fh:
                data = fh.read()
            digests.add(hashlib.md5(data).hexdigest())
            self.assertNotIn(b"RebalancePolicy", data, rel)
        self.assertEqual(len(digests), 1)
        with open(os.path.join(ROOT, "desk3/contract.py"), "rb") as fh:
            self.assertIn(b"RebalancePolicy", fh.read())

    def test_sleeve_config_carries_policy_by_default(self):
        from desk3.contract import RebalancePolicy, SleeveConfig
        cfg = SleeveConfig(sleeve_id="x", cadence_s=60)
        self.assertEqual(cfg.rebalance, RebalancePolicy())
        from desk3.contract import _describe_config
        self.assertEqual(
            _describe_config(cfg)["rebalance_policy"], DEFAULT_BLOCK)

    def test_validation_refuses_undeclared_enforcement_claims(self):
        from desk3.contract import RebalancePolicy
        with self.assertRaises(ValueError):
            RebalancePolicy(enforcement="enforced")  # unknown value
        with self.assertRaises(ValueError):
            RebalancePolicy(frequency="whenever")
        with self.assertRaises(ValueError):
            RebalancePolicy(drift_threshold=0.05)  # needs drift_type
        with self.assertRaises(ValueError):
            RebalancePolicy(drift_type="absolute")  # needs threshold
        with self.assertRaises(ValueError):
            RebalancePolicy(drift_threshold=1.5, drift_type="absolute")
        with self.assertRaises(ValueError):
            RebalancePolicy(tracking_error_window_days=20)  # needs TE
        with self.assertRaises(ValueError):
            RebalancePolicy(max_annual_turnover=-1.0)
        with self.assertRaises(ValueError):
            RebalancePolicy.from_dict({"bogus_key": 1})
        # A dimension with NO declared value cannot be claimed
        # enforced, and enforcement/status must agree with the
        # claimed dimensions.
        with self.assertRaises(ValueError):
            RebalancePolicy(
                enforcement="enforced_for_declared_dimensions",
                status="ACTIVE_DECLARED_DIMENSIONS_ONLY",
                enforced_dimensions=("drift_threshold",))
        with self.assertRaises(ValueError):
            RebalancePolicy(
                enforcement="enforced_for_declared_dimensions",
                status="ACTIVE_DECLARED_DIMENSIONS_ONLY",
                enforced_dimensions=("max_annual_turnover",))
        with self.assertRaises(ValueError):
            RebalancePolicy(enforced_dimensions=("frequency",))
        with self.assertRaises(ValueError):
            RebalancePolicy(
                enforcement="enforced_for_declared_dimensions",
                status="ACTIVE_DECLARED_DIMENSIONS_ONLY")
        ok = RebalancePolicy(
            frequency="monthly", drift_threshold=0.05,
            drift_type="absolute", partial_rebalance=True,
            tracking_error_threshold=0.06,
            tracking_error_window_days=20, max_annual_turnover=4.0,
            signal_change_rebalance=False)
        self.assertEqual(RebalancePolicy.from_dict(ok.to_dict()), ok)
        enforced = RebalancePolicy(
            frequency="monthly", drift_threshold=0.05,
            drift_type="absolute",
            enforcement="enforced_for_declared_dimensions",
            status="ACTIVE_DECLARED_DIMENSIONS_ONLY",
            enforced_dimensions=("frequency", "drift_threshold"))
        self.assertEqual(
            RebalancePolicy.from_dict(enforced.to_dict()), enforced)
        self.assertEqual(enforced.to_dict()["enforced_dimensions"],
                         ["frequency", "drift_threshold"])


class TestConfigRowsCarryPolicy(unittest.TestCase):
    def test_every_row_has_a_valid_policy_block(self):
        from desk3.contract import RebalancePolicy
        with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
            rows = json.load(fh)["sleeves"]
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(rows), 400)
        for row in rows:
            self.assertIn("rebalance_policy", row, row["id"])
            parsed = RebalancePolicy.from_dict(row["rebalance_policy"])
            self.assertEqual(parsed.to_dict(), row["rebalance_policy"],
                             row["id"])

    def test_only_the_declared_books_are_flipped_enforced(self):
        with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
            rows = json.load(fh)["sleeves"]
        flipped = set()
        for row in rows:
            pol = row["rebalance_policy"]
            self.assertIsNone(pol["drift_threshold"], row["id"])
            self.assertIsNone(pol["tracking_error_threshold"], row["id"])
            self.assertIsNone(pol["max_annual_turnover"], row["id"])
            for dim in DECLARED_ONLY:
                self.assertNotIn(dim, pol["enforced_dimensions"], row["id"])
            if pol["enforcement"] == "enforced_for_declared_dimensions":
                flipped.add(row["id"])
                self.assertEqual(pol["status"],
                                 "ACTIVE_DECLARED_DIMENSIONS_ONLY",
                                 row["id"])
            else:
                self.assertEqual(pol["enforcement"],
                                 "declared_not_enforced", row["id"])
                self.assertEqual(pol["enforced_dimensions"], [], row["id"])
        self.assertEqual(flipped, ENFORCED_IDS)
        by_id = {r["id"]: r for r in rows}
        for sid in ENFORCED_IDS:
            want = ASTER_DIMS if sid.startswith("aster_etf_") else BOOK_DIMS
            self.assertEqual(
                by_id[sid]["rebalance_policy"]["enforced_dimensions"],
                want, sid)

    def test_named_books_carry_their_spec_frequency(self):
        with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
            by_id = {r["id"]: r for r in json.load(fh)["sleeves"]}
        self.assertEqual(
            by_id["momentum_rotation"]["rebalance_policy"]["frequency"],
            "weekly")
        self.assertEqual(
            by_id["ts_momentum_decile"]["rebalance_policy"]["frequency"],
            "monthly")
        self.assertEqual(
            by_id["aster_etf_qqq_buy_hold"]["rebalance_policy"]
                 ["frequency"], "buy_hold")
        self.assertEqual(
            by_id["aster_etf_qqq_monthly_c098"]["rebalance_policy"]
                 ["frequency"], "monthly")
        for sid in ("aster_etf_qqq_buy_hold",
                    "aster_etf_qqq_monthly_c098"):
            self.assertIs(
                by_id[sid]["rebalance_policy"]["partial_rebalance"],
                True, sid)


class TestBooksDeclarePolicy(unittest.TestCase):
    BOOKS = ("desk3.aster_etf", "desk3.port_b5.momentum_rotation",
             "adapters3.ts_momentum_decile")

    def test_every_book_declares_its_enforced_dimensions(self):
        for name in self.BOOKS:
            mod = importlib.import_module(name)
            pol = getattr(mod, "REBALANCE_POLICY", None)
            self.assertIsInstance(pol, dict, name)
            self.assertEqual(pol["mechanism"], "rebalance-policy", name)
            self.assertEqual(pol["enforcement"],
                             "enforced_for_declared_dimensions", name)
            self.assertEqual(pol["status"],
                             "ACTIVE_DECLARED_DIMENSIONS_ONLY", name)
            self.assertEqual(pol["declared_only_dimensions"],
                             DECLARED_ONLY, name)
            self.assertIn("drift", pol["ruling_needed"], name)
            self.assertIn("turnover", pol["ruling_needed"], name)
            want = ASTER_DIMS if name == "desk3.aster_etf" else BOOK_DIMS
            self.assertEqual(pol["enforced_dimensions"], want, name)

    def test_book_frequencies_match_their_existing_specs(self):
        from desk3.aster_etf import REBALANCE_POLICY as aster_pol, SPECS
        self.assertEqual(aster_pol["frequency"], "per_spec")
        self.assertIs(aster_pol["partial_rebalance"], True)
        self.assertEqual({s["freq"] for s in SPECS.values()},
                         {"MONTHLY", "BUY_HOLD"})
        from desk3.port_b5.momentum_rotation import REBALANCE_POLICY
        self.assertEqual(REBALANCE_POLICY["frequency"], "weekly")
        from adapters3.ts_momentum_decile import REBALANCE_POLICY as ts_pol
        self.assertEqual(ts_pol["frequency"], "monthly")

    def test_byte_pinned_strategy_ports_stay_clean(self):
        for rel in ("sleeves/momentum_rotation.py",
                    "sleeves/ts_momentum_decile.py"):
            with open(os.path.join(ROOT, rel)) as fh:
                self.assertNotIn("REBALANCE_POLICY", fh.read(), rel)


class TestEnforcedBehavior(unittest.TestCase):
    @staticmethod
    def _flat(px, n=130):
        return [{"t": "2026-01-%02d" % ((i % 28) + 1), "o": px,
                 "h": px, "l": px, "c": px, "v": 1000}
                for i in range(n)]

    def _aster_view(self, positions, now="2026-10-01T09:36:00"):
        return {"now": now, "bars": {"QQQ": self._flat(100.0)},
                "positions": positions, "quotes": {}, "extra": {}}

    _CTX = {"session": "2026-10-01", "now": "2026-10-01T09:36:00",
            "slice": {"capital_usd": 10000.0}}

    @staticmethod
    def _prime(evaluate, sleeve_id, view):
        """WEIGHT-LAG-ACTIVE-20261031: the first evaluation of a
        sleeve emits nothing and only records pending targets; the
        NEXT evaluation acts on them. That lag is designed and
        blocked by the weight-lag suites. These rebalance tests
        prime it explicitly (one discarded evaluation on the same
        view) so every assertion below is on the acting evaluation
        and no test depends on another test, or another file in the
        gate process, having evaluated the sleeve first. Before
        this priming, two tests here passed only in gate order and
        failed standalone (REBALANCE-ENFORCE-20261031 recheck
        disagreement, 2026-11-01 and 2026-11-08)."""
        evaluate(sleeve_id, view, dict(TestEnforcedBehavior._CTX))

    def test_aster_buy_hold_frequency_enforced(self):
        from desk3.aster_etf import evaluate
        pos = [{"symbol": "QQQ", "qty": 10, "avg_price": 90.0,
                "entry_date": "2026-09-01"}]
        out = evaluate("aster_etf_qqq_buy_hold",
                       self._aster_view(pos), dict(self._CTX))
        self.assertEqual(out, [])

    def test_aster_monthly_same_month_suppressed_new_month_allowed(self):
        from desk3.aster_etf import evaluate
        same = [{"symbol": "QQQ", "qty": 10, "avg_price": 90.0,
                 "entry_date": "2026-10-01"}]
        self.assertEqual(
            evaluate("aster_etf_qqq_monthly_c098",
                     self._aster_view(same), dict(self._CTX)), [])
        prior = [{"symbol": "QQQ", "qty": 10, "avg_price": 90.0,
                  "entry_date": "2026-09-15"}]
        self._prime(evaluate, "aster_etf_qqq_monthly_c098",
                    self._aster_view(prior))
        out = evaluate("aster_etf_qqq_monthly_c098",
                       self._aster_view(prior), dict(self._CTX))
        self.assertTrue(out)

    def test_aster_partial_rebalance_is_delta_only(self):
        from desk3.aster_etf import evaluate
        held = [{"symbol": "QQQ", "qty": 50, "avg_price": 90.0,
                 "entry_date": "2026-09-15"}]
        self._prime(evaluate, "aster_etf_qqq_monthly_c098",
                    self._aster_view(held))
        out = evaluate("aster_etf_qqq_monthly_c098",
                       self._aster_view(held), dict(self._CTX))
        # Target is int(0.98 * 10000 / 100) = 98 shares; a partial
        # (delta-only) rebalance buys only the 48-share difference.
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 48)

    def test_momentum_weekly_frequency_enforced(self):
        from sleeves.momentum_rotation import rebalance_due
        self.assertFalse(rebalance_due("2026-10-01", "2026-10-05"))
        self.assertFalse(rebalance_due("2026-10-01", "2026-10-07"))
        self.assertTrue(rebalance_due("2026-10-01", "2026-10-08"))
        self.assertTrue(rebalance_due(None, "2026-10-08"))

    def test_ts_monthly_gate_suppresses_same_month(self):
        from adapters3.ts_momentum_decile import (
            _monthly_rebalance_suppressed, evaluate)
        view = {"now": "2026-10-23T15:30:00-04:00",
                "positions": [{"symbol": "NVDA", "qty": 5,
                               "opened_at": "2026-10-02T14:00:00Z"}]}
        self.assertTrue(_monthly_rebalance_suppressed(view, {}))
        self.assertEqual(evaluate(view, {"state_dir": "/tmp/ts_gate"}), [])

    def test_ts_monthly_gate_allows_new_month_and_initial(self):
        from adapters3.ts_momentum_decile import (
            _monthly_rebalance_suppressed)
        prior = {"now": "2026-10-23T15:30:00-04:00",
                 "positions": [{"symbol": "NVDA", "qty": 5,
                                "opened_at": "2026-09-01T14:00:00Z"}]}
        self.assertFalse(_monthly_rebalance_suppressed(prior, {}))
        empty = {"now": "2026-10-23T15:30:00-04:00", "positions": []}
        self.assertFalse(_monthly_rebalance_suppressed(empty, {}))


class TestNoLiveConsumption(unittest.TestCase):
    def test_dispatcher_never_consumes_the_policy(self):
        with open(os.path.join(ROOT, "desk3", "dispatcher.py")) as fh:
            src = fh.read()
        self.assertNotIn("RebalancePolicy", src)
        self.assertNotIn("rebalance_policy", src)

    def test_aster_evaluate_intents_unchanged_by_declaration(self):
        def flat(px, n=130):
            return [{"t": "2026-01-%02d" % ((i % 28) + 1), "o": px,
                     "h": px, "l": px, "c": px, "v": 1000}
                    for i in range(n)]
        from desk3.aster_etf import evaluate
        view = {"now": "2026-10-01T09:36:00",
                "bars": {"QQQ": flat(100.0)},
                "positions": [], "quotes": {}, "extra": {}}
        ctx = {"session": "2026-10-01", "now": "2026-10-01T09:36:00",
               "slice": {"capital_usd": 10000.0}}
        # weight-lag priming (see TestEnforcedBehavior._prime): the
        # first evaluation only records pending targets by design.
        evaluate("aster_etf_qqq_buy_hold", view, dict(ctx))
        out = evaluate("aster_etf_qqq_buy_hold", view, dict(ctx))
        self.assertEqual(len(out), 1)
        self.assertNotIn("rebalance", str(out[0]).lower())


if __name__ == "__main__":
    unittest.main()
