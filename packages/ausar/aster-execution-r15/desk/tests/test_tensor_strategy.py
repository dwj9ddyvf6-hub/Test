"""Operational boundaries for the executable, frozen R11 repair policy."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from types import SimpleNamespace
import unittest

from backend.tensor_strategy import StateRepairPolicy, VOTE_NAMES, rank_signals


MANIFEST = "a" * 64
INPUT_HASH = "b" * 64
AS_OF = 1_800_000_000_000


def panel(symbol="AAPL", frame="1h", index=233, *, votes=None):
    if votes is None:
        votes = [(-1,) * 7, (1, -1, -1, -1, -1, -1, -1),
                 (1, 1, -1, -1, -1, -1, -1), (1, 1, -1, -1, -1, -1, -1)]
    features = []
    for offset, values in enumerate(votes):
        i = index - 3 + offset
        completed = AS_OF - (3 - offset) * 3_600_000
        features.append({
            "symbol": symbol, "frame": frame, "bar_index": i,
            "bar_id": f"{frame}:{symbol}:{i}",
            "timestamp_ms": completed - 3_600_000,
            "completed_at_ms": completed, "usable_at_ms": completed,
            "source_origin_timestamp_ms": 1_700_000_000_000,
            "native_status": "ready", "close": 10.0, "volume": 10_000.0,
            "atr14": .5, "obv_slope5": 20_000.0, "dollar_volume20": 2_000_000.0,
            "votes": values, "bullish_votes": values.count(1),
            "bearish_votes": values.count(-1), "total_votes": sum(v is not None for v in values),
        })
    return {
        "symbol": symbol, "frame": frame, "as_of_ms": AS_OF,
        "source_origin_timestamp_ms": 1_700_000_000_000,
        "source_bar_count": index + 1, "input_sha256": INPUT_HASH,
        "source_manifest_sha256": MANIFEST, "features": features,
    }


class StateRepairTest(unittest.TestCase):
    def setUp(self):
        self.policy = StateRepairPolicy("1h", MANIFEST)

    def decision(self, data=None, **kwargs):
        data = data or panel()
        return self.policy.evaluate(data["symbol"], data, as_of_ms=AS_OF, **kwargs)

    def signal(self, data=None):
        result = self.decision(data)
        self.assertTrue(result.originated, result.reason)
        return result.signal

    def test_frozen_manifest_and_separate_presets(self):
        with self.assertRaises(FrozenInstanceError):
            self.policy.frame = "1wk"
        manifest = self.policy.manifest
        manifest["hold_native_bars"] = 1
        self.assertEqual(self.policy.manifest["hold_native_bars"], 20)
        self.assertNotEqual(self.policy.policy_sha256, StateRepairPolicy("1wk", MANIFEST).policy_sha256)
        for frame in ("1d", "60m", "weekly"):
            with self.assertRaises(ValueError):
                StateRepairPolicy(frame, MANIFEST)
        with self.assertRaises(ValueError):
            StateRepairPolicy("1h", "missing")

    def test_exact_positive_repair_without_glyph_inputs(self):
        signal = self.signal()
        self.assertEqual(signal.balance_change_3, 4)
        self.assertEqual(signal.increasing_vote_count, 2)
        self.assertEqual(signal.balance, -3)
        self.assertAlmostEqual(signal.score, 3.972)
        self.assertEqual(signal.earliest_entry_bar_index, 234)
        self.assertEqual(signal.next_eligible_bar_index, 253)
        self.assertEqual(signal.hold_native_bars, 20)
        self.assertEqual(signal.decision_at_ms, AS_OF)
        self.assertNotIn("buy_green", signal.to_dict())

    def test_dataclass_like_snapshot_and_named_vote_maps(self):
        data = panel()
        for row in data["features"]:
            row["votes"] = dict(zip(VOTE_NAMES, row["votes"]))
        expected = self.signal(data)
        object_data = SimpleNamespace(**{**data, "features": tuple(SimpleNamespace(**row) for row in data["features"])})
        actual = self.policy.evaluate("AAPL", object_data, as_of_ms=AS_OF)
        self.assertEqual(actual.signal, expected)

    def test_vote_turns_count_distinct_channels_and_any_adjacent_increase(self):
        # Two different channels improve; one then falls back. Net B repair is
        # exactly two. Testing only endpoint directions would miss this origin.
        values = [(-1, -1, 1, -1, -1, -1, -1),
                  (1, -1, 1, -1, -1, -1, -1),
                  (1, 1, 1, -1, -1, -1, -1),
                  (-1, 1, 1, -1, -1, -1, -1)]
        signal = self.signal(panel(votes=values))
        self.assertEqual(signal.balance_change_3, 2)
        self.assertEqual(signal.increasing_vote_count, 2)
        oscillating_one = [(-1,) * 7, (1, -1, -1, -1, -1, -1, -1),
                           (-1,) * 7, (1, -1, -1, -1, -1, -1, -1)]
        self.assertEqual(self.decision(panel(votes=oscillating_one)).reason, "no_state_repair")

    def test_null_intermediate_comparisons_false_and_endpoints_require_seven(self):
        values = [(-1,) * 7, (None, 1, -1, -1, -1, -1, -1),
                  (1, 1, 1, -1, -1, -1, -1), (1, 1, 1, -1, -1, -1, -1)]
        signal = self.signal(panel(votes=values))
        self.assertEqual(signal.increasing_vote_count, 2)  # channel0's null transitions are ignored
        for endpoint in (0, 3):
            changed = list(values)
            changed[endpoint] = (None,) + changed[endpoint][1:]
            self.assertEqual(self.decision(panel(votes=changed)).reason, "no_state_repair")

    def test_warmup_and_inclusive_price_liquidity_boundaries(self):
        self.assertEqual(self.decision(panel(index=232)).reason, "warming")
        self.assertTrue(self.decision(panel(index=233)).originated)
        data = panel()
        data["features"][-1].update(close=5.0, dollar_volume20=1_000_000.0, atr14=.00001)
        self.assertTrue(self.decision(data).originated)
        for field, value in (("close", 4.999), ("dollar_volume20", 999_999.999), ("atr14", 0)):
            changed = deepcopy(data)
            changed["features"][-1][field] = value
            self.assertEqual(self.decision(changed).reason, "ineligible_price_liquidity_or_atr")
        data["features"][-1]["native_status"] = "warming"
        self.assertEqual(self.decision(data).reason, "warming")

    def test_cooldown_is_origin_anchored_even_without_entry(self):
        first = self.signal(panel(index=233))
        # Caller records this on opportunity creation, before cash/slot tests.
        denial = self.policy.size_entry(first, execution_price=10, equity=0,
                                       settled_cash=0, open_positions=0)
        self.assertFalse(denial.allowed)
        self.assertEqual(self.decision(panel(index=252), next_eligible_bar_index=first.next_eligible_bar_index).reason, "cooldown")
        self.assertTrue(self.decision(panel(index=253), next_eligible_bar_index=first.next_eligible_bar_index).originated)
        self.assertTrue(self.decision(panel(index=233), next_eligible_bar_index=-1).originated)
        # Evaluation is pure: runtime must retain its cooldown across restarts.
        self.assertTrue(self.decision(panel(index=233)).originated)

    def test_future_clocks_misordered_bars_and_history_origin_fail_closed(self):
        changes = []
        data = panel(); data["as_of_ms"] += 1; changes.append((data, "future_snapshot"))
        data = panel(); data["features"][-1]["usable_at_ms"] += 1; changes.append((data, "invalid_feature_panel"))
        data = panel(); data["features"][1]["completed_at_ms"] = data["features"][1]["timestamp_ms"]; changes.append((data, "invalid_feature_panel"))
        data = panel(); data["features"][1]["bar_index"] += 1; changes.append((data, "noncontiguous_native_indices"))
        data = panel(); data["source_bar_count"] += 1; changes.append((data, "noncontiguous_native_indices"))
        data = panel(); data["features"][1]["bar_id"] = data["features"][0]["bar_id"]; changes.append((data, "nonmonotone_native_bars"))
        data = panel(); data["features"][1]["source_origin_timestamp_ms"] -= 1; changes.append((data, "source_origin_mismatch"))
        data = panel(); data["features"] = data["features"][1:]; changes.append((data, "missing_four_bar_panel"))
        for data, reason in changes:
            with self.subTest(reason=reason):
                self.assertEqual(self.decision(data).reason, reason)

    def test_snapshot_identity_manifest_hash_and_exclusions(self):
        for symbol in ("SPY", "QQQ", "B", "GOLD"):
            self.assertEqual(self.decision(panel(symbol=symbol)).reason, "excluded_symbol")
        self.assertEqual(self.decision(panel(symbol="lower")).reason, "invalid_symbol")
        data = panel(); data["frame"] = "1wk"
        self.assertEqual(self.decision(data).reason, "snapshot_identity_mismatch")
        data = panel(); data["source_manifest_sha256"] = "c" * 64
        self.assertEqual(self.decision(data).reason, "source_manifest_mismatch")
        for field in ("input_sha256", "source_manifest_sha256"):
            data = panel(); data[field] = ""
            self.assertEqual(self.decision(data).reason, "invalid_feature_panel")

    def test_bad_signed_votes_and_nonfinite_numeric_inputs_fail_closed(self):
        for value in (0, True, 1.0, "bullish", 2):
            data = panel()
            data["features"][-1]["votes"] = (value,) + data["features"][-1]["votes"][1:]
            self.assertEqual(self.decision(data).reason, "invalid_feature_panel")
        for field in ("close", "atr14", "volume", "obv_slope5", "dollar_volume20"):
            for value in (float("nan"), float("inf"), True, "10"):
                data = panel(); data["features"][-1][field] = value
                self.assertEqual(self.decision(data).reason, "invalid_feature_panel")
        for field in ("volume", "dollar_volume20", "atr14"):
            data = panel(); data["features"][-1][field] = -1
            self.assertEqual(self.decision(data).reason, "invalid_feature_panel")
        data = panel(); data["features"][-1]["bullish_votes"] += 1
        self.assertEqual(self.decision(data).reason, "invalid_feature_panel")
        data = panel(); data["features"][-1]["votes"] = {"wrong": 1}
        self.assertEqual(self.decision(data).reason, "invalid_feature_panel")
        data = panel(); del data["features"][-1]["volume"]
        self.assertEqual(self.decision(data).reason, "invalid_feature_panel")

    def test_fixed_priority_clip_zero_volume_and_lexical_ties(self):
        data = panel(); data["features"][-1].update(volume=0, obv_slope5=1_000_000)
        self.assertAlmostEqual(self.signal(data).score, 3.97)
        data["features"][-1].update(volume=1, obv_slope5=1_000_000)
        self.assertAlmostEqual(self.signal(data).score, 3.98)
        data["features"][-1]["obv_slope5"] = -1_000_000
        self.assertAlmostEqual(self.signal(data).score, 3.96)
        a = self.signal(panel(symbol="AAPL"))
        z = self.signal(panel(symbol="ZM"))
        high = replace(self.signal(panel(symbol="MSFT")), score=a.score + 1)
        self.assertEqual([s.symbol for s in rank_signals((z, a, high))], ["MSFT", "AAPL", "ZM"])
        self.assertEqual(rank_signals(()), ())
        with self.assertRaises(ValueError):
            rank_signals((a, a))
        weekly = StateRepairPolicy("1wk", MANIFEST).evaluate("AAPL", panel(frame="1wk"), as_of_ms=AS_OF).signal
        with self.assertRaises(ValueError):
            rank_signals((a, weekly))
        with self.assertRaises(ValueError):
            rank_signals((replace(a, score=float("nan")),))

    def test_origin_identity_stable_on_input_revision_with_provenance_preserved(self):
        original = self.signal()
        revised = panel(); revised["input_sha256"] = "c" * 64
        changed = self.signal(revised)
        self.assertEqual(original.signal_id, changed.signal_id)
        self.assertNotEqual(original.input_sha256, changed.input_sha256)
        self.assertEqual(self.signal().to_dict(), original.to_dict())
        self.assertNotEqual(self.signal(panel(index=234)).signal_id, original.signal_id)

    def test_same_visible_prefix_is_invariant_to_later_decision_clock(self):
        data = panel()
        early = self.policy.evaluate("AAPL", data, as_of_ms=AS_OF)
        later = self.policy.evaluate("AAPL", data, as_of_ms=AS_OF + 10_000_000)
        self.assertEqual(early, later)
        # Appending a future-only snapshot cannot leak its vote changes into
        # the decision at the original availability boundary.
        future = panel(index=234)
        future["as_of_ms"] += 3_600_000
        future["features"][-1]["usable_at_ms"] += 3_600_000
        self.assertEqual(self.policy.evaluate("AAPL", future, as_of_ms=AS_OF).reason, "future_snapshot")

    def test_real_native_adapter_component_and_reference_rule_conformance(self):
        from backend.tensor_engine import (ENGINE_ROOT, SOURCE_MANIFEST_SHA256,
            NativeBar, extract_native_feature_rows, extract_tensor_features)

        for frame in ("1h", "1wk"):
            raw = json.loads((ENGINE_ROOT / "fixtures" / f"AMD-{frame}-completed.json").read_text())
            bars = [NativeBar(**bar) for bar in raw["bars"]]
            complete = extract_native_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms)
            policy = StateRepairPolicy(frame, SOURCE_MANIFEST_SHA256)
            decision = policy.evaluate("AMD", complete.snapshot, as_of_ms=bars[-1].usable_at_ms)
            rows = complete.rows

            # Direct translation of the sealed pandas mask, with no labels,
            # ranking, sizing, or financial outcomes used to pick a case.
            def native_mask(index):
                current, oldest = rows[index], rows[index - 3]
                repair = current["bullish_votes"] - current["bearish_votes"] - oldest["bullish_votes"] + oldest["bearish_votes"]
                channels = 0
                for name in VOTE_NAMES:
                    values = [rows[j]["vote_" + name] for j in range(index - 3, index + 1)]
                    channels += any(a is not None and b is not None and b > a for a, b in zip(values, values[1:]))
                return (index >= 233 and current["close"] >= 5 and current["dollar_volume20"] >= 1_000_000
                        and current["atr14"] > 0 and current["completed_at"] <= current["usable_at"]
                        and current["total_votes"] == oldest["total_votes"] == 7
                        and repair >= 2 and channels >= 2)

            self.assertEqual(decision.originated, native_mask(len(rows) - 1))
            positive = next((i for i in range(233, len(rows)) if native_mask(i)), None)
            if positive is not None:
                prefix = bars[:positive + 1]
                snapshot = extract_tensor_features("AMD", frame, prefix, prefix[-1].usable_at_ms)
                actual = policy.evaluate("AMD", snapshot, as_of_ms=prefix[-1].usable_at_ms)
                self.assertTrue(actual.originated, actual.reason)
                self.assertEqual(actual.signal.origin_bar_index, positive)
                self.assertEqual(actual.signal.balance_change_3, snapshot.state_repair_change)
                self.assertEqual(actual.signal.increasing_vote_count, snapshot.increasing_vote_count)

    def test_bar_count_exit_uses_entry_and_handles_calendar_gaps(self):
        self.assertEqual(self.policy.exit_bar_index(234), 254)
        self.assertFalse(self.policy.exit_due(234, 253))
        self.assertTrue(self.policy.exit_due(234, 254))
        self.assertTrue(self.policy.exit_due(234, 257))
        # A delayed, documented fill anchors to its actual native entry bar.
        self.assertEqual(self.policy.exit_bar_index(236), 256)
        weekly = StateRepairPolicy("1wk", MANIFEST)
        self.assertEqual(weekly.exit_bar_index(234), 254)
        for value in (-1, True, 234.0):
            with self.assertRaises(ValueError):
                self.policy.exit_bar_index(value)

    def test_size_total_debit_cost_and_one_share_boundary(self):
        signal = self.signal()
        sized = self.policy.size_entry(signal, execution_price=10, equity=100_000,
                                       settled_cash=100_000, open_positions=0)
        self.assertEqual(sized.capped_budget, Decimal("10000"))
        self.assertEqual(sized.shares, 999)
        self.assertEqual(sized.gross, Decimal("9990"))
        self.assertEqual(sized.fee, Decimal("9.990"))
        self.assertEqual(sized.total_debit, Decimal("9999.990"))
        self.assertEqual(sized.settled_cash_after + sized.gross + sized.fee, Decimal("100000"))
        one = self.policy.size_entry(signal, execution_price=10, equity=1000,
                                     settled_cash="10.01", open_positions=9)
        self.assertEqual(one.shares, 1)
        below = self.policy.size_entry(signal, execution_price=10, equity=1000,
                                       settled_cash="10.009999", open_positions=9)
        self.assertEqual(below.shares, 0)
        self.assertEqual(below.reason, "insufficient_settled_cash_or_capacity")

    def test_liquidity_cash_slots_and_existing_position_caps(self):
        signal = replace(self.signal(), dollar_volume20=1_000_000)
        liquid = self.policy.size_entry(signal, execution_price=100, equity=1_000_000,
                                        settled_cash=1_000_000, open_positions=0)
        self.assertEqual(liquid.capped_budget, Decimal("10000"))
        self.assertEqual(liquid.shares, 99)
        cash = self.policy.size_entry(signal, execution_price=100, equity=1_000_000,
                                      settled_cash=500, open_positions=0)
        self.assertEqual(cash.capped_budget, Decimal("500"))
        self.assertEqual(cash.shares, 4)
        full = self.policy.size_entry(signal, execution_price=100, equity=1_000_000,
                                      settled_cash=1_000_000, open_positions=10)
        self.assertEqual(full.reason, "positions_full")
        self.assertEqual(full.total_debit, 0)
        held = self.policy.size_entry(signal, execution_price=100, equity=1_000_000,
                                      settled_cash=1_000_000, open_positions=0, already_held=True)
        self.assertEqual(held.reason, "already_held")

    def test_sequential_sizing_conserves_cash_after_all_reservations(self):
        cash = Decimal("1000")
        debits = Decimal(0)
        for i in range(10):
            signal = self.signal(panel(symbol=f"S{i}"))
            sized = self.policy.size_entry(signal, execution_price="10.03", equity=1000,
                                           settled_cash=cash, open_positions=i)
            self.assertLessEqual(sized.total_debit, sized.capped_budget)
            self.assertGreaterEqual(sized.settled_cash_after, 0)
            self.assertEqual(sized.shares, int(sized.shares))
            cash = sized.settled_cash_after
            debits += sized.total_debit
        self.assertEqual(cash + debits, Decimal("1000"))

    def test_size_rejects_invalid_economics_and_foreign_policy(self):
        signal = self.signal()
        defaults = {"execution_price": 10, "equity": 1000,
                    "settled_cash": 1000, "open_positions": 0}
        for key, value in (("execution_price", 0), ("execution_price", float("nan")),
                           ("equity", -1), ("equity", True), ("settled_cash", "Infinity"),
                           ("settled_cash", -1), ("open_positions", 1.0), ("open_positions", True)):
            with self.subTest(key=key, value=value), self.assertRaises((ValueError, ArithmeticError)):
                self.policy.size_entry(signal, **{**defaults, key: value})
        with self.assertRaises(ValueError):
            StateRepairPolicy("1wk", MANIFEST).size_entry(signal, **defaults)


if __name__ == "__main__":
    unittest.main()
