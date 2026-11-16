"""SILENT-SKIP-SIZING-20261116 blockers (Phase B5, desk full audit).

Defect: whole-share floor sizing with a SILENT continue when the
floored quantity is 0. A fired signal on a name priced above its
per-slot budget emitted no intent and no journal line; the fire died
for price, invisibly. Owner price ruling 2026-11-14: a fired signal
must never be unbuyable for price; fractional sizing from the same
dollar budget, rounded down to the door's 6dp precision, where the
path carries fractional quantities; where it cannot (whole-contract
options, the shared batch-7 bridge that also serves the pinned
saty_sol), a named fail-closed journal row (sizing_zero_or_cap,
DMAC shape) instead of silence.

Every test in the Cure classes drives a sizing path with a price
above the budget and asserts the cured behavior; on the pre-cure
tree each returns silence (no intent, no journal row) and FAILS.
The Guard class pins quantity >= 1 behavior unchanged on both trees.
"""
import importlib
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

UTC = timezone.utc


def _b(t, c, v=10000.0):
    return {"t": t, "o": c, "h": c * 1.001, "l": c * 0.999, "c": c, "v": v}


def _daily(closes, end=date(2026, 10, 23)):
    days, d = [], end
    while len(days) < len(closes):
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    return [_b(f"{x.isoformat()}T04:00:00Z", float(c))
            for x, c in zip(days, closes)]


def _hourly(n, price=50.0, end_day=date(2026, 10, 23)):
    out, d, made = [], end_day, 0
    days = []
    while made < (n // 7 + 2):
        if d.weekday() < 5:
            days.append(d)
            made += 1
        d -= timedelta(days=1)
    for day in sorted(days):
        for k in range(7):
            out.append(_b(f"{day.isoformat()}T{13 + k:02d}:30:00Z", price))
    return out[-n:]


# ------------------------------------------------------- laz8 (s_mn_*)
class TestLaz8QtyFor(unittest.TestCase):
    def test_qty_for_fractional_when_price_above_budget(self):
        from sleeves.laz8_common import qty_for
        q = qty_for(1000.0, 1500.0)
        self.assertAlmostEqual(q, 0.666666, places=6)
        self.assertLessEqual(q * 1500.0, 1000.0)

    def test_intent_accepts_fractional_qty_hint(self):
        from sleeves.laz8_common import Intent
        it = Intent(kind="enter", symbol="SPY", qty_hint=0.4, side="buy")
        self.assertEqual(it.qty_hint, 0.4)

    def test_faber_entry_fractional_through_adapter(self):
        # Faber: close above the 210-session average fires; PER_ETF
        # budget is $600, price $1,500 floors to 0 pre-cure.
        from adapters.laz8_common import make_evaluate
        start = datetime(2025, 12, 1, tzinfo=UTC)
        bars = {"SPY": [{"t": (start + timedelta(days=i)).timestamp(),
                         "o": 1000.0 + 2.0 * i, "h": 1000.0 + 2.0 * i,
                         "l": 1000.0 + 2.0 * i, "c": 1000.0 + 2.0 * i,
                         "v": 1e6} for i in range(230)]}
        # last close 1458 < 1500: scale so the last close is 1500
        bars["SPY"][-1].update({"o": 1500.0, "h": 1500.0, "l": 1500.0,
                                "c": 1500.0})
        view = {"bars": bars, "positions": []}
        last_day = start + timedelta(days=229)
        ctx = {"now": last_day.strftime("%Y-%m-%dT15:00:00-04:00"),
               "session": last_day.date().isoformat()}
        out = make_evaluate("s_mn_faber", 3000.0)(view, ctx)
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.4, places=6)


