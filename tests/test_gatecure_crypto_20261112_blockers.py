"""Blockers: GATE-CURE-CRYPTO-20261112 — the funding-squeeze and
absorption gate loosenings (STRICTNESS-CENSUS-2026-11-12 proposals
8-12), landed exactly as registered:

- Proposal 8 (ADA negative funding squeeze: the 9 aster_r19 nfs
  variants in desk3/aster_crypto.py and aster_squeeze_ada_fullcash
  in aster_sleeves/_common.py): entry funding leg < 0 -> < 0.0002.
  Census: 0 -> 13 entry days over the 2.43-month funding window.
- Proposal 9 (LINK negative funding squeeze: the 9 aster_r19 nfs
  variants in desk3/aster_b12_crypto.py and aster_link_nfs_norm_vol
  in desk3/aster_batch13.py): entry funding leg < 0 -> < 0.00005.
  Census: 0 -> 5 entry days.
- Proposal 10 (aster_abs_neg_ada pair, _common absorption):
  shock multiple 2.0 -> 1.5. Census: 0 -> 3 days. The family's
  negative-funding leg stays < 0 exactly.
- Proposal 11 (aster_abs_nonneg_ada pair, _common absorption):
  shock multiple 2.0 -> 1.25. Census: 1 -> 5 days.
- Proposal 12 (aster_r19_linkusdt_absorption_negative_funding
  pair, desk3/aster_b11_crypto.py): shock multiple 2.0 -> 1.25.
  Census: 1 -> 3 days. The b11 absorption_base and
  absorption_nonnegative_funding families keep 2.0 (no proposal
  registered for them); the b11 funding legs are unchanged.

Exit and normalization legs (funding >= 0) are untouched
everywhere. Fail direction: proven on the pre-cure tree (every
"enters post-cure" case below is refused pre-cure). Pre-cure
copies preserved under ~/workspace/.gatecure-20261112/pre/.
"""
import importlib, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _ctx(sid):
    return {"sleeve_id": sid, "cycle_id": "fx",
            "state_dir": tempfile.mkdtemp()}


# ------------------------------------------------------- fixtures
def brk_bars(sym_key, n=25, price=10.0, last=11.0):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        c = last if i == n - 1 else price
        out.append({"t": t.isoformat(), "o": price, "h": price + 0.5,
                    "l": price - 0.5, "c": c, "v": 100000.0})
    return out


