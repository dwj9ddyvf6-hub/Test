"""EDGE PASS batch 8 blockers (ENH-B8): stale-signal entry gate over the
12 LINKUSDT sleeves of desk3/aster_b11_crypto.py + aster_b12_crypto.py.

Leak (measured pre-change): entry fired on the latest snapshot bar
regardless of age — a signal bar closed 12h earlier (3 unseen 4h bars)
entered 12/12 sleeves at the stale close. Cure: default-ON per-sleeve
switch refuses entry when the signal bar closed >4h (one bar interval)
before now; OFF restores the faithful rule exactly; exits untouched
(owned deadlines survive stale/missing bars); shadow faithful arm is
recorded paired in extra["aster_edge_journal"] and never emits.
Fail-first: pre-change engines enter on the stale fixtures => these
tests fail there (proven by stash, see BUGLOG ENH-B8).
"""
import importlib, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
P = "aster_r19_linkusdt_"
B11 = [P+"absorption_negative_funding_fixed16_fullcash", P+"absorption_negative_funding_fixed16_volume1pct",
       P+"absorption_nonnegative_funding_fixed16_fullcash", P+"absorption_nonnegative_funding_fixed16_volume1pct",
       P+"breakout_base_fixed16_fullcash"]
B12 = [P+"breakout_base_fixed16_volume1pct", P+"negative_funding_squeeze_fixed16_fullcash",
       P+"negative_funding_squeeze_fixed16_volume1pct", P+"negative_funding_squeeze_fixed96_fullcash",
       P+"negative_funding_squeeze_fixed96_volume1pct", P+"negative_funding_squeeze_lost_breakout_fullcash",
       P+"negative_funding_squeeze_lost_breakout_volume1pct"]
IDS = B11 + B12
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)
SYM = "LINKUSDT"

def abs_bars(shift=0, n=302):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=shift) - timedelta(hours=4 * (n - i))
        o = c = 20.0; h = 20.2; l = 19.8; v = 1000.0
        if i == n - 2: o, c, h, l, v = 20.0, 19.0, 20.0, 18.8, 5000.0
        if i == n - 1: o, c = 19.0, 19.6
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l, "c": c, "v": v})
    return out

def brk_bars(shift=0, n=25):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=shift) - timedelta(hours=4 * (n - i))
        c = 22.0 if i == n - 1 else 20.0
        out.append({"t": t.isoformat(), "o": 20.0, "h": 20.5, "l": 19.5, "c": c, "v": 100000.0})
    return out

def funding_for(sid):
    if "breakout_base" in sid: return None
    return 0.01 if "nonnegative" in sid else -0.01

def bars_for(sid, shift=0):
    return abs_bars(shift) if "absorption" in sid else brk_bars(shift)

def drive(sid, shift=0, extra=None, positions=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    fund = funding_for(sid)
    view = {"now": NOW.isoformat(), "bars": {f"{SYM}|4Hour": bars_for(sid, shift)},
            "funding": {SYM: fund} if fund is not None else {},
            "positions": positions or [], "slice": {"cash_usd": 10000.0},
            "params": {}, "extra": extra or {}, "session_fills": []}
    return mod.evaluate(view, {"sleeve_id": sid, "state_dir": tempfile.mkdtemp()})

class TestStaleGate(unittest.TestCase):
    def test_fresh_signal_enters_all(self):
        for sid in IDS:
            out = drive(sid, shift=0)
            self.assertEqual([o.kind for o in out], ["enter"], sid)

    def test_stale_signal_refused_all_default_on(self):
        for sid in IDS:
            self.assertEqual(drive(sid, shift=12), [], sid)

    def test_switch_off_restores_faithful_stale_entry(self):
        for sid in IDS:
            extra = {"aster_edge": {sid: {"stale_signal_gate": False}}}
            out = drive(sid, shift=12, extra=extra)
            self.assertEqual([o.kind for o in out], ["enter"], sid)

    def test_boundary_age_exactly_4h_enters(self):
        for sid in IDS:
            self.assertEqual(len(drive(sid, shift=4)), 1, sid)

    def test_paired_shadow_journal(self):
        for sid in IDS:
            j = []
            self.assertEqual(drive(sid, shift=12, extra={"aster_edge_journal": j}), [], sid)
            self.assertEqual(len(j), 1, sid)
            self.assertEqual(j[0]["enhanced"], "refuse_stale_signal", sid)
            self.assertEqual(j[0]["shadow_faithful"], "enter", sid)
            self.assertAlmostEqual(j[0]["signal_age_h"], 12.0, places=2, msg=sid)
            j2 = []
            self.assertEqual(len(drive(sid, shift=0, extra={"aster_edge_journal": j2})), 1, sid)
            self.assertEqual(j2[0]["enhanced"], "enter", sid)
            self.assertEqual(j2[0]["shadow_faithful"], "enter", sid)

    def test_exit_deadline_survives_stale_bars(self):
        for sid in IDS:  # fixed16 arms at 20h; lost_breakout arms at their 96h backstop
            hrs = 100 if ("lost_breakout" in sid or "fixed96" in sid) else 20
            pos = [{"symbol": SYM, "qty": 100.0, "avg_price": 20.0,
                    "opened_at": (NOW - timedelta(hours=hrs)).isoformat(), "breakout_level": 20.5}]
            out = drive(sid, shift=12, positions=pos)
            self.assertEqual([o.kind for o in out], ["exit"], sid)

if __name__ == "__main__":
    unittest.main()
