"""GATE-CURE-20261112 blockers, Tensor C1 family (STRICTNESS-CENSUS
proposals 4-6):
- Proposal 4 (all variants, marker-kept pair): the close cap 5 is
  removed entirely and ret60 relaxes 31 -> 0, buy-cyan marker kept
  (0 -> 3 qualifications: TEM, AXTI, CLS).
- Proposal 5 (hot variants): the marker requirement is removed,
  the numeric profile (close<=5, ret60>=31, vol20>=0.07) is kept
  (0 -> 3).
- Proposal 6 (cool variants) is SKIPPED as identity-erasing (its
  registered atr move 1.0 -> 1.75 erases the cool variant's
  distinction from the all variant); the cool pins below assert
  the pre-cure behavior still holds exactly.
Fail direction: on pre-cure code the all-variant TEM-shaped fire
(price 77.84, ret60 5) and the hot-variant marker-free fire are
both refused.
"""
import unittest

from desk3 import aster_batch13, aster_batch14, tensor_native

CTX = {"session": "2026-10-23", "now": "2026-10-23T15:00:00"}


def _fire(**kw):
    f = {"symbol": "TEM", "signal": "buy-cyan", "price": 77.84,
         "ret60": 5.0, "vol20": 0.10, "adv_usd": 3_000_000,
         "atr_ratio": 0.8, "date": "2026-10-22"}
    f.update(kw)
    return f


def _view(fire):
    return {"fires": [fire], "positions": [], "bars": {}}


class TestBatch13C1All(unittest.TestCase):
    def test_tem_shaped_fire_enters_all_variant(self):
        # AMENDED 2026-11-14 (STRICTNESS-ROUND2-COMPLETION-20261114,
        # CADENCE-SWEEPS S3 row R2): the all trio's ret60 floor is
        # restored 0 -> 31 in the swept registered form, so the
        # entering probe carries TEM's census ret60 (34.9) instead
        # of the round-1 fixture's 5.0. Purpose preserved: a
        # high-price all-variant fire enters (no close cap).
        # Pre-amendment copy preserved in
        # ~/workspace/.gatecure-20261114/pre/tests/.
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25",
            _view(_fire(ret60=34.9)), dict(CTX))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")

    def test_marker_still_required_for_all_variant(self):
        # SUPERSEDED 2026-11-14 (STRICTNESS-ROUND2-COMPLETION-
        # 20261114): the buy-cyan marker requirement is REMOVED
        # for the all trio (the marker-kept ceiling was 3
        # symbol-weeks, 0.30/wk, at every cap and ret60); a
        # marker-free fire with ret60 >= 31 now enters. The
        # marker-required pin survives on the cool variant in
        # TestBatch13C1CoolSkipped and in
        # test_strictness_round2_completion_20261114_blockers.py.
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25",
            _view(_fire(signal="tensor", ret60=40.0)), dict(CTX))
        self.assertEqual(len(out), 1)

    def test_ret60_zero_floor_still_binds(self):
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25",
            _view(_fire(ret60=-1.0)), dict(CTX))
        self.assertEqual(out, [])


class TestBatch13C1Hot(unittest.TestCase):
    def test_marker_free_fire_enters_hot_variant(self):
        f = _fire(symbol="ABC", signal="tensor", price=4.0,
                  ret60=40.0, atr_ratio=1.5)
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_hot_25", _view(f), dict(CTX))
        self.assertEqual(len(out), 1)

    def test_hot_numeric_profile_still_binds(self):
        # READINESS-ROUND2-20261112 supersession, named: the $5
        # close cap is removed for the hot trio (CADENCE-SWEEPS
        # S3 R3), so the binding probe moves from price to the
        # ret60 floor that round 2 kept at 31.
        f = _fire(symbol="ABC", signal="tensor", price=6.0,
                  ret60=20.0, atr_ratio=1.5)
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_hot_25", _view(f), dict(CTX))
        self.assertEqual(out, [])


class TestBatch13C1CoolSkipped(unittest.TestCase):
    def test_cool_behavior_unchanged(self):
        hot_atr = _fire(symbol="ABC", price=4.0, ret60=40.0,
                        atr_ratio=1.5)
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_cool_25", _view(hot_atr), dict(CTX))
        self.assertEqual(out, [])
        cool_atr = _fire(symbol="ABC", price=4.0, ret60=40.0,
                         atr_ratio=0.8)
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_cool_25", _view(cool_atr), dict(CTX))
        self.assertEqual(len(out), 1)


class TestBatch14C1Hot(unittest.TestCase):
    def test_marker_free_fire_passes(self):
        spec = aster_batch14.SPECS["aster_tensor_c1_reserve_hot_25"]
        f = {"markers": [], "signal": "", "adv_usd": 3_000_000,
             "atr_ratio": 1.5, "ret60": 40.0, "vol20": 0.10}
        self.assertTrue(aster_batch14._passes(spec, f, 4.0))
        # READINESS-ROUND2-20261112 supersession, named: the $5
        # close cap is removed for the hot trio, so 6.0 now
        # passes; the ret60 floor (kept at 31) is the binding
        # probe instead.
        self.assertTrue(aster_batch14._passes(spec, f, 6.0))
        self.assertFalse(aster_batch14._passes(
            spec, dict(f, ret60=20.0), 4.0))


class TestNativeC1(unittest.TestCase):
    def _feats(self, **kw):
        f = {"native_close": 365.44, "depth60": 80.0, "ret60": 0.5,
             "vol20": 0.10, "dv20": 3_000_000, "atr_ratio": 0.8}
        f.update(kw)
        return f

    def test_all_variant_cls_shaped(self):
        # AMENDED 2026-11-14 (STRICTNESS-ROUND2-COMPLETION-20261114):
        # the native all branch takes the swept (marker off, cap
        # removed, ret60 >= 31) form, so the CLS-shaped probe
        # carries ret60 above the restored floor (the round-1
        # fixture's 0.5 measured the superseded ret60 >= 0 form)
        # and a marker-free rep now passes instead of refusing.
        # Pre-amendment copy preserved in
        # ~/workspace/.gatecure-20261114/pre/tests/.
        f = self._feats(ret60=40.0)
        rep = {"last": {"primaryMarkers": ["buy-cyan"]}}
        self.assertTrue(tensor_native.r19_passes(
            "C1", "all", f, rep))
        rep2 = {"last": {"primaryMarkers": []}}
        self.assertTrue(tensor_native.r19_passes(
            "C1", "all", f, rep2))
        self.assertFalse(tensor_native.r19_passes(
            "C1", "all", self._feats(), rep))

    def test_hot_variant_marker_free(self):
        rep = {"last": {"primaryMarkers": []}}
        f = self._feats(native_close=4.0, ret60=40.0, atr_ratio=1.5)
        self.assertTrue(tensor_native.r19_passes("C1", "hot", f, rep))

    def test_cool_variant_unchanged(self):
        rep = {"last": {"primaryMarkers": ["buy-cyan"]}}
        f = self._feats(native_close=4.0, ret60=40.0, atr_ratio=1.5)
        self.assertFalse(tensor_native.r19_passes("C1", "cool", f, rep))


if __name__ == "__main__":
    unittest.main()