def drive_r19(sid, sym, brs, funding):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": NOW.isoformat(), "bars": {f"{sym}|4Hour": brs},
            "funding": {sym: funding} if funding is not None else {},
            "positions": [], "slice": {"capital_usd": 10000.0,
                                       "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    return mod.evaluate(view, _ctx(sid))


# ------------------------------------------- proposal 8: ADA nfs
class TestAdaFundingSqueeze(unittest.TestCase):
    SID = "aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash"

    def ev(self, funding):
        from desk3 import aster_crypto
        view = {"now": NOW.isoformat(),
                "bars": {"ADAUSDT|4Hour": brk_bars("ADAUSDT")},
                "funding": {"ADAUSDT": funding},
                "positions": [], "slice": {"cash_usd": 10000.0}}
        return aster_crypto.evaluate(self.SID, view)

    def test_small_positive_funding_now_enters(self):
        out = self.ev(0.0001)  # in [0, 0.0002): refused pre-cure
        self.assertEqual(len([o for o in out if o.kind == "enter"]), 1)

    def test_above_threshold_still_refuses(self):
        self.assertEqual(self.ev(0.0003), [])
        self.assertEqual(self.ev(0.001), [])

    def test_negative_and_missing_unchanged(self):
        self.assertEqual(
            len([o for o in self.ev(-0.001) if o.kind == "enter"]), 1)
        self.assertEqual(self.ev(None), [])


# --------------------------------- proposal 8: squeeze_ada sleeve
def _mk4(specs):
    n = len(specs)
    return [{"t": _iso(NOW - timedelta(hours=4 * (n - i))),
             "o": o, "h": h, "l": l, "c": c, "v": v}
            for i, (o, c, v, h, l) in enumerate(specs)]


def _breakout_bars_ada():
    specs = [(1.0, 1.0, 1000.0, 1.01, 0.99)] * 300
    specs.append((1.0, 1.05, 2000.0, 1.06, 0.99))
    specs.append((1.05, 1.05, 1000.0, 1.06, 1.04))
    return _mk4(specs)


def _funding_rec(rate):
    settled = NOW - timedelta(hours=5)
    return {"ADAUSDT": [{"rate": rate, "settled_at": _iso(settled),
                         "received_at": _iso(settled + timedelta(minutes=30)),
                         "observed_public_endpoint": True}]}


def _view_ada(bars4, funding=None):
    v = {"now": _iso(NOW), "bars": {"ADAUSDT|4Hour": bars4},
         "positions": [],
         "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    if funding is not None:
        v["funding"] = funding
    return v


def ev_sleeve(sid, view):
    return importlib.import_module(f"aster_sleeves.{sid}").evaluate(
        view, {"sleeve_id": sid})


class TestSqueezeAdaFunding(unittest.TestCase):
    SID = "aster_squeeze_ada_fullcash"

    def test_small_positive_funding_now_enters(self):
        # Signal-time gate AND the ENH-B11 entry-bar revalidation
        # both carry the registered 0.0002 threshold.
        out = ev_sleeve(self.SID, _view_ada(
            _breakout_bars_ada(), _funding_rec(0.0001)))
        self.assertEqual(len(out), 1)

    def test_above_threshold_still_refuses(self):
        self.assertEqual(ev_sleeve(self.SID, _view_ada(
            _breakout_bars_ada(), _funding_rec(0.0003))), [])

    def test_negative_funding_unchanged(self):
        out = ev_sleeve(self.SID, _view_ada(
            _breakout_bars_ada(), _funding_rec(-0.0005)))
        self.assertEqual(len(out), 1)


# ------------------------------------------ proposal 9: LINK nfs
class TestLinkFundingSqueeze(unittest.TestCase):
    SID = "aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash"

    def test_small_positive_funding_now_enters(self):
        out = drive_r19(self.SID, "LINKUSDT", brk_bars("LINKUSDT"),
                        0.00003)  # in [0, 0.00005): refused pre-cure
        self.assertEqual(len([o for o in out if o.kind == "enter"]), 1)

    def test_above_threshold_still_refuses(self):
        # READINESS-ROUND2-20261112 supersession, named: the LINK
        # nfs threshold moved 0.00005 -> 0.00015 (CADENCE-SWEEPS
        # S4), so the above-threshold probe moves 0.0001 ->
        # 0.0002. The pin's purpose (a threshold exists and binds
        # above it) is unchanged.
        self.assertEqual(drive_r19(self.SID, "LINKUSDT",
                                   brk_bars("LINKUSDT"), 0.0002), [])

    def test_negative_funding_unchanged(self):
        out = drive_r19(self.SID, "LINKUSDT", brk_bars("LINKUSDT"),
                        -0.01)
        self.assertEqual(len([o for o in out if o.kind == "enter"]), 1)


class TestLinkNfsNormVol(unittest.TestCase):
    SID = "aster_link_nfs_norm_vol"

    def view(self, funding, positions=None):
        bars = [{"t": f"h{i}", "o": 10, "h": 10.0, "l": 9, "c": 10,
                 "v": 100000} for i in range(20)]
        bars.append({"t": "h20", "o": 10, "h": 11.0, "l": 9,
                     "c": 11.0, "v": 100000})
        return {"now": "2026-10-24T15:00:00",
                "bars": {"LINKUSDT": bars},
                "funding": {"LINKUSDT": funding},
                "positions": positions or [], "extra": {}}

    def ev(self, funding, positions=None):
        mod = importlib.import_module(f"adapters3.{self.SID}")
        return mod.evaluate(self.view(funding, positions),
                            _ctx(self.SID))

    def test_small_positive_funding_now_enters(self):
        out = self.ev(0.00003)
        self.assertEqual(len([o for o in out
                              if o["kind"] == "entry"]), 1)

    def test_above_threshold_still_refuses(self):
        # READINESS-ROUND2-20261112 supersession, named: probe
        # moved 0.0001 -> 0.0002 with the threshold (see the r19
        # case above).
        self.assertEqual(self.ev(0.0002), [])

    def test_normalization_exit_untouched(self):
        pos = [{"symbol": "LINKUSDT", "qty": 50, "avg_price": 10.0,
                "hours_held": 4}]
        out = self.ev(0.0, positions=pos)
        self.assertEqual(len(out), 1)
        self.assertIn("funding_normalization", out[0]["reason"])


# ------------------------------ proposals 10-11: ADA absorption
def _absorption_bars_ada(shock_vol):
    specs = [(1.0, 1.0, 1000.0, 1.001, 0.999)] * 300
    specs.append((1.0, 0.95, shock_vol, 1.001, 0.949))     # shock
    specs.append((0.95, 1.02, 1500.0, 1.021, 0.949))       # confirm
    specs.append((1.02, 1.02, 1000.0, 1.021, 1.019))       # entry
    return _mk4(specs)


class TestAdaAbsorptionMultiples(unittest.TestCase):
    def test_neg_pair_shock_at_1p5_now_confirms(self):
        # Shock volume 1800: 1.5 x EMA (~1614) clears, 2.0 x EMA
        # (~2152) refuses. Funding leg stays < 0 (rate -0.0005).
        bars = _absorption_bars_ada(1800.0)
        for sid in ("aster_abs_neg_ada_fullcash",
                    "aster_abs_neg_ada_vol1pct"):
            out = ev_sleeve(sid, _view_ada(bars, _funding_rec(-0.0005)))
            self.assertEqual(len(out), 1, sid)

    def test_neg_pair_below_1p5_still_refuses(self):
        bars = _absorption_bars_ada(1400.0)
        out = ev_sleeve("aster_abs_neg_ada_fullcash",
                        _view_ada(bars, _funding_rec(-0.0005)))
        self.assertEqual(out, [])

    def test_nonneg_pair_shock_at_1p25_now_confirms(self):
        # Shock volume 1400: 1.25 x EMA (~1298) clears, 2.0 refuses.
        bars = _absorption_bars_ada(1400.0)
        for sid in ("aster_abs_nonneg_ada_fullcash",
                    "aster_abs_nonneg_ada_vol1pct"):
            out = ev_sleeve(sid, _view_ada(bars, _funding_rec(0.0005)))
            self.assertEqual(len(out), 1, sid)

    def test_base_pair_multiple_unchanged(self):
        # absorption_base keeps 2.0: the 1400 shock still refuses.
        bars = _absorption_bars_ada(1400.0)
        out = ev_sleeve("aster_abs_base_ada_fullcash", _view_ada(bars))
        self.assertEqual(out, [])


# --------------------------- proposal 12: LINK absorption (b11)
def abs_bars_link(shock_vol, n=302):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        o = c = 20.0; h = 20.2; l = 19.8; v = 1000.0
        if i == n - 2:
            o, c, h, l, v = 20.0, 19.0, 20.0, 18.8, shock_vol
        if i == n - 1:
            o, c = 19.0, 19.6
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l,
                    "c": c, "v": v})
    return out


class TestLinkAbsorptionMultiple(unittest.TestCase):
    NEG = "aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash"
    BASE = "aster_r19_linkusdt_absorption_base_fixed16_fullcash"
    NONNEG = ("aster_r19_linkusdt_absorption_nonnegative_funding"
              "_fixed16_fullcash")

    def test_neg_pair_shock_at_1p25_now_confirms(self):
        # Shock volume 1400 vs EMA ~1038: 1.25 x (~1298) clears,
        # 2.0 x refuses. Funding leg stays < 0 (rate -0.001).
        out = drive_r19(self.NEG, "LINKUSDT", abs_bars_link(1400.0),
                        -0.001)
        self.assertEqual(len([o for o in out if o.kind == "enter"]), 1)

    def test_base_multiple_unchanged(self):
        out = drive_r19(self.BASE, "LINKUSDT", abs_bars_link(1400.0),
                        -0.001)
        self.assertEqual(out, [])

    def test_b11_nonneg_multiple_unchanged(self):
        # Proposal 11 covers only the ADA pair in aster_sleeves;
        # the b11 nonnegative family keeps the 2.0 multiple.
        out = drive_r19(self.NONNEG, "LINKUSDT", abs_bars_link(1400.0),
                        0.001)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
