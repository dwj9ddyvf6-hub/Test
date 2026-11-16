"""Blockers: GATE-CURE-W1-20261112 — aster_tensor_w1_recovery's
234-bar minimum re-based from the weekly panel index to the
underlying daily source series (STRICTNESS-CENSUS-2026-11-12
proposal 7).

Defect: the entry adapter applied the engine's 234-bar minimum to
the weekly panel's own bar_index (max ~70 bars in any real weekly
panel), so no weekly panel could ever clear it: 0 lifetime entries
by construction. Registered cure: for the weekly spec the minimum
applies to the underlying daily source series (warm cache: 346
sessions per symbol); the hourly spec keeps the panel-index rule
exactly.

Fail direction: proven on the pre-cure tree (the 70-bar weekly
panel with a 250-bar daily series is refused pre-cure and enters
post-cure). Pre-cure copies preserved under
~/workspace/.gatecure-20261112/pre/.
"""
import importlib, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def ctx():
    return {"sleeve_id": "x", "state_dir": tempfile.mkdtemp(),
            "cycle_id": "fx"}


def ev(sid, view):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, ctx())


def trow(idx, votes, frame="1wk", **kw):
    bull = sum(1 for v in votes if v == 1)
    bear = sum(1 for v in votes if v == -1)
    d = {"bar_index": idx, "votes": votes, "bullish_votes": bull,
         "bearish_votes": bear, "total_votes": bull + bear,
         "balance": bull - bear, "close": 50.0, "atr14": 1.0,
         "dollar_volume20": 2_000_000, "volume": 100000,
         "obv_slope5": 500.0, "native_status": "ready",
         "frame": frame}
    d.update(kw)
    return d


def repair_panel(start, frame):
    return [trow(start + 0, [-1, -1, -1, -1, 1, -1, -1], frame),
            trow(start + 1, [-1, -1, 1, -1, 1, -1, -1], frame),
            trow(start + 2, [1, -1, 1, -1, 1, -1, -1], frame),
            trow(start + 3, [1, 1, 1, -1, 1, -1, -1], frame)]


def daily(n, sym="ACME"):
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return {f"{sym}|1Day": [
        {"t": (base + timedelta(days=i)).isoformat(), "o": 50.0,
         "h": 50.05, "l": 49.95, "c": 50.0, "v": 100000}
        for i in range(n)]}


def view(panels, bars):
    return {"now": "2026-10-23T14:00:00+00:00", "tensor": panels,
            "bars": bars, "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class T(unittest.TestCase):
    def test_w1_enters_on_realistic_weekly_panel(self):
        # A real weekly panel tops out near 70 bars; the daily
        # source series (250 bars) carries the 234 minimum.
        out = ev("aster_tensor_w1_recovery",
                 view({"ACME": repair_panel(66, "1wk")}, daily(250)))
        self.assertEqual(len([o for o in out
                              if o["kind"] == "entry"]), 1)

    def test_w1_still_refuses_when_daily_series_short(self):
        out = ev("aster_tensor_w1_recovery",
                 view({"ACME": repair_panel(66, "1wk")}, daily(150)))
        self.assertEqual(out, [])

    def test_w1_still_requires_the_repair_pattern(self):
        flat = [trow(66 + i, [1, 1, 1, -1, 1, -1, -1], "1wk")
                for i in range(4)]
        out = ev("aster_tensor_w1_recovery",
                 view({"ACME": flat}, daily(250)))
        self.assertEqual(out, [])

    def test_h1_panel_index_rule_unchanged(self):
        # The hourly spec keeps the panel-index minimum exactly.
        out = ev("aster_tensor_h1_recovery",
                 view({"ACME": repair_panel(100, "1h")}, daily(300)))
        self.assertEqual(out, [])
        out = ev("aster_tensor_h1_recovery",
                 view({"ACME": repair_panel(240, "1h")}, daily(300)))
        self.assertEqual(len([o for o in out
                              if o["kind"] == "entry"]), 1)


if __name__ == "__main__":
    unittest.main()
