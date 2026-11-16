"""HARDEN Edge batch 2 blockers (2026-10-24) — ENH-EDGE-B2.

Per-sleeve binding leaks + one decision-changing cure each, switch
default ON, OFF = pre-change rule exactly, shadow control paired in
ctx["enhance_paired"] (never emits):
- aster_breakout_ada_{fullcash,vol1pct}: signal is read on the bar
  before the entry bar (4h stale); cure revalidates the entry bar's
  close against the breakout boundary — a breakout already lost on
  the entry bar is refused instead of chased.
- aster_abs_nonneg_ada_vol1pct: its defining funding>=0 condition was
  checked only at signal close; cure re-checks the latest eligible
  funding receipt at the entry close — a flip to negative refuses.
- aster_enj_nfs_{lost,norm,normfail}_{full,vol}: the batch-8 engine
  has NO entry window at all; cure refuses entries whose last 4h bar
  closed more than one cadence hour (3600s) before evaluation.
- aster_enj_nfs_fixed96_vol: volume cap read the signal bar's volume
  (4h stale); cure also caps by the entry bar's volume.
- aster_core_rsi2_{long,vertical}: contract selection/execution was
  spread-blind (debit at the ask, market order); cure refuses a long
  leg whose spread exceeds 25% of its ask.
Fail-first: pre-cure engines have no gates — every ON assertion here
fails on them (verified by gate-neutralized run, BUGLOG HARDEN-EDGE-B2).
"""
import importlib, os, sys, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------- ADA
def _mk4(specs, end=NOW):
    n = len(specs)
    return [{"t": _iso(end - timedelta(hours=4 * (n - i))), "o": o, "h": h,
             "l": l, "c": c, "v": v} for i, (o, c, v, h, l) in enumerate(specs)]


def _breakout_bars(entry_close=1.05):
    specs = [(1.0, 1.0, 1000.0, 1.01, 0.99)] * 300
    specs.append((1.0, 1.05, 2000.0, 1.06, 0.99))        # signal bar
    specs.append((1.05, entry_close, 50000.0, 1.06, 0.99))  # entry bar
    return _mk4(specs)


def _absorption_bars():
    specs = [(1.0, 1.0, 1000.0, 1.001, 0.999)] * 300
    specs.append((1.0, 0.95, 3000.0, 1.001, 0.949))       # shock
    specs.append((0.95, 1.02, 1500.0, 1.021, 0.949))      # confirm=signal
    specs.append((1.02, 1.02, 1000.0, 1.021, 1.019))      # entry interval
    return _mk4(specs)


def _ada_view(sid, bars, funding=None, off_key=None):
    v = {"now": _iso(NOW), "bars": {"ADAUSDT|4Hour": bars}, "positions": [],
         "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "extra": {}}
    if funding is not None:
        v["funding"] = funding
    if off_key:
        v["extra"][f"{sid}_enhance"] = {off_key: False}
    return v


def _ada_ev(sid, view):
    ctx = {"sleeve_id": sid}
    out = importlib.import_module(f"aster_sleeves.{sid}").evaluate(view, ctx)
    return out, ctx


class TestAdaBreakoutRevalidation(unittest.TestCase):
    def test_entry_bar_lost_breakout_refused_on_enters_off(self):
        for sid in ("aster_breakout_ada_fullcash", "aster_breakout_ada_vol1pct"):
            on, ctx = _ada_ev(sid, _ada_view(sid, _breakout_bars(entry_close=1.00)))
            self.assertEqual(on, [], sid)
            self.assertTrue(any(r["treatment"] == "refuse_stale_breakout"
                                for r in ctx.get("enhance_paired", [])), sid)
            off, _ = _ada_ev(sid, _ada_view(sid, _breakout_bars(entry_close=1.00),
                                            off_key="entry_revalidation"))
            self.assertEqual(len(off), 1, sid)

    def test_entry_bar_holds_breakout_enters_both(self):
        for sid in ("aster_breakout_ada_fullcash", "aster_breakout_ada_vol1pct"):
            on, _ = _ada_ev(sid, _ada_view(sid, _breakout_bars(entry_close=1.05)))
            self.assertEqual(len(on), 1, sid)


class TestAdaAbsFundingRevalidation(unittest.TestCase):
    SID = "aster_abs_nonneg_ada_vol1pct"

    def _funding_flip(self):
        def row(rate, settled_h, recv_h):
            s = NOW - timedelta(hours=settled_h)
            return {"rate": rate, "settled_at": _iso(s),
                    "received_at": _iso(NOW - timedelta(hours=recv_h)),
                    "observed_public_endpoint": True}
        return {"ADAUSDT": [row(0.0005, 5, 4.5), row(-0.0005, 2, 1.5)]}

    def test_funding_flip_refused_on_enters_off(self):
        on, ctx = _ada_ev(self.SID, _ada_view(self.SID, _absorption_bars(),
                                              funding=self._funding_flip()))
        self.assertEqual(on, [])
        self.assertTrue(any(r["treatment"] == "refuse_funding_flipped"
                            for r in ctx.get("enhance_paired", [])))
        off, _ = _ada_ev(self.SID, _ada_view(self.SID, _absorption_bars(),
                                             funding=self._funding_flip(),
                                             off_key="funding_revalidation"))
        self.assertEqual(len(off), 1)


# ---------------------------------------------------------------- ENJ
ENJ_NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)
ENJ_FRESH = ["aster_enj_nfs_lost_full", "aster_enj_nfs_lost_vol",
             "aster_enj_nfs_norm_full", "aster_enj_nfs_norm_vol",
             "aster_enj_nfs_normfail_full", "aster_enj_nfs_normfail_vol"]


