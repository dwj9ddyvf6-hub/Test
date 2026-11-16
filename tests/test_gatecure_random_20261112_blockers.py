"""Blockers: GATE-CURE-RANDOM-20261112 — slot allocation by
alphabet is replaced with deterministic ranking by the sleeve's
own signal strength (RULE-LOGIC-LEDGER-2026-11-12 Section 3,
RANDOM register; composition note: "where a slot cap binds,
selection must rank by the sleeve's own signal strength instead
of symbol order").

Sites and rankings (each stated in BUGLOG_2026-11-12.md):
- laz_sleeves/_common.py q07_evaluate (sorted(fires)): the Tensor
  fire's own confidence, descending; where a fire carries no
  numeric confidence, the fire's own date, freshest first; then
  symbol. (Brief fallback: timestamp then symbol.)
- laz_sleeves/_common.py mn_hourly_evaluate (sorted(signals)):
  the hourly signal carries neither strength nor a timestamp
  (the sleeve's own ENH20 note), so ranking is by the symbol's
  last 1Hour bar timestamp — the sleeve's own staleness measure,
  already computed for ENH20 — freshest first, then symbol.
- laz_sleeves/s_cl_qm_small.py (sorted(bars_map)): breakout
  strength = close / prior-20-session high, descending, then
  symbol.
- sleeves/s_mn_vwap.py (sorted(bars), first up-cross): cross
  strength = close / rolling VWAP20 − 1 on the cross bar,
  descending, then symbol.
- sleeves/s_mn_opt_turtle.py (sorted(bars), first breakout):
  breakout strength = close / prior-20-close high − 1,
  descending, then symbol.

Every fixture below makes alphabetical order and ranked order
disagree; fail direction proven on the pre-cure tree (each
"ranked winner" assertion fails pre-cure because the
alphabetically first candidate takes the slot). Pre-cure copies
preserved under ~/workspace/.gatecure-20261112/pre/.
"""
import os, sys, unittest
from datetime import date, timedelta
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = "2026-10-23T15:30:00-04:00"
SESS = date(2026, 10, 23)


def _b(t, c, v=10000.0, h=None, l=None):
    return {"t": t, "o": c, "h": h if h is not None else c * 1.001,
            "l": l if l is not None else c * 0.999, "c": c, "v": v}


def _daily(closes, end=SESS):
    days, d = [], end
    while len(days) < len(closes):
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return [_b(f"{x.isoformat()}T04:00:00Z", float(c))
            for x, c in zip(reversed(days), closes)]


# ------------------------------------------------------------- Q07
class TestQ07Ranking(unittest.TestCase):
    def _view(self, fires):
        bars = {"QQQ|1Day": _daily([500.0, 499.0])}
        alt = {}
        for sym in fires:
            bars[f"{sym}|1Day"] = _daily([50.0] * 30)
            alt[sym] = {"mcap_band": "midlarge"}
        return {"now": NOW, "bars": bars, "positions": [],
                "tensor_fires": fires, "alt_data": alt,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}

    def _enter(self, fires):
        from laz_sleeves._common import q07_evaluate
        out = q07_evaluate(self._view(fires), {}, "s_q07w_test",
                           band="midlarge", horizon_weeks=52,
                           filters=(), slots=1)
        return [o["symbol"] for o in out if o["kind"] == "entry"]

    def test_confidence_outranks_alphabet_and_freshness(self):
        fires = {"AAA": {"family": "swing", "date": "2026-10-22",
                         "confidence": 3},
                 "ZZZ": {"family": "swing", "date": "2026-10-20",
                         "confidence": 9}}
        self.assertEqual(self._enter(fires), ["ZZZ"])

    def test_timestamp_fallback_when_no_confidence(self):
        fires = {"AAA": {"family": "swing", "date": "2026-10-19"},
                 "ZZZ": {"family": "swing", "date": "2026-10-22"}}
        self.assertEqual(self._enter(fires), ["ZZZ"])

    def test_symbol_tiebreak_is_deterministic(self):
        fires = {"ZZZ": {"family": "swing", "date": "2026-10-22",
                         "confidence": 5},
                 "AAA": {"family": "swing", "date": "2026-10-22",
                         "confidence": 5}}
        self.assertEqual(self._enter(fires), ["AAA"])


