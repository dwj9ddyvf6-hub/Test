"""FEED80-TIMING-20261114 blockers for desk3.swing_timing.

Pre-cure state: desk3.swing_timing did not exist and no drop was
ever written, so every assertion here failed (import error). The
fixtures are synthetic close paths with known structure; the
expected values were measured from the cured module and pin its
documented rule (fractal k=3 pivots, HH/HL confirmation, measured
move target, stated score components).
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desk3 import swing_timing


def _bars(closes, vol_spike_at=None, spread=0.003):
    out = []
    for i, c in enumerate(closes):
        o = closes[i - 1] if i else c * 0.999
        v = 3000.0 if vol_spike_at is not None and i == vol_spike_at else 1000.0
        out.append({"t": f"2026-11-13T{i // 60:02d}:{i % 60:02d}:00Z",
                    "o": o,
                    "h": max(o, c) * (1 + spread) * (1 + (i % 7) * 0.0002),
                    "l": min(o, c) * (1 - spread) * (1 - (i % 5) * 0.0002),
                    "c": c, "v": v})
    return out


def _bullish():
    closes, p = [], 100.0
    for _ in range(60):
        p *= 1.0015; closes.append(p)
    for _ in range(6):
        p *= 0.996; closes.append(p)
    for _ in range(8):
        p *= 1.004; closes.append(p)
    for _ in range(5):
        p *= 0.997; closes.append(p)
    spike = len(closes) + 3
    for _ in range(4):
        p *= 1.006; closes.append(p)
    for _ in range(6):
        p *= 1.0005; closes.append(p)
    return _bars(closes, vol_spike_at=spike)


def _bearish():
    closes, p = [], 200.0
    for _ in range(60):
        p *= 0.9985; closes.append(p)
    for _ in range(6):
        p *= 1.004; closes.append(p)
    for _ in range(8):
        p *= 0.996; closes.append(p)
    for _ in range(5):
        p *= 1.003; closes.append(p)
    for _ in range(4):
        p *= 0.994; closes.append(p)
    for _ in range(6):
        p *= 0.9995; closes.append(p)
    return _bars(closes, vol_spike_at=len(closes) - 10)


class TestSwingSemantics(unittest.TestCase):
    def test_bullish_swing_confirms_with_geometry(self):
        sw = swing_timing.compute_swing(_bullish())
        self.assertIsNotNone(sw)
        self.assertTrue(sw["confirmed"])
        self.assertFalse(sw["usesFutureData"])
        self.assertEqual(sw["direction"], "bullish")
        self.assertGreaterEqual(sw["score"], 8)
        self.assertLess(sw["invalidation"], sw["target"])

    def test_bearish_swing_mirrors(self):
        sw = swing_timing.compute_swing(_bearish())
        self.assertIsNotNone(sw)
        self.assertEqual(sw["direction"], "bearish")
        self.assertLess(sw["target"], sw["invalidation"])

    def test_flat_series_no_swing(self):
        closes = [100 + (0.05 if i % 2 else -0.05) for i in range(80)]
        self.assertIsNone(swing_timing.compute_swing(_bars(closes)))

    def test_causality_prefix_stable(self):
        bars = _bullish()
        first = None
        for n in range(40, len(bars) + 1):
            s = swing_timing.compute_swing(bars[:n])
            if s:
                first = (s["confirmed_at"], s["invalidation"], s["target"])
                break
        self.assertIsNotNone(first)
        full = swing_timing.compute_swing(bars)
        self.assertEqual(first, (full["confirmed_at"],
                                 full["invalidation"], full["target"]))


class TestDropRoundTrip(unittest.TestCase):
    def test_drop_serves_through_ingest_producer(self):
        from desk3.producers3 import TimingSignalsProducer
        signals = swing_timing.build_signals({"TEST": _bullish()})
        self.assertIn("TEST", signals)
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "state", "ingest"))
            doc = {"generated_at": "2026-11-14T20:00:00+00:00",
                   "source": "desk-swing-timing-v1 (reconstruction; NOT v625)",
                   "signals": signals}
            with open(os.path.join(td, "state", "ingest",
                                   "timing_signals.json"), "w") as fh:
                json.dump(doc, fh)
            from datetime import datetime, timezone
            out = TimingSignalsProducer(td)(
                {"now": datetime(2026, 11, 14, 20, 5, tzinfo=timezone.utc)})
        served = (out.get("timing_signals") or {}).get("TEST") or {}
        self.assertTrue((served.get("swing") or {}).get("confirmed"))

    def test_builder_stamps_reconstruction_provenance(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "research_notes", "sleeve-activation-calibration-20261111",
            "build_timing_signals_drop.py")
        text = open(path).read()
        self.assertIn("desk-swing-timing-v1", text)
        self.assertIn("NOT v625", text)


if __name__ == "__main__":
    unittest.main()
