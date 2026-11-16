"""GATE-CURE-20261112 blockers, Tensor G4 family (census proposals
1-3, STRICTNESS-CENSUS-2026-11-12): the buy-green primary marker
requirement is removed from the G4 passes functions; the numeric
profile (close<=10, depth60>=70, ret60>=0, vol20>=0.09, dv20>=2e6)
becomes the gate. Proposal 3: the G4 cool atr cap moves 1.0 -> 1.1
jointly with the marker removal; the hot filter (atr>1) is kept
exactly (proposal 2). The leaps pair consumes the native bridge
(tensor_native.r19_passes via build_g4_events), so the bridge gate
is pinned here too. Fail direction: on pre-cure code every
marker-free numeric fire is refused (marker required), and a G4
cool fire at atr_ratio 1.08 is refused (cap 1.0).
"""
import unittest

from desk3 import aster_batch14, aster_batch15, tensor_native


def _fire(**kw):
    f = {"markers": [], "signal": "", "adv_usd": 3_000_000,
         "depth60": 80.0, "ret60": 5.0, "vol20": 0.12,
         "atr_ratio": 0.8}
    f.update(kw)
    return f


class TestBatch14G4(unittest.TestCase):
    def test_all_variant_marker_free_numeric_fire_passes(self):
        spec = aster_batch14.SPECS["aster_tensor_g4_cash_all_25"]
        self.assertTrue(aster_batch14._passes(spec, _fire(), 8.0))

    def test_numeric_gates_still_bind(self):
        spec = aster_batch14.SPECS["aster_tensor_g4_cash_all_25"]
        self.assertFalse(aster_batch14._passes(spec, _fire(), 11.0))
        self.assertFalse(aster_batch14._passes(
            spec, _fire(depth60=60.0), 8.0))
        self.assertFalse(aster_batch14._passes(
            spec, _fire(vol20=0.05), 8.0))
        self.assertFalse(aster_batch14._passes(
            spec, _fire(ret60=-1.0), 8.0))
        self.assertFalse(aster_batch14._passes(
            spec, _fire(adv_usd=1_000_000), 8.0))

    def test_hot_filter_kept_at_atr_above_1(self):
        spec = aster_batch14.SPECS["aster_tensor_g4_cash_hot_25"]
        self.assertTrue(aster_batch14._passes(
            spec, _fire(atr_ratio=1.05), 8.0))
        self.assertFalse(aster_batch14._passes(
            spec, _fire(atr_ratio=0.9), 8.0))

    def test_cool_cap_moved_to_1_1(self):
        # READINESS-ROUND2-20261112 supersession, named: the G4
        # cool cap moved on to 1.5 (CADENCE-SWEEPS S2), so the
        # refusal probe moves 1.2 -> 1.6. The wave-1 facts below
        # the new cap (1.08 and 1.2 both pass) are kept.
        spec = aster_batch14.SPECS["aster_tensor_g4_cash_cool_25"]
        self.assertTrue(aster_batch14._passes(
            spec, _fire(atr_ratio=1.08), 8.0))
        self.assertTrue(aster_batch14._passes(
            spec, _fire(atr_ratio=1.2), 8.0))
        self.assertFalse(aster_batch14._passes(
            spec, _fire(atr_ratio=1.6), 8.0))


class TestBatch15G4(unittest.TestCase):
    def _f(self, **kw):
        f = {"markers": [], "native_close": 8.0, "depth60": 80.0,
             "ret60": 5.0, "vol20": 0.12, "dv20": 3_000_000,
             "atr_ratio": 0.8}
        f.update(kw)
        return f

    def test_marker_free_numeric_fire_passes_all(self):
        self.assertTrue(aster_batch15.g4_passes(
            {"volatility": "all"}, self._f()))

    def test_marker_free_numeric_fire_passes_hot(self):
        self.assertTrue(aster_batch15.g4_passes(
            {"volatility": "hot"}, self._f(atr_ratio=1.05)))
        self.assertFalse(aster_batch15.g4_passes(
            {"volatility": "hot"}, self._f(atr_ratio=0.9)))

    def test_numeric_gates_still_bind(self):
        self.assertFalse(aster_batch15.g4_passes(
            {"volatility": "all"}, self._f(native_close=11.0)))
        self.assertFalse(aster_batch15.g4_passes(
            {"volatility": "all"}, self._f(depth60=60.0)))


class TestNativeBridgeG4(unittest.TestCase):
    def _feats(self, **kw):
        f = {"native_close": 8.0, "depth60": 80.0, "ret60": 5.0,
             "vol20": 0.12, "dv20": 3_000_000, "atr_ratio": 0.8}
        f.update(kw)
        return f

    def test_r19_passes_marker_free(self):
        rep = {"last": {"primaryMarkers": []}}
        self.assertTrue(tensor_native.r19_passes(
            "G4", "all", self._feats(), rep))

    def test_r19_passes_numeric_still_binds(self):
        rep = {"last": {"primaryMarkers": []}}
        self.assertFalse(tensor_native.r19_passes(
            "G4", "all", self._feats(native_close=11.0), rep))
        self.assertFalse(tensor_native.r19_passes(
            "G4", "all", self._feats(depth60=60.0), rep))


if __name__ == "__main__":
    unittest.main()
