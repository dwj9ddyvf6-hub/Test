"""Independent formula, causal-input and executable-rule checks for the freeze."""
import copy
import hashlib
import json
import math
from pathlib import Path
import random
from types import SimpleNamespace
import unittest

from backend.trader_signals import (
    CONFIG_SHA256, DEFINITIONS, DONCHIAN, RSI2, RULES_DOCUMENT_SHA256,
    SQUEEZE, UNIVERSE, _ema, _linreg_endpoint, _normalize, _rma, _rsi,
    _sma, _squeeze_series, _true_range, evaluate,
)


def bars(closes, *, volume=1_000_000.0, width=1.0):
    return [dict(timestamp_ms=1_000_000 + i * 86_400_000,
                 completed_at_ms=1_000_001 + i * 86_400_000,
                 usable_at_ms=1_000_002 + i * 86_400_000,
                 open=float(c), high=float(c) + width, low=float(c) - width,
                 close=float(c), volume=volume) for i, c in enumerate(closes)]


def config(rule):
    return copy.deepcopy(DEFINITIONS[rule]["rule_config"])


class FormulaTests(unittest.TestCase):
    def test_sma_uses_current_and_exact_period(self):
        self.assertEqual(_sma([1, 2, 3, 4, 5], 3), [None, None, 2, 3, 4])

    def test_ema_sma_seed_and_standard_alpha(self):
        self.assertEqual(_ema([1, 2, 3, 4, 5], 3), [None, None, 2, 3, 4])
        self.assertEqual(_ema([1, 2], 3), [None, None])

    def test_wilder_rma_seed_and_recursion(self):
        values = _rma([1, 2, 3, 4, 5], 3)
        self.assertEqual(values[:3], [None, None, 2])
        self.assertAlmostEqual(values[3], 8 / 3)
        self.assertAlmostEqual(values[4], 31 / 9)

    def test_true_range_includes_previous_close_and_first_high_low(self):
        rows = bars([10, 12, 9])
        rows[1].update(open=12, high=13, low=11)
        rows[2].update(open=9, high=10, low=8)
        tr = _true_range(_normalize(rows))
        self.assertEqual(tr, [2, 3, 4])
        self.assertEqual(_rma(tr, 2), [None, 2.5, 3.25])

    def test_rsi2_seed_uses_two_real_changes_not_synthetic_zero(self):
        values = _rsi([10, 11, 9, 10, 10, 8], 2)
        self.assertEqual(values[:2], [None, None])
        self.assertAlmostEqual(values[2], 100 / 3)
        self.assertAlmostEqual(values[3], 60)
        self.assertAlmostEqual(values[4], 60)
        self.assertAlmostEqual(values[5], 100 / 7)

    def test_rsi_zero_gain_loss_and_flat_conventions(self):
        self.assertEqual(_rsi([1, 2, 3, 4], 2)[2:], [100, 100])
        self.assertEqual(_rsi([4, 3, 2, 1], 2)[2:], [0, 0])
        self.assertEqual(_rsi([2, 2, 2, 2], 2)[2:], [50, 50])

    def test_welles_wilder_published_rsi14_handworked_seed(self):
        closes = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
                  45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00]
        values = _rsi(closes, 14)
        self.assertAlmostEqual(values[14], 70.46413502109705, places=11)
        self.assertAlmostEqual(values[15], 66.24961855355505, places=11)

    def test_endpoint_linreg_is_fitted_last_value_not_slope(self):
        self.assertEqual(_linreg_endpoint([3, 5, 7, 9]), 9)
        self.assertEqual(_linreg_endpoint([0, 1, 4, 9]), 8)

    def test_squeeze_population_sigma_and_modern_ema_atr_formula(self):
        rows = _normalize(bars([100] * 299 + [110]))
        result = _squeeze_series(rows, config(SQUEEZE))
        self.assertTrue(result["squeeze"][-2])
        self.assertFalse(result["squeeze"][-1])
        self.assertAlmostEqual(result["kc_center"][-1], 100 + 10 * 2 / 21)
        # Last true range includes the previous 100 close, hence 11.
        self.assertAlmostEqual(result["kc_atr"][-1], 2 + 9 / 20)
        # HH=111, LL=99, SMA=100.5 -> final delta=7.25.
        # The OLS fitted endpoint for nineteen zeros and 7.25 is 7.25*39/210.
        self.assertAlmostEqual(result["momentum"][-1], 7.25 * 39 / 210)
        self.assertEqual(result["momentum"][-2], 0)
        self.assertIsNone(result["momentum"][37])
        self.assertEqual(result["momentum"][38], 0)

    def test_all_indicator_prefixes_invariant_to_unseen_future(self):
        rng = random.Random(1411)
        closes = [100 + i * .02 + rng.uniform(-.3, .3) for i in range(330)]
        normalized = _normalize(bars(closes))
        for count in (40, 100, 252, 300):
            for fn, period in ((_sma, 20), (_ema, 20), (_rma, 14), (_rsi, 2)):
                with self.subTest(count=count, fn=fn.__name__):
                    self.assertEqual(fn(closes[:count], period), fn(closes, period)[:count])
            short = _squeeze_series(normalized[:count], config(SQUEEZE))
            whole = _squeeze_series(normalized, config(SQUEEZE))
            for field in short:
                self.assertEqual(short[field], whole[field][:count])


