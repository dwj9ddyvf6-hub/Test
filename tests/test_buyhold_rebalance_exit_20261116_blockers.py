"""BUYHOLD-REBALANCE-EXIT-20261116 blockers (owner ruling
2026-11-16 12:46 ET, "Make it work").

The six aster BUY_HOLD ETF sleeves — aster_etf_qld_buy_hold,
aster_etf_qqq_buy_hold, aster_etf_qqq_qld_buy_hold,
aster_etf_smh_hold_c098, aster_etf_smh_hold_m150,
aster_etf_spy_buy_hold — had their entries cured earlier today
(own_book_view, ETF-BUYHOLD-ENTRY-20261116) but carried NO exit
of any kind: desk3/aster_etf.evaluate returned [] for a BUY_HOLD
sleeve whenever it held anything. The owner's ruling: the exit a
buy-and-hold book honestly has is rebalancing back to its fixed
target weights; the excess over target is what exits.

Cure: a drift-band rebalance exit in desk3/aster_etf.evaluate.
A held BUY_HOLD sleeve falls through to its fixed targets and
the module's weight-lag path, but emits SELL-ONLY intents: for a
fixed-target symbol, when the held weight (held value / sizing
equity) exceeds the target weight (gross * fixed weight) by
more than the band, exactly the whole-share excess over the
target share count is sold (kind "exit", sell_to_close, the
module's normal intent shape). Positions at or under
target+band are held untouched; a held sleeve never buys;
entries (the flat path) are unchanged.

Band provenance (ADOPTED, not invented): the estate's sole
genuine weight-deviation tolerance is the ENH-B5 no-trade
deadband in desk3/aster_batch1.py — comment lines 1010-1015
("drift adjustments within 0.5% of book value are refused") and
code lines 1137-1146 (abs(drift) <= 0.005 * book). The other
leads carry no band: aster_batch8/aster_etf_b9 DRIFT1 is
incumbent-share retention, and aster_etf's own REBALANCE_POLICY
declared drift_threshold None. Adopted value:
BUYHOLD_DRIFT_BAND = 0.005, drift_type "absolute" (contract
terms, desk3/contract.py), declared in REBALANCE_POLICY's
"buyhold_rebalance_exit" block (book-level drift_threshold
stays None: the band is scoped to the BUY_HOLD subset only).

Falsifier (forward, checkable): the band is falsified if, on
any live session from the first forward read on Tue
2026-11-17, a held position in any of the six sleeves shows
drift beyond 0.005 above its target weight at an in-window
(09:35-09:40 ET) evaluation and no exit intent for the excess
is emitted by that sleeve that session (read from the
dispatcher journal / sleeve intents of record).

Fixture prices: the recorded warm snapshot used by the entry
cure (state/warm_bars.json fetched 2026-11-16T16:38:20Z; last
1Day closes, 2026-11-13): SPY 754.37, QQQ 679.89, QLD 79.30,
SMH 486.75. At $10K slices the initial entries are SPY 13;
QQQ 14; QLD 126; QQQ 7 + QLD 63; SMH 20 (gross 0.98);
SMH 30 (gross 1.5). Entries go through the module's weight lag
(WEIGHT-LAG-ACTIVE-20261031) exactly as before (first flat
evaluation stores, second emits). The held rebalance exit does
not consume or advance the lag: the target weights are fixed
constants, the band is measured on the current closed-bar
price, and the pre-cure held path never touched the pending
state (pinned by test_aster_batch11_blockers refusals) — so a
moved-price evaluation emits the exit immediately, and after
the exit fills, the remainder sits at target and emits nothing.
"""
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# aster_etf_spy_buy_hold's spec registers into desk3.aster_etf.SPECS
# when desk3.aster_batch11 is imported — exactly what loading its
# adapters3 module does on the live runner path.
import desk3.aster_batch11  # noqa: F401,E402
import desk3.aster_etf as ae  # noqa: E402

ET = ZoneInfo("America/New_York")

