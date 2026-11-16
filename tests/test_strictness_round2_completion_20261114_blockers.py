"""STRICTNESS-ROUND2-COMPLETION-20261114 blockers — Lane B of the
ALL SLEEVES FIRING program, Sat 2026-11-14: the one round-2 row
whose gate lives in the tensor sleeve-side gating modules and had
not landed.

Row R2 (CADENCE-AUDIT-2026-11-12 section 3, priced in
CADENCE-SWEEPS-2026-11-12.md S3): C1 all trio
(aster_tensor_c1_cash_all_25, aster_tensor_c1_delay_all_25,
aster_tensor_c1_reserve_all_25).
  Gate: the C1 entry conjunction in desk3/aster_batch13.py
  (_tensor C1 branch) and its native mirror
  desk3/tensor_native.py (r19_passes C1 "all" branch).
  Old (landed round-1 form): buy-cyan marker required, close cap
  removed, ret60 >= 0 — replay 3 symbol-weeks / 10.0 wk = 0.30/wk,
  BELOW-WEEKLY; with the marker kept, 3 is the ceiling at every
  cap and ret60 (CADENCE-SWEEPS S3, verified).
  New (the swept registered form): buy-cyan marker requirement
  removed, close cap removed (already), ret60 floor restored to
  the canonical 31 — grid cell (marker off, cap removed,
  ret60 >= 31) = 31 symbol-weeks / 10.0 wk = 3.10/wk,
  MEETS-WEEKLY.
  Forward falsifier (CADENCE-AUDIT section 3 standard): in the
  first full quarter after this change the trio must produce
  live qualification events averaging at least 1 per week (at
  least 13 over the quarter) on the desk's own dispatcher and
  journal records; fewer reverts the change automatically.
  Rollback: restore the marker conjunct and the ret60 >= 0 floor
  in both sites (the round-1 form).

Honest-proxy note: the replay counts above are the CADENCE-SWEEPS
S3 measurement on the rebuilt census table (its anchors reproduce
the census exactly). These blockers are the closest proxy the
test harness supports: they prove the implemented gate IS the
swept (off, removed, 31) cell — marker absent admitted, the
ret60 = 31 boundary binding, no close cap at the census's own
marker-week prices (77.84 / 365.44) — at both mirror sites, and
that the C1 cool branch (parked trio, proposal 6 skipped) is
byte-for-byte behavior-identical.

Fail direction: on pre-cure code the marker-free all-variant
fires are refused at both sites and a ret60 = 20 marker fire
enters (floor 0); both directions are asserted below.
"""
import hashlib
import os
import unittest

from desk3 import aster_batch13, tensor_native

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = {"session": "2026-10-23", "now": "2026-10-23T15:00:00"}
SATY_SOL_PIN = "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc"


def _fire(**kw):
    f = {"symbol": "SKYQ", "signal": "tensor", "price": 8.0,
         "ret60": 40.0, "vol20": 0.10, "adv_usd": 3_000_000,
         "atr_ratio": 0.8, "date": "2026-10-22"}
    f.update(kw)
    return f


def _view(fire):
    return {"fires": [fire], "positions": [], "bars": {}}


def _feats(**kw):
    f = {"native_close": 8.0, "depth60": 80.0, "ret60": 40.0,
         "vol20": 0.10, "dv20": 3_000_000, "atr_ratio": 0.8}
    f.update(kw)
    return f


NO_MARKER = {"last": {"primaryMarkers": []}}
CYAN = {"last": {"primaryMarkers": ["buy-cyan"]}}


class TestNativeC1AllRound2(unittest.TestCase):
    def test_marker_free_fire_passes(self):
        self.assertTrue(tensor_native.r19_passes(
            "C1", "all", _feats(), NO_MARKER))

    def test_no_close_cap_at_census_marker_week_prices(self):
        # TEM / CLS shapes from the census marker weeks: closes
        # 77.84 and 365.44, ret60 above 31, no marker on the fire.
        self.assertTrue(tensor_native.r19_passes(
            "C1", "all",
            _feats(native_close=77.84, ret60=34.9), NO_MARKER))
        self.assertTrue(tensor_native.r19_passes(
            "C1", "all",
            _feats(native_close=365.44, ret60=161.3), NO_MARKER))

    def test_ret60_floor_restored_to_31(self):
        self.assertFalse(tensor_native.r19_passes(
            "C1", "all", _feats(ret60=20.0), CYAN))
        self.assertTrue(tensor_native.r19_passes(
            "C1", "all", _feats(ret60=31.0), NO_MARKER))

    def test_vol_and_dv_floors_still_bind(self):
        self.assertFalse(tensor_native.r19_passes(
            "C1", "all", _feats(vol20=0.06), NO_MARKER))
        self.assertFalse(tensor_native.r19_passes(
            "C1", "all", _feats(dv20=1_999_999), NO_MARKER))


class TestBatch13C1AllRound2(unittest.TestCase):
    def test_marker_free_fire_enters_cash_all(self):
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25", _view(_fire()), dict(CTX))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")

    def test_marker_free_fire_enters_delay_and_reserve_all(self):
        for sid in ("aster_tensor_c1_delay_all_25",
                    "aster_tensor_c1_reserve_all_25"):
            out = aster_batch13.evaluate(sid, _view(_fire()),
                                         dict(CTX))
            self.assertEqual(len(out), 1, sid)
            self.assertEqual(out[0]["kind"], "entry", sid)

    def test_ret60_below_31_refused_even_with_marker(self):
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25",
            _view(_fire(signal="buy-cyan", ret60=20.0)), dict(CTX))
        self.assertEqual(out, [])

    def test_marker_week_price_shape_enters(self):
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25",
            _view(_fire(price=77.84, ret60=34.9)), dict(CTX))
        self.assertEqual(len(out), 1)


class TestC1CoolUnchanged(unittest.TestCase):
    """The parked cool trio's gate is NOT touched by this landing
    (proposal 6 skipped as identity-erasing; the trio was parked
    in READINESS-ROUND2-20261112 with the reason recorded)."""

    def test_native_cool_still_requires_marker_and_cap(self):
        self.assertFalse(tensor_native.r19_passes(
            "C1", "cool",
            _feats(native_close=4.0, ret60=40.0), NO_MARKER))
        self.assertFalse(tensor_native.r19_passes(
            "C1", "cool",
            _feats(native_close=8.0, ret60=40.0), CYAN))
        self.assertTrue(tensor_native.r19_passes(
            "C1", "cool",
            _feats(native_close=4.0, ret60=40.0), CYAN))

    def test_batch13_cool_still_requires_marker(self):
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_cool_25", _view(_fire(price=4.0)),
            dict(CTX))
        self.assertEqual(out, [])
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_cool_25",
            _view(_fire(signal="buy-cyan", price=4.0)), dict(CTX))
        self.assertEqual(len(out), 1)


class TestSatyPinUntouched(unittest.TestCase):
    def test_saty_sol_pin(self):
        with open(os.path.join(ROOT, "sleeves", "saty_sol.py"),
                  "rb") as fh:
            self.assertEqual(
                hashlib.sha256(fh.read()).hexdigest(), SATY_SOL_PIN)


if __name__ == "__main__":
    unittest.main()
