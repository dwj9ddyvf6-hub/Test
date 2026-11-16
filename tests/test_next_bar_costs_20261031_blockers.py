"""Blockers NEXT-BAR-COSTS-20261031: next-bar fills with explicit
per-strategy cost objects.

Audit (research_notes/quants-mechanisms-steal-20261031/AUDIT.md item 2):
the fill half was strong (closed bars, broker read-back fills, the
forecast contract "a decision at the close of d fills at the open of
d+1") but the cost half was weak: config/sleeves.json (336 rows) had
no commission/slippage keys, and no per-strategy cost object existed
in the sleeve contract (the sleeve contract. NOTE (preservation, proven in-pass):
core/sleeve.py and desk3/vendor/core/sleeve.py are byte-pinned to
the v2 ports by the port-fidelity blockers, so the object lives in
desk3/contract.py, the unpinned v3-native SleeveConfig); the only forecast
cost model was the global per-name model in desk3/forecast/costs.py.

What lands (risk BACKTEST; the live dispatcher keeps real broker
fills and is not touched):
  - StrategyCosts in the v3 sleeve contract (desk3/contract.py): fill_timing "next_bar",
    commission scheme (per-share, bps, minimum per order) and a
    slippage model ("forecast_per_name" default, "fixed_bps"
    override, or "none"), validated, with from_dict/to_dict and an
    extra_per_side_fraction() the forecast layer consumes.
  - SleeveConfig carries costs, defaulting to the explicit default
    object, and describe() surfaces it.
  - Every row of config/sleeves.json carries a costs block that
    parses into StrategyCosts.
  - desk3/forecast/costs.py consumes it: per_side_for_strategy()
    returns EXACTLY the old per-name per_side() under the default
    object, and raises the cost by exactly the declared fraction
    under an explicit override.

These tests fail on the pre-change tree (no StrategyCosts, no costs
blocks, no resolver) and pass on the landed tree.
"""
import hashlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DEFAULT_BLOCK = {
    "fill_timing": "next_bar",
    "commission_per_share": 0.0,
    "commission_bps": 0.0,
    "min_commission_per_order": 0.0,
    "slippage_model": "forecast_per_name",
    "slippage_bps": None,
}


class TestStrategyCostsContract(unittest.TestCase):
    def test_default_object_is_explicit(self):
        from desk3.contract import StrategyCosts
        c = StrategyCosts()
        self.assertEqual(c.fill_timing, "next_bar")
        self.assertEqual(c.commission_per_share, 0.0)
        self.assertEqual(c.commission_bps, 0.0)
        self.assertEqual(c.min_commission_per_order, 0.0)
        self.assertEqual(c.slippage_model, "forecast_per_name")
        self.assertIsNone(c.slippage_bps)
        self.assertEqual(c.extra_per_side_fraction(100.0, 10.0), 0.0)
        self.assertEqual(c.to_dict(), DEFAULT_BLOCK)

    def test_pinned_port_copies_stay_untouched(self):
        # core/sleeve.py and desk3/vendor/core/sleeve.py are
        # byte-pinned to the v2 ports (port b5/b7/batch4/batch6
        # fidelity blockers): they stay identical to each other and
        # carry no StrategyCosts; the object lives only in the
        # unpinned v3 contract, desk3/contract.py.
        digests = set()
        for rel in ("core/sleeve.py", "desk3/vendor/core/sleeve.py"):
            with open(os.path.join(ROOT, rel), "rb") as fh:
                data = fh.read()
            digests.add(hashlib.md5(data).hexdigest())
            self.assertNotIn(b"StrategyCosts", data, rel)
        self.assertEqual(len(digests), 1)
        with open(os.path.join(ROOT, "desk3/contract.py"), "rb") as fh:
            self.assertIn(b"StrategyCosts", fh.read())

    def test_sleeve_config_carries_costs_by_default(self):
        from desk3.contract import SleeveConfig, StrategyCosts
        cfg = SleeveConfig(sleeve_id="x", cadence_s=60)
        self.assertEqual(cfg.costs, StrategyCosts())
        from desk3.contract import _describe_config
        self.assertEqual(_describe_config(cfg)["costs"], DEFAULT_BLOCK)

    def test_validation_rejects_bad_objects(self):
        from desk3.contract import StrategyCosts
        with self.assertRaises(ValueError):
            StrategyCosts(fill_timing="same_bar")
        with self.assertRaises(ValueError):
            StrategyCosts(commission_per_share=-0.01)
        with self.assertRaises(ValueError):
            StrategyCosts(slippage_model="fixed_bps")  # needs slippage_bps
        with self.assertRaises(ValueError):
            StrategyCosts(slippage_bps=5.0)  # only valid for fixed_bps
        with self.assertRaises(ValueError):
            StrategyCosts.from_dict({"bogus_key": 1})

    def test_override_fraction_is_exact(self):
        from desk3.contract import StrategyCosts
        c = StrategyCosts(commission_per_share=0.005,
                          min_commission_per_order=1.0,
                          slippage_model="fixed_bps", slippage_bps=5.0)
        # notional 100*10=1000; commission max(1.0, 0.005*10)=1.0 -> 0.001
        # slippage 5 bps -> 0.0005; total extra = 0.0015
        self.assertAlmostEqual(
            c.extra_per_side_fraction(100.0, 10.0), 0.0015, places=12)
        rt = StrategyCosts.from_dict(c.to_dict())
        self.assertEqual(rt, c)


