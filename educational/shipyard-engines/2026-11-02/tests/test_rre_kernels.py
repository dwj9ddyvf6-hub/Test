"""Direct synthetic checks of the in-memory RRE core and RRE1/2/3 policies."""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from python.rre.raschke_core import Bar, Core, Session
from python.rre.raschke_engine import PolicyConfig, PolicyEngine, PriorSessionReference

UTC = timezone.utc


def fixture_calendar():
    prior_open = datetime(2024, 1, 1, 14, 30, tzinfo=UTC)
    prior = Session('SYN-PREV', prior_open, prior_open + timedelta(hours=6, minutes=30))
    current_open = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    session = Session('SYN-CURRENT', current_open, current_open + timedelta(hours=6, minutes=30), previous_id=prior.id)
    reference = PriorSessionReference('SYN', session.id, prior, current_open,
                                      101.0, 99.0, 100.0, 'series-fixture', 'calendar-fixture', True)
    return prior, session, reference


def synthetic_bar(index: int, session: Session, symbol='SYN') -> Bar:
    start = session.open + timedelta(minutes=5 * index)
    end = start + timedelta(minutes=5)
    close = 100.0
    return Bar(symbol, start, end, end, session.id, close, 101.0, 99.0, close, 100.0)


class RREKernelTests(unittest.TestCase):
    def test_core_known_answer_warmup_causality_and_snapshot_integrity(self) -> None:
        _, session, _ = fixture_calendar()
        core = Core()
        outputs = []
        for i in range(78):
            bar = synthetic_bar(i, session)
            output = core.update(bar, session, bar.end)
            if output is not None:
                outputs.append(output)
        self.assertEqual(len(outputs), 53)
        first = outputs[0]
        self.assertEqual(first.bar_count, 26)
        self.assertAlmostEqual(first.atr14, 2.0, places=12)
        self.assertAlmostEqual(first.ema20, 100.0, places=12)
        self.assertAlmostEqual(first.m2, 0.0, places=12)
        last = outputs[-1]
        self.assertAlmostEqual(last.vwap or 0.0, 100.0, places=12)
        self.assertEqual(last.pf3, 0)

        restored = Core.from_snapshot(core.snapshot())
        self.assertEqual(restored.snapshot(), core.snapshot())
        tampered = core.snapshot()
        tampered['state']['bar_count'] += 1
        with self.assertRaises(ValueError):
            Core.from_snapshot(tampered)

    def test_core_rejects_unavailable_or_out_of_grid_inputs_without_state_change(self) -> None:
        _, session, _ = fixture_calendar()
        core = Core()
        first = synthetic_bar(0, session)
        with self.assertRaises(ValueError):
            core.update(first, session, first.end - timedelta(seconds=1))
        self.assertEqual(core.bar_count, 0)
        core.update(first, session, first.end)
        snapshot = core.snapshot()
        off_grid = Bar('SYN', first.start + timedelta(minutes=1), first.end + timedelta(minutes=1),
                       first.end + timedelta(minutes=1), session.id, 100, 101, 99, 100, 100)
        with self.assertRaises(ValueError):
            core.update(off_grid, session, off_grid.end)
        self.assertEqual(core.snapshot(), snapshot)

    def test_each_policy_variant_accepts_synthetic_sequence_and_roundtrips(self) -> None:
        _, session, reference = fixture_calendar()
        for variant in ('RRE1', 'RRE2', 'RRE3'):
            symbol = 'SPY' if variant == 'RRE3' else 'SYN'
            ref = PriorSessionReference(symbol, session.id, reference.previous_session,
                                        reference.available_at, reference.high, reference.low,
                                        reference.close, reference.series_id, reference.calendar_version,
                                        reference.complete)
            policy = PolicyEngine(PolicyConfig(0.01, 'series-fixture', 'calendar-fixture', variant))
            for i in range(78):
                bar = synthetic_bar(i, session, symbol=symbol)
                result = policy.update(bar, session, ref, bar.end)
                self.assertIsInstance(result, tuple)
            snapshot = policy.snapshot()
            restored = PolicyEngine.from_snapshot(snapshot)
            self.assertEqual(restored.snapshot(), snapshot)
            tampered = dict(snapshot)
            tampered['state'] = dict(snapshot['state'])
            tampered['state_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                PolicyEngine.from_snapshot(tampered)

    def test_reference_rejects_wrong_series_and_policy_requires_explicit_config(self) -> None:
        _, session, reference = fixture_calendar()
        with self.assertRaises(ValueError):
            PolicyEngine()
        policy = PolicyEngine(PolicyConfig(0.01, 'series-fixture', 'calendar-fixture', 'RRE1'))
        wrong = PriorSessionReference('SYN', session.id, reference.previous_session,
                                      reference.available_at, reference.high, reference.low,
                                      reference.close, 'other-series', reference.calendar_version, True)
        bar = synthetic_bar(0, session)
        with self.assertRaises(ValueError):
            policy.update(bar, session, wrong, bar.end)
        self.assertEqual(policy.core.bar_count, 0)


if __name__ == '__main__':
    unittest.main()
