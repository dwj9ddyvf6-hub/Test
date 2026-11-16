"""Blockers HARDEN batch 4 (G4 producers): bars_1day+vix,
bars_secondary, bars:<sym>:<tf> slices, xsp_state, saty_setups,
qulla + buyback_scan file channels, journal:self.

Fail on the pre-cure tree (desk3/producers_g4.py and the warm.py
extra slices did not exist; run_live registered none of these keys).
Each family proves: producer fail-closed honesty, the registry FED
transition in a real Desk cycle, and a fixture E2E
entry -> manage -> exit -> flat for a touched sleeve.
"""
import json, os, shutil, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker
from desk3.cycle import Desk
from desk3.warm import WarmBars
import desk3.producers_g4 as g4


def bizdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def rows_for(dates, closes, v=1000.0):
    return [{"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c + 1.0,
             "l": c - 1.0, "c": c, "v": v} for d, c in zip(dates, closes)]


def mkroot():
    tmp = tempfile.mkdtemp(prefix="hb4-")
    os.makedirs(os.path.join(tmp, "state"), exist_ok=True)
    os.makedirs(os.path.join(tmp, "config"), exist_ok=True)
    with open(os.path.join(tmp, "config", "universes.json"), "w") as fh:
        json.dump({}, fh)
    return tmp


def write_warm_cache(root, bars, fetched_at):
    with open(os.path.join(root, "state", "warm_bars.json"), "w") as fh:
        json.dump({"fetched_at": fetched_at.isoformat(), "bars": bars}, fh)


def desk_with(root, broker=None):
    return Desk(root, broker=broker or FakeBroker(prices={}),
                sleeve_path=ROOT, timeout_s=30.0)


