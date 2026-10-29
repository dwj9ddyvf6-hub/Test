from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
import inspect
import math
import unittest

from research.forecast_engines.catalog import ENGINES
from research.forecast_engines.contracts import FeatureObservation, ForecastRequest
from research.forecast_engines.edge_cards import EDGE_CARDS
from research.forecast_engines.engine import ForecastEngine
from research.forecast_engines.scorers import _FORMULAS, f_13f, f_har, f_options_flow, f_gamma, f_index_flow, f_macro, f_ofi, score
from research.forecast_engines.target_contract import TARGET_LABEL_CONTRACTS


def _neutral_features(spec):
    values = {}
    for requirement in spec.inputs:
        if requirement.unit == "ratio":
            values[requirement.name] = 0.5
        elif requirement.unit == "signed_ratio":
            values[requirement.name] = 0.0
        elif requirement.unit == "beta":
            values[requirement.name] = 1.0
        elif requirement.unit == "days":
            values[requirement.name] = 3.0
        elif requirement.unit == "log_variance":
            values[requirement.name] = -10.0
        elif requirement.unit in {"return", "absolute_return"}:
            values[requirement.name] = 0.02
        else:
            values[requirement.name] = 0.0
    return values


class ForecastSemanticsTests(unittest.TestCase):
    def test_all_30_scorers_use_exactly_the_declared_inputs(self):
        for spec in ENGINES:
            with self.subTest(engine=spec.engine_id):
                source = inspect.getsource(_FORMULAS[spec.formula])
                tree = ast.parse(source)
                accessed = {
                    node.slice.value
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Subscript)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "x"
                    and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)
                }
                self.assertEqual(accessed, {item.name for item in spec.inputs})
                signal = score(spec.formula, _neutral_features(spec))
                self.assertTrue(math.isfinite(signal.value))
                self.assertTrue(math.isfinite(signal.model_score))
                self.assertTrue(all(math.isfinite(value) for value in signal.drivers.values()))

    def test_every_edge_card_uses_its_frozen_primary_target(self):
        self.assertEqual(len(EDGE_CARDS), 30)
        for card in EDGE_CARDS:
            with self.subTest(engine=card.engine_id):
                self.assertEqual(
                    card.target_definition,
                    TARGET_LABEL_CONTRACTS[card.engine_id]["label_definition"],
                )

    def test_ratio_units_enforce_declared_bounds(self):
        for spec in ENGINES:
            for requirement in spec.inputs:
                if requirement.unit == "ratio":
                    self.assertEqual(requirement.value_range, (0.0, 1.0))
                elif requirement.unit == "signed_ratio":
                    self.assertEqual(requirement.value_range, (-1.0, 1.0))
                elif requirement.unit == "beta":
                    self.assertIsNone(requirement.value_range)

    def test_options_flow_direction_uses_signed_aggressor_delta_and_confidence(self):
        common = {
            "customer_signed_delta_flow_z": 2.0,
            "sweep_quality": 1.0,
            "open_close_confidence": 1.0,
            "aggressor_side_confidence": 1.0,
            "quote_condition_quality": 1.0,
        }
        self.assertGreater(f_options_flow(common).value, 0.0)
        common["customer_signed_delta_flow_z"] = -2.0
        self.assertLess(f_options_flow(common).value, 0.0)
        common["aggressor_side_confidence"] = 0.0
        self.assertEqual(f_options_flow(common).value, 0.0)

    def test_ofi_replenishment_damps_order_flow_pressure(self):
        features = {
            "ofi_z": 1.0,
            "depth_z": 0.0,
            "depth_replenishment_ratio": 0.0,
            "historical_post_fill_drift_z": 0.0,
            "trade_condition_quality": 1.0,
        }
        no_refill = f_ofi(features).value
        with_refill = f_ofi({**features, "depth_replenishment_ratio": 1.0}).value
        self.assertGreater(no_refill, with_refill)
        self.assertGreater(with_refill, 0.0)

    def test_13f_staleness_reduces_crowding_evidence(self):
        fresh = {
            "ownership_crowding_z": 2.0,
            "fundamental_deterioration_z": 0.0,
            "liquidity_stress_z": 0.0,
            "filing_staleness": 0.0,
        }
        stale = {**fresh, "filing_staleness": 1.0}
        self.assertGreater(f_13f(fresh).value, f_13f(stale).value)

    def test_gamma_scenario_has_counter_trend_hedge_sign_for_long_gamma(self):
        up = {"gamma_assumption_z": 1.0, "spot_move_z": 1.0, "oi_concentration_z": 0.0, "gamma_input_quality": 1.0}
        down = {**up, "spot_move_z": -1.0}
        self.assertLess(f_gamma(up).value, 0.0)
        self.assertGreater(f_gamma(down).value, 0.0)

    def test_index_flow_is_zero_after_effective_date(self):
        features = {
            "flow_estimate_z": 2.0,
            "flow_model_confidence": 1.0,
            "days_to_effective": -1.0,
            "crowding_z": 0.0,
        }
        result = f_index_flow(features)
        self.assertEqual(result.value, 0.0)
        self.assertEqual(result.drivers["event_passed"], 1.0)

    def test_macro_reaction_coordinate_is_bounded(self):
        base = {"release_surprise_z": 1.0, "market_pricing_z": 0.0, "regime_confidence": 1.0}
        self.assertEqual(
            f_macro({**base, "cycle_reaction_sign": 100.0}).value,
            f_macro({**base, "cycle_reaction_sign": 1.0}).value,
        )

    def test_har_ratio_uses_the_same_clipped_values_as_variance(self):
        result = f_har({"log_rv_1": 100.0, "log_rv_5": 100.0, "log_rv_22": 100.0, "log_rv_baseline": -100.0})
        self.assertAlmostEqual(result.value, math.exp(10.0))
        self.assertAlmostEqual(result.model_score, 50.0)

    def test_direct_scorer_rejects_non_finite_and_boolean_features(self):
        spec = ENGINES[0]
        features = _neutral_features(spec)
        features["ret_21d_z"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            score(spec.formula, features)
        features["ret_21d_z"] = True
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            score(spec.formula, features)

    def test_forecast_abstains_on_out_of_range_ratio(self):
        spec = next(item for item in ENGINES if item.engine_id == "FE16")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        features = {}
        for requirement in spec.inputs:
            value = 1.5 if requirement.name == "aggressor_side_confidence" else 0.5 if requirement.unit == "ratio" else 0.0
            available = now - timedelta(seconds=1)
            features[requirement.name] = FeatureObservation(
                value=value,
                unit=requirement.unit,
                observed_at=available,
                available_at=available,
                ingested_at=available,
                source_id=f"test:{requirement.name}",
                source_hash="a" * 64,
                independence_group=f"test:{requirement.name}",
                rights_approved=True,
                quality=1.0,
            )
        forecast = ForecastEngine().forecast(ForecastRequest("FE16", "TEST", now, features))
        self.assertEqual(forecast.status, "abstain")
        self.assertIn("value_out_of_range:aggressor_side_confidence", forecast.abstain_reasons)


if __name__ == "__main__":
    unittest.main()
