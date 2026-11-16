"""READINESS-ROUND2-20261112 blockers — gate round-2 landings from
CADENCE-SWEEPS-2026-11-12.md, each in registration format in
BUGLOG_2026-11-12.md (sleeve, gate, old/new, replay before/after,
forward falsifier, rollback line):

(a) G4 cool atr cap 1.1 -> 1.5 (sweep S2: 1.00/wk at 1.5, exact
    crossing 1.3175). Sites: aster_batch14._vol_ok and
    tensor_native.r19_passes (the two mirrors carrying the cool
    cap; aster_batch15 serves no cool G4 variant). Midna's
    identity call: the cool gate's name describes its marker
    family, not an atr ceiling; the falsifier watches the cool
    variants' first ten fills for hot-like behavior.
(b) C1 hot trio close cap removed (sweep S3 row R3: cap removal
    alone, marker already removed in wave 1, ret60 kept at 31:
    29 hot-filtered symbol-weeks, 2.90/wk). This is the C1 ret60
    reconciliation's one correction: the instruments agree on
    every configuration either implements (see
    C1-RET60-RECONCILIATION-2026-11-12.md in the rule-logic
    ledger home); the hot trio's landed form sat at 3 because
    its $5 close cap still bound. Sites: tensor_native.r19_passes
    C1 hot branch, aster_batch13._tensor cap (hot only; cool
    keeps 5.0), aster_batch14._passes C1 (reserve_hot book).
(c) LINK nfs funding threshold 0.00005 -> 0.00015 (sweep S4: any
    threshold above the 0.0001 cap print reaches 1.42/wk; landed
    at 0.00015, the smallest step past the cap print the sweep
    supports). Sites: aster_b12_crypto nfs leg and
    aster_batch13 link_nfs_norm_vol entry leg. Exit and
    normalization legs (funding >= 0) untouched.

Fail direction: proven on a worktree at the pre-cure HEAD — the
atr-1.3 cool fire, the $8 C1 hot fire, and the 0.0001-funding
LINK entries are all refused pre-cure.
"""
import importlib
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
CTX13 = {"session": "2026-10-24", "now": "2026-10-24T15:00:00"}


def _ctx(sid):
    return {"sleeve_id": sid, "cycle_id": "fx",
            "state_dir": tempfile.mkdtemp()}


# ------------------------------------------------------------ (a) G4
class TestG4CoolCap15(unittest.TestCase):
    def _f(self, **kw):
        f = {"markers": [], "signal": "", "native_close": 8.0,
             "depth60": 80.0, "ret60": 5.0, "vol20": 0.12,
             "dv20": 3_000_000, "adv_usd": 3_000_000,
             "atr_ratio": 0.8}
        f.update(kw)
        return f

    def test_batch14_cool_cap(self):
        from desk3 import aster_batch14
        spec = aster_batch14.SPECS["aster_tensor_g4_cash_cool_25"]
        self.assertTrue(aster_batch14._passes(
            spec, self._f(atr_ratio=1.3), 8.0))
        self.assertFalse(aster_batch14._passes(
            spec, self._f(atr_ratio=1.6), 8.0))

    def test_native_cool_cap(self):
        from desk3.tensor_native import r19_passes
        rep = {"last": {"primaryMarkers": []}}
        self.assertTrue(r19_passes(
            "G4", "cool", self._f(atr_ratio=1.3), rep))
        self.assertFalse(r19_passes(
            "G4", "cool", self._f(atr_ratio=1.6), rep))