# ------------------------------------------------------------ bars_1day/vix
class TestBars1DayVix(unittest.TestCase):
    def setUp(self):
        self.tmp = mkroot()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.now = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)

    def test_projection_fail_closed_without_warm_cache(self):
        p = g4.BarsProjection(self.tmp, ["bars_1day"])
        self.assertEqual(p({"now": self.now}), {})

    def test_projection_marks_only_present_timeframes(self):
        dates = bizdays(date(2026, 10, 23), 30)
        bars = {"QQQ": rows_for(dates, [500.0] * 30),
                "QQQ|1Day": rows_for(dates, [500.0] * 30)}
        write_warm_cache(self.tmp, bars, self.now)
        out = g4.BarsProjection(self.tmp, ["bars_1day", "bars_1hour"])(
            {"now": self.now})
        self.assertIn("bars_1day", out)
        self.assertEqual(out["bars_1day"]["symbols"], ["QQQ"])
        self.assertNotIn("bars_1hour", out)  # no hourly slice produced

    def test_projection_stale_cache_fail_closed(self):
        write_warm_cache(self.tmp, {"QQQ|1Day": []},
                         self.now - timedelta(hours=2))
        p = g4.BarsProjection(self.tmp, ["bars_1day"])
        self.assertEqual(p({"now": self.now}), {})

    def test_vix_scalar_and_fail_closed(self):
        dates = bizdays(date(2026, 10, 23), 10)
        good = g4.VixProducer(self.tmp,
                              fetcher=lambda s: rows_for(dates, [30.0] * 10))
        out = good({"now": self.now})
        self.assertEqual(out["vix"], 30.0)
        self.assertEqual(len(out["bars:VIX:1Day"]), 10)

        def boom(sym):
            raise RuntimeError("yahoo down")

        bad = g4.VixProducer(self.tmp, fetcher=boom)
        bad.daily.cache_path = os.path.join(self.tmp, "state", "nope.json")
        self.assertEqual(bad({"now": self.now}), {})

    def test_vmr_e2e_entry_time_exit_flat(self):
        dates1 = bizdays(date(2026, 10, 23), 30)
        bars1 = {"QQQ": rows_for(dates1, [500.0] * 30),
                 "QQQ|1Day": rows_for(dates1, [500.0] * 30)}
        dates2 = bizdays(date(2026, 11, 2), 36)
        bars2 = {"QQQ": rows_for(dates2, [500.0] * 36),
                 "QQQ|1Day": rows_for(dates2, [500.0] * 36)}
        feed = {"bars": bars1}
        warm = WarmBars(self.tmp, {}, fetcher=lambda s, e, n: feed["bars"])
        positions = {"rows": []}
        broker = FakeBroker(prices={"QQQ": 500.0})
        desk = desk_with(self.tmp, broker)
        desk.add_producer("bars", warm, ["bars"], 3600)
        desk.add_producer("bars_daily",
                          g4.BarsProjection(self.tmp, ["bars_1day"]),
                          ["bars_1day"], 93600)
        desk.add_producer("vix", g4.VixProducer(
            self.tmp, fetcher=lambda s: rows_for(dates1, [30.0] * 30)),
            ["vix", "bars:VIX:1Day"], 3600)
        desk.add_producer("account", lambda c: {"positions": positions["rows"]},
                          ["positions"], 3600)
        desk.add_sleeve("s_cl_vmr_qqq", "laz_sleeves.s_cl_vmr_qqq",
                        ["bars_1day", "positions", "vix"], 300, 10000.0)
        roll = desk.run_cycle(now=self.now)
        self.assertEqual(roll["sleeves"]["s_cl_vmr_qqq"]["state"], "FED")
        self.assertEqual(broker.positions.get("QQQ"), 2.0)  # $1000 slot
        # manage -> time exit after 5 sessions -> flat
        feed["bars"] = bars2
        positions["rows"] = [{"symbol": "QQQ", "qty": 2, "avg_price": 500.0,
                              "opened_at": "2026-10-26",
                              "sleeve_id": "s_cl_vmr_qqq"}]
        roll2 = desk.run_cycle(
            now=datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(roll2["sleeves"]["s_cl_vmr_qqq"]["state"], "FED")
        self.assertEqual(broker.positions, {})

    def test_red_day_reversal_fed_not_unfed(self):
        dates = bizdays(date(2026, 10, 23), 210)
        bars = {"SPY": rows_for(dates, [600.0] * 210),
                "SPY|1Day": rows_for(dates, [600.0] * 210)}
        desk = desk_with(self.tmp)
        desk.add_producer("bars", WarmBars(self.tmp, {},
                                           fetcher=lambda s, e, n: bars),
                          ["bars"], 3600)
        desk.add_producer("bars_daily",
                          g4.BarsProjection(self.tmp, ["bars_1day"]),
                          ["bars_1day"], 93600)
        desk.add_producer("account", lambda c: {"positions": []},
                          ["positions"], 3600)
        desk.add_sleeve("red_day_reversal", "desk_sleeves.red_day_reversal",
                        ["bars_1day", "positions"], 300, 10000.0)
        roll = desk.run_cycle(now=self.now)
        self.assertEqual(roll["sleeves"]["red_day_reversal"]["state"], "FED")
        self.assertEqual(roll["sleeves"]["red_day_reversal"]["status"], "ok")


# ------------------------------------------------------------ bars_secondary
def etf_closes(growth, n=260, base=100.0):
    return [base * ((1 + growth) ** i) for i in range(n)]


class TestBarsSecondary(unittest.TestCase):
    def setUp(self):
        self.tmp = mkroot()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_secondary_fail_closed(self):
        def boom(sym):
            raise RuntimeError("yahoo down")

        p = g4.SecondaryBars(self.tmp, fetcher=boom)
        now = datetime(2026, 11, 2, 14, 37, tzinfo=timezone.utc)
        self.assertEqual(p({"now": now}), {})

    def test_interval_etf_e2e_entry_rotation_exit_flat(self):
        dates = bizdays(date(2026, 10, 30), 260)
        growth = {s: 0.001 for s in g4.SecondaryBars.UNIVERSE}
        growth["XLK"] = 0.004
        growth["QQQ"] = 0.002
        primary = {s: rows_for(dates, etf_closes(growth[s], base=300.0))
                   for s in growth}
        bars_map = {}
        for s, rows in primary.items():
            bars_map[s] = rows
            bars_map[f"{s}|1Day"] = rows

        def secondary_fetch(sym):
            g = growth[sym] + (0.0002 if sym == "XLK" else -0.0002)
            return rows_for(dates, etf_closes(g, base=300.0))

        positions = {"rows": []}
        broker = FakeBroker(prices={s: 300.0 for s in growth})
        desk = desk_with(self.tmp, broker)
        desk.add_producer("bars", WarmBars(self.tmp, {},
                                           fetcher=lambda s, e, n: bars_map),
                          ["bars"], 3600)
        desk.add_producer("bars_secondary",
                          g4.SecondaryBars(self.tmp, fetcher=secondary_fetch),
                          ["bars_secondary"], 3600)
        desk.add_producer("account", lambda c: {"positions": positions["rows"]},
                          ["positions"], 3600)
        desk.add_sleeve("aster_etf_interval1_m150",
                        "adapters3.aster_etf_interval1_m150",
                        ["bars", "bars_secondary", "positions"], 300, 20000.0)
        now1 = datetime(2026, 11, 2, 14, 37, tzinfo=timezone.utc)  # 09:37 EST
        roll = desk.run_cycle(now=now1)
        st = roll["sleeves"]["aster_etf_interval1_m150"]
        self.assertEqual(st["state"], "FED")
        self.assertGreater(broker.positions.get("XLK", 0), 0)
        held_qty = broker.positions["XLK"]
        # next month: QQQ becomes the robust leader in BOTH maps ->
        # rotation exit (sell-then-settle) -> flat
        dates2 = bizdays(date(2026, 11, 30), 281)
        growth2 = dict(growth, XLK=0.0005, QQQ=0.004)
        bars_map2 = {}
        for s in growth2:
            rows = rows_for(dates2, etf_closes(growth2[s], n=281, base=300.0))
            bars_map2[s] = rows
            bars_map2[f"{s}|1Day"] = rows
        desk.producers["bars"] = WarmBars(
            self.tmp, {}, fetcher=lambda s, e, n: bars_map2)

        def secondary_fetch2(sym):
            g = growth2[sym] + (0.0002 if sym == "QQQ" else -0.0002)
            return rows_for(dates2, etf_closes(g, n=281, base=300.0))

        desk.producers["bars_secondary"] = g4.SecondaryBars(
            self.tmp, fetcher=secondary_fetch2)
        os.remove(os.path.join(self.tmp, "state", "bars_secondary.json"))
        positions["rows"] = [{"symbol": "XLK", "qty": held_qty,
                              "avg_price": 300.0}]
        for s in growth2:
            broker.prices[s] = bars_map2[s][-1]["c"]
        roll2 = desk.run_cycle(
            now=datetime(2026, 12, 1, 14, 37, tzinfo=timezone.utc))
        self.assertEqual(roll2["sleeves"]["aster_etf_interval1_m150"]["state"],
                         "FED")
        self.assertNotIn("XLK", broker.positions)


# ------------------------------------------------------- symbol/timeframe
class TestSymbolTimeframes(unittest.TestCase):
    def setUp(self):
        self.tmp = mkroot()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.now = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)

    def test_warm_fetch_all_extra_slices(self):
        import desk3.warm as warm_mod
        orig_fetch, orig_crypto = warm_mod._fetch, warm_mod._fetch_crypto

        def fake_fetch(symbols, tf, start, env, limit=10000):
            return {s: rows_for(bizdays(date(2026, 10, 23), 5), [100.0] * 5)
                    for s in symbols}

        def fake_crypto(symbol, tf, start, env, limit=10000):
            return rows_for(bizdays(date(2026, 10, 23), 5), [100.0] * 5)

        warm_mod._fetch, warm_mod._fetch_crypto = fake_fetch, fake_crypto
        # ENJ-FEED-CONV27-20261115: stub the Kraken spot fetch too
        # so this suite stays hermetic (fetch_all gained the
        # KRAKEN_SPOT_FETCHES loop on that landing).
        orig_kraken = warm_mod._fetch_kraken_spot
        warm_mod._fetch_kraken_spot = lambda *a, **k: []
        try:
            bars = warm_mod.fetch_all(["SPY", "QQQ"], {}, self.now)
        finally:
            warm_mod._fetch, warm_mod._fetch_crypto = orig_fetch, orig_crypto
            warm_mod._fetch_kraken_spot = orig_kraken
        for key in ("SPY|1Week", "QQQ|15Min", "SPY|5Min", "QQQ|1Min",
                    "ADA/USD|1Hour", "ENJ/USD|1Min", "LINK/USD|4Hour",
                    "BTC/USD|1Day", "BTC-USD|1Day"):
            self.assertIn(key, bars)

    def test_timeframe_keys_only_when_slice_present(self):
        dates = bizdays(date(2026, 10, 23), 10)
        bars = {"QQQ|1Day": rows_for(dates, [500.0] * 10)}
        write_warm_cache(self.tmp, bars, self.now)
        p = g4.BarsProjection(self.tmp, list(g4._BARS_TF_KEYS), mode="keys")
        out = p({"now": self.now})
        self.assertIn("bars:*:1Day", out)
        self.assertIn("bars:QQQ:1Day", out)
        self.assertNotIn("bars:*:1Week", out)
        self.assertNotIn("bars:BTC-USD:1Day", out)
        self.assertNotIn("bars:QQQ:15Min", out)

    def test_coinbase_sma200_e2e_entry_and_exit(self):
        # 200 flat closes then a push above the 200d mean -> entry;
        # then closes collapse below it -> exit -> flat. BTC trades
        # 7d/week: prepare() requires consecutive CALENDAR days.
        dates = [date(2026, 10, 23) - timedelta(days=i)
                 for i in range(214, -1, -1)]
        closes = [100.0] * 205 + [130.0] * 10
        rows = rows_for(dates, closes)
        bars_map = {"BTC-USD": rows, "BTC-USD|1Day": rows}
        # CANONICAL-DIALECT-20261030 pinned update: the door now
        # translates the sleeve's BTC-USD intent to the broker
        # dialect BTC/USD before the wire (BTC-USD 422s at the
        # real broker), so this fixture's broker book is keyed
        # BTC/USD throughout the round trip below.
        broker = FakeBroker(prices={"BTC/USD": 130.0})
        desk = desk_with(self.tmp, broker)
        desk.add_producer("bars", WarmBars(self.tmp, {},
                                           fetcher=lambda s, e, n: bars_map),
                          ["bars"], 3600)
        desk.add_producer("bars_timeframes",
                          g4.BarsProjection(self.tmp, ["bars:BTC-USD:1Day"],
                                            mode="keys"),
                          ["bars:BTC-USD:1Day"], 3600)
        desk.add_producer("journal_self", g4.JournalSelfProducer(self.tmp),
                          ["journal:self", "journal:momentum"], 3600)
        positions = {"rows": []}
        desk.add_producer("account", lambda c: {"positions": positions["rows"]},
                          ["positions"], 3600)
        desk.add_sleeve("fwd_coinbase_sma200",
                        "desk3.sleeves.fwd_coinbase_sma200",
                        ["bars:BTC-USD:1Day", "positions", "journal:self"],
                        300, 10000.0)
        # the sleeve's decision window is 00:00-00:05 UTC with the
        # just-closed day (Fri 2026-10-23) as the last history bar
        roll = desk.run_cycle(now=datetime(2026, 10, 24, 0, 2,
                                           tzinfo=timezone.utc))
        st = roll["sleeves"]["fwd_coinbase_sma200"]
        self.assertEqual(st["state"], "FED")
        self.assertGreater(broker.positions.get("BTC/USD", 0), 0)
        # collapse below the mean -> exit -> flat
        dates2 = dates + [date(2026, 10, 24) + timedelta(days=i)
                          for i in range(3)]
        rows2 = rows_for(dates2, closes + [130.0, 130.0, 50.0])
        bars_map2 = {"BTC-USD": rows2, "BTC-USD|1Day": rows2}
        desk.producers["bars"] = WarmBars(self.tmp, {},
                                          fetcher=lambda s, e, n: bars_map2)
        held = broker.positions["BTC/USD"]
        positions["rows"] = [{"symbol": "BTC/USD", "qty": held,
                              "avg_price": 130.0, "opened_at": "2026-10-23"}]
        broker.prices["BTC/USD"] = 50.0
        roll2 = desk.run_cycle(
            now=datetime(2026, 10, 27, 0, 2, tzinfo=timezone.utc))
        self.assertEqual(roll2["sleeves"]["fwd_coinbase_sma200"]["state"],
                         "FED")
        self.assertNotIn("BTC/USD", broker.positions)