class TestLaz8OptionsJournal(unittest.TestCase):
    """Whole contracts cannot fractionalize: the named journal row
    in extra['sizing_journal'] replaces the silent continue."""

    def _ctx(self, chains, quotes):
        return SimpleNamespace(
            now=0.0, session="2026-10-23", equity=1000.0,
            extra={"chains": chains, "quotes": quotes,
                   "sizing_journal": []})

    def _bars(self, closes):
        start = datetime(2026, 9, 20, tzinfo=UTC)
        return [{"t": (start + timedelta(days=i)).timestamp(),
                 "o": c, "h": c, "l": c, "c": c, "v": 1e6}
                for i, c in enumerate(closes)]

    def test_opt_turtle_zero_contracts_journalled(self):
        from sleeves.s_mn_opt_turtle import signal
        closes = [90.0 + 0.5 * i for i in range(60)]  # breakout (>=56 bars)
        occ = "ACME261120C00100000"
        chains = {"ACME": [{"symbol": occ, "strike": 100.0,
                            "expiration": "2026-11-20", "type": "call"}]}
        quotes = {occ: {"bid": 14.0, "ask": 15.0}}  # 15*100 > $1,000
        ctx = self._ctx(chains, quotes)
        out = signal({"ACME": self._bars(closes)}, {}, ctx)
        self.assertEqual(out, [])
        rows = ctx.extra["sizing_journal"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["sizing_zero_or_cap"])
        self.assertEqual(rows[0]["sleeve"], "s_mn_opt_turtle")
        self.assertEqual(rows[0]["symbol"], occ)
        self.assertEqual(rows[0]["price"], 15.0)
        self.assertEqual(rows[0]["budget"], 1000.0)

    def test_opt_reversal_zero_contracts_journalled(self):
        from sleeves.s_mn_opt_reversal import signal
        closes = [120.0 - 1.0 * i for i in range(22)]  # worst performer
        occ = "ACME261120C00100000"
        chains = {"ACME": [{"symbol": occ, "strike": 100.0,
                            "expiration": "2026-11-20", "type": "call"}]}
        quotes = {occ: {"bid": 14.0, "ask": 15.0}}
        ctx = self._ctx(chains, quotes)
        out = signal({"ACME": self._bars(closes)}, {}, ctx)
        self.assertEqual(out, [])
        rows = ctx.extra["sizing_journal"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["sizing_zero_or_cap"])
        self.assertEqual(rows[0]["sleeve"], "s_mn_opt_reversal")

    def test_opt_pairs_zero_contracts_journalled(self):
        from sleeves.s_mn_opt_pairs import signal
        # Registered pair (KO, PEP): KO jumps, spread z = 3.32 >= 2,
        # so KO is rich (put leg) and PEP is cheap (call leg).
        rich = [100.0] * 65 + [130.0] * 5
        cheap = [100.0] * 70
        bars = {"KO": self._bars(rich), "PEP": self._bars(cheap)}
        occ_c = "PEP261120C00100000"
        occ_p = "KO261120P00130000"
        chains = {"PEP": [{"symbol": occ_c, "strike": 100.0,
                           "expiration": "2026-11-20", "type": "call"}],
                  "KO": [{"symbol": occ_p, "strike": 130.0,
                           "expiration": "2026-11-20", "type": "put"}]}
        # PER_LEG $500: ask 6.00 -> 6*100=600 > 500 -> 0 contracts
        quotes = {occ_c: {"bid": 5.5, "ask": 6.0},
                  occ_p: {"bid": 5.5, "ask": 6.0}}
        ctx = self._ctx(chains, quotes)
        out = signal(bars, {}, ctx)
        self.assertEqual(out, [])
        rows = ctx.extra["sizing_journal"]
        self.assertTrue(any(r["sizing_zero_or_cap"] for r in rows))