class ExecutableRuleTests(unittest.TestCase):
    def test_frozen_json_bytes_match_canonical_document_and_sha(self):
        path = Path(__file__).resolve().parents[1] / "strategies/trader_catalogue/rules-v1.json"
        data = path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), RULES_DOCUMENT_SHA256)
        document = json.loads(data)
        for rule in DEFINITIONS:
            self.assertEqual(document["rules"][rule], config(rule))
            raw = json.dumps(document["rules"][rule], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), CONFIG_SHA256[rule])
        self.assertEqual(len(UNIVERSE), 15)
        self.assertEqual(len(set(UNIVERSE)), 15)

    def test_donchian_prior_channel_excludes_current_high(self):
        rows = bars([100] * 299 + [110])
        rows[-1]["high"] = 115
        result = evaluate(DONCHIAN, {"SPY": rows})
        self.assertEqual([x["symbol"] for x in result["candidates"]], ["SPY"])
        feature = result["features"]["SPY"]
        self.assertEqual(feature["prior55_high"], 101)
        self.assertEqual(feature["prior20_low"], 99)
        self.assertAlmostEqual(feature["breakout_atr"], (110 - 101) / feature["atr14"])
        candidate = result["candidates"][0]
        self.assertEqual(candidate["stop_distance"], 2 * candidate["atr"])
        self.assertEqual(candidate["risk_budget_fraction"], .005)
        self.assertEqual(candidate["max_hold_bars"], 126)

    def test_donchian_entry_needs_above_sma200(self):
        rows = bars([200] * 240 + [100] * 59 + [110])
        result = evaluate(DONCHIAN, {"SPY": rows})
        self.assertEqual(result["candidates"], [])
        self.assertGreater(result["features"]["SPY"]["sma200"], 110)

    def test_donchian_breakout_strict_equality_does_not_enter(self):
        result = evaluate(DONCHIAN, {"SPY": bars([100] * 299 + [101])})
        self.assertEqual(result["candidates"], [])

    def test_donchian_exit_channel_excludes_current_low(self):
        rows = bars([100] * 299 + [90])
        rows[-1]["low"] = 50
        result = evaluate(DONCHIAN, {"SPY": rows}, held_symbols=("SPY",))
        self.assertEqual(result["features"]["SPY"]["prior20_low"], 99)
        self.assertIn("close_below_prior20_low", result["exits"][0]["reason"])
        self.assertIn("close_below_sma200", result["exits"][0]["reason"])

    def test_rsi2_extreme_pullback_in_uptrend_enters_without_stop(self):
        closes = [100 + .1 * i for i in range(300)]
        closes[-2:] = [126.8, 125.8]
        result = evaluate(RSI2, {"SPY": bars(closes)})
        self.assertEqual(len(result["candidates"]), 1)
        feature = result["features"]["SPY"]
        self.assertLessEqual(feature["rsi2"], 5)
        self.assertGreater(feature["close"], feature["sma200"])
        self.assertLess(feature["close"], feature["sma5"])
        self.assertIsNone(result["candidates"][0]["stop_distance"])
        self.assertIsNone(result["candidates"][0]["risk_budget_fraction"])
        self.assertEqual(result["candidates"][0]["max_hold_bars"], 10)

    def test_rsi2_pullback_in_downtrend_rejected(self):
        result = evaluate(RSI2, {"SPY": bars([200] * 240 + [110] * 58 + [105, 100])})
        self.assertEqual(result["candidates"], [])
        self.assertLessEqual(result["features"]["SPY"]["rsi2"], 5)
        self.assertLess(result["features"]["SPY"]["close"], result["features"]["SPY"]["sma200"])

    def test_rsi2_exit_needs_strictly_above_sma5(self):
        trend = bars([100 + .1 * i for i in range(300)])
        result = evaluate(RSI2, {"SPY": trend}, held_symbols=("SPY",))
        self.assertEqual(result["exits"][0]["reason"], "close_above_sma5")
        flat = evaluate(RSI2, {"SPY": bars([100] * 300)}, held_symbols=("SPY",))
        self.assertEqual(flat["exits"], [])

    def test_squeeze_release_rising_positive_momentum_and_breakout_enters(self):
        result = evaluate(SQUEEZE, {"SPY": bars([100] * 299 + [110])})
        self.assertEqual(len(result["candidates"]), 1)
        f = result["features"]["SPY"]
        self.assertTrue(f["previous_squeeze_on"])
        self.assertFalse(f["squeeze_on"])
        self.assertGreater(f["momentum"], 0)
        self.assertGreater(f["momentum"], f["previous_momentum"])
        self.assertGreater(f["close"], f["prior20_high"])
        self.assertEqual(result["candidates"][0]["max_hold_bars"], 20)

    def test_squeeze_still_on_does_not_enter(self):
        result = evaluate(SQUEEZE, {"SPY": bars([100] * 300)})
        self.assertTrue(result["features"]["SPY"]["squeeze_on"])
        self.assertEqual(result["candidates"], [])

    def test_squeeze_negative_release_does_not_enter(self):
        result = evaluate(SQUEEZE, {"SPY": bars([100] * 299 + [90])})
        self.assertTrue(result["features"]["SPY"]["squeeze_release"])
        self.assertLess(result["features"]["SPY"]["momentum"], 0)
        self.assertEqual(result["candidates"], [])

    def test_squeeze_both_close_center_and_nonpositive_momentum_exits(self):
        result = evaluate(SQUEEZE, {"SPY": bars([100] * 299 + [90])}, held_symbols=("SPY",))
        self.assertIn("close_below_kc_center", result["exits"][0]["reason"])
        self.assertIn("momentum_nonpositive", result["exits"][0]["reason"])
        atzero = evaluate(SQUEEZE, {"SPY": bars([100] * 300)}, held_symbols=("SPY",))
        self.assertEqual(atzero["exits"][0]["reason"], "momentum_nonpositive")

    def test_held_symbols_are_not_reselected(self):
        rows = bars([100] * 299 + [110])
        for rule in (DONCHIAN, SQUEEZE):
            with self.subTest(rule=rule):
                self.assertEqual(evaluate(rule, {"SPY": rows}, held_symbols=("SPY",))["candidates"], [])

    def test_rank_ties_are_stably_symbol_ascending_independent_input_order(self):
        rows = bars([100] * 299 + [110])
        for rule in (DONCHIAN, SQUEEZE):
            with self.subTest(rule=rule):
                first = evaluate(rule, {"SPY": rows, "QQQ": rows})
                second = evaluate(rule, {"QQQ": rows, "SPY": rows})
                self.assertEqual(first, second)
                self.assertEqual([c["symbol"] for c in first["candidates"]], ["QQQ", "SPY"])

    def test_rsi_secondary_rank_more_atr_normalized_pullback_first(self):
        closes = [100 + .1 * i for i in range(300)]
        closes[-2:] = [126.8, 125.8]
        narrow, wide = bars(closes, width=.5), bars(closes, width=5)
        result = evaluate(RSI2, {"QQQ": wide, "SPY": narrow})
        self.assertEqual([c["symbol"] for c in result["candidates"]], ["SPY", "QQQ"])
        self.assertEqual(result["candidates"][0]["features"]["rsi2"], result["candidates"][1]["features"]["rsi2"])
        self.assertGreater(result["candidates"][0]["features"]["pullback_atr"], result["candidates"][1]["features"]["pullback_atr"])

    def test_candidate_mean_dollar_volume_and_risk_caps_exact(self):
        rows = bars([100] * 299 + [110], volume=2_000_000)
        result = evaluate(DONCHIAN, {"SPY": rows})
        candidate = result["candidates"][0]
        self.assertEqual(candidate["dollar_volume20"], (19 * 100 + 110) * 2_000_000 / 20)
        self.assertEqual(candidate["max_notional_fraction"], .10)
        self.assertEqual(candidate["max_dollar_volume_fraction"], .01)


