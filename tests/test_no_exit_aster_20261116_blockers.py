"""Blockers: NO-EXIT-ASTER-20261116 (desk full audit escalation 1,
owner ruling 2026-11-16: firing means entering, exiting, closing).

RSI2 pair (aster_core_rsi2_long / aster_core_rsi2_vertical): the QQQ
equity core leg (95% of the slice) had NO exit rule in
desk3/aster_b2.py — the exit loop skipped every position without
option legs. Cure: the core leg carries the family's own exit in the
same shape the options legs use (planned session exit at
hold_sessions=5; touch exit at entry*1.02 — both core books are
touch books). Sibling sources: desk3/aster_b2.py options-leg exit
block; desk3/aster_batch3.py _exit_intents. The core-exit tests FAIL
on the pre-cure tree (no exit intent is ever emitted for the core
leg) and PASS post-cure.

ETF six (buy-hold family): design pins, pass both ways by design —
they record the verified design fact the escalation report rests
on: freq == BUY_HOLD in desk3/aster_etf.SPECS (SPY row registered
by desk3/aster_batch11), the initial allocation IS reachable
(two-evaluation weight-lag drive returns an entry), and a held
position returns no exit intent because the source design carries
no exit mechanism at all (FIDELITY-LEDGER ASTER-B10/B11: buy-hold
no-exit is the source reading; SPY_HOLD_FULL "no designed exit —
operator liquidation only"). These six stay OPEN for an owner exit
ruling; no exit was invented for them.
"""
import importlib, os, sys, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EPOCH = date(1970, 1, 1)
START = date(2025, 1, 1)

CORE_SIDS = ["aster_core_rsi2_long", "aster_core_rsi2_vertical"]
ETF_TARGET = {"aster_etf_qld_buy_hold": ("QLD", 50.0),
              "aster_etf_qqq_buy_hold": ("QQQ", 100.0),
              "aster_etf_qqq_qld_buy_hold": ("QQQ", 100.0),
              "aster_etf_smh_hold_c098": ("SMH", 100.0),
              "aster_etf_smh_hold_m150": ("SMH", 100.0),
              "aster_etf_spy_buy_hold": ("SPY", 100.0)}


def bars(closes, start=START):
    return [{"t": float(((start + timedelta(days=i)) - EPOCH).days * 86400),
             "o": c, "h": c * 1.001, "l": c * .999, "c": c, "v": 10000}
            for i, c in enumerate(closes)]


def ctx(sid, session="2025-10-06"):
    return {"sleeve_id": sid, "session": session,
            "now": session + "T09:37:00", "equity": 10000.0}


def ev(sid, view):
    return importlib.import_module(f"adapters3.{sid}").evaluate(view, ctx(sid))


def core_pos(qty=47.5, avg=100.0, held=0):
    return [{"symbol": "QQQ", "qty": qty, "avg_price": avg,
             "entry_spot": avg, "sessions_held": held,
             "opened_at": "2025-10-06"}]