# ------------------------------------------------- laz_sleeves/_common
class TestLazCommon(unittest.TestCase):
    NOW = "2026-10-23T15:30:00-04:00"

    def _view(self, **kw):
        v = {"now": self.NOW, "bars": {}, "positions": [],
             "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        v.update(kw)
        return v

    def test_qty_for_fractional(self):
        from laz_sleeves._common import _qty_for
        self.assertAlmostEqual(_qty_for(1000.0, 1500.0), 0.666666,
                               places=6)

    def test_mn_hourly_entry_fractional(self):
        mod = importlib.import_module("laz_sleeves.s_mn_hourly")
        v = self._view(bars={"ACME|1Hour": _hourly(70, 1500.0)},
                       midna_signals={"ACME": {"signal": True}})
        out = mod.evaluate(v, {"sleeve_id": "s_mn_hourly",
                               "state_dir": "/tmp"})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.666666, places=6)

    def test_q07_entry_fractional(self):
        closes = [1300.0 + 1.5 * i for i in range(140)]  # mom6 > 0
        bars = [{"t": (date(2026, 10, 23) - timedelta(
            days=len(closes) - 1 - i)).isoformat(),
            "o": c, "h": c, "l": c, "c": c, "v": 1000}
            for i, c in enumerate(closes)]
        qqq = [{"t": "2026-10-22", "o": 500.0, "h": 500.0, "l": 500.0,
                "c": 500.0, "v": 1},
               {"t": "2026-10-23", "o": 490.0, "h": 490.0, "l": 490.0,
                "c": 490.0, "v": 1}]
        view = {"now": "2026-10-23T15:55:00+00:00",
                "bars": {"ACME|1Day": bars, "QQQ|1Day": qqq},
                "positions": [],
                "tensor_fires": [{"symbol": "ACME",
                                  "date": "2026-10-22", "confidence": 5}],
                "alt_data": {"ACME": {"mcap_band": "midlarge"}},
                "fires": [{"symbol": "ACME",
                           "tags": {"insider_buys": 3, "wiki_low": True}}],
                "vix": 25.0}
        sid = "s_q07w_s52_ml_ins2_mom6_wlow"
        mod = importlib.import_module(f"laz_sleeves.{sid}")
        out = mod.evaluate(view, {"sleeve_id": sid})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 1000.0 / closes[-1],
                               places=4)
        self.assertLess(entries[0]["qty"], 1)


# ---------------------------------------------------- desk3 engines
class TestLazarusMidna(unittest.TestCase):
    def test_entry_fractional_when_price_above_budget(self):
        from desk3 import lazarus_midna
        from desk3.tensor_native import apply_native_to_fire
        fire = {"symbol": "NBIS", "decision": "TRADE", "confidence": 8,
                "phenotype": "TRANSITION", "regime": "bullish",
                "bar_date": "2026-11-13", "t": 1794601800,
                "entry": 1500.0, "stop": 1490.0, "target": 1600.0,
                "price": 1500.0, "date": "2026-11-13"}
        rec = {"features": {}, "signal_end": "2026-11-13",
               "rep_g": {"last": {"primaryMarkers": ["buy-cyan"]}}}
        fire = apply_native_to_fire(fire, rec)
        bars = {"NBIS|1Day": [{"t": f"2026-11-{d:02d}T05:00:00Z",
                               "o": 1500.0, "h": 1500.0, "l": 1500.0,
                               "c": 1500.0, "v": 1000}
                              for d in range(1, 26)],
                "SMH|1Day": [{"t": f"2026-11-{d:02d}T05:00:00Z",
                              "o": 300.0, "h": 300.0, "l": 300.0,
                              "c": 300.0, "v": 1000} for d in range(1, 26)]}
        view = {"tensor": {"fires": [fire]}, "bars": bars,
                "positions": [], "extra": {"breadth_pct": 0.60}}
        ctx = {"session": "2026-11-13",
               "now": datetime(2026, 11, 13, 15, 0, tzinfo=UTC)}
        out = lazarus_midna.evaluate("s_mn_w_cyan_breadth", view, ctx)
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.666666, places=6)