# --------------------------------------------------------- mn hourly
class TestMnHourlyRanking(unittest.TestCase):
    def _hourly(self, last_iso, n=10, price=50.0):
        base = date(2026, 10, 23)
        out = []
        hh, mm = int(last_iso[11:13]), int(last_iso[14:16])
        for i in range(n):
            h = hh - (n - 1 - i)
            out.append(_b(f"{base.isoformat()}T{h:02d}:{mm:02d}:00Z",
                          price))
        return out

    def test_freshest_feed_wins_the_slot(self):
        from laz_sleeves._common import mn_hourly_evaluate
        view = {"now": NOW, "positions": [],
                "midna_signals": {"AAA": {"signal": True},
                                  "ZZZ": {"signal": True}},
                "bars": {"AAA|1Hour": self._hourly("2026-10-23T17:30:00"),
                         "ZZZ|1Hour": self._hourly("2026-10-23T19:30:00")},
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        out = mn_hourly_evaluate(view, {}, "s_mn_test", stop=True,
                                 slots=1)
        entries = [o["symbol"] for o in out if o["kind"] == "entry"]
        self.assertEqual(entries, ["ZZZ"])


# ------------------------------------------------------- cl_qm_small
class TestClQmSmallRanking(unittest.TestCase):
    def _bars(self, last):
        rows = []
        for i in range(24):
            rows.append({"t": f"2026-09-{i + 1:02d}T04:00:00Z",
                         "o": 10.0, "h": 10.0, "l": 9.9, "c": 10.0,
                         "v": 10000.0})
        rows.append({"t": "2026-10-23T04:00:00Z", "o": 10.0,
                     "h": last, "l": 9.9, "c": last, "v": 10000.0})
        return rows

    def test_weakest_breakout_loses_the_last_slot(self):
        import importlib
        mod = importlib.import_module("laz_sleeves.s_cl_qm_small")
        lasts = {"AAA": 10.10, "BBB": 10.50, "CCC": 10.60,
                 "DDD": 10.70, "EEE": 10.80, "FFF": 10.90,
                 "GGG": 11.00, "HHH": 11.10, "ZZZ": 12.00}
        bars = {"QQQ|1Day": _daily([500.0, 499.0])}
        alt = {}
        for sym, last in lasts.items():
            bars[f"{sym}|1Day"] = self._bars(last)
            alt[sym] = {"mcap_band": "small"}
        view = {"now": NOW, "bars": bars, "positions": [],
                "alt_data": alt,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        out = mod.evaluate(view, {"sleeve_id": "s_cl_qm_small"})
        entries = sorted(o["symbol"] for o in out
                         if o["kind"] == "entry")
        self.assertEqual(len(entries), 8)
        self.assertIn("ZZZ", entries)       # strongest breakout
        self.assertNotIn("AAA", entries)    # weakest loses the slot


# ---------------------------------------------------------- mn vwap
def _flat_bars(closes, vol=100.0):
    return [{"t": 1700000000.0 + i * 86400, "o": c, "h": c, "l": c,
             "c": c, "v": vol} for i, c in enumerate(closes)]


class TestMnVwapRanking(unittest.TestCase):
    def test_strongest_cross_wins_the_slot(self):
        from sleeves.s_mn_vwap import signal
        bars = {"AAA": _flat_bars([10.0] * 24 + [10.10]),
                "ZZZ": _flat_bars([10.0] * 24 + [11.00])}
        ctx = SimpleNamespace(extra={}, session="2026-10-23")
        out = signal(bars, {}, ctx)
        entries = [o for o in out if o.kind == "enter"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].symbol, "ZZZ")


# ------------------------------------------------------- opt turtle
class TestOptTurtleRanking(unittest.TestCase):
    def _setup(self):
        def bars(closes):
            return [{"t": 1700000000.0 + i * 86400, "o": c, "h": c,
                     "l": c, "c": c, "v": 10000.0}
                    for i, c in enumerate(closes)]

        def chain(sym, strike):
            occ = f"{sym}261207C{int(strike * 1000):08d}"
            return occ, {"symbol": occ, "strike": strike,
                         "expiration": "2026-12-07", "type": "call"}

        bars_map, chains, quotes = {}, {}, {}
        for sym, jump in (("AAA", 51.0), ("ZZZ", 60.0)):
            bars_map[sym] = bars([50.0] * 60 + [jump])
            occ, contract = chain(sym, jump)
            chains[sym] = [contract]
            quotes[occ] = {"bid": 1.9, "ask": 2.0}
        ctx = SimpleNamespace(
            extra={"chains": chains, "quotes": quotes},
            session="2026-10-23")
        return bars_map, ctx

    def test_strongest_breakout_wins_the_slot(self):
        from sleeves.s_mn_opt_turtle import signal
        bars_map, ctx = self._setup()
        out = signal(bars_map, {}, ctx)
        entries = [o for o in out if o.kind == "enter"]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].symbol.startswith("ZZZ"),
                        entries[0].symbol)


if __name__ == "__main__":
    unittest.main()