SIX = ["aster_etf_qld_buy_hold", "aster_etf_qqq_buy_hold",
       "aster_etf_qqq_qld_buy_hold", "aster_etf_smh_hold_c098",
       "aster_etf_smh_hold_m150", "aster_etf_spy_buy_hold"]

CLOSES = {"SPY": 754.37, "QQQ": 679.89, "QLD": 79.30, "SMH": 486.75}

EXPECTED_ENTRY = {
    "aster_etf_spy_buy_hold": [("SPY", 13)],
    "aster_etf_qqq_buy_hold": [("QQQ", 14)],
    "aster_etf_qld_buy_hold": [("QLD", 126)],
    "aster_etf_qqq_qld_buy_hold": [("QQQ", 7), ("QLD", 63)],
    "aster_etf_smh_hold_c098": [("SMH", 20)],
    "aster_etf_smh_hold_m150": [("SMH", 30)],
}

# Price move per sleeve -> the single rebalance exit it must emit.
# SPY +10%: target floor(10000/829.807)=12, excess 13-12=1.
# QQQ +10%: target floor(10000/747.879)=13, excess 14-13=1.
# QLD +10%: target floor(10000/87.23)=114, excess 126-114=12.
# QQQ_QLD, QQQ +20% only: QQQ target floor(5000/815.868)=6,
#   excess 7-6=1; QLD price/target/held unchanged -> untouched.
# SMH c098 +10%: target floor(9800/535.425)=18, excess 20-18=2.
# SMH m150 +10%: target floor(15000/535.425)=28, excess 30-28=2.
MOVES = {
    "aster_etf_spy_buy_hold": ("SPY", 1.10, ("SPY", 1)),
    "aster_etf_qqq_buy_hold": ("QQQ", 1.10, ("QQQ", 1)),
    "aster_etf_qld_buy_hold": ("QLD", 1.10, ("QLD", 12)),
    "aster_etf_qqq_qld_buy_hold": ("QQQ", 1.20, ("QQQ", 1)),
    "aster_etf_smh_hold_c098": ("SMH", 1.10, ("SMH", 2)),
    "aster_etf_smh_hold_m150": ("SMH", 1.10, ("SMH", 2)),
}


def _view(now, positions, closes=None):
    closes = CLOSES if closes is None else closes
    return {"now": now,
            "bars": {f"{s}|1Day": [{"c": px}]
                     for s, px in closes.items()},
            "positions": positions}


def _ctx(state_dir):
    return {"state_dir": state_dir,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {"account_value": 10000.0}}


def _t(minute):
    return datetime(2026, 11, 16, 9, minute, tzinfo=ET)