class TestConfigRowsCarryCosts(unittest.TestCase):
    def test_every_row_has_a_valid_costs_block(self):
        from desk3.contract import StrategyCosts
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
            self.assertIn("costs", row, row["id"])
            parsed = StrategyCosts.from_dict(row["costs"])
            self.assertEqual(parsed.fill_timing, "next_bar", row["id"])
            self.assertEqual(parsed.to_dict(), row["costs"], row["id"])


class TestForecastConsumption(unittest.TestCase):
    def _bars(self, n=40):
        px = [100.0 + 0.1 * i for i in range(n)]
        return ([p * 1.01 for p in px], [p * 0.99 for p in px], px,
                [1e6] * n)

    def test_default_resolves_to_old_per_name_model_exactly(self):
        import numpy as np
        from desk3.contract import StrategyCosts
        from desk3.forecast import costs as fc
        h, l, c, dv = self._bars()
        base, _, _ = fc.per_side(h, l, c, dv)
        got, _, _ = fc.per_side_for_strategy(
            h, l, c, dv, StrategyCosts(), reference_shares=10.0)
        self.assertTrue(np.array_equal(np.nan_to_num(base),
                                       np.nan_to_num(got)))

    def test_override_adds_exactly_the_declared_fraction(self):
        import numpy as np
        from desk3.contract import StrategyCosts
        from desk3.forecast import costs as fc
        h, l, c, dv = self._bars()
        over = StrategyCosts(slippage_model="fixed_bps", slippage_bps=10.0)
        base, _, _ = fc.per_side(h, l, c, dv)
        got, _, _ = fc.per_side_for_strategy(
            h, l, c, dv, over, reference_shares=10.0)
        mask = np.isfinite(base) & (base < fc.CAP - 0.002)
        self.assertTrue(mask.any())
        self.assertTrue(np.allclose(got[mask], base[mask] + 0.001))

    def test_resolver_accepts_a_config_row_dict(self):
        from desk3.forecast import costs as fc
        h, l, c, dv = self._bars()
        got, _, _ = fc.per_side_for_strategy(
            h, l, c, dv, dict(DEFAULT_BLOCK), reference_shares=1.0)
        base, _, _ = fc.per_side(h, l, c, dv)
        import numpy as np
        self.assertTrue(np.array_equal(np.nan_to_num(base),
                                       np.nan_to_num(got)))

    def test_live_dispatcher_source_has_no_modelled_cost_consumption(self):
        # Preservation: modelled costs belong to the research layer;
        # the live dispatcher must keep broker read-back fills.
        with open(os.path.join(ROOT, "desk3", "dispatcher.py")) as fh:
            src = fh.read()
        self.assertNotIn("StrategyCosts", src)
        self.assertNotIn("per_side_for_strategy", src)


if __name__ == "__main__":
    unittest.main()