class TestLazarus(unittest.TestCase):
    def test_entry_fractional_when_price_above_per_slot(self):
        from desk3.lazarus import evaluate
        now = datetime(2026, 10, 26, 14, 0, tzinfo=UTC)
        base = datetime(2026, 10, 20, tzinfo=UTC)
        iso = lambda d: d.isoformat().replace("+00:00", "Z")
        bars = [{"t": iso(base + timedelta(days=i)), "o": 2000.0,
                 "h": 2020.0, "l": 1980.0, "c": 2000.0, "v": 1e6}
                for i in range(10)]
        bars[-1]["c"] = 1999.9  # red last bar (both_red gate)
        fire = {"sleeve_id": "1d", "symbol": "ACME",
                "fired_at": iso(now - timedelta(hours=47)),
                "price": 2000.0, "qqq_red": True, "stock_red": True}
        view = {"now": iso(now), "lazarus_fires": [fire],
                "bars": {"ACME|1Day": bars}, "positions": []}
        out = evaluate("1d", view, {"state_dir": tempfile.mkdtemp()})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        # per_slot = 51750/30 = 1725; 1725/1999.9 floors to 0 pre-cure
        self.assertAlmostEqual(entries[0]["qty"], 1725.0 / 1999.9,
                               places=4)
        self.assertLess(entries[0]["qty"], 1)


class TestLazarusQ07(unittest.TestCase):
    def test_entry_fractional_when_price_above_slot_budget(self):
        from desk3.lazarus_q07 import evaluate_sleeve
        sid = "s_q07w_s52_ml_deep70_wlow"  # budget 1000, slots 1
        days = [date(2026, 10, 23) - timedelta(days=i)
                for i in range(29, -1, -1)]
        bars = [{"date": d.isoformat(), "c": 2000.0} for d in days]
        fire = {"symbol": "TEST", "family": "swing", "band": "midlarge",
                "signal_date": "2026-10-23", "price": 2000.0,
                "tags": {"deep70": True, "wiki_low": True}}
        v = {"bars": {"QQQ": [{"date": "2026-10-22", "c": 101.0},
                              {"date": "2026-10-23", "c": 100.0}],
                      "TEST": bars},
             "positions": [], "fires": [fire],
             "extra": {"q07_exp_journal": {"records": []}}}
        out = evaluate_sleeve(sid, v, {"session": "2026-10-23",
                                       "now": "2026-10-23"})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.5, places=6)


class TestQ07Engine(unittest.TestCase):
    SID = "s_q07w_g52_ml_ins2_wlow"  # SLOT_USD 1000

    def test_entry_fractional_when_price_above_slot(self):
        mod = importlib.import_module(f"adapters3.{self.SID}")

        def series(n, close, last_down=False):
            rows = []
            d = date(2026, 10, 23) - timedelta(days=n - 1)
            for i in range(n):
                rows.append({"t": (d + timedelta(days=i)).isoformat(),
                             "o": close, "h": close, "l": close,
                             "c": close, "v": 1000})
            if last_down:
                rows[-1]["c"] = close - 10.0
            return rows

        fire = {"sleeve": self.SID, "symbol": "ABC",
                "signal_date": "2026-10-21", "insider_buys": 3,
                "wiki_views_30d": 100, "cap_band": "midlarge",
                "band": "midlarge"}
        view = {"now": "2026-10-23T15:55:00+00:00",
                "bars": {"QQQ|1day": series(300, 500.0, last_down=True),
                         "ABC|1day": series(300, 1500.0)},
                "positions": [], "extra": {"sleeve_fires": [fire]}}
        out = mod.evaluate(view, {})
        entries = [i for i in out if i.kind == "enter"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0].qty, 0.666666, places=6)


# --------------------------------------------------------- free_etf
class TestFreeEtf(unittest.TestCase):
    def _drive(self, ask):
        mod = importlib.import_module("adapters3.free_etf")
        now = "2026-10-14T09:37:00-04:00"
        hist = [{"session": f"2025-{(i % 12) + 1:02d}-01",
                 "close": 100.0 + i * 0.1} for i in range(252)]
        extra = {"etf_books": [{"id": "B1",
                                "fixed_weights": {"SPY": 0.5}}],
                 "etf_receipt": {"histories": {"SPY": hist},
                                 "source_receipts_verified": True,
                                 "feed": "sip", "adjustment": "all",
                                 "signal_session": "2026-10-13"},
                 "quotes": {"SPY": {"t": now, "received_at": now,
                                    "bp": ask - 0.1, "ap": ask}},
                 "held_rows": {}}
        view = {"now": now, "bars": {}, "positions": [],
                "slice": {"capital_usd": 100000.0, "cash_usd": 100000.0},
                "params": {"extra": extra}, "session_fills": []}
        ctx = {"state_dir": tempfile.mkdtemp(), "sleeve_id": "free_etf",
               "cycle_id": "fixture"}
        return mod.evaluate(view, ctx)

    def test_entry_fractional_when_target_floors_to_zero(self):
        # slice $10,000 x weight 0.5 = $5,000 target; ask $20,000
        out = self._drive(20000.0)
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.25, places=6)