class TestRsi2CoreExit(unittest.TestCase):
    def test_core_entry_still_fires(self):
        for sid in CORE_SIDS:
            with self.subTest(sid=sid):
                out = ev(sid, {"bars": {"QQQ": bars([100.0] * 210)},
                               "options": [], "positions": []})
                self.assertEqual(len(out), 1)
                self.assertEqual(out[0]["kind"], "entry")
                self.assertEqual(out[0]["symbol"], "QQQ")

    def test_core_planned_session_exit_at_hold(self):
        for sid in CORE_SIDS:
            with self.subTest(sid=sid):
                out = ev(sid, {"bars": {"QQQ": bars([100.0] * 10)},
                               "options": [],
                               "positions": core_pos(held=5)})
                self.assertEqual(len(out), 1, (sid, out))
                self.assertEqual(out[0]["kind"], "exit")
                self.assertEqual(out[0]["symbol"], "QQQ")
                self.assertEqual(out[0]["side"], "sell")
                self.assertEqual(out[0]["position_intent"], "sell_to_close")
                self.assertIn("planned_session_exit", out[0]["reason"])
                self.assertEqual(float(out[0]["qty"]), 47.5)  # full close

    def test_core_touch_exit(self):
        for sid in CORE_SIDS:
            with self.subTest(sid=sid):
                out = ev(sid, {"bars": {"QQQ": bars([103.0] * 10)},
                               "options": [],
                               "positions": core_pos(held=2)})
                self.assertEqual(len(out), 1, (sid, out))
                self.assertEqual(out[0]["kind"], "exit")
                self.assertIn("touch_two_percent_recovery_exit",
                              out[0]["reason"])

    def test_core_no_premature_exit(self):
        for sid in CORE_SIDS:
            with self.subTest(sid=sid):
                out = ev(sid, {"bars": {"QQQ": bars([101.0] * 210)},
                               "options": [],
                               "positions": core_pos(held=2)})
                self.assertEqual(out, [], (sid, out))

    def test_core_entry_then_exit_end_to_end(self):
        for sid in CORE_SIDS:
            with self.subTest(sid=sid):
                entry = ev(sid, {"bars": {"QQQ": bars([100.0] * 210)},
                                 "options": [], "positions": []})
                self.assertEqual(entry[0]["kind"], "entry")
                qty = float(entry[0]["qty"])
                held = core_pos(qty=qty, avg=100.0, held=5)
                out = ev(sid, {"bars": {"QQQ": bars([100.0] * 10)},
                               "options": [], "positions": held})
                self.assertEqual(len(out), 1, (sid, out))
                self.assertEqual(out[0]["kind"], "exit")
                self.assertEqual(float(out[0]["qty"]), qty)


def _etf_bars():
    out = {}
    for sym, px in (("QQQ", 100.0), ("QLD", 50.0), ("SMH", 100.0),
                    ("SPY", 100.0)):
        out[sym] = [{"t": "2026-10-01", "o": px, "h": px, "l": px,
                     "c": px, "v": 10000}] * 260
    return out


def _etf_ev(sid, positions, now="2026-10-01T09:36:00", reset=False):
    from desk3 import aster_etf
    import desk3.aster_batch11  # registers the SPY buy-hold spec
    if reset:
        aster_etf._PENDING_TARGETS.pop(sid, None)
    view = {"bars": _etf_bars(), "positions": positions,
            "quotes": {}, "now": now}
    c = {"session": "2026-10-01", "extra": {"account_value": 10000.0}}
    return aster_etf.evaluate(sid, view, c)


class TestEtfBuyHoldDesignPins(unittest.TestCase):
    def test_specs_are_buy_hold_by_design(self):
        from desk3 import aster_etf
        import desk3.aster_batch11  # noqa: F401
        for sid in ETF_TARGET:
            with self.subTest(sid=sid):
                self.assertEqual(aster_etf.SPECS[sid]["freq"], "BUY_HOLD")

    def test_initial_allocation_entry_reachable(self):
        for sid in ETF_TARGET:
            with self.subTest(sid=sid):
                self.assertEqual(_etf_ev(sid, [], reset=True), [])  # lag
                out = _etf_ev(sid, [])
                self.assertIn("entry", [o["kind"] for o in out], (sid, out))

    def test_held_position_has_no_designed_exit(self):
        # Design fact (see module docstring): the buy-hold source
        # design carries no exit mechanism; these sleeves stay OPEN
        # for an owner exit ruling — this pin records the fact, it
        # does not bless it as a cure.
        for sid, (sym, px) in ETF_TARGET.items():
            with self.subTest(sid=sid):
                pos = [{"symbol": sym, "qty": 50, "avg_price": px,
                        "entry_date": "2026-09-02"}]
                out = _etf_ev(sid, pos, now="2026-11-02T09:36:00")
                self.assertEqual(out, [], (sid, out))


if __name__ == "__main__":
    unittest.main()