def _enj_bars(n=25, shift_h=0, entry_vol=100000.0):
    out = []
    for i in range(n):
        t = ENJ_NOW - timedelta(hours=shift_h + 4 * (n - i))
        c = 1.10 if i == n - 1 else 1.0
        v = entry_vol if i == n - 1 else 100000.0
        out.append({"t": t.isoformat(), "o": 1.0, "h": 1.05, "l": 0.95,
                    "c": c, "v": v})
    return out


def _enj_ev(sid, bars, off=False):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": ENJ_NOW.isoformat(),
            "bars": {"ENJUSDT|4Hour": bars},
            "funding": {"ENJUSDT": -0.01}, "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    if off:
        view["extra"][f"{sid}_enhance"] = {"entry_freshness": False,
                                            "entry_volume_cap": False}
    ctx = {"sleeve_id": sid, "session": "2026-10-23"}
    return mod.evaluate(view, ctx), ctx


class TestEnjEntryFreshness(unittest.TestCase):
    def test_stale_bar_refused_on_enters_off(self):
        for sid in ENJ_FRESH:
            on, ctx = _enj_ev(sid, _enj_bars(shift_h=8))
            self.assertEqual(on, [], sid)
            self.assertTrue(any(r["treatment"] == "refuse_stale_entry"
                                for r in ctx.get("enhance_paired", [])), sid)
            off, _ = _enj_ev(sid, _enj_bars(shift_h=8), off=True)
            self.assertEqual(len(off), 1, sid)

    def test_fresh_bar_enters_on(self):
        for sid in ENJ_FRESH:
            on, _ = _enj_ev(sid, _enj_bars())
            self.assertEqual(len(on), 1, sid)


class TestEnjFixed96EntryVolumeCap(unittest.TestCase):
    SID = "aster_enj_nfs_fixed96_vol"

    def test_entry_bar_volume_caps_below_signal_bar(self):
        on, ctx = _enj_ev(self.SID, _enj_bars(entry_vol=10000.0))
        self.assertEqual(len(on), 1)
        self.assertAlmostEqual(on[0]["qty"], 100.0, 4)  # 1% of entry bar
        self.assertTrue(any("enter_qty=100" in r.get("treatment", "")
                            for r in ctx.get("enhance_paired", [])))
        off, _ = _enj_ev(self.SID, _enj_bars(entry_vol=10000.0), off=True)
        self.assertAlmostEqual(off[0]["qty"], 1000.0, 4)  # signal-bar cap


# ------------------------------------------------------------- RSI2 core
from datetime import date  # noqa: E402
EPOCH = date(1970, 1, 1)
START = date(2025, 1, 1)


def _d_bars(closes):
    return [{"t": float(((START + timedelta(days=i)) - EPOCH).days * 86400),
             "o": c, "h": c * 1.001, "l": c * .999, "c": c, "v": 10000}
            for i, c in enumerate(closes)]


def _rsi2_series(n=210):
    return [100 + 0.5 * i for i in range(n - 3)] + [200.0, 190.0, 180.0]


def _chain(bid=0.35, ask=0.4):
    exp = (date(2025, 10, 6) + timedelta(days=17)).isoformat()
    return [{"symbol": "QQQ251023C00180000", "underlying": "QQQ",
             "right": "call", "expiry": exp, "strike": 180.0, "delta": 0.55,
             "bid": bid, "ask": ask, "bid_size": 50, "ask_size": 50},
            {"symbol": "QQQWING", "underlying": "QQQ", "right": "call",
             "expiry": exp, "strike": 185.0, "delta": 0.3, "bid": 0.2,
             "ask": 0.25, "bid_size": 50, "ask_size": 50}]


def _core_ev(sid, bid=0.35, ask=0.4, off=False):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"bars": {"QQQ": _d_bars(_rsi2_series())}, "options": _chain(bid, ask),
            "positions": [{"symbol": "QQQ", "qty": 52, "avg_price": 180.0}],
            "extra": {}}
    if off:
        view["extra"][f"{sid}_enhance"] = {"spread_gate": False}
    ctx = {"sleeve_id": sid, "session": "2025-10-06",
           "now": "2025-10-06T09:37:00", "equity": 10000.0}
    return mod.evaluate(view, ctx), ctx


class TestCoreSpreadGate(unittest.TestCase):
    def test_wide_spread_refused_on_enters_off(self):
        for sid in ("aster_core_rsi2_long", "aster_core_rsi2_vertical"):
            on, ctx = _core_ev(sid, bid=0.05, ask=0.4)
            self.assertEqual(on, [], sid)
            self.assertTrue(any(r["treatment"] == "refuse_wide_spread"
                                for r in ctx.get("enhance_paired", [])), sid)
            off, _ = _core_ev(sid, bid=0.05, ask=0.4, off=True)
            self.assertEqual(len(off), 1, sid)

    def test_tight_spread_enters_on(self):
        for sid in ("aster_core_rsi2_long", "aster_core_rsi2_vertical"):
            on, _ = _core_ev(sid)
            self.assertEqual(len(on), 1, sid)


if __name__ == "__main__":
    unittest.main()