# ------------------------------------------------------------------ xsp_state
def xsp_daily_fixture():
    dates = bizdays(date(2026, 10, 23), 420)
    closes = [550.0 + 0.1 * i for i in range(len(dates))]
    return rows_for(dates, closes)


def xsp_chain_fixture(expiry="2026-10-30", spot=592.0):
    out = []
    for k in range(560, 645, 5):
        bid, ask = 1.0, 1.2
        if k == 590:
            bid, ask = 5.8, 6.2   # mid 6.0
        if k == 595:
            bid, ask = 6.8, 7.2   # mid 7.0 -> digital (7-6)/5 = 0.2
        out.append({"symbol": f"XSP261030P{k}", "underlying": "XSP",
                    "right": "put", "expiry": expiry, "strike": float(k),
                    "bid": bid, "ask": ask, "bid_size": 50, "ask_size": 50})
    return out


class TestXspState(unittest.TestCase):
    def setUp(self):
        self.tmp = mkroot()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_calendar_facts(self):
        cal = g4.build_calendar(date(2026, 10, 26))  # Monday
        self.assertEqual(cal["session"], "2026-10-26")
        self.assertEqual(cal["previous_session"], "2026-10-23")
        self.assertTrue(cal["first_session_of_week"])
        self.assertEqual(cal["weekly_pm_expiry"], "2026-10-30")
        cal2 = g4.build_calendar(date(2026, 10, 27))
        self.assertFalse(cal2["first_session_of_week"])

    def test_producer_pair_ledger_and_prior_exclusion(self):
        now = datetime(2026, 10, 26, 14, 2, tzinfo=timezone.utc)
        prod = g4.XspStateProducer(
            self.tmp, {}, daily_fetcher=lambda s: xsp_daily_fixture(),
            chain_fetcher=lambda env, n: xsp_chain_fixture())
        out = prod({"now": now})
        st = out["xsp_state"]
        self.assertGreaterEqual(len(st["weekly_bars"]), 15)
        self.assertEqual(st["weekly_bars"][-1]["week_end"], "2026-10-23")
        self.assertEqual(len(st["adjacent_put_symbols"]), 2)
        # current week's observation is in the ledger but NOT in priors
        self.assertEqual(st["prior_digitals"], [])
        ledger = json.load(open(os.path.join(self.tmp, "state",
                                              "xsp_digitals.json")))
        self.assertAlmostEqual(ledger["2026-10-30"]["value"], 0.2)
        # next week the same observation is a finalized prior
        out2 = prod({"now": datetime(2026, 11, 2, 14, 2,
                                      tzinfo=timezone.utc)})
        priors = out2["xsp_state"]["prior_digitals"]
        self.assertEqual([p["week_end"] for p in priors], ["2026-10-30"])

    def test_producer_fail_closed_without_daily(self):
        def boom(sym):
            raise RuntimeError("yahoo down")

        prod = g4.XspStateProducer(self.tmp, {}, daily_fetcher=boom,
                                   chain_fetcher=lambda e, n: [])
        prod.daily.cache_path = os.path.join(self.tmp, "state", "none.json")
        now = datetime(2026, 10, 26, 14, 2, tzinfo=timezone.utc)
        self.assertEqual(prod({"now": now}), {})

    def test_xsp_e2e_entry_then_settle(self):
        # seed 30 finalized weekly digital observations
        ledger = {}
        d = date(2025, 10, 3)
        for i in range(30):
            wd = d - timedelta(days=7 * i)
            ledger[wd.isoformat()] = {"value": 0.30, "pair": []}
        with open(os.path.join(self.tmp, "state", "xsp_digitals.json"),
                  "w") as fh:
            json.dump(ledger, fh)
        positions = {"rows": []}
        desk = desk_with(self.tmp)
        desk.add_producer("calendar", g4.CalendarProducer(), ["calendar"], 3600)
        desk.add_producer("xsp_index_regime", g4.XspStateProducer(
            self.tmp, {}, daily_fetcher=lambda s: xsp_daily_fixture(),
            chain_fetcher=lambda env, n: xsp_chain_fixture()),
            ["xsp_state"], 900)
        desk.add_producer("options_chain",
                          lambda c: {"options": xsp_chain_fixture()},
                          ["options"], 300)
        desk.add_producer("account", lambda c: {"positions": positions["rows"]},
                          ["positions"], 3600)
        desk.add_sleeve("aster_xsp_pcs_calm_a",
                        "adapters3.aster_xsp_pcs_calm_a",
                        ["options", "positions", "xsp_state"], 300, 10000.0)
        # Monday 10:02 ET (the designed 10:00-10:05 ET entry
        # window). The cycle stamp is UTC: 14:02Z = 10:02 ET.
        # ENH-B13-XSP-ETWIN cured the sleeve's window read to ET —
        # a 10:02Z stamp is 06:02 ET and correctly opens nothing
        # (the pre-cure fixture used exactly that stamp and relied
        # on the raw-clock read the ETWIN cure removed).
        roll = desk.run_cycle(now=datetime(2026, 10, 26, 14, 2,
                                           tzinfo=timezone.utc))
        st = roll["sleeves"]["aster_xsp_pcs_calm_a"]
        self.assertEqual(st["state"], "FED")
        journal = open(os.path.join(
            self.tmp, "state", "aster_xsp_pcs_calm_a", "journal.jsonl")).read()
        self.assertIn('"event":"intent"', journal)
        self.assertIn("aster_xsp_pcs_calm_a-xsp-2026-10-26", journal)
        # settle at the weekly PM expiry -> exit intent -> flat record
        positions["rows"] = [{
            "symbol": "XSP261030P590", "qty": 1, "avg_price": 2.5,
            "entry_spot": 592.0, "opened_at": "2026-10-26",
            "legs": [{"symbol": "XSP261030P585", "underlying": "XSP",
                      "right": "put", "expiry": "2026-10-30",
                      "strike": 585.0, "ratio": 1},
                     {"symbol": "XSP261030P590", "underlying": "XSP",
                      "right": "put", "expiry": "2026-10-30",
                      "strike": 590.0, "ratio": -1}]}]
        desk.run_cycle(now=datetime(2026, 10, 30, 20, 0,
                                    tzinfo=timezone.utc))
        journal2 = open(os.path.join(
            self.tmp, "state", "aster_xsp_pcs_calm_a", "journal.jsonl")).read()
        self.assertIn("settle", journal2)


