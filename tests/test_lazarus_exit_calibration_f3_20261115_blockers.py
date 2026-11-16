"""F3-LAZARUS-EXITS-20261115 blockers (KG-7 exit calibration, Lane F3).

KG-7 paired per-trade replay deltas vs each sleeve's registered base
(KG-7-EXIT-VARIATIONS.md / KG-7-REGISTER.jsonl) ordered exactly four
exit-profile changes, applied at the single registered source
(desk3/lazarus.py SPECS):

  1w         stop_pct 0.15 -> 0.30  (WIDEN_STOP_X2 +1423.0bp, n=28,
             beats DROP_STOP +1212.8bp)
  1wa        stop_pct 0.15 -> None  (DROP_STOP +1029.1bp, n=34,
             beats WIDEN_STOP_X2 +1021.0bp)
  s_1wlab    stop_pct 0.15 -> None  (DROP_STOP +676.4bp, n=80,
             beats WIDEN_STOP_X2 +654.1bp)
  s_rules_1w horizon_sessions 27 -> 54 (EXTEND_HORIZON_X2 +497.7bp,
             n=58, t=2.28; stop stays 0.15)

Protected, NOT touched (load-bearing registered profiles):
  1d   stop_pct 0.15 / target_pct 0.20 / partial_pct 0.30 / h=40
       (DROP_STOP printed -213.3bp, n=56: stop pairs with the +20%
       partial target)
  1dc  stop_pct None / h=21 (EXTEND_HORIZON_X2 printed -604.3bp,
       t=-4.06: the 21-session horizon is load-bearing)

Fail direction: proven on the preserved pre-cure copy of
desk3/lazarus.py in /tmp (lazarus_precure_F3.py) — every changed-value
assertion below fails there; all pass on the cured tree.
"""
import importlib, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from desk3.lazarus import SPECS

NOW = datetime(2026, 11, 15, 14, 0, tzinfo=timezone.utc)


def mod(sid):
    return importlib.import_module(f"adapters3.laz_{sid}")


def bars(sym, closes):
    return {f"{sym}|1Day": [{"t": f"2026-11-{10 + i:02d}T14:00:00Z",
                             "o": c, "h": c, "l": c, "c": c, "v": 1000}
                            for i, c in enumerate(closes)]}


def view(positions=None, extra_bars=None):
    v = {"now": NOW.isoformat(), "lazarus_fires": [],
         "positions": positions or [], "bars": {}}
    if extra_bars:
        v["bars"].update(extra_bars)
    return v


def ctx():
    return {"sleeve_id": "x", "state_dir": tempfile.mkdtemp(),
            "cycle_id": "fx", "snapshot_hash": "fx"}


def pos(sym="AAA", qty=10, avg=100.0, days_ago=1):
    return {"symbol": sym, "qty": qty, "avg_price": avg,
            "opened_at": (NOW - timedelta(days=days_ago)).isoformat()}


class TestChangedRegisteredValues(unittest.TestCase):
    def test_1w_stop_widened_x2(self):
        self.assertEqual(SPECS["1w"]["stop_pct"], 0.30)
        self.assertEqual(SPECS["1w"]["horizon_sessions"], 252)

    def test_1wa_stop_dropped(self):
        self.assertIsNone(SPECS["1wa"]["stop_pct"])
        self.assertEqual(SPECS["1wa"]["horizon_sessions"], 252)

    def test_s_1wlab_stop_dropped(self):
        self.assertIsNone(SPECS["s_1wlab"]["stop_pct"])
        self.assertEqual(SPECS["s_1wlab"]["horizon_sessions"], 126)

    def test_s_rules_1w_horizon_extended_x2(self):
        self.assertEqual(SPECS["s_rules_1w"]["horizon_sessions"], 54)
        self.assertEqual(SPECS["s_rules_1w"]["stop_pct"], 0.15)


class TestProtectedRegisteredValues(unittest.TestCase):
    def test_1d_stop_target_pair_untouched(self):
        s = SPECS["1d"]
        self.assertEqual(s["stop_pct"], 0.15)
        self.assertEqual(s["target_pct"], 0.20)
        self.assertEqual(s["partial_pct"], 0.30)
        self.assertEqual(s["horizon_sessions"], 40)

    def test_1dc_horizon_21_untouched(self):
        s = SPECS["1dc"]
        self.assertIsNone(s["stop_pct"])
        self.assertEqual(s["horizon_sessions"], 21)


class TestChangedBehavior(unittest.TestCase):
    def test_1w_holds_through_16pct_dip_stops_at_35pct(self):
        out = mod("1w").evaluate(view([pos()], bars("AAA", [100, 84])), ctx())
        self.assertEqual(out, [])
        out = mod("1w").evaluate(view([pos()], bars("AAA", [100, 65])), ctx())
        self.assertEqual(len(out), 1)
        self.assertIn("stop", out[0]["reason"])

    def test_1wa_and_s_1wlab_hold_through_50pct_dip(self):
        for sid in ["1wa", "s_1wlab"]:
            out = mod(sid).evaluate(view([pos()], bars("AAA", [100, 50])), ctx())
            self.assertEqual(out, [], sid)

    def test_1d_still_stops_at_16pct_dip(self):
        out = mod("1d").evaluate(view([pos()], bars("AAA", [100, 84])), ctx())
        self.assertEqual(len(out), 1)
        self.assertIn("stop15", out[0]["reason"])


if __name__ == "__main__":
    unittest.main()
