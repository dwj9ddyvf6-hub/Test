"""Blockers: HARDEN Edge batch 17 — completed-bar-only inputs
(ENH-CBAR-20261024) for momentum, momentum_rotation, qullamaggie,
morning_dip.

Binding leak: the served bar series includes the current session's
still-forming bar; these strategies read bars[-1] as a completed
close (momentum's -40% breaker, rotation's ranks/pricing,
qullamaggie's features/stop/trail, morning_dip's "last closed
candle" indicators). Treatment (default ON, desk3/port_b5/_enh2.py):
the wrapper serves completed bars only — a 1Day bar dated the
current ET session is trimmed, an intraday bar whose span has not
closed is trimmed — and stamps a paired shadow record (control =
untrimmed evaluation in a throwaway state dir, never emitted).
Switch OFF (view.extra["<sleeve>_enh2"]["completed_bars"]=False)
restores the pre-change rule exactly.

Fail direction: on the pre-cure tree the wrappers served the
untrimmed view, so every *_treatment_* case below fails (treatment
== control); proven 2026-10-24 by running this file against the
stashed wrapper change.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SESSION = date(2026, 10, 21)  # Wednesday
NOW = "2026-10-21T10:00:00-04:00"


def _weekdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return list(reversed(out))


def daily(end, closes, vol=200000.0):
    days = _weekdays(end, len(closes))
    return [{"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c + 1,
             "l": c - 1, "c": c, "v": vol}
            for d, c in zip(days, closes)]


def ev(sid, view, cash=10000.0):
    view = dict(view)
    view.setdefault("slice", {"capital_usd": cash, "cash_usd": cash})
    view.setdefault("positions", [])
    mod = importlib.import_module(f"desk3.port_b5.{sid}")
    sd = tempfile.mkdtemp()
    return mod.evaluate(view, {"sleeve_id": sid, "state_dir": sd,
                               "cycle_id": "cyc-b17"})


def ev2(sid, view, cash=10000.0):
    # WEIGHT-LAG-ACTIVE-20261031: momentum_rotation holds one
    # evaluation's intents and emits them at the next DUE evaluation,
    # with the pending state in the cycle state_dir — so drive two
    # evaluations on ONE state dir: the first (due) computes weights
    # and emits nothing; the second is the next due weekly rebalance
    # (+7d, same bars), which acts on the held intents. (A same-day
    # second drive is a non-due rebalance and by design neither emits
    # nor advances the lag.) Returns (first, second).
    from datetime import datetime
    view = dict(view)
    view.setdefault("slice", {"capital_usd": cash, "cash_usd": cash})
    view.setdefault("positions", [])
    mod = importlib.import_module(f"desk3.port_b5.{sid}")
    ctx = {"sleeve_id": sid, "state_dir": tempfile.mkdtemp(),
           "cycle_id": "cyc-b17"}
    first = mod.evaluate(view, ctx)
    view2 = dict(view)
    view2["now"] = (datetime.fromisoformat(str(view["now"]))
                    + timedelta(days=7)).isoformat()
    return first, mod.evaluate(view2, ctx)


def off(view, sid):
    v = dict(view)
    v["extra"] = {f"{sid}_enh2": {"completed_bars": False}}
    return v


class TestMomentumBreaker(unittest.TestCase):
    def _view(self):
        # 139 completed bars 200 -> 130 (above the -40% breaker at
        # 120), plus a FORMING session bar at 100 (below it).
        closes = [200.0 - 70.0 * i / 138 for i in range(139)] + [100.0]
        bars = {"NVDA|1Day": daily(SESSION, closes),
                "SPY|1Day": daily(SESSION, [500.0] * 140),
                "VIX|1Day": daily(SESSION, [15.0] * 10)}
        return {"now": NOW, "bars": bars,
                "positions": [{"symbol": "NVDA", "qty": 3,
                               "avg_price": 200.0,
                               "opened_at": "2026-09-01T04:00:00Z"}]}

    def test_control_breaker_fires_on_forming_bar(self):
        out = ev("momentum", off(self._view(), "momentum"))
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1)
        self.assertIn("breaker", exits[0]["reason"])

    def test_treatment_breaker_waits_for_completed_close(self):
        out = ev("momentum", self._view())
        self.assertEqual([i for i in out if i["kind"] == "exit"], [])


class TestMomentumRotationRanks(unittest.TestCase):
    def _view(self):
        # AAA completed 100 -> 160, forming bar crashes to 100.
        # BBB completed 100 -> 130, forming bar flat at 130.
        aaa = [100.0 + 60.0 * i / 68 for i in range(69)] + [100.0]
        bbb = [100.0 + 30.0 * i / 68 for i in range(69)] + [130.0]
        return {"now": NOW, "params": {"symbols": ["AAA", "BBB"]},
                "bars": {"AAA|1Day": daily(SESSION, aaa),
                         "BBB|1Day": daily(SESSION, bbb)}}

    def test_control_ranks_off_forming_close(self):
        first, out = ev2("momentum_rotation", off(self._view(), "momentum_rotation"))
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        entries = {i["symbol"] for i in out if i["kind"] == "entry"}
        # AAA's forming crash makes its mom60 negative: the v1
        # absolute-momentum floor refuses it in the control too.
        self.assertEqual(entries, {"BBB"})

    def test_treatment_ranks_off_completed_close(self):
        first, out = ev2("momentum_rotation", self._view())
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        entries = {i["symbol"] for i in out if i["kind"] == "entry"}
        self.assertEqual(entries, {"AAA", "BBB"})
        stamped = [i for i in out if i.get("enhance_exp")]
        self.assertTrue(stamped, "paired shadow record must ride an intent")
        rec = stamped[0]["enhance_exp"]["records"][0]
        self.assertEqual(rec["exp_id"], "ENH-CBAR-20261024")
        self.assertEqual(rec["trimmed"], {"AAA|1Day": 1, "BBB|1Day": 1})
        self.assertEqual({c["symbol"] for c in rec["control_intents"]
                          if c["kind"] == "entry"}, {"BBB"})


class TestQullamaggieStop(unittest.TestCase):
    def _view(self):
        closes = [100.0] * 30 + [85.0]  # forming bar dips under entry
        return {"now": "2026-10-21T16:00:00-04:00",
                "bars": {"NVDA|1Day": daily(SESSION, closes)},
                "positions": [{"symbol": "NVDA", "qty": 10,
                               "avg_price": 100.0,
                               "opened_at": "2026-10-01T04:00:00Z"}]}

    def test_control_stop_breach_on_forming_close(self):
        out = ev("qullamaggie", off(self._view(), "qullamaggie"))
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1)
        self.assertIn("stop breach", exits[0]["reason"])

    def test_treatment_stop_breach_is_close_based(self):
        out = ev("qullamaggie", self._view())
        self.assertEqual([i for i in out if i["kind"] == "exit"], [])


class TestMorningDipCandle(unittest.TestCase):
    def _candles(self):
        rows = []
        for k, start in enumerate(("14:15", "14:18", "14:21", "14:24")):
            rows.append({"t": f"2026-10-21T{start}:00Z", "o": 495.0,
                         "h": 496.0, "l": 494.0, "c": 495.0, "v": 1000,
                         "healthy": True})
        # forming candle 14:27-14:30Z, now is 14:29Z: closes at 480
        rows.append({"t": "2026-10-21T14:27:00Z", "o": 495.0,
                     "h": 496.0, "l": 479.0, "c": 480.0, "v": 1000,
                     "healthy": True})
        return rows

    def _view(self):
        return {"now": "2026-10-21T10:29:00-04:00",
                "bars": {"QQQ|3Min": self._candles()},
                "positions": [{"symbol": "QQQ", "qty": 10,
                               "avg_price": 500.0, "stop_px": 490.0,
                               "opened_at": "2026-10-21T14:20:00Z"}]}

    def test_control_stop_hit_on_forming_candle(self):
        out = ev("morning_dip", off(self._view(), "morning_dip"),
                 cash=20000.0)
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1)
        self.assertIn("stop", exits[0]["reason"])

    def test_treatment_uses_last_closed_candle(self):
        out = ev("morning_dip", self._view(), cash=20000.0)
        self.assertEqual([i for i in out if i["kind"] == "exit"], [])


if __name__ == "__main__":
    unittest.main()