class InputContractTests(unittest.TestCase):
    def setUp(self):
        self.rows = bars([100] * 299 + [110])

    def test_native_attribute_objects_have_identical_signals(self):
        objects = [SimpleNamespace(**row, executable_at_ms=row["timestamp_ms"]) for row in self.rows]
        self.assertEqual(evaluate(DONCHIAN, {"SPY": self.rows}), evaluate(DONCHIAN, {"SPY": objects}))

    def test_evaluate_leaves_input_and_config_unchanged(self):
        mapping = {"SPY": self.rows}
        c = config(DONCHIAN)
        before = copy.deepcopy((mapping, c))
        evaluate(DONCHIAN, mapping, c)
        self.assertEqual((mapping, c), before)

    def test_actual_minimum_warmup_252_inclusive(self):
        short = evaluate(DONCHIAN, {"SPY": self.rows[:251]})
        ready = evaluate(DONCHIAN, {"SPY": self.rows[:252]})
        self.assertEqual(short["diagnostics"]["SPY"]["status"], "ineligible")
        self.assertEqual(ready["diagnostics"]["SPY"]["status"], "ready")

    def test_empty_history_and_unknown_symbol_have_no_fabricated_signal(self):
        result = evaluate(DONCHIAN, {"SPY": [], "TSLA": self.rows})
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["diagnostics"]["SPY"]["status"], "ineligible")
        self.assertEqual(result["diagnostics"]["TSLA"]["reason"], "outside_frozen_etf_universe")

    def test_invalid_ohlcv_fail_closed_per_symbol_including_old_rows(self):
        alterations = [
            ("close", math.nan), ("volume", math.inf), ("high", -math.inf),
            ("open", True), ("close", "100"), ("volume", -1),
            ("close", 0), ("high", 1), ("low", 200), ("open", None),
        ]
        for field, value in alterations:
            with self.subTest(field=field, value=value):
                malformed = copy.deepcopy(self.rows)
                malformed[0][field] = value
                result = evaluate(DONCHIAN, {"SPY": malformed, "QQQ": self.rows}, held_symbols=("SPY",))
                self.assertEqual(result["diagnostics"]["SPY"]["status"], "failed")
                self.assertEqual([c["symbol"] for c in result["candidates"]], ["QQQ"])
                self.assertEqual(result["exits"], [])

    def test_duplicate_and_out_of_order_timestamps_not_silently_sorted(self):
        for replace in (self.rows[0]["timestamp_ms"], self.rows[0]["timestamp_ms"] - 1):
            with self.subTest(replace=replace):
                rows2 = copy.deepcopy(self.rows)
                rows2[1]["timestamp_ms"] = replace
                self.assertEqual(evaluate(DONCHIAN, {"SPY": rows2})["diagnostics"]["SPY"]["status"], "failed")

    def test_clock_types_and_causal_order_are_strict(self):
        for field, value in (("timestamp_ms", True), ("timestamp_ms", 1.0),
                             ("completed_at_ms", .5), ("usable_at_ms", True),
                             ("completed_at_ms", 1), ("usable_at_ms", 1)):
            with self.subTest(field=field, value=value):
                altered = copy.deepcopy(self.rows)
                altered[0][field] = value
                self.assertEqual(evaluate(DONCHIAN, {"SPY": altered})["diagnostics"]["SPY"]["status"], "failed")

    def test_explicit_asof_blocks_future_observation_and_accepts_exact_usable_clock(self):
        clock = self.rows[-1]["usable_at_ms"]
        self.assertEqual(evaluate(DONCHIAN, {"SPY": self.rows}, as_of_ms=clock)["diagnostics"]["SPY"]["status"], "ready")
        self.assertEqual(evaluate(DONCHIAN, {"SPY": self.rows}, as_of_ms=clock - 1)["diagnostics"]["SPY"]["status"], "failed")
        without = copy.deepcopy(self.rows)
        del without[-1]["usable_at_ms"]
        self.assertEqual(evaluate(DONCHIAN, {"SPY": without}, as_of_ms=clock)["diagnostics"]["SPY"]["status"], "failed")

    def test_no_wall_clock_or_implicit_asof_is_used(self):
        # Timestamps in the future remain an explicit caller responsibility when
        # no as_of is supplied; evaluation never invents their completion date.
        far_future = copy.deepcopy(self.rows)
        for row in far_future:
            for field in ("timestamp_ms", "completed_at_ms", "usable_at_ms"):
                row[field] += 10 ** 15
        first = evaluate(DONCHIAN, {"SPY": self.rows})
        second = evaluate(DONCHIAN, {"SPY": far_future})
        self.assertEqual(first["candidates"][0]["score"], second["candidates"][0]["score"])

    def test_config_and_universe_cannot_be_changed_by_runtime_argument(self):
        self.assertEqual(evaluate(DONCHIAN, {"SPY": self.rows}, config(DONCHIAN))["config_sha256"], CONFIG_SHA256[DONCHIAN])
        for field, value in (("channel_entry_period", 20), ("max_hold_bars", 2), ("universe", ["SPY"]), ("risk_budget_fraction", .05)):
            with self.subTest(field=field):
                altered = config(DONCHIAN)
                altered[field] = value
                with self.assertRaises(ValueError):
                    evaluate(DONCHIAN, {"SPY": self.rows}, altered)

    def test_public_metadata_mutation_cannot_change_private_rule_freeze(self):
        before = copy.deepcopy(DEFINITIONS[DONCHIAN]["rule_config"])
        try:
            DEFINITIONS[DONCHIAN]["rule_config"]["channel_entry_period"] = 1
            self.assertEqual(len(evaluate(DONCHIAN, {"SPY": self.rows})["candidates"]), 1)
            with self.assertRaises(ValueError):
                evaluate(DONCHIAN, {"SPY": self.rows}, DEFINITIONS[DONCHIAN]["rule_config"])
        finally:
            DEFINITIONS[DONCHIAN]["rule_config"] = before

    def test_unknown_rule_and_nonmapping_contract_reject(self):
        with self.assertRaises(ValueError):
            evaluate("not_a_frozen_rule", {"SPY": self.rows})
        with self.assertRaises(ValueError):
            evaluate(DONCHIAN, self.rows)

    def test_zero_range_zero_volume_and_overflow_do_not_create_orders(self):
        inputs = [bars([100] * 300, width=0), bars([100] * 300, volume=0), bars([1e150] * 300, volume=1e200, width=1e140)]
        for rows2 in inputs:
            with self.subTest(value=rows2[-1]["volume"]):
                result = evaluate(DONCHIAN, {"SPY": rows2})
                self.assertEqual(result["diagnostics"]["SPY"]["status"], "failed")
                self.assertEqual(result["candidates"], [])


if __name__ == "__main__":
    unittest.main()
