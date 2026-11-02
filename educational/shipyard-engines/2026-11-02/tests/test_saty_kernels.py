"""Direct synthetic checks of the relocated in-memory Saty research kernels."""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python' / 'saty'))

from saty_reference import Bar, Config, Indicators  # noqa: E402
from saty_system.models import Signal  # noqa: E402
from saty_system.routing import candidate_sort_key  # noqa: E402
from saty_system.strategies import StrategyConfig, StrategyEngine  # noqa: E402
from saty_system.structure import FeatureBook, StructureConfig  # noqa: E402

UTC = timezone.utc


def synthetic_bar(index: int, *, close: float | None = None) -> Bar:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=5 * index)
    c = 100.0 + index if close is None else close
    return Bar(start, start + timedelta(minutes=5), c - 0.25, c + 1.0, c - 1.0, c, 100.0)


class SatyKernelTests(unittest.TestCase):
    def test_indicators_known_answer_ema_atr_and_caller_supplied_bar_proxies(self) -> None:
        cfg = Config(symbol='SYN', ribbon_version='legacy')
        indicator = Indicators(cfg)
        last = None
        expected_ema8 = 100.0
        for i in range(14):
            bar = synthetic_bar(i)
            bar.validate()
            last = indicator.update(bar)
            if i:
                expected_ema8 += (2.0 / 9.0) * (bar.close - expected_ema8)
        self.assertIsNotNone(last)
        assert last is not None
        self.assertAlmostEqual(last.atr or 0, 2.0, places=12)
        self.assertAlmostEqual(last.ema[8], expected_ema8, places=12)
        self.assertAlmostEqual(last.buying_proxy, 50.0, places=12)
        self.assertAlmostEqual(last.selling_proxy, 50.0, places=12)
        self.assertTrue(last.volume_proxy_valid)

    def test_bar_contract_rejects_bad_ohlc_and_naive_clock(self) -> None:
        good = synthetic_bar(0)
        bad = Bar(good.start, good.end, good.open, good.low - 2, good.low, good.close, good.volume)
        with self.assertRaises(ValueError):
            bad.validate()
        naive = Bar(good.start.replace(tzinfo=None), good.end, good.open, good.high, good.low, good.close, good.volume)
        with self.assertRaises(ValueError):
            naive.validate()

    def test_feature_book_and_strategy_state_are_in_memory_roundtrips(self) -> None:
        book = FeatureBook(StructureConfig(required_timeframes=('5m',), warmup_bars=21))
        empty = book.dump_state()
        restored_book = FeatureBook(StructureConfig(required_timeframes=('5m',), warmup_bars=21))
        restored_book.load_state(empty)
        self.assertEqual(restored_book.dump_state(), empty)
        tampered = dict(empty)
        tampered['streams'] = [{'symbol': 'SYN'}]
        with self.assertRaises(ValueError):
            restored_book.load_state(tampered)

        cfg = StrategyConfig(enabled=('compression_breakout',), warmup_bars=21)
        engine = StrategyEngine(cfg)
        state = engine.dump_state()
        restarted = StrategyEngine(cfg)
        restarted.load_state(state)
        self.assertEqual(restarted.dump_state(), state)
        broken = dict(state)
        broken['config'] = 'not-the-same-config'
        with self.assertRaises(ValueError):
            StrategyEngine(cfg).load_state(broken)

    def test_signal_geometry_and_router_ordering_contract(self) -> None:
        at = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
        valid = Signal('synthetic-id', 'SYN', '5m', 'pivot_pullback', 1, at, at,
                       at + timedelta(minutes=10), 100.0, 99.0, (102.0, 104.0),
                       1.0, 100.0, 'caller_reference')
        valid.validate()
        key = candidate_sort_key(valid)
        self.assertEqual(key, candidate_sort_key(valid))
        self.assertEqual(len(key), 7)
        better = Signal('better-id', 'SYN', '5m', 'pivot_pullback', 1, at, at,
                        at + timedelta(minutes=10), 100.0, 99.0, (106.0,),
                        1.0, 100.0, 'caller_reference')
        self.assertLess(candidate_sort_key(better), candidate_sort_key(valid),
                        'stronger declared net reward/risk ranks first')
        invalid = Signal('bad-id', 'SYN', '5m', 'pivot_pullback', 1, at, at,
                         at + timedelta(minutes=10), 100.0, 99.0, (98.0,),
                         1.0, 100.0, 'caller_reference')
        with self.assertRaises(ValueError):
            candidate_sort_key(invalid)


if __name__ == '__main__':
    unittest.main()
