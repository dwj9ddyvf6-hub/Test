"""Exact state transport parity, causal clocks and bounded worker behavior."""
import dataclasses
import gzip
import json
import subprocess
import hashlib
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from backend import tensor_engine as engine
from backend.tensor_runtime import historical_state_cooldown


FIXTURES = engine.ENGINE_ROOT / "fixtures"
BASE_KEYS = engine.STATE_ROW_KEYS[:26]


def fixture_bars(frame, count=330):
    body = json.loads((FIXTURES / f"AMD-{frame}-completed.json").read_text())
    return [engine.NativeBar(**b) for b in body["bars"][:count]]


def source_bars(path):
    body = json.loads(gzip.decompress(Path(path).read_bytes()))
    return [engine.NativeBar(
        timestamp_ms=b["timestamp"] * 1000,
        completed_at_ms=b["completedAt"] * 1000,
        usable_at_ms=b["usableAt"] * 1000,
        open=b["open"], high=b["high"], low=b["low"], close=b["close"], volume=b["volume"],
    ) for b in body["bars"]]


class TensorFastStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(gzip.decompress((FIXTURES / "REFERENCE_NATIVE_FEATURES.json.gz").read_bytes()))

    def assert_reference(self, history, expected, bars):
        self.assertEqual(len(history.rows), len(bars))
        for i, (row, reference) in enumerate(zip(history.rows, expected)):
            self.assertEqual(set(row), set(engine.STATE_ROW_KEYS))
            self.assertEqual({k: row[k] for k in BASE_KEYS}, {k: reference[k] for k in BASE_KEYS})
            self.assertEqual(row["bar_id"], f"AMD:{history.snapshot.frame}:{bars[i].timestamp_ms}")
            self.assertEqual(row["timestamp_ms"], bars[i].timestamp_ms)
            self.assertEqual(row["completed_at_ms"], bars[i].completed_at_ms)
            self.assertEqual(row["usable_at_ms"], bars[i].usable_at_ms)
            self.assertEqual(row["executable_at_ms"], bars[i].executable_at_ms)
            self.assertEqual(row["source_origin_timestamp_ms"], bars[0].timestamp_ms)
            self.assertEqual(row["balance"], reference["bullish_votes"] - reference["bearish_votes"])

    def test_entire_real_hourly_and_weekly_state_rows_match_original_exporter(self):
        for frame in ("1h", "1wk"):
            with self.subTest(frame=frame):
                bars = fixture_bars(frame)
                fast = engine.extract_state_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms)
                full = engine.extract_native_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms)
                self.assert_reference(fast, self.reference[frame], bars)
                self.assertEqual(fast.snapshot, full.snapshot)
                self.assertEqual(historical_state_cooldown(fast.rows, len(bars) - 1),
                                 historical_state_cooldown(full.rows, len(bars) - 1))

    def test_warmup_boundaries_and_complete_prefixes_are_identical(self):
        for frame in ("1h", "1wk"):
            for count in (1, 3, 4, 13, 14, 19, 20, 34, 35, 233, 234, 265, 300):
                with self.subTest(frame=frame, count=count):
                    bars = fixture_bars(frame, count)
                    fast = engine.extract_state_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms)
                    if count < (4 if frame == "1wk" else 35):
                        expected = engine.extract_native_feature_rows("AMD", frame, bars, bars[-1].usable_at_ms).rows
                    else:
                        expected = self.reference[frame][:count]
                    self.assert_reference(fast, expected, bars)
                    self.assertEqual(fast.snapshot.latest.strategy_ready, count >= 234)

    def test_future_wild_price_volume_changes_leave_every_past_state_row_unchanged(self):
        for frame in ("1h", "1wk"):
            with self.subTest(frame=frame):
                bars = fixture_bars(frame)
                changed = bars[:234] + [dataclasses.replace(
                    b, open=b.open * (10 + i), high=b.high * (10 + i),
                    low=b.low * (10 + i), close=b.close * (10 + i), volume=b.volume * (50 + i),
                ) for i, b in enumerate(bars[234:])]
                fast = engine.extract_state_feature_rows("AMD", frame, changed, changed[-1].usable_at_ms)
                self.assert_reference(dataclasses.replace(fast, rows=fast.rows[:234]), self.reference[frame][:234], bars[:234])
                self.assertNotEqual(fast.rows[-1]["close"], self.reference[frame][-1]["close"])

    def test_millisecond_availability_and_observed_open_are_preserved(self):
        bars = fixture_bars("1h", 234)
        bars[-1] = dataclasses.replace(bars[-1], usable_at_ms=bars[-1].usable_at_ms + 125,
                                      executable_at_ms=bars[-1].timestamp_ms + 250)
        fast = engine.extract_state_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms)
        full = engine.extract_native_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms)
        self.assertEqual(fast.snapshot, full.snapshot)
        canonical = {"schema": "aster-tensor-native-request/1", "symbol": "AMD", "frame": "1h",
                     "as_of_ms": bars[-1].usable_at_ms, "bars": [dataclasses.asdict(b) for b in bars]}
        self.assertEqual(fast.snapshot.input_sha256,
                         hashlib.sha256(json.dumps(canonical, separators=(",", ":"), allow_nan=False).encode()).hexdigest())
        self.assertEqual(fast.rows[-1]["usable_at_ms"], bars[-1].usable_at_ms)
        self.assertEqual(fast.rows[-1]["usable_at"], bars[-1].usable_at_ms // 1000 + 1)
        self.assertEqual(fast.rows[-1]["executable_at_ms"], bars[-1].executable_at_ms)
        with patch.object(engine, "_run_state_process") as process, self.assertRaises(engine.TensorEngineError):
            engine.extract_state_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms - 1)
        process.assert_not_called()

    def test_reusable_workers_do_not_leak_one_request_history_into_another(self):
        bars = fixture_bars("1h")
        variants = [("1h", 234), ("1wk", 265), ("1h", 300), ("1wk", 35)] * 3
        def run(spec):
            frame, count = spec
            rows = fixture_bars(frame, count)
            return engine.extract_state_feature_rows("AMD", frame, rows, rows[-1].usable_at_ms)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(run, variants))
        for history, (frame, count) in zip(results, variants):
            self.assert_reference(history, self.reference[frame][:count], fixture_bars(frame, count))
        self.assertLessEqual(len(engine._STATE_ALL_WORKERS), engine._STATE_WORKER_LIMIT)

    def test_fast_timeout_and_failed_child_fail_closed_then_recover(self):
        bars = fixture_bars("1h", 234)
        args = ("AMD", "1h", bars, bars[-1].usable_at_ms)
        with self.assertRaises(engine.TensorEngineError):
            engine.extract_state_feature_rows(*args, timeout_seconds=0.000001)
        recovered = engine.extract_state_feature_rows(*args)
        self.assertEqual(recovered.snapshot.latest.bar_index, 233)
        with patch.object(engine, "_run_state_process", side_effect=OSError("isolated fixture failure")), \
                self.assertRaises(engine.TensorEngineError):
            engine.extract_state_feature_rows(*args)

    def test_real_nonresponsive_child_and_invalid_framing_are_bounded(self):
        real_popen = subprocess.Popen
        cases = (
            "process.stdin.resume();",  # Accepts the request and never replies.
            "process.stdin.once('data', () => process.stdout.write('{}\\n{}\\n'));",
        )
        for program in cases:
            def spawn(args, **kwargs):
                return real_popen([args[0], "--eval", program], **kwargs)
            with self.subTest(program=program), patch.object(engine.subprocess, "Popen", side_effect=spawn):
                worker = engine._StateWorker("node", engine.ENGINE_ROOT)
                started = time.monotonic()
                try:
                    with self.assertRaises(engine.TensorEngineError):
                        worker.request(b"{}", started + 0.15)
                    self.assertLess(time.monotonic() - started, 1)
                finally:
                    worker.close()
                self.assertIsNotNone(worker.process.poll())

    def test_capacity_timeout_does_not_spawn_an_unbounded_child(self):
        for _ in range(engine._STATE_WORKER_LIMIT):
            engine._STATE_WORKER_SLOTS.acquire()
        try:
            with patch.object(engine.subprocess, "Popen") as process, self.assertRaises(engine.TensorEngineError):
                engine._run_state_process("node", b"{}", 0.01)
            process.assert_not_called()
        finally:
            for _ in range(engine._STATE_WORKER_LIMIT):
                engine._STATE_WORKER_SLOTS.release()

    def test_unexpected_or_inconsistent_state_output_is_rejected(self):
        bars = fixture_bars("1h", 234)
        args = ("AMD", "1h", bars, bars[-1].usable_at_ms)
        encoded = json.dumps({"schema": "aster-tensor-native-request/1", "symbol": "AMD", "frame": "1h",
            "as_of_ms": bars[-1].usable_at_ms, "bars": [dataclasses.asdict(b) for b in bars], "include_full_rows": True}).encode()
        original = json.loads(engine._run_state_process("node", encoded, 30))
        for kind in ("missing_header", "bad_ordinal", "bad_vote_count", "bad_balance", "bad_receipt", "bad_snapshot"):
            result = json.loads(json.dumps(original))
            if kind == "missing_header": result["full_header"] = result["full_header"][:-1]
            elif kind == "bad_ordinal": result["full_rows"][0]["bar_index"] = 1
            elif kind == "bad_vote_count": result["full_rows"][100]["total_votes"] = 0
            elif kind == "bad_balance": result["full_rows"][100]["balance"] = 100
            elif kind == "bad_receipt": result["full_rows"][100]["usable_at_ms"] -= 1
            elif kind == "bad_snapshot": result["features"][-1]["obv_slope5"] += 1
            with self.subTest(kind=kind), patch.object(engine, "_run_state_process", return_value=json.dumps(result).encode()), \
                    self.assertRaises(engine.TensorEngineError):
                engine.extract_state_feature_rows(*args)

    def test_full_restored_hourly_seed_has_exact_every_row_and_greedy_clock_parity(self):
        path = Path("data/research-seed-r11/native-inputs/bars/1h/AMD.json.gz")
        if not path.is_file():
            self.skipTest("full immutable native input cache not installed")
        bars = source_bars(path)
        fast = engine.extract_state_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms)
        full = engine.extract_native_feature_rows("AMD", "1h", bars, bars[-1].usable_at_ms)
        self.assert_reference(fast, full.rows, bars)
        self.assertEqual(fast.snapshot, full.snapshot)
        for before in (234, 400, 1200, 2600, len(bars) - 1):
            self.assertEqual(historical_state_cooldown(fast.rows, before), historical_state_cooldown(full.rows, before))


if __name__ == "__main__":
    unittest.main()