# ------------------------------------------------------------- aster
class TestAsterBatch13(unittest.TestCase):
    CTX = {"session": "2026-10-24", "now": "2026-10-24T15:00:00"}

    def test_c1_entry_fractional_when_price_above_ticket(self):
        sid = "aster_tensor_c1_cash_all_25"  # ticket $400
        mod = importlib.import_module(f"adapters3.{sid}")
        fire = {"sleeve_id": sid, "symbol": "AAA", "signal": "buy-cyan",
                "date": "2026-10-23", "price": 500.0, "ret60": 40,
                "vol20": 0.1, "adv_usd": 3000000, "atr_ratio": 0.5}
        view = {"now": self.CTX["now"], "tensor": {"fires": [fire]},
                "bars": {}, "positions": [], "extra": {}}
        out = mod.evaluate(view, dict(self.CTX))
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.8, places=6)


class TestAsterBatch14(unittest.TestCase):
    CTX = {"session": "2026-10-23", "now": "2026-10-23T15:00:00"}

    def test_c1_hot_reserve_entry_fractional_above_ticket(self):
        sid = "aster_tensor_c1_reserve_hot_25"  # ticket $400, cap removed
        mod = importlib.import_module(f"adapters3.{sid}")
        fire = {"symbol": "ABC", "signal": "buy-green", "price": 500.0,
                "depth60": 80.0, "ret60": 40.0, "vol20": 0.12,
                "adv_usd": 3000000, "atr_ratio": 1.5,
                "date": "2026-10-22"}
        view = {"tensor": [fire], "bars": {}, "positions": []}
        out = mod.evaluate(view, dict(self.CTX))
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertAlmostEqual(entries[0]["qty"], 0.8, places=6)


class TestAsterBatch15(unittest.TestCase):
    def test_g4_weekly_entry_fractional_above_ticket(self):
        # Pending G4 fire (native close $5 passes intake); the entry
        # session's last close is $500 against the $400 ticket.
        import importlib as _il
        from datetime import time as _time
        ET = __import__("zoneinfo").ZoneInfo("America/New_York")

        def weekdays(start, n):
            out, d = [], start
            while len(out) < n:
                if d.weekday() < 5:
                    out.append(d)
                d += timedelta(days=1)
            return out

        sessions = weekdays(date(2025, 1, 6), 640)
        strs = [d.isoformat() for d in sessions]
        sid = "aster_r19_tensor_g4_hot_delay_25"
        mod = _il.import_module(f"adapters3.{sid}")
        sd = tempfile.mkdtemp()

        def at(d, hh=9, mm=30):
            return datetime.combine(d, _time(hh, mm), ET).astimezone(UTC)

        fire = {"symbol": "AAA", "issuer_id": "iss-AAA",
                "signal_end": "2025-02-14", "markers": ["buy-green"],
                "native_close": 5.0, "depth60": 80.0, "ret60": 5.0,
                "vol20": 0.12, "dv20": 5e6, "atr_ratio": 1.5}
        bars = {"AAA|1Day": [{"t": "2025-02-17", "o": 500.0, "h": 500.0,
                             "l": 500.0, "c": 500.0, "v": 1e6}]}

        def view(now):
            return {"now": now.isoformat(), "tensor_fires": [fire],
                    "positions": [], "bars": bars,
                    "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                    "quotes": {}, "extra": {"session_dates": strs}}

        ctx = {"sleeve_id": sid, "cycle_id": "fx", "state_dir": sd}
        mod.evaluate(view(at(sessions[25])), dict(ctx))
        follow = [d for d in strs if d > "2025-02-14"]
        entry_day = date.fromisoformat(follow[1])
        out = mod.evaluate(view(at(entry_day)), dict(ctx))
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertLess(entries[0]["qty"], 1)
        # fee tier at $500 is 10bp: floor6(400 / (500 * 1.001))
        self.assertAlmostEqual(entries[0]["qty"], 0.7992, places=4)

    def test_timing_hourly_entry_fractional_above_budget(self):
        sid = "aster_r19_timing_hour_floor0_delay0"
        mod = importlib.import_module(f"adapters3.{sid}")
        now_h = datetime(2026, 10, 23, 15, 0, tzinfo=UTC)
        bars = []
        for i in range(61):
            t = now_h - timedelta(hours=61 - i)
            bars.append({"t": t.isoformat(),
                         "end": (t + timedelta(hours=1)).isoformat(),
                         "o": 2000.0, "h": 2001.0, "l": 1999.0,
                         "c": 2000.0, "v": 1000})
        sw = {"swing": {"confirmed": True, "score": 9,
                        "invalidation": 1999.0, "target": 2200.0,
                        "phenotype": "BULL", "usesFutureData": False,
                        "bearishConflict": False}}
        view = {"now": now_h.isoformat(), "bars": {"MU|1Hour": bars},
                "timing_signals": {"MU": sw},
                "quotes": {"MU": {"bid": 1999.9, "ask": 2000.0}},
                "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "extra": {}}
        out = mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx",
                                  "state_dir": tempfile.mkdtemp()})
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertLess(entries[0]["qty"], 1)
        self.assertGreater(entries[0]["qty"], 0)