# --------------------------------------------------------------- saty_setups
class TestSatySetups(unittest.TestCase):
    def setUp(self):
        self.tmp = mkroot()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.now = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)

    def _write_setups(self, rows):
        doc = {"generated_at": self.now.isoformat(), "setups": rows}
        with open(os.path.join(self.tmp, "state", "setups_latest.json"),
                  "w") as fh:
            json.dump(doc, fh)

    def test_translation_spy_only(self):
        self._write_setups([
            {"symbol": "SPY", "side": "long", "entry": 600.0, "stop": 590.0,
             "target": 630.0, "score": 26, "families": ["saty_day"]},
            {"symbol": "NTAP", "side": "long", "entry": 215.0,
             "stop": 196.0, "target": 240.0, "score": 26, "families": []}])
        out = g4.SatySetupsProducer(self.tmp)({"now": self.now})
        self.assertEqual(len(out["saty_setups"]), 1)
        c = out["saty_setups"][0]
        self.assertEqual((c["entry"], c["invalidation"], c["targets"]),
                         (600.0, 590.0, [630.0]))
        self.assertEqual(c["family"], "saty_day")

    def test_empty_setups_is_produced_honest_zero(self):
        self._write_setups([])
        out = g4.SatySetupsProducer(self.tmp)({"now": self.now})
        self.assertEqual(out, {"saty_setups": []})

    def test_saty_e2e_entry_invalidation_exit(self):
        self._write_setups([
            {"symbol": "SPY", "side": "long", "entry": 600.0, "stop": 590.0,
             "target": 630.0, "score": 26, "families": ["saty_day"]}])
        quote = {"bid": 599.9, "ask": 600.1}
        positions = {"rows": []}
        dates = bizdays(date(2026, 10, 23), 30)
        bars = {"SPY": rows_for(dates, [600.0] * 30),
                "SPY|1Day": rows_for(dates, [600.0] * 30),
                "SPY|10Min": rows_for(dates, [600.0] * 30)}

        def quotes_fn(pctx):
            now = pctx["now"]
            return {"quotes": {"SPY": {**quote, "at": now.isoformat(),
                                       "feed": "sip"}}}

        broker = FakeBroker(prices={"SPY": 600.0})
        desk = desk_with(self.tmp, broker)
        desk.add_producer("bars", WarmBars(self.tmp, {},
                                           fetcher=lambda s, e, n: bars),
                          ["bars"], 3600)
        desk.add_producer("quotes", quotes_fn, ["quotes"], 60)
        desk.add_producer("saty_setup_families",
                          g4.SatySetupsProducer(self.tmp), ["saty_setups"], 60)
        desk.add_producer("account", lambda c: {"positions": positions["rows"]},
                          ["positions"], 3600)
        desk.add_sleeve("aster_saty_research", "adapters3.aster_saty_research",
                        ["saty_setups", "quotes", "bars", "positions"],
                        600, 10000.0)
        roll = desk.run_cycle(now=self.now)
        st = roll["sleeves"]["aster_saty_research"]
        self.assertEqual(st["state"], "FED")
        self.assertEqual(broker.positions.get("SPY"), 2.0)  # $25 risk / $10
        # price breaks the invalidation -> structural exit -> flat
        quote.update({"bid": 584.9, "ask": 585.1})
        broker.prices["SPY"] = 585.0
        positions["rows"] = [{"symbol": "SPY", "qty": 2, "avg_price": 600.0,
                              "invalidation": 590.0, "targets": [630.0],
                              "direction": "long"}]
        roll2 = desk.run_cycle(now=datetime(2026, 10, 26, 16, 0,
                                            tzinfo=timezone.utc))
        self.assertEqual(roll2["sleeves"]["aster_saty_research"]["state"],
                         "FED")
        self.assertEqual(broker.positions, {})


