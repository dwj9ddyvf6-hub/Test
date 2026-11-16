"""Blockers EDGE-B20: cross-symbol stale-feed (xstale) entry gate for
the Midna laz8 sleeves + second-look gates for s_mn_nostop (laz_b7
engine) and s_mn_hourly_1w / s_mn_w_cyan_breadth (lazarus_midna).

Binding leak: entries decide on a symbol's last bar as if current
even when that symbol's feed stopped >4 days (daily) / >4h (hourly)
before the rest of the snapshot. ON (default): refuse the entry,
journal the paired shadow record. OFF: pre-change rule exactly.
Fail direction: pre-cure none of the gates exist, so every ON
assertion fails (stale entries emit).
"""
import importlib, os, sys, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EPOCH = date(1970, 1, 1)
START = date(2025, 1, 1)


def bars(closes, start=START, vol=10000):
    out = []
    for i, c in enumerate(closes):
        d = start + timedelta(days=i)
        out.append({"t": float((d - EPOCH).days * 86400), "o": c,
                    "h": c * 1.001, "l": c * 0.999, "c": c, "v": vol})
    return out


def ctx(sid, extra=None, session="2025-04-10"):
    return {"sleeve_id": sid, "session": session,
            "now": session + "T15:00:00", "equity": 10000.0,
            "extra": extra or {}}


def ev(sid, view, extra=None):
    return importlib.import_module(f"adapters.{sid}").evaluate(
        view, ctx(sid, extra))


def off(sid):
    return {f"{sid}_enh20": {"stale_gate": False}}


class TestLaz8XStale(unittest.TestCase):
    def test_macd(self):
        from sleeves.s_mn_macd import macd_hist
        cl = [100 - 0.3 * i for i in range(45)] + [86.5 + 1.2 * i for i in range(1, 30)]
        h = macd_hist(cl)
        idx = next(i for i in range(35, len(h)) if h[i - 1] <= 0 < h[i])
        view = {"bars": {"AAA": bars(cl[:idx + 1]), "BBB": bars([100.0] * 140)},
                "positions": []}
        j = []
        self.assertEqual(ev("s_mn_macd", view, {"enh20_journal": j}), [])
        self.assertTrue(j and j[0]["enhanced"] == "refuse_xstale_entry")
        out = ev("s_mn_macd", view, off("s_mn_macd"))
        self.assertEqual([o["symbol"] for o in out], ["AAA"])

    def test_vwap(self):
        view = {"bars": {"AAA": bars([100.0] * 25 + [110.0]),
                         "BBB": bars([100.0] * 120)}, "positions": []}
        self.assertEqual(ev("s_mn_vwap", view), [])
        self.assertEqual(len(ev("s_mn_vwap", view, off("s_mn_vwap"))), 1)

    def test_reversal(self):
        def mk(r, n=22):
            return bars([100.0] * 10 + [100 * (1 + r)] * (n - 10))
        view = {"bars": {"AAA": mk(-0.3), "BBB": mk(-0.1),
                         "CCC": bars([100.0] * 80)}, "positions": []}
        on = ev("s_mn_reversal", view)
        self.assertNotIn("AAA", [o["symbol"] for o in on])
        off_out = ev("s_mn_reversal", view, off("s_mn_reversal"))
        self.assertIn("AAA", [o["symbol"] for o in off_out])

    def test_pairs(self):
        base = [50 + 0.05 * i for i in range(70)]
        ko = base[:60] + [x * 1.12 for x in base[60:]]
        view = {"bars": {"KO": bars(ko), "PEP": bars(base),
                         "XOM": bars([80.0] * 90), "CVX": bars([80.0] * 90)},
                "positions": []}
        self.assertEqual(ev("s_mn_pairs", view), [])
        self.assertEqual(len(ev("s_mn_pairs", view, off("s_mn_pairs"))), 2)

    def _chain(self, sym, strike, typ="call", exp="2025-05-20"):
        cp = "C" if typ == "call" else "P"
        occ = f"{sym}250520{cp}{int(strike * 1000):08d}"
        return occ, {"symbol": occ, "strike": strike, "expiration": exp, "type": typ}

    def test_opt_pairs(self):
        base = [50 + 0.05 * i for i in range(70)]
        ko = base[:60] + [x * 1.12 for x in base[60:]]
        occ_c, call = self._chain("PEP", base[-1], "call")
        occ_p, put = self._chain("KO", ko[-1], "put")
        view = {"bars": {"KO": bars(ko), "PEP": bars(base),
                         "XOM": bars([80.0] * 90), "CVX": bars([80.0] * 90)},
                "positions": [],
                "options": {"chains": {"PEP": [call], "KO": [put]},
                            "quotes": {occ_c: {"bid": 1.9, "ask": 2.0},
                                       occ_p: {"bid": 1.9, "ask": 2.0}}}}
        self.assertEqual(ev("s_mn_opt_pairs", view), [])
        self.assertEqual(len(ev("s_mn_opt_pairs", view, off("s_mn_opt_pairs"))), 2)

    def test_opt_reversal(self):
        def mk(r):
            return bars([100.0] * 10 + [100 * (1 + r)] * 12)
        occ, contract = self._chain("AAA", 80)
        view = {"bars": {"AAA": mk(-0.2), "BBB": bars([100.0] * 90)},
                "positions": [],
                "options": {"chains": {"AAA": [contract]},
                            "quotes": {occ: {"bid": 1.9, "ask": 2.0}}}}
        self.assertEqual(ev("s_mn_opt_reversal", view), [])
        self.assertEqual(len(ev("s_mn_opt_reversal", view, off("s_mn_opt_reversal"))), 1)

    def test_opt_turtle(self):
        occ, contract = self._chain("AAA", 60)
        view = {"bars": {"AAA": bars([50.0] * 60 + [60.0]),
                         "BBB": bars([100.0] * 120)}, "positions": [],
                "options": {"chains": {"AAA": [contract]},
                            "quotes": {occ: {"bid": 1.9, "ask": 2.0}}}}
        self.assertEqual(ev("s_mn_opt_turtle", view), [])
        self.assertEqual(len(ev("s_mn_opt_turtle", view, off("s_mn_opt_turtle"))), 1)

    def test_kronos(self):
        series = bars([25.0] * 60)
        barsmap = {s: series for s in ("AAA", "BBB", "CCC", "DDD")}
        barsmap["EEE"] = bars([25.0] * 120)
        fires = [{"sleeve_id": "s_mn_kronos", "symbol": s, "date": "2025-04-09",
                  "rank": i + 1} for i, s in enumerate(("AAA", "BBB", "CCC", "DDD"))]
        view = {"bars": barsmap, "positions": [], "fires": fires}
        self.assertEqual(ev("s_mn_kronos", view), [])
        self.assertEqual(len(ev("s_mn_kronos", view, off("s_mn_kronos"))), 4)

    def test_moonshot(self):
        view = {"bars": {"XYZ": bars([20.0] * 400), "QQQ": bars([20.0] * 430)},
                "positions": [],
                "fires": [{"sleeve_id": "s_mn_moonshot", "symbol": "XYZ",
                           "date": "2025-04-09"}]}
        self.assertEqual(ev("s_mn_moonshot", view), [])
        self.assertEqual(len(ev("s_mn_moonshot", view, off("s_mn_moonshot"))), 1)