class TestAsterBatch16D20(unittest.TestCase):
    def test_d20_entry_fractional_when_price_above_cap(self):
        import json, math
        b16 = importlib.import_module("desk3.aster_batch16")
        assets = os.path.join(ROOT, "desk3", "aster_d20_assets")
        anchors = json.load(open(os.path.join(
            assets, "DAILY_SOURCE_ANCHORS.json")))["symbols"]
        recipe = dict(ret20=-0.0004355548709383747,
                      ret60=0.6079143587172864,
                      atr_pct=0.047010904409629364, rvol=1.901925765372908,
                      logdv=16.300964163076298,
                      emadist=1.0704537780305432)
        close = 2000.0  # cap is min(0.1*10000, 1% DV, cash) = $1,000
        a = anchors["ADSK"]
        t0 = a["first_timestamp"]
        atr14 = recipe["atr_pct"] * close
        rows = []
        for i in range(240):
            ts = t0 + i * 86400
            rows.append({"symbol": "ADSK", "bar_index": i,
                         "timestamp": ts, "completed_at": ts + 3600,
                         "usable_at": ts + 3600,
                         "source_origin_timestamp": t0,
                         "native_status": "ready", "open": close,
                         "close": close, "volume": 100000.0,
                         "atr14": atr14, "return20": recipe["ret20"],
                         "return60": recipe["ret60"], "rvol": recipe["rvol"],
                         "dollar_volume20": math.expm1(recipe["logdv"]),
                         "ema21": close - recipe["emadist"] * atr14,
                         "bullish_votes": 3.0, "bearish_votes": 3.0,
                         "ribbon_inversion_count": 8.0,
                         "ribbon_width": 0.05, "ribbon_slope": 0.0004,
                         "obv_slope5": 3000.0, "squeeze_on": 1.0,
                         "squeeze_momentum": 0.005 * atr14,
                         "squeeze_length": 14.0, "ut_regime": "bullish",
                         "mcdx_position": 56.0,
                         "mcdx_position_delta3": 0.18,
                         "macd_histogram": 0.008 * atr14,
                         "efficiency10": 0.29,
                         "normalized_sign_entropy20": 0.62,
                         "prior_sell_avwap": close - 0.5 * atr14,
                         "prior_sell_completed_at": ts - 3600,
                         "overhead60_atr": 1.2, "vote_stoch": 0.0,
                         "vote_aroon": 1.0, "vote_di": 1.0,
                         "vote_obv": 1.0, "vote_squeeze": -1.0,
                         "vote_pivot": 1.0, "vote_wave": 1.0})
        view = {"now": "2026-10-23T15:00:00-04:00",
                "tensor_daily20": {"ADSK": rows}, "bars": {},
                "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        for sid in ("aster_tensor_d20_pv", "aster_tensor_d20_tensor"):
            mod = importlib.import_module(f"adapters3.{sid}")
            out = mod.evaluate(view, {})
            entries = [i for i in out if i["kind"] == "entry"]
            self.assertEqual(len(entries), 1, sid)
            self.assertAlmostEqual(entries[0]["qty"], 0.5, places=6,
                                   msg=sid)


# ---------------------------------------------------- tensor_red_dip
class TestTensorRedDip(unittest.TestCase):
    def test_sized_zero_named_in_stamp_not_silent(self):
        # The sleeve's path to the door rides the shared batch-7
        # bridge (int(round(qty))), which also serves the pinned
        # saty_sol, so fractional quantities cannot be carried; the
        # cure is the named fail-closed row in the evaluation stamp
        # (dispatch merges last_evaluation into the evaluation row).
        from sleeves.tensor_red_dip import TensorRedDip
        sleeve = TensorRedDip()
        bars = {"ACME": [{"t": f"2026-10-{d:02d}", "o": 400.0,
                          "h": 400.0, "l": 400.0, "c": 400.0, "v": 1e6}
                         for d in range(19, 24)]}
        ctx = SimpleNamespace(
            now=0.0, session="2026-10-23", equity=10000.0,
            extra={"tensor_signals": [{"symbol": "ACME",
                                       "decision": "TRADE",
                                       "confidence": 8,
                                       "phenotype": "RECLAIM"}],
                   "qqq_day_return": -0.02,
                   "day_returns": {"ACME": -0.03},
                   "nyse_holidays": [], "sleeve_state": {}})
        out = sleeve.signal(bars, {}, ctx)
        self.assertEqual([i for i in out if i.kind == "enter"], [])
        stamp = sleeve.last_evaluation
        self.assertEqual(stamp["skip_counts"].get("sized_zero"), 1)
        rows = stamp.get("sizing_zero_or_cap") or []
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sleeve"], "tensor_red_dip")
        self.assertEqual(rows[0]["symbol"], "ACME")
        self.assertEqual(rows[0]["price"], 400.0)


# ------------------------------------------------------------ guards
class TestWholeQtyUnchanged(unittest.TestCase):
    def test_qty_for_whole_stays_int(self):
        from sleeves.laz8_common import qty_for
        from laz_sleeves._common import _qty_for
        self.assertEqual(qty_for(1000.0, 40.0), 25)
        self.assertIsInstance(qty_for(1000.0, 40.0), int)
        self.assertEqual(_qty_for(1000.0, 40.0), 25)
        self.assertIsInstance(_qty_for(1000.0, 40.0), int)

    def test_qty_for_zero_budget_and_bad_price_stay_zero(self):
        from sleeves.laz8_common import qty_for
        from laz_sleeves._common import _qty_for
        self.assertEqual(qty_for(0.0, 100.0), 0)
        self.assertEqual(qty_for(1000.0, 0.0), 0)
        self.assertEqual(_qty_for(1000.0, 0.0), 0)
        self.assertEqual(_qty_for(0.0, 100.0), 0)

    def test_contracts_for_stays_whole(self):
        from sleeves.laz8_opt import contracts_for
        self.assertEqual(contracts_for(1000.0, 5.0), 2)
        self.assertEqual(contracts_for(1000.0, 15.0), 0)

    def test_red_dip_size_qty_verbatim(self):
        from sleeves.tensor_red_dip import size_qty
        self.assertEqual(size_qty(10000.0, 100.0), 3)
        self.assertEqual(size_qty(10000.0, 400.0), 0)


if __name__ == "__main__":
    unittest.main()
