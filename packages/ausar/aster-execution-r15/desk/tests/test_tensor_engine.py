import dataclasses
import gzip
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import tensor_engine as engine


FIXTURES = engine.ENGINE_ROOT / "fixtures"


def fixture_bars(frame, count=330):
    body = json.loads((FIXTURES / f"AMD-{frame}-completed.json").read_text())
    return [engine.NativeBar(**b) for b in body["bars"][:count]]


class TensorEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.references = json.loads(gzip.decompress((FIXTURES / "REFERENCE_NATIVE_FEATURES.json.gz").read_bytes()))

    def test_source_closure_matches_sealed_research_bytes(self):
        manifest = engine.verify_engine_source()
        exact = [x for x in manifest["files"] if x["byte_identical_to_sealed_r11"]]
        self.assertEqual(len(exact), 24)
        self.assertEqual(manifest["frozen_module_count"], 20)
        by_name = {x["path"]: x for x in exact}
        self.assertEqual(by_name["engine/frozen-v690/lib/anna-replica.mjs"]["sha256"],
                         "aa5c902509b9483b6b25cbb5a81c4978f434c7fb0bd58ec21874a3ffbe04ddb6")
        self.assertEqual(by_name["scripts/replay_native_features.mjs"]["sha256"],
                         "4926490334864a440f88857565e62d6b6d8194f65307226bf645bc3f7ab63f82")
        research = Path("/workspace/tensor-forensic-edge-study-r11-2026-10-09")
        if research.is_dir():
            for entry in exact:
                self.assertEqual((engine.ENGINE_ROOT / entry["path"]).read_bytes(),
                                 (research / entry["sealed_r11_path"]).read_bytes())

    def test_real_fixture_and_reference_hashes(self):
        provenance = json.loads((FIXTURES / "PROVENANCE.json").read_text())
        for entry in provenance["fixtures"]:
            self.assertEqual(hashlib.sha256((FIXTURES / entry["fixture"]).read_bytes()).hexdigest(),
                             entry["fixture_sha256"])
        reference = provenance["reference"]
        self.assertEqual(hashlib.sha256((FIXTURES / reference["path"]).read_bytes()).hexdigest(), reference["sha256"])

    def test_all_93_fields_match_original_exporter_for_real_frames(self):
        for frame in engine.SUPPORTED_FRAMES:
            with self.subTest(frame=frame):
                bars = fixture_bars(frame)
                result = engine.extract_native_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms)
                self.assertEqual(list(result.rows), self.references[frame])
                self.assertEqual(len(result.rows[0]), 93)
                self.assertEqual(result.snapshot.source_bar_count, 330)
                self.assertEqual(result.snapshot.source_origin_timestamp_ms, bars[0].timestamp_ms)
                self.assertEqual([x.bar_index for x in result.snapshot.features], [326, 327, 328, 329])
                for feature, row in zip(result.snapshot.features, result.rows[-4:]):
                    self.assertEqual(feature.votes, tuple(row["vote_" + k] for k in engine.VOTE_NAMES))
                    self.assertEqual(feature.balance, row["bullish_votes"] - row["bearish_votes"])
                    self.assertEqual(feature.atr14, row["atr14"])
                    self.assertEqual(feature.obv_slope5, row["obv_slope5"])
                    self.assertEqual(feature.dollar_volume20, row["dollar_volume20"])

    def test_full_and_component_snapshots_bind_same_input(self):
        bars = fixture_bars("1h", 234)
        full = engine.extract_native_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms)
        compact = engine.extract_tensor_features("AMD", "1h", bars, bars[-1].usable_at_ms)
        self.assertEqual(full.snapshot, compact)
        self.assertTrue(compact.latest.strategy_ready)
        self.assertEqual(compact.source_manifest_sha256, engine.SOURCE_MANIFEST_SHA256)

    def test_complete_prefixes_do_not_repaint_against_later_real_bars(self):
        for frame in engine.SUPPORTED_FRAMES:
            for count in (4 if frame == "1wk" else 35, 233, 234, 265, 300):
                with self.subTest(frame=frame, count=count):
                    bars = fixture_bars(frame, count)
                    result = engine.extract_native_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms)
                    self.assertEqual(list(result.rows), self.references[frame][:count])
                    self.assertEqual(result.snapshot.latest.strategy_ready, count >= 234)

    def test_future_price_and_volume_perturbations_leave_all_past_features_unchanged(self):
        for frame in engine.SUPPORTED_FRAMES:
            with self.subTest(frame=frame):
                bars = fixture_bars(frame)
                changed = bars[:234] + [dataclasses.replace(
                    b, open=b.open * (10 + i), high=b.high * (10 + i),
                    low=b.low * (10 + i), close=b.close * (10 + i), volume=b.volume * (50 + i),
                ) for i, b in enumerate(bars[234:])]
                result = engine.extract_native_feature_rows("AMD", frame, changed, changed[-1].usable_at_ms)
                self.assertEqual(list(result.rows[:234]), self.references[frame][:234])
                self.assertNotEqual(result.rows[-1]["close"], self.references[frame][-1]["close"])

    def test_atr_obv_slope_and_dollar_volume_match_independent_arithmetic(self):
        for frame in engine.SUPPORTED_FRAMES:
            bars = fixture_bars(frame)
            result = engine.extract_tensor_features("AMD", frame, bars, bars[-1].usable_at_ms)
            ranges = [b.high - b.low if i == 0 else max(
                b.high - b.low, abs(b.high - bars[i - 1].close), abs(b.low - bars[i - 1].close)
            ) for i, b in enumerate(bars)]
            atr = sum(ranges[:14]) / 14
            for true_range in ranges[14:]:
                atr = (atr * 13 + true_range) / 14
            obv = [0.0]
            for previous, current in zip(bars, bars[1:]):
                sign = 1 if current.close > previous.close else -1 if current.close < previous.close else 0
                obv.append(obv[-1] + sign * current.volume)
            last_five = obv[-5:]
            slope = sum((i - 2) * (v - sum(last_five) / 5) for i, v in enumerate(last_five)) / 10
            dv20 = sum(b.close * b.volume for b in bars[-20:]) / 20
            self.assertAlmostEqual(result.latest.atr14, atr, places=12)
            self.assertAlmostEqual(result.latest.obv_slope5, slope, places=7)
            # Native JavaScript and independent Python can differ by a few ULP
            # when summing $23bn weekly volume; exact exporter parity is checked
            # separately for all 93 fields above.
            self.assertTrue(math.isclose(result.latest.dollar_volume20, dv20, rel_tol=1e-12, abs_tol=1e-7))

    def test_full_four_channel_history_and_any_adjacent_increase(self):
        bars = fixture_bars("1h", 234)
        snapshot = engine.extract_tensor_features("AMD", "1h", bars, bars[-1].usable_at_ms)
        votes = ((-1, 1, -1, -1, -1, -1, -1), (1, 1, None, -1, -1, -1, -1),
                 (-1, 1, -1, -1, -1, -1, -1), (-1, 1, 1, -1, -1, -1, -1))
        features = tuple(dataclasses.replace(
            f, votes=v, bullish_votes=sum(x == 1 for x in v), bearish_votes=sum(x == -1 for x in v),
            total_votes=sum(x is not None for x in v),
        ) for f, v in zip(snapshot.features, votes))
        revised = dataclasses.replace(snapshot, features=features)
        self.assertEqual(revised.increasing_vote_count, 2)  # stoch increased then reversed; DI increases after its null.
        self.assertEqual(revised.state_repair_change, 2)
        self.assertEqual(revised.latest.vote_values["stoch"], -1)

    def test_warming_history_is_explicit_and_not_financially_ready(self):
        bars = fixture_bars("1h", 3)
        result = engine.extract_tensor_features("AMD", "1h", bars, bars[-1].usable_at_ms)
        self.assertEqual(result.latest.native_status, "warming")
        self.assertFalse(result.latest.strategy_ready)
        self.assertEqual(result.latest.votes, (None,) * 7)
        self.assertIsNone(result.state_repair_change)
        self.assertEqual(result.increasing_vote_count, 0)

    def test_millisecond_first_seen_clock_is_preserved_and_conservatively_exported(self):
        bars = fixture_bars("1h", 35)
        bars[-1] = dataclasses.replace(bars[-1], usable_at_ms=bars[-1].usable_at_ms + 125)
        result = engine.extract_native_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms)
        self.assertEqual(result.snapshot.latest.usable_at_ms, bars[-1].usable_at_ms)
        self.assertEqual(result.rows[-1]["usable_at"], math.ceil(bars[-1].usable_at_ms / 1000))
        with self.assertRaises(engine.TensorEngineError):
            engine.extract_tensor_features("AMD", "1h", bars, bars[-1].usable_at_ms - 1)

    def test_invalid_and_future_bars_fail_before_subprocess(self):
        bars = fixture_bars("1h", 35)
        invalid = [
            dataclasses.replace(bars[-1], usable_at_ms=bars[-1].usable_at_ms + 1),
            dataclasses.replace(bars[-1], completed_at_ms=bars[-1].timestamp_ms),
            dataclasses.replace(bars[-1], timestamp_ms=bars[-2].timestamp_ms),
            dataclasses.replace(bars[-1], volume=-1),
            dataclasses.replace(bars[-1], volume=10**400),
            dataclasses.replace(bars[-1], close=float("nan")),
            dataclasses.replace(bars[-1], high=bars[-1].low / 2),
            dataclasses.replace(bars[-1], executable_at_ms=bars[-1].completed_at_ms),
            dataclasses.replace(bars[-1], timestamp_ms=bars[-1].timestamp_ms + 1),
        ]
        with patch.object(engine.subprocess, "run") as process:
            for value in invalid:
                with self.subTest(value=value), self.assertRaises(engine.TensorEngineError):
                    engine.extract_tensor_features("AMD", "1h", bars[:-1] + [value], bars[-1].usable_at_ms)
            process.assert_not_called()

    def test_invalid_symbol_frame_empty_history_and_timeout_fail_closed(self):
        bars = fixture_bars("1h", 35)
        with patch.object(engine.subprocess, "run") as process:
            cases = [("AMD", "2h", bars, 30), ("amd", "1h", bars, 30),
                     ("AMD", "1h", [], 30), ("AMD", "1h", bars, 0), ("AMD", "1h", bars, float("nan"))]
            for symbol, frame, values, timeout in cases:
                with self.subTest(symbol=symbol, frame=frame), self.assertRaises(engine.TensorEngineError):
                    engine.extract_tensor_features(symbol, frame, values, bars[-1].usable_at_ms, timeout)
            process.assert_not_called()

    def test_missing_node_process_failure_timeout_and_invalid_output_fail_closed(self):
        bars = fixture_bars("1h", 35)
        args = ("AMD", "1h", bars, bars[-1].usable_at_ms)
        with patch.object(engine.shutil, "which", return_value=None), self.assertRaises(engine.TensorEngineError):
            engine.extract_tensor_features(*args)
        with patch.object(engine.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 30)), \
                self.assertRaises(engine.TensorEngineError):
            engine.extract_tensor_features(*args)
        with patch.object(engine.subprocess, "run", side_effect=OSError("fixture process unavailable")), \
                self.assertRaises(engine.TensorEngineError):
            engine.extract_tensor_features(*args)
        for code, output in [(1, b""), (0, b"not JSON"), (0, b"{}"),
                             (0, b'{"schema":"aster-tensor-native-result/1","features":[]}')]:
            process = subprocess.CompletedProcess(["node"], code, output, b"private fixture output")
            with self.subTest(code=code, output=output), patch.object(engine.subprocess, "run", return_value=process), \
                    self.assertRaises(engine.TensorEngineError):
                engine.extract_tensor_features(*args)

    def test_source_tamper_is_detected_without_touching_sealed_or_installed_sources(self):
        manifest = engine.verify_engine_source()
        with tempfile.TemporaryDirectory(prefix="tensor-native-integrity-") as directory:
            root = Path(directory)
            shutil.copyfile(engine.ENGINE_ROOT / "SOURCE_MANIFEST.json", root / "SOURCE_MANIFEST.json")
            for entry in manifest["files"]:
                destination = root / entry["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(engine.ENGINE_ROOT / entry["path"], destination)
            target = root / "engine/frozen-v690/lib/anna-replica.mjs"
            target.write_bytes(target.read_bytes() + b"\n// fixture mutation\n")
            with patch.object(engine, "ENGINE_ROOT", root), patch.object(engine.subprocess, "run") as process, \
                    self.assertRaises(engine.TensorEngineError):
                engine.extract_tensor_features("AMD", "1h", fixture_bars("1h", 35), fixture_bars("1h", 35)[-1].usable_at_ms)
            process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