def _hourly(day_end, n_days=3, price=50.0):
    out = []
    for k in range(n_days):
        d = day_end - timedelta(days=n_days - 1 - k)
        for h in range(7):
            out.append({"t": f"{d.isoformat()}T{13 + h:02d}:30:00Z",
                        "o": price, "h": price, "l": price, "c": price, "v": 1000})
    return out


class TestNostopXStale(unittest.TestCase):
    def test_stale_hourly_symbol_refused(self):
        j = []
        view = {"now": "2026-10-23T15:30:00-04:00",
                "bars": {"AAA|1Hour": _hourly(date(2026, 10, 21)),
                         "BBB|1Hour": _hourly(date(2026, 10, 23))},
                "positions": [],
                "midna_signals": {"AAA": {"signal": True}, "BBB": {"signal": True}},
                "extra": {"enh20_journal": j}}
        mod = importlib.import_module("laz_sleeves.s_mn_nostop")
        out = mod.evaluate(view, {"sleeve_id": "s_mn_nostop"})
        self.assertEqual([o["symbol"] for o in out], ["BBB"])
        self.assertTrue(j)
        view["extra"] = {"s_mn_nostop_enh20": {"xstale_gate": False}}
        out = mod.evaluate(view, {"sleeve_id": "s_mn_nostop"})
        # AMENDED 2026-11-12 (GATE-CURE-RANDOM-20261112): the base
        # iteration the switch restores is no longer alphabetical:
        # slot allocation is ranked by last-bar freshness under
        # the rule-logic ledger's RANDOM cure, so with the stale
        # gate OFF the freshest signal (BBB) takes the single
        # slot. OFF still removes exactly the ENH20 stale gate and
        # nothing else. Pre-amendment copy preserved in
        # ~/workspace/.gatecure-20261112/pre/tests/.
        self.assertEqual([o["symbol"] for o in out], ["BBB"])


def _daily(closes, end):
    days, d = [], end
    while len(days) < len(closes):
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    return [{"t": x.isoformat(), "o": c, "h": c, "l": c, "c": c, "v": 1000}
            for x, c in zip(days, closes)]


class TestMidnaXStale(unittest.TestCase):
    CTX = {"session": "2026-10-24", "now": "2026-10-24T15:00:00"}

    def _view(self, sid, fam, extra=None):
        stale = _daily([10.0] * 30, date(2026, 9, 30))
        fresh = _daily([10.0] * 30, date(2026, 10, 23))
        fire = {"sleeve_id": sid, "symbol": "AAA", "family": fam,
                "timeframe": "1W", "date": "2026-10-23", "price": 10.0}
        return {"now": "2026-10-24T15:00:00", "midna_fires": [fire],
                "bars": {"AAA": stale, "ZZZ": fresh}, "positions": [],
                "extra": extra or {}}

    def test_hourly_1w(self):
        mod = importlib.import_module("adapters3.s_mn_hourly_1w")
        v = self._view("s_mn_hourly_1w", "cyan")
        self.assertEqual(mod.evaluate(v, dict(self.CTX)), [])
        v["extra"] = {"s_mn_hourly_1w_enh20": {"xstale_gate": False}}
        self.assertEqual(len(mod.evaluate(v, dict(self.CTX))), 1)

    def test_w_cyan_breadth(self):
        mod = importlib.import_module("adapters3.s_mn_w_cyan_breadth")
        v = self._view("s_mn_w_cyan_breadth", "cyan", {"breadth_pct": 0.6})
        self.assertEqual(mod.evaluate(v, dict(self.CTX)), [])
        v["extra"] = {"breadth_pct": 0.6,
                      "s_mn_w_cyan_breadth_enh20": {"xstale_gate": False}}
        self.assertEqual(len(mod.evaluate(v, dict(self.CTX))), 1)


if __name__ == "__main__":
    unittest.main()
