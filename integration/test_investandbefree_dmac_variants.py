"""investandbefree_dmac variant-family blockers
(INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29, FROZEN).

Edge UNPROVEN for every variant; no backtest is claimed — these
tests pin the frozen variant axes. Golden expectations are
independent: hand arithmetic, an in-test MACD implementation
(written from the definitions), and fixture geometry stated in
each test. The sleeves' own functions never generate an
expectation (they only receive fixture inputs).

Base identity: the base sleeve's golden entry (crossover fixture
from the base blocker file: ATM 2026-11-28 call, strike 239,
qty 4 = floor(2000/500)) must be reproduced byte-identically
after the parameterization refactor.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
SESSION = "2026-10-29"
EQUITY = 10000.0
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=ET)

VARIANTS = ("investandbefree_dmac_intraday",
            "investandbefree_dmac_dailyonly",
            "investandbefree_dmac_deep",
            "investandbefree_dmac_premacd")


def ind_smooth(values, period, wilder):
    alpha = 1.0 / period if wilder else 2.0 / (period + 1)
    out = [None] * len(values)
    if len(values) < period:
        return out
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = prev + alpha * (values[i] - prev)
        out[i] = prev
    return out


def ind_macd(closes, wilder):
    fast = ind_smooth(closes, 12, wilder)
    slow = ind_smooth(closes, 26, wilder)
    mac = [None if f is None or s is None else f - s
           for f, s in zip(fast, slow)]
    defined = [v for v in mac if v is not None]
    sig_def = ind_smooth(defined, 9, wilder)
    sig = [None] * len(closes)
    j = 0
    for i, v in enumerate(mac):
        if v is not None:
            sig[i] = sig_def[j]
            j += 1
    return mac, sig


def bull_closes(n=60):
    return [50 + 0.05 * i * i for i in range(n)]


def bear_closes(n=60):
    return [300 - 0.05 * i * i for i in range(n)]


def crossover_closes():
    c = bull_closes()
    last = c[-1]
    for _ in range(3):
        last -= 5
        c.append(last)
    c.append(last + 30)
    return c


def _bars(closes):
    end = datetime(2026, 10, 29, 0, 0, tzinfo=ET).timestamp()
    out = []
    n = len(closes)
    for i, c in enumerate(closes):
        t = end - (n - i) * 86400
        out.append({"t": t, "o": float(c), "h": float(c), "l": float(c),
                    "c": float(c), "v": 1000.0})
    return out


def _ctx(extra, now_dt=NOW, session=SESSION):
    from core.sleeve import Context
    return Context(now=now_dt.timestamp(), session=session,
                   equity=EQUITY, extra=extra)


OCC_CALL = "SPY261128C00239000"
OCC_PUT = "SPY261128P00239000"


def chain_quotes(spot_ask=5.0, spot_bid=4.9):
    chain = [
        {"symbol": "SPY261110C00239000", "strike": 239.0,
         "expiry": "2026-11-10", "right": "call"},
        {"symbol": OCC_CALL, "strike": 239.0,
         "expiry": "2026-11-28", "right": "call"},
        {"symbol": "SPY261128C00245000", "strike": 245.0,
         "expiry": "2026-11-28", "right": "call"},
        {"symbol": "SPY261219C00239000", "strike": 239.0,
         "expiry": "2026-12-19", "right": "call"},
        {"symbol": OCC_PUT, "strike": 239.0,
         "expiry": "2026-11-28", "right": "put"},
    ]
    quotes = {c["symbol"]: {"bid": spot_bid, "ask": spot_ask} for c in chain}
    return chain, quotes


def hourly_bars(closes_per_day_fn, days=40):
    """7 RTH hourly bars/day over `days` weekdays from 2026-09-01;
    closes drawn sequentially from closes_per_day_fn(i)."""
    out = []
    d = datetime(2026, 9, 1, tzinfo=ET)
    made = 0
    i = 0
    while made < days:
        if d.weekday() < 5:
            for h in range(7):
                t = datetime(d.year, d.month, d.day, 9, 30,
                             tzinfo=ET).timestamp() + h * 3600
                c = closes_per_day_fn(i)
                i += 1
                out.append({"t": t, "o": float(c), "h": float(c),
                            "l": float(c), "c": float(c), "v": 10.0})
            made += 1
        d += timedelta(days=1)
    return out


class TestBaseIdentityAndParams(unittest.TestCase):
    def test_base_golden_entry_unchanged_after_refactor(self):
        from sleeves.investandbefree_dmac import InvestAndBeFreeDmacSleeve
        chain, quotes = chain_quotes()
        sleeve = InvestAndBeFreeDmacSleeve()
        extra = {"bars_weekly": {"SPY": _bars(bull_closes())},
                 "bars_1h": {}, "chains": {"SPY": chain},
                 "quotes": quotes, "sleeve_state": {}, "dmac_state": {}}
        intents = sleeve.signal({"SPY": _bars(crossover_closes())}, {},
                                _ctx(extra))
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].qty, 4)  # floor(2000/(5.0*100))
        self.assertIn("occ=%s" % OCC_CALL, intents[0].reason)
        self.assertIn("strike=239.00", intents[0].reason)
        self.assertIn("expiry=2026-11-28", intents[0].reason)
        self.assertIn("trigger=crossover", intents[0].reason)
        self.assertTrue(intents[0].reason.startswith(
            "investandbefree_dmac long_call SPY:"))

    def test_each_variant_differs_in_exactly_its_axis(self):
        from sleeves.investandbefree_dmac import PRIMARY_PARAMS
        import dataclasses
        expected = {
            "investandbefree_dmac_intraday":
                {"stack_order", "entry_tf", "min_dte", "flat_by_close"},
            "investandbefree_dmac_dailyonly": {"stack_order"},
            "investandbefree_dmac_deep": {"min_dte", "strike_mode"},
            "investandbefree_dmac_premacd": {"premium_macd"},
        }
        for sid, fields in expected.items():
            mod = importlib.import_module("sleeves." + sid)
            cls = mod.InvestAndBeFreeDmacSleeve
            diff = {f.name for f in dataclasses.fields(PRIMARY_PARAMS)
                    if getattr(cls.PARAMS, f.name)
                    != getattr(PRIMARY_PARAMS, f.name)}
            self.assertEqual(diff, fields, sid)
            self.assertEqual(cls.CONFIG.sleeve_id, sid)


# ------------------------------------------------------------ intraday
def intraday_fixture():
    """60 weekdays from Mon 2026-08-03; the final day is shortened
    to 10 30-minute buckets (ends 14:30 ET) whose last four buckets
    carry the crossover pattern (dips of 0.4 x3, then +3.0) on a
    rising quadratic trend. Returns (bars5, session, now_dt)."""
    days = []
    d = datetime(2026, 8, 3, tzinfo=ET)
    while len(days) < 60:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    K = 59 * 13 + 10
    P = [100 + 0.01 * k + 0.00005 * k * k for k in range(K)]
    b = P[-1]
    P[-4:] = [b - 0.4, b - 0.8, b - 1.2, b - 1.2 + 3.0]
    bars = []
    for di, day in enumerate(days):
        st = datetime(day.year, day.month, day.day, 9, 30, tzinfo=ET)
        nb = 78 if di < 59 else 60
        for i in range(nb):
            k30 = di * 13 + i // 6
            if k30 >= K:
                break
            prev = P[k30 - 1] if k30 > 0 else P[0] - 0.01
            frac = (i % 6 + 1) / 6.0
            c = prev + (P[k30] - prev) * frac
            bars.append({"t": st.timestamp() + i * 300, "o": c, "h": c,
                         "l": c, "c": c, "v": 100.0})
    ld = days[-1]
    now_dt = datetime(ld.year, ld.month, ld.day, 14, 30, tzinfo=ET)
    return bars, ld.date().isoformat(), now_dt


class TestIntradayAggregation(unittest.TestCase):
    def test_complete_clock_anchored_buckets_only(self):
        from sleeves.investandbefree_dmac import aggregate_intraday
        day = datetime(2026, 10, 23, 9, 30, tzinfo=ET)
        bars = [{"t": day.timestamp() + i * 300, "o": 100 + i * 0.1,
                 "h": 100 + i * 0.1, "l": 100 + i * 0.1,
                 "c": 100 + i * 0.1, "v": 1.0} for i in range(78)]
        m15 = aggregate_intraday(bars, 15)
        m30 = aggregate_intraday(bars, 30)
        h4 = aggregate_intraday(bars, 240)
        self.assertEqual(len(m15), 26)          # 78 / 3
        self.assertEqual(len(m30), 13)          # 78 / 6
        self.assertEqual(len(h4), 1)            # only 09:30-13:30 completes
        self.assertAlmostEqual(m15[0]["c"], 100.2)   # close of bar 2
        self.assertAlmostEqual(m30[0]["c"], 100.5)   # close of bar 5
        self.assertAlmostEqual(h4[0]["c"], 104.7)    # close of bar 47
        # Remove one bar inside the second 15m bucket: that bucket
        # alone drops; later buckets stay clock-anchored.
        broken = bars[:4] + bars[5:]
        m15b = aggregate_intraday(broken, 15)
        self.assertEqual(len(m15b), 25)
        self.assertAlmostEqual(m15b[1]["o"], 100.6)  # bucket 2 opens at bar 6


class TestIntradayVariant(unittest.TestCase):
    def _drive(self, extra, bars5, session, now_dt):
        mod = importlib.import_module(
            "sleeves.investandbefree_dmac_intraday")
        sleeve = mod.InvestAndBeFreeDmacSleeve()
        return sleeve.signal({}, {}, _ctx(extra, now_dt, session)), sleeve

    def test_entry_on_30m_trigger_and_5day_expiry(self):
        bars5, session, now_dt = intraday_fixture()
        chain = [
            {"symbol": "SPY261027C00140000", "strike": 140.0,
             "expiry": "2026-10-27", "right": "call"},   # 4 days: too soon
            {"symbol": "SPY261028C00140000", "strike": 140.0,
             "expiry": "2026-10-28", "right": "call"},   # exactly 5 days
            {"symbol": "SPY261028C00139000", "strike": 139.0,
             "expiry": "2026-10-28", "right": "call"},
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        extra = {"bars_5min": {"SPY": bars5}, "chains": {"SPY": chain},
                 "quotes": quotes, "sleeve_state": {}, "dmac_state": {}}
        intents, _ = self._drive(extra, bars5, session, now_dt)
        self.assertEqual(len(intents), 1, intents)
        self.assertEqual(intents[0].qty, 4)  # floor(2000/(5.0*100))
        self.assertIn("occ=SPY261028C00140000", intents[0].reason)
        self.assertIn("trigger=crossover", intents[0].reason)
        self.assertIn("dominant=h4", intents[0].reason)

    def test_flat_by_close_exits_position_and_runner(self):
        bars5, session, _ = intraday_fixture()
        flat_now = datetime(2026, 10, 23, 15, 56, tzinfo=ET)
        occ = "SPY261028C00140000"
        for partial in (False, True):
            pos = {"occ": occ, "qty": 2, "entry_premium": 5.0,
                   "expiry": "2026-10-28", "direction": 1,
                   "partial_done": partial}
            extra = {"bars_5min": {"SPY": bars5}, "chains": {},
                     "quotes": {occ: {"bid": 5.9, "ask": 6.1}},
                     "sleeve_state": {"SPY": {"position": pos}},
                     "dmac_state": {"SPY": dict(pos)}}
            intents, _ = self._drive(extra, bars5, session, flat_now)
            self.assertEqual(len(intents), 1, partial)
            self.assertEqual(intents[0].qty, 2)
            self.assertIn("flat_by_close_1555", intents[0].reason)

    def test_select_contract_5day_bound(self):
        from sleeves.investandbefree_dmac import select_contract
        chain = [
            {"symbol": "SPY261102C00100000", "strike": 100.0,
             "expiry": "2026-11-02", "right": "call"},   # 4 days
            {"symbol": "SPY261103C00100000", "strike": 100.0,
             "expiry": "2026-11-03", "right": "call"},   # exactly 5 days
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        sel = select_contract(chain, quotes, 100.0, SESSION, 1, min_dte=5)
        self.assertEqual(sel["expiry"], "2026-11-03")


# ------------------------------------------------------------ dailyonly
class TestDailyOnlyVariant(unittest.TestCase):
    def _drive(self, cls_module, daily, weekly, h1, pos=None, quotes=None):
        mod = importlib.import_module(cls_module)
        sleeve = mod.InvestAndBeFreeDmacSleeve()
        chain, q = chain_quotes()
        extra = {"bars_weekly": {"SPY": _bars(weekly)},
                 "bars_1h": {"SPY": h1},
                 "chains": {"SPY": chain} if pos is None else {},
                 "quotes": quotes if quotes is not None else q,
                 "sleeve_state": ({"SPY": {"position": pos}} if pos else {}),
                 "dmac_state": ({"SPY": dict(pos)} if pos else {})}
        return sleeve.signal({"SPY": _bars(daily)}, {}, _ctx(extra)), sleeve

    def test_trades_on_weekly_daily_despite_bearish_4h(self):
        bear_h1 = hourly_bars(lambda i: 300 - 0.002 * i * i)
        intents, _ = self._drive(
            "sleeves.investandbefree_dmac_dailyonly",
            crossover_closes(), bull_closes(), bear_h1)
        self.assertEqual(len(intents), 1)
        self.assertIn("occ=%s" % OCC_CALL, intents[0].reason)
        self.assertEqual(intents[0].qty, 4)

    def test_4h_layer_absent_from_management(self):
        # Weekly+daily flat (no alignment); 4H bullish. The BASE
        # holds (dominant = h4 = position direction); the variant
        # has no 4H layer, so dominant is None = a break = exit.
        bull_h1 = hourly_bars(lambda i: 50 + 0.002 * i * i)
        pos = {"occ": OCC_CALL, "qty": 4, "entry_premium": 5.0,
               "expiry": "2026-11-28", "direction": 1,
               "partial_done": False}
        quotes = {OCC_CALL: {"bid": 5.9, "ask": 6.1}}  # mid 6.0: no stop/partial
        base_intents, _ = self._drive(
            "sleeves.investandbefree_dmac",
            [100.0] * 60, [100.0] * 60, bull_h1, pos=pos, quotes=quotes)
        self.assertEqual(base_intents, [])
        var_intents, _ = self._drive(
            "sleeves.investandbefree_dmac_dailyonly",
            [100.0] * 60, [100.0] * 60, bull_h1, pos=pos, quotes=quotes)
        self.assertEqual(len(var_intents), 1)
        self.assertIn("dominant_alignment_break", var_intents[0].reason)


# ------------------------------------------------------------ deep
class TestDeepVariant(unittest.TestCase):
    def test_strike_boundary_2pct_itm(self):
        from sleeves.investandbefree_dmac import select_contract
        # spot 200: call threshold 0.98*200 = 196.0 exactly; put
        # threshold 1.02*200 = 204.0 exactly.
        chain = []
        for strike in (195.0, 196.0, 197.0):
            chain.append({"symbol": "SPYXXC%03d" % strike, "strike": strike,
                          "expiry": "2026-12-13", "right": "call"})
        for strike in (203.0, 204.0, 205.0):
            chain.append({"symbol": "SPYXXP%03d" % strike, "strike": strike,
                          "expiry": "2026-12-13", "right": "put"})
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        call = select_contract(chain, quotes, 200.0, SESSION, 1,
                               min_dte=45, strike_mode="deep_itm_2pct")
        self.assertEqual(call["strike"], 196.0)
        put = select_contract(chain, quotes, 200.0, SESSION, -1,
                              min_dte=45, strike_mode="deep_itm_2pct")
        self.assertEqual(put["strike"], 204.0)

    def test_entry_drive_picks_deep_strike_and_45d_expiry(self):
        mod = importlib.import_module("sleeves.investandbefree_dmac_deep")
        sleeve = mod.InvestAndBeFreeDmacSleeve()
        chain = [
            {"symbol": "SPY261212C00234000", "strike": 234.0,
             "expiry": "2026-12-12", "right": "call"},   # 44 days: too soon
            {"symbol": "SPY261213C00230000", "strike": 230.0,
             "expiry": "2026-12-13", "right": "call"},   # 45 days
            {"symbol": "SPY261213C00234000", "strike": 234.0,
             "expiry": "2026-12-13", "right": "call"},
            {"symbol": "SPY261213C00239000", "strike": 239.0,
             "expiry": "2026-12-13", "right": "call"},   # ATM, not deep
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        extra = {"bars_weekly": {"SPY": _bars(bull_closes())},
                 "bars_1h": {}, "chains": {"SPY": chain},
                 "quotes": quotes, "sleeve_state": {}, "dmac_state": {}}
        intents = sleeve.signal({"SPY": _bars(crossover_closes())}, {},
                                _ctx(extra))
        # spot 239.05; call threshold 0.98*239.05 = 234.27 -> 234.
        self.assertEqual(len(intents), 1)
        self.assertIn("occ=SPY261213C00234000", intents[0].reason)
        self.assertIn("expiry=2026-12-13", intents[0].reason)
        self.assertEqual(intents[0].qty, 4)  # sizing inherited unchanged


# ------------------------------------------------------------ premacd
class TestPremacdVariant(unittest.TestCase):
    def _drive(self, pos, quotes, samples, daily=None, weekly=None,
               occ_plan=None):
        mod = importlib.import_module("sleeves.investandbefree_dmac_premacd")
        sleeve = mod.InvestAndBeFreeDmacSleeve()
        plan = dict(pos)
        plan["premium_samples"] = samples
        plan["premium_occ"] = occ_plan if occ_plan is not None else pos["occ"]
        extra = {"bars_weekly": {"SPY": _bars(weekly or bull_closes())},
                 "bars_1h": {}, "chains": {}, "quotes": quotes,
                 "sleeve_state": {"SPY": {"position": pos}},
                 "dmac_state": {"SPY": plan}}
        intents = sleeve.signal(
            {"SPY": _bars(daily or bull_closes())}, {}, _ctx(extra))
        return intents, sleeve

    def _pos(self, **kw):
        pos = {"occ": OCC_CALL, "qty": 4, "entry_premium": 5.0,
               "expiry": "2026-11-28", "direction": 1,
               "partial_done": False}
        pos.update(kw)
        return pos

    def test_sample_accrual_once_per_cycle(self):
        samples = [{"t": 1.0, "mid": 6.0}]
        intents, sleeve = self._drive(
            self._pos(), {OCC_CALL: {"bid": 5.9, "ask": 6.1}}, samples)
        self.assertEqual(intents, [])
        got = sleeve.dmac_state["SPY"]["premium_samples"]
        self.assertEqual(len(got), 2)
        self.assertEqual(got[-1]["mid"], 6.0)
        self.assertEqual(got[-1]["t"], NOW.timestamp())

    def test_warmup_falls_back_to_base_exits(self):
        samples = [{"t": float(i), "mid": 6.0} for i in range(10)]
        intents, _ = self._drive(
            self._pos(), {OCC_CALL: {"bid": 5.9, "ask": 6.1}}, samples,
            daily=bear_closes(), weekly=bear_closes())
        self.assertEqual(len(intents), 1)
        self.assertIn("dominant_alignment_break", intents[0].reason)

    def test_premium_cross_exit_after_warmup(self):
        samples = [{"t": float(i), "mid": 4 + 0.002 * i * i}
                   for i in range(40)]
        series = [s["mid"] for s in samples] + [5.5]
        mac, sig = ind_macd(series, False)
        # Independent check: MACD-E crosses DOWN on the accrued bar.
        self.assertGreater(mac[-2] - sig[-2], 0)
        self.assertLess(mac[-1] - sig[-1], 0)
        # Underlying stays bullish-aligned: no base exit can fire;
        # mid 5.5 is above the 2.5 stop and below the 10.0 partial.
        intents, _ = self._drive(
            self._pos(), {OCC_CALL: {"bid": 5.4, "ask": 5.6}}, samples)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].qty, 4)
        self.assertIn("premium_macd_cross_against", intents[0].reason)

    def test_series_reset_on_new_position(self):
        samples = [{"t": float(i), "mid": 6.0} for i in range(50)]
        pos = self._pos()
        pos.pop("premium_samples", None)
        intents, sleeve = self._drive(
            pos, {OCC_CALL: {"bid": 5.9, "ask": 6.1}}, samples,
            occ_plan="SPY260101C00100000")  # stale contract's series
        self.assertEqual(intents, [])
        got = sleeve.dmac_state["SPY"]["premium_samples"]
        self.assertEqual(len(got), 1)  # reset, then this cycle's sample
        self.assertEqual(got[0]["mid"], 6.0)

    def test_entry_plan_starts_empty_series(self):
        mod = importlib.import_module("sleeves.investandbefree_dmac_premacd")
        sleeve = mod.InvestAndBeFreeDmacSleeve()
        chain, quotes = chain_quotes()
        extra = {"bars_weekly": {"SPY": _bars(bull_closes())},
                 "bars_1h": {}, "chains": {"SPY": chain},
                 "quotes": quotes, "sleeve_state": {}, "dmac_state": {}}
        intents = sleeve.signal({"SPY": _bars(crossover_closes())}, {},
                                _ctx(extra))
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].qty, 4)  # sizing inherited
        plan = sleeve.dmac_state["SPY"]
        self.assertEqual(plan["premium_samples"], [])
        self.assertEqual(plan["premium_occ"], OCC_CALL)


# ------------------------------------------------------------ wiring
class TestVariantWiring(unittest.TestCase):
    def test_config_rows_roster_333(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        self.assertEqual(len(rows), 333)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        cadence = {"investandbefree_dmac_intraday": 300,
                   "investandbefree_dmac_dailyonly": 3600,
                   "investandbefree_dmac_deep": 3600,
                   "investandbefree_dmac_premacd": 3600}
        for sid, cad in cadence.items():
            mine = [r for r in rows if r["id"] == sid]
            self.assertEqual(len(mine), 1, sid)
            row = mine[0]
            self.assertEqual(row["module"], "adapters3." + sid)
            self.assertFalse(row["parked"])
            self.assertEqual(row["cadence_s"], cad)
            self.assertEqual(row["session"], "rth")
            self.assertEqual(row["slice"]["capital_usd"], 10000.0)
            self.assertEqual(row["slice"]["cash_usd"], 10000.0)
            if sid == "investandbefree_dmac_intraday":
                self.assertTrue(row["flat_by_close"])
                self.assertEqual(row["flatten_time_et"], "15:55")
            else:
                self.assertFalse(row["flat_by_close"])

    def test_inputs_equal_config_and_producer_keys(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        from desk3.producers_g4 import _BARS_TF_KEYS
        for sid in VARIANTS:
            mod = importlib.import_module("adapters3." + sid)
            row = [r for r in cfg["sleeves"] if r["id"] == sid][0]
            self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]), sid)
            for key in mod.INPUTS:
                if key.startswith("bars:"):
                    self.assertIn(key, _BARS_TF_KEYS, (sid, key))

    def test_warm_product_serves_intraday_5min(self):
        path = os.path.join(ROOT, "state", "warm_bars.json")
        if not os.path.exists(path):
            self.skipTest("warm product absent on this tree")
        doc = json.load(open(path))
        bars = doc.get("bars") or {}
        for sym in ("SPY", "QQQ"):
            self.assertGreaterEqual(len(bars.get(sym + "|5Min") or []), 3000)


class TestAdapterDrives(unittest.TestCase):
    def _view(self, bars_map, chain, quotes, now_dt=NOW):
        return {"now": now_dt.isoformat(),
                "bars": bars_map,
                "options": {"SPY": {"chains": {"SPY": chain},
                                    "quotes": quotes}},
                "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}

    def _iso(self, bars):
        from datetime import timezone as _tz
        return [{"t": datetime.fromtimestamp(b["t"], _tz.utc).isoformat(),
                 "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                 "v": b["v"]} for b in bars]

    def test_dailyonly_adapter_drive(self):
        mod = importlib.import_module(
            "adapters3.investandbefree_dmac_dailyonly")
        chain, quotes = chain_quotes()
        view = self._view(
            {"SPY|1Day": self._iso(_bars(crossover_closes())),
             "SPY|1Week": self._iso(_bars(bull_closes())),
             "QQQ|1Day": self._iso(_bars(bull_closes())),
             "QQQ|1Week": self._iso(_bars(bull_closes()))}, chain, quotes)
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], OCC_CALL)
        self.assertEqual(entries[0]["qty"], 4)

    def test_deep_adapter_drive(self):
        mod = importlib.import_module("adapters3.investandbefree_dmac_deep")
        chain = [
            {"symbol": "SPY261213C00234000", "strike": 234.0,
             "expiry": "2026-12-13", "right": "call"},
            {"symbol": "SPY261213C00239000", "strike": 239.0,
             "expiry": "2026-12-13", "right": "call"},
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        view = self._view(
            {"SPY|1Day": self._iso(_bars(crossover_closes())),
             "SPY|1Week": self._iso(_bars(bull_closes())),
             "QQQ|1Day": self._iso(_bars(bull_closes())),
             "QQQ|1Week": self._iso(_bars(bull_closes()))}, chain, quotes)
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "SPY261213C00234000")

    def test_premacd_adapter_drive_entry_state(self):
        mod = importlib.import_module(
            "adapters3.investandbefree_dmac_premacd")
        chain, quotes = chain_quotes()
        view = self._view(
            {"SPY|1Day": self._iso(_bars(crossover_closes())),
             "SPY|1Week": self._iso(_bars(bull_closes())),
             "QQQ|1Day": self._iso(_bars(bull_closes())),
             "QQQ|1Week": self._iso(_bars(bull_closes()))}, chain, quotes)
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
            saved = json.load(open(os.path.join(td, "dmac_state.json")))
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], OCC_CALL)
        self.assertEqual(saved["dmac_state"]["SPY"]["premium_samples"], [])
        self.assertEqual(saved["dmac_state"]["SPY"]["premium_occ"], OCC_CALL)

    def test_intraday_adapter_drive(self):
        mod = importlib.import_module(
            "adapters3.investandbefree_dmac_intraday")
        bars5, session, now_dt = intraday_fixture()
        chain = [
            {"symbol": "SPY261028C00140000", "strike": 140.0,
             "expiry": "2026-10-28", "right": "call"},
            {"symbol": "SPY261028C00139000", "strike": 139.0,
             "expiry": "2026-10-28", "right": "call"},
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        view = self._view(
            {"SPY|5Min": self._iso(bars5),
             "QQQ|5Min": self._iso(bars5[:500])}, chain, quotes,
            now_dt=now_dt)
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "SPY261028C00140000")
        self.assertEqual(entries[0]["qty"], 4)

    # --- F1 repair blockers (2026-10-29 variants verifier): the
    # live cycle snapshot carries NO 'slice' key, so each variant
    # adapter must size from its own $10,000 slice fallback. Each
    # drive below deletes the 'slice' key from the view (the exact
    # live shape) and requires the same golden entry as the
    # slice-supplied drive above. Hand arithmetic at ask 5.0:
    # qty = floor(2000/500) = 4 under the 2500 cap.
    def test_dailyonly_adapter_drive_sliceless(self):
        mod = importlib.import_module(
            "adapters3.investandbefree_dmac_dailyonly")
        chain, quotes = chain_quotes()
        view = self._view(
            {"SPY|1Day": self._iso(_bars(crossover_closes())),
             "SPY|1Week": self._iso(_bars(bull_closes())),
             "QQQ|1Day": self._iso(_bars(bull_closes())),
             "QQQ|1Week": self._iso(_bars(bull_closes()))}, chain, quotes)
        del view["slice"]
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], OCC_CALL)
        self.assertEqual(entries[0]["qty"], 4)

    def test_deep_adapter_drive_sliceless(self):
        mod = importlib.import_module("adapters3.investandbefree_dmac_deep")
        chain = [
            {"symbol": "SPY261213C00234000", "strike": 234.0,
             "expiry": "2026-12-13", "right": "call"},
            {"symbol": "SPY261213C00239000", "strike": 239.0,
             "expiry": "2026-12-13", "right": "call"},
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        view = self._view(
            {"SPY|1Day": self._iso(_bars(crossover_closes())),
             "SPY|1Week": self._iso(_bars(bull_closes())),
             "QQQ|1Day": self._iso(_bars(bull_closes())),
             "QQQ|1Week": self._iso(_bars(bull_closes()))}, chain, quotes)
        del view["slice"]
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "SPY261213C00234000")
        self.assertEqual(entries[0]["qty"], 4)

    def test_premacd_adapter_drive_sliceless(self):
        mod = importlib.import_module(
            "adapters3.investandbefree_dmac_premacd")
        chain, quotes = chain_quotes()
        view = self._view(
            {"SPY|1Day": self._iso(_bars(crossover_closes())),
             "SPY|1Week": self._iso(_bars(bull_closes())),
             "QQQ|1Day": self._iso(_bars(bull_closes())),
             "QQQ|1Week": self._iso(_bars(bull_closes()))}, chain, quotes)
        del view["slice"]
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], OCC_CALL)
        self.assertEqual(entries[0]["qty"], 4)

    def test_intraday_adapter_drive_sliceless(self):
        mod = importlib.import_module(
            "adapters3.investandbefree_dmac_intraday")
        bars5, session, now_dt = intraday_fixture()
        chain = [
            {"symbol": "SPY261028C00140000", "strike": 140.0,
             "expiry": "2026-10-28", "right": "call"},
            {"symbol": "SPY261028C00139000", "strike": 139.0,
             "expiry": "2026-10-28", "right": "call"},
        ]
        quotes = {c["symbol"]: {"bid": 4.9, "ask": 5.0} for c in chain}
        view = self._view(
            {"SPY|5Min": self._iso(bars5),
             "QQQ|5Min": self._iso(bars5[:500])}, chain, quotes,
            now_dt=now_dt)
        del view["slice"]
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], "SPY261028C00140000")
        self.assertEqual(entries[0]["qty"], 4)


if __name__ == "__main__":
    unittest.main()