# ------------------------------------------------------------ (b) C1
class TestC1HotCapRemoved(unittest.TestCase):
    def _f(self, **kw):
        f = {"markers": [], "signal": "", "native_close": 8.0,
             "depth60": 80.0, "ret60": 40.0, "vol20": 0.10,
             "dv20": 3_000_000, "adv_usd": 3_000_000,
             "atr_ratio": 1.2}
        f.update(kw)
        return f

    def test_native_hot_no_cap(self):
        from desk3.tensor_native import r19_passes
        rep = {"last": {"primaryMarkers": []}}
        self.assertTrue(r19_passes("C1", "hot", self._f(), rep))
        # ret60 still binds at 31 for the hot trio.
        self.assertFalse(r19_passes(
            "C1", "hot", self._f(ret60=20.0), rep))

    def test_batch14_hot_no_cap(self):
        from desk3 import aster_batch14
        spec = aster_batch14.SPECS[
            "aster_tensor_c1_reserve_hot_25"]
        self.assertTrue(aster_batch14._passes(spec, self._f(), 8.0))

    def test_batch13_hot_no_cap(self):
        sid = "aster_tensor_c1_cash_hot_25"
        fire = {"sleeve_id": sid, "symbol": "AAA",
                "signal": "buy-green", "date": "2026-10-23",
                "price": 8.0, "ret60": 40, "vol20": 0.1,
                "adv_usd": 3000000, "atr_ratio": 1.2}
        view = {"now": CTX13["now"], "tensor": {"fires": [fire]},
                "bars": {}, "positions": [], "extra": {}}
        mod = importlib.import_module(f"adapters3.{sid}")
        out = mod.evaluate(view, dict(CTX13))
        entries = [o for o in out if o["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["qty"], 50)  # $400 / $8


# ----------------------------------------------------------- (c) LINK
def _brk_bars(sym_key, n=25, price=10.0, last=11.0):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        out.append({"t": t.isoformat().replace("+00:00", "Z"),
                    "o": price, "h": price if i < n - 1 else last,
                    "l": price - 1, "c": price if i < n - 1 else last,
                    "v": 100000})
    return out


def _drive_r19(sid, sym, brs, funding):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": NOW.isoformat(), "bars": {f"{sym}|4Hour": brs},
            "funding": {sym: funding}, "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    return mod.evaluate(view, _ctx(sid))


class TestLinkNfs15(unittest.TestCase):
    SID = ("aster_r19_linkusdt_negative_funding_squeeze"
           "_fixed16_fullcash")

    def test_b12_at_0_0001_now_enters(self):
        out = _drive_r19(self.SID, "LINKUSDT",
                         _brk_bars("LINKUSDT"), 0.0001)
        self.assertEqual(
            len([o for o in out if o.kind == "enter"]), 1, out)

    def test_b12_above_0_00015_still_refuses(self):
        self.assertEqual(_drive_r19(self.SID, "LINKUSDT",
                                    _brk_bars("LINKUSDT"), 0.0002),
                         [])

    def test_batch13_at_0_0001_now_enters(self):
        sid = "aster_link_nfs_norm_vol"
        bars = [{"t": f"h{i}", "o": 10, "h": 10.0, "l": 9, "c": 10,
                 "v": 100000} for i in range(20)]
        bars.append({"t": "h20", "o": 10, "h": 11.0, "l": 9,
                     "c": 11.0, "v": 100000})
        view = {"now": "2026-10-24T15:00:00",
                "bars": {"LINKUSDT": bars},
                "funding": {"LINKUSDT": 0.0001},
                "positions": [], "extra": {}}
        mod = importlib.import_module(f"adapters3.{sid}")
        out = mod.evaluate(view, _ctx(sid))
        self.assertEqual(
            len([o for o in out if o["kind"] == "entry"]), 1, out)

    def test_batch13_above_0_00015_still_refuses(self):
        sid = "aster_link_nfs_norm_vol"
        bars = [{"t": f"h{i}", "o": 10, "h": 10.0, "l": 9, "c": 10,
                 "v": 100000} for i in range(20)]
        bars.append({"t": "h20", "o": 10, "h": 11.0, "l": 9,
                     "c": 11.0, "v": 100000})
        view = {"now": "2026-10-24T15:00:00",
                "bars": {"LINKUSDT": bars},
                "funding": {"LINKUSDT": 0.0002},
                "positions": [], "extra": {}}
        mod = importlib.import_module(f"adapters3.{sid}")
        self.assertEqual(mod.evaluate(view, _ctx(sid)), [])


# ------------------------------------------------- (f) C1 cool park
class TestC1CoolParked(unittest.TestCase):
    def test_cool_trio_parked_with_reason(self):
        # UNPARK-REGISTRY-20261114 (owner's 2026-11-14
        # all-sleeves-firing order supersedes the 2026-11-12 park):
        # the trio is UNPARKED and evaluates on its own rules; the
        # 2026-11-12 parking reason is preserved in the stamp as
        # prior_parked_reason, and the identity question stays open
        # (it is a gate question, not a parking).
        import json
        with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
            rows = json.load(fh)["sleeves"]
        by_id = {r["id"]: r for r in rows}
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(rows), 400)
        for sid in ("aster_tensor_c1_cash_cool_25",
                    "aster_tensor_c1_delay_cool_25",
                    "aster_tensor_c1_reserve_cool_25"):
            self.assertFalse(by_id[sid]["parked"], sid)
            self.assertEqual(by_id[sid]["params"].get("unparked_on"),
                             "2026-11-14", sid)
            self.assertIn("identity-preserving",
                          by_id[sid]["params"]["prior_parked_reason"])
        for sid in ("aster_tensor_c1_cash_all_25",
                    "aster_tensor_c1_cash_hot_25",
                    "aster_tensor_c1_reserve_hot_25"):
            self.assertFalse(by_id[sid]["parked"], sid)


if __name__ == "__main__":
    unittest.main()


class TestDecisions20261114(unittest.TestCase):
    # DECISIONS-20261114 (parent close-out of the All Sleeves Firing
    # program's three carried rows; CALIBRATION-LEDGER.md section 6):
    # every decided sleeve carries its decision stamp in config
    # params, so the roster itself records the verdicts.
    def _rows(self):
        import json
        with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
            return {r["id"]: r for r in json.load(fh)["sleeves"]}

    def test_ada_pairs_hold_stamp(self):
        by_id = self._rows()
        for sid in ("aster_abs_neg_ada_fullcash",
                    "aster_abs_neg_ada_vol1pct",
                    "aster_abs_nonneg_ada_fullcash",
                    "aster_abs_nonneg_ada_vol1pct"):
            stamp = by_id[sid]["params"].get("decision_20261114", "")
            self.assertIn("HOLD-RARE-BUT-REAL-20261114", stamp, sid)
            self.assertFalse(by_id[sid]["parked"], sid)

    def test_c1_trio_keep_identity_stamp(self):
        by_id = self._rows()
        for sid in ("aster_tensor_c1_cash_cool_25",
                    "aster_tensor_c1_delay_cool_25",
                    "aster_tensor_c1_reserve_cool_25"):
            stamp = by_id[sid]["params"].get(
                "identity_decision_20261114", "")
            self.assertIn("KEEP-IDENTITY-20261114", stamp, sid)
            self.assertFalse(by_id[sid]["parked"], sid)

    def test_squeeze_redesign_stamp(self):
        by_id = self._rows()
        stamp = by_id["aster_squeeze_1d"]["params"].get(
            "decision_20261114", "")
        self.assertIn("REDESIGN-CANDIDATE-20261114", stamp)
        self.assertFalse(by_id["aster_squeeze_1d"]["parked"])