# ------------------------------------------------------------ qulla / buyback
class TestQullaBuyback(unittest.TestCase):
    def setUp(self):
        self.tmp = mkroot()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.now = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)

    def _write_qulla(self, session, proposals):
        path = os.path.join(self.tmp, "cache", "qulla", "proposals.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"session": session, "proposals": proposals}, fh)

    def test_qulla_session_gate(self):
        p = g4.QullaFileProducer(self.tmp)
        self.assertEqual(p({"now": self.now}), {})  # no file
        self._write_qulla("2026-10-23", [{"symbol": "NVDA"}])
        self.assertEqual(p({"now": self.now}), {})  # stale session
        self._write_qulla("2026-10-26", [{"symbol": "NVDA"}])
        out = p({"now": self.now})
        self.assertEqual(out["qulla"]["proposals"][0]["symbol"], "NVDA")

    def test_qulla_e2e_entry_dispatched(self):
        self._write_qulla("2026-10-26", [
            {"symbol": "NVDA", "side": 1, "setup": "breakout",
             "quantity": 10, "entry": 100.0, "stop": 95.0}])
        dates = bizdays(date(2026, 10, 23), 30)
        bars = {"NVDA": rows_for(dates, [100.0] * 30),
                "NVDA|1Day": rows_for(dates, [100.0] * 30)}
        broker = FakeBroker(prices={"NVDA": 100.0})
        desk = desk_with(self.tmp, broker)
        desk.add_producer("bars", WarmBars(self.tmp, {},
                                           fetcher=lambda s, e, n: bars),
                          ["bars"], 3600)
        desk.add_producer("qulla", g4.QullaFileProducer(self.tmp),
                          ["qulla"], 3600)
        desk.add_producer("account", lambda c: {"positions": []},
                          ["positions"], 3600)
        desk.add_sleeve("qullamaggie_paper", "desk3.port_b5.qullamaggie_paper",
                        ["positions", "qulla"], 300, 10000.0)
        roll = desk.run_cycle(now=self.now)
        st = roll["sleeves"]["qullamaggie_paper"]
        self.assertEqual(st["state"], "FED")
        self.assertEqual(broker.positions.get("NVDA"), 10.0)

    def _write_buyback(self, scanned_at, signals):
        path = os.path.join(self.tmp, "cache", "scan", "buyback.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"scanned_at": scanned_at.isoformat(),
                       "scan_signals": signals}, fh)

    def test_buyback_freshness_gate(self):
        p = g4.BuybackFileProducer(self.tmp)
        self.assertEqual(p({"now": self.now}), {})  # no file
        sig = [{"symbol": "XYZ", "buyback_pct": 7.5,
                "filing_date": "2026-10-13"}]
        self._write_buyback(self.now - timedelta(days=9), sig)
        self.assertEqual(p({"now": self.now}), {})  # stale > 8 days
        self._write_buyback(self.now - timedelta(days=1), sig)
        out = p({"now": self.now})
        self.assertEqual(out["buyback_scan"]["scan_signals"], sig)
        self.assertAlmostEqual(out["buyback_scan"]["scan_age_days"], 1.0,
                               places=1)

    def test_buyback_parse_threshold(self):
        from desk3.buyback_scan import parse_buyback
        text = ("The Board authorized a stock repurchase program under "
                "which the Company may repurchase up to 10 percent of "
                "its outstanding shares of common stock.")
        hit = parse_buyback(text, "XYZ", "2026-10-13")
        self.assertEqual(hit["buyback_pct"], 10.0)
        small = ("The Board authorized a share repurchase program of "
                 "up to 2 percent of outstanding shares.")
        self.assertIsNone(parse_buyback(small, "XYZ", "2026-10-13"))
        self.assertIsNone(parse_buyback("No news here.", "XYZ", "2026-10-13"))

    def test_buyback_e2e_entry_and_t_plus_15_exit(self):
        # view-level E2E (the repo's fixture-drive pattern): the view
        # is assembled from the batch-4 producer outputs + the batch-2
        # drive shapes for chains/quotes/earnings.
        import importlib
        sig = [{"symbol": "XYZ", "buyback_pct": 7.5,
                "filing_date": "2026-10-13"}]
        self._write_buyback(self.now - timedelta(days=1), sig)
        scan = g4.BuybackFileProducer(self.tmp)(
            {"now": self.now})["buyback_scan"]
        mod = importlib.import_module("adapters3.earnings_buyback")
        dates = bizdays(date(2026, 10, 23), 5)
        extra = {"scan_signals": scan["scan_signals"],
                 "scan_age_days": scan["scan_age_days"],
                 "earnings": {"XYZ": "2026-11-02"},
                 "chains": {"XYZ": [{"symbol": "XYZ261127C00105000",
                                     "strike": 105.0,
                                     "expiration": "2026-11-27"}]},
                 "quotes": {"XYZ261127C00105000": {"bid": 0.38, "ask": 0.40}},
                 "earnings_buyback_improve": {"expiry_gap_gate": False}}
        view = {"now": "2026-10-23T15:00:00-04:00",
                "bars": {"XYZ|1Day": rows_for(dates, [100.0] * 5)},
                "positions": [], "slice": {"capital_usd": 100000.0,
                                           "cash_usd": 100000.0},
                "params": {"extra": extra}, "session_fills": []}
        ctx = {"state_dir": tempfile.mkdtemp(prefix="hb4-eb-"),
               "sleeve_id": "earnings_buyback", "cycle_id": "fixture"}
        out = mod.evaluate(view, ctx)
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertIn("long_call", entries[0]["reason"])
        # exit: T+15 trading days after the 2026-10-01 earnings date
        pos = {"qty": 2, "kind": "long_call", "occ": "XYZ261127C00105000",
               "earnings_date": "2026-10-01", "debit": 0.40,
               "expiry": "2026-11-27"}
        extra2 = {"quotes": extra["quotes"],
                  "sleeve_state": {"XYZ": {"position": pos}}}
        view2 = {"now": "2026-10-23T15:00:00-04:00",
                 "bars": {"XYZ|1Day": rows_for(
                     bizdays(date(2026, 10, 23), 20), [100.0] * 20)},
                 "positions": [{"symbol": "XYZ261127C00105000", "qty": 2,
                                "avg_price": 0.40,
                                "opened_at": "2026-09-20T14:00:00Z",
                                "intent_id": "seed"}],
                 "slice": {"capital_usd": 100000.0, "cash_usd": 100000.0},
                 "params": {"extra": extra2}, "session_fills": []}
        out2 = mod.evaluate(view2, ctx)
        exits = [i for i in out2 if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1)
        self.assertIn("time_stop_t_plus_15", exits[0]["reason"])


# -------------------------------------------------------------------- wiring
class TestWiring(unittest.TestCase):
    def test_register_all_g4_outputs_cover_batch4_keys(self):
        desk = Desk(mkroot(), broker=FakeBroker(), sleeve_path=ROOT)
        g4.register_all_g4(desk, ROOT, env={})
        outputs = set()
        for spec in desk.registry.producers.values():
            outputs.update(spec["outputs"])
        for key in ("bars_1day", "bars_1hour", "bars_5min", "bars_1min",
                    "bars:*:1Day", "bars:*:1Week", "bars:QQQ:15Min",
                    "bars:BTC-USD:1Day", "bars:ADA/USD:1Hour",
                    "bars:VIX:1Day", "vix", "bars_secondary", "calendar",
                    "xsp_state", "saty_setups", "qulla", "buyback_scan",
                    "journal:self"):
            self.assertIn(key, outputs)

    def test_run_live_registers_batch4(self):
        src = open(os.path.join(ROOT, "desk3", "run_live.py")).read()
        self.assertIn("register_all_g4", src)


if __name__ == "__main__":
    unittest.main()