class TestBuyHoldRebalanceExit(unittest.TestCase):
    def setUp(self):
        # Module pending state is shared across the gate process:
        # start clean and leave nothing behind for other suites.
        for sid in SIX:
            ae._PENDING_TARGETS.pop(sid, None)

    def tearDown(self):
        for sid in SIX:
            ae._PENDING_TARGETS.pop(sid, None)

    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def _enter(self, sid):
        """Enter to target through the sleeve's own flat path;
        returns (held positions, state_dir)."""
        ae._PENDING_TARGETS.pop(sid, None)
        sd = os.path.join(self._root(), sid)
        out1 = ae.evaluate(sid, _view(_t(35), []), _ctx(sd))
        self.assertEqual(out1, [], sid)  # weight lag: 1st stores
        out2 = ae.evaluate(sid, _view(_t(36), []), _ctx(sd))
        got = sorted((o["symbol"], o["qty"]) for o in out2)
        self.assertEqual(got, sorted(EXPECTED_ENTRY[sid]), sid)
        for o in out2:
            self.assertEqual(o["kind"], "entry", sid)
            self.assertEqual(o["side"], "buy", sid)
        held = [{"symbol": s, "qty": float(q),
                 "avg_price": CLOSES[s]} for s, q in EXPECTED_ENTRY[sid]]
        return held, sd

    def _act(self, sid, view, sd):
        """Evaluate twice at the same view: a correct held
        rebalance is stable — the drift drive asserts the exit
        on the first and the controls assert silence on both."""
        first = ae.evaluate(sid, view, _ctx(sd))
        second = ae.evaluate(sid, view, _ctx(sd))
        return first, second

    def test_band_is_the_adopted_estate_deadband(self):
        self.assertEqual(ae.BUYHOLD_DRIFT_BAND, 0.005)
        self.assertEqual(ae.BUYHOLD_DRIFT_BAND_TYPE, "absolute")
        decl = ae.REBALANCE_POLICY["buyhold_rebalance_exit"]
        self.assertEqual(decl["drift_threshold"], 0.005)
        self.assertEqual(decl["drift_type"], "absolute")
        self.assertIn("aster_batch1", decl["source"])
        # Book-level band stays undeclared: MONTHLY sleeves in
        # this book carry no drift band.
        self.assertIsNone(ae.REBALANCE_POLICY["drift_threshold"])

    def test_drift_beyond_band_exits_excess_only(self):
        for sid in SIX:
            with self.subTest(sid=sid):
                held, sd = self._enter(sid)
                sym, mult, (xsym, xqty) = MOVES[sid]
                moved = dict(CLOSES)
                moved[sym] = CLOSES[sym] * mult
                out = ae.evaluate(sid, _view(_t(37), held, moved),
                                  _ctx(sd))
                self.assertEqual(len(out), 1, (sid, out))
                o = out[0]
                self.assertEqual(o["kind"], "exit", sid)
                self.assertEqual(o["side"], "sell", sid)
                self.assertEqual(o["position_intent"],
                                 "sell_to_close", sid)
                self.assertEqual((o["symbol"], o["qty"]),
                                 (xsym, xqty), sid)
                self.assertIn("drift-band", o["reason"], sid)
                # The remainder is held: exit qty is only the
                # excess over the fixed target, never the position.
                entry_qty = dict(EXPECTED_ENTRY[sid])[xsym]
                self.assertLess(o["qty"], entry_qty, sid)
                # After the exit fills, the remainder sits at the
                # target at the moved price: no further intent.
                filled = [dict(p) for p in held]
                for p in filled:
                    if p["symbol"] == xsym:
                        p["qty"] -= o["qty"]
                self.assertEqual(
                    ae.evaluate(sid, _view(_t(38), filled, moved),
                                _ctx(sd)), [], sid)

    def test_no_drift_control_emits_nothing(self):
        for sid in SIX:
            with self.subTest(sid=sid):
                held, sd = self._enter(sid)
                first, second = self._act(
                    sid, _view(_t(37), held), sd)
                self.assertEqual(first, [], sid)
                self.assertEqual(second, [], sid)

    def test_within_band_excess_is_held(self):
        # QLD +0.4%: the target share count drops to 125 (one
        # share of share-count excess) but the weight drift is
        # (126*79.6172 - 10000)/10000 = 0.0034 <= 0.005 band, so
        # the band — not raw delta — gates the exit: no intent.
        sid = "aster_etf_qld_buy_hold"
        held, sd = self._enter(sid)
        moved = dict(CLOSES)
        moved["QLD"] = CLOSES["QLD"] * 1.004
        first, second = self._act(sid, _view(_t(37), held, moved), sd)
        self.assertEqual(first, [], sid)
        self.assertEqual(second, [], sid)

    def test_under_target_held_sleeve_never_buys(self):
        # Price -10% on the moved leg raises its target share
        # count above the holding; a held buy-hold sleeve is
        # sell-only, so it stays untouched (entries are flat-only).
        for sid in SIX:
            with self.subTest(sid=sid):
                held, sd = self._enter(sid)
                sym = MOVES[sid][0]
                moved = dict(CLOSES)
                moved[sym] = CLOSES[sym] * 0.90
                first, second = self._act(
                    sid, _view(_t(37), held, moved), sd)
                self.assertEqual(first, [], sid)
                self.assertEqual(second, [], sid)


if __name__ == "__main__":
    unittest.main()
