"""Blockers QULLA-EXIT-CANON-20261116 (Mon 2026-11-16 total audit,
row 2): qullamaggie_paper's only exit was the core GTC stop.

Cure: the sleeve now evaluates the Qullamaggie exit structure AS
ADOPTED in the estate's 2026-10-28 master-trader playbook
(research_notes/master-traders-deep-dive-20261029-0229/report.md
section 1.10 Setup 1 step 6: sell 1/3 to 1/2 after 3-5 days into
strength, stop on the rest to breakeven, trail the 10-day or
20-day MA, exit on first close below the trailing MA; section 7.2
cards 2-3 carry the same two-stage exit), with the reconstruction's
frozen constants (qualla_desk/config.json: scale_days 3,
scale_fraction 1/3, trail MAs 10/20, extension 1.5 ATR) — the same
form sleeves/qullamaggie.py already runs. Plumbing: the adapter
serves positions + 1Day bars for held symbols; the wrapper/config
inputs gain 'bars'. Entry signal, sizing, stops-as-specified are
unchanged.

Fixture drives below run the full v3 evaluate(view, ctx) path.
Every exit case is a position the OLD exit held (the pre-cure
sleeve emitted no exit intents at all).

Fail direction: on the pre-cure tree (git archive of the row-1
commit) the trail/scale/stop-breach drives emit no exits and fail;
the no-exit control and the entry-preservation drive pass both
ways by design.
"""
import importlib
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sleeves import qullamaggie_paper as qp  # noqa: E402

MOD = importlib.import_module("desk3.port_b5.qullamaggie_paper")
NOW = "2026-10-21T16:00:00-04:00"


def _weekdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return list(reversed(out))


def _bars(closes, end=date(2026, 10, 21)):
    days = _weekdays(end, len(closes))
    return [{"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c + 0.3,
             "l": c - 0.3, "c": c, "v": 1000000}
            for d, c in zip(days, closes)], days


def _ev(view):
    view = dict(view)
    view.setdefault("slice", {"capital_usd": 10000.0, "cash_usd": 10000.0})
    view.setdefault("now", NOW)
    ctx = {"sleeve_id": "qullamaggie_paper",
           "state_dir": tempfile.mkdtemp(), "cycle_id": "cyc-test"}
    return MOD.evaluate(view, ctx)


def _pos(qty=10, avg=100.0, stop=85.0, opened="2026-09-14"):
    return {"symbol": "NVDA", "qty": qty, "avg_price": avg,
            "opened_at": f"{opened}T04:00:00Z", "intent_id": "seed-1",
            "stop_px": stop, "exit_rules": None}


class TestExitCanonDrives(unittest.TestCase):
    def test_trail_breach_exits_residual(self):
        # Playbook 1.10 step 6: exit on first close below the
        # trailing MA. 25 sessions at 100, final close 90 < 10MA 99;
        # above the 85 stop, so ONLY the trail can exit this.
        bars, days = _bars([100.0] * 25 + [90.0])
        out = _ev({"bars": {"NVDA|1Day": bars},
                   "positions": [_pos(opened=days[0].isoformat())]})
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertEqual(exits[0]["qty"], 10)
        self.assertIn("trail breach (10MA)", exits[0]["reason"])

    def test_scale_third_into_strength_declares_breakeven(self):
        # Playbook 1.10 step 6 / qualla_desk scale_days 3,
        # scale_fraction 1/3: held 5 sessions, profitable, qty 9
        # -> exit 3, residual stop declared to breakeven.
        closes = [100.0 + 30.0 * i / 25 for i in range(26)]
        bars, days = _bars(closes)
        out = _ev({"bars": {"NVDA|1Day": bars},
                   "positions": [_pos(qty=9, stop=90.0,
                                      opened=days[-6].isoformat())]})
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertEqual(exits[0]["qty"], 3)
        self.assertIn("scale 1/3", exits[0]["reason"])
        self.assertIn("residual stop -> breakeven", exits[0]["reason"])
        self.assertIn("scaled_third=1", exits[0]["reason"])

    def test_stop_breach_exits_in_signal(self):
        bars, days = _bars([100.0] * 25 + [88.0])
        out = _ev({"bars": {"NVDA|1Day": bars},
                   "positions": [_pos(stop=95.0,
                                      opened=days[0].isoformat())]})
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertEqual(exits[0]["qty"], 10)
        self.assertIn("stop breach", exits[0]["reason"])

    def test_young_profitable_position_is_held(self):
        # Control: held 2 sessions (< scale_days / trail minimum),
        # close above the MA -> no exit of any kind.
        closes = [100.0 + 30.0 * i / 25 for i in range(26)]
        bars, days = _bars(closes)
        out = _ev({"bars": {"NVDA|1Day": bars},
                   "positions": [_pos(qty=9, stop=90.0,
                                      opened=days[-3].isoformat())]})
        self.assertEqual(out, [])

    def test_already_scaled_position_does_not_scale_again(self):
        # Sent entry order was 9, position is 6: a partial exit
        # already happened, so the scale leg is spent; price above
        # the MA -> no trail either.
        closes = [100.0 + 30.0 * i / 25 for i in range(26)]
        bars, days = _bars(closes)
        view = {"bars": {"NVDA|1Day": bars},
                "params": {
                    "positions": [_pos(qty=6, stop=90.0,
                                       opened=days[-6].isoformat())],
                    "sleeve_state": {"orders": [{
                        "client_id": "qulla-x-NVDA-buy", "status": "sent",
                        "quantity": 9, "entry": 100.0, "symbol": "NVDA"}]}}}
        self.assertEqual(_ev(view), [])

    def test_entry_path_preserved_beside_a_held_position(self):
        closes = [100.0 + 30.0 * i / 25 for i in range(26)]
        bars, days = _bars(closes)
        view = {"bars": {"NVDA|1Day": bars},
                "positions": [_pos(qty=9, stop=90.0,
                                   opened=days[-3].isoformat())],
                "params": {"proposals": [
                    {"symbol": "META", "side": 1, "setup": "breakout",
                     "quantity": 5, "entry": 150.0, "stop": 140.0}]}}
        out = _ev(view)
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "META")
        self.assertFalse([i for i in out if i["kind"] == "exit"], out)


class TestTrailTargetShape(unittest.TestCase):
    def test_extended_name_trails_on_20ma(self):
        # qualla_desk extension_threshold_atr 1.5: a close extended
        # > 1.5 ATR above the 10MA trails on the 20MA instead.
        bars, _ = _bars([100.0] * 39 + [130.0])
        epoch_bars = []
        import calendar
        for b in bars:
            t = calendar.timegm(
                (int(b["t"][:4]), int(b["t"][5:7]), int(b["t"][8:10]),
                 4, 0, 0, 0, 0, 0))
            epoch_bars.append({**b, "t": float(t)})
        ma, lbl = qp._trail_target(epoch_bars)
        self.assertEqual(lbl, "20MA-ext")
        self.assertAlmostEqual(ma, (19 * 100.0 + 130.0) / 20)

    def test_constants_are_the_reconstructions_frozen_config(self):
        self.assertEqual(qp.SCALE_DAYS, 3)
        self.assertAlmostEqual(qp.SCALE_FRACTION, 1 / 3)
        self.assertEqual(qp.TRAIL_MA_FAST, 10)
        self.assertEqual(qp.TRAIL_MA_SLOW, 20)
        self.assertEqual(qp.EXTENSION_ATR, 1.5)
        self.assertIn("QULLA-EXIT-CANON-20261116", qp.__doc__)


if __name__ == "__main__":
    unittest.main()
