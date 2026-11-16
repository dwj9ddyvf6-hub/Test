"""Regression blockers: ENJ-FEED-CONV27-20261115 (2026-11-15).

Defect class: CONV-27 (the ENJ breakout stream's forward grade)
could never accrue, for three stacked reasons, each proven on the
live desk before this cure:

- desk3/aster_batch7.py carried a private _bars that tried only
  archive spellings (ENJUSDT|4Hour, ENJUSDT|4h, ENJUSDT|240min,
  bare) that no producer serves, returning 0 bars on every live
  snapshot, while every sibling Aster crypto engine delegates to
  desk3/crypto_bars.resolve_bars, which also tries the served
  spot form ENJ/USD|4Hour (721 bars live from the desk's Kraken
  producer). All ten batch7 ENJ sleeves evaluated on an empty
  tape forever.
- The warm layer persisted no ENJ series at all: ENJ/USD is
  unlisted at the broker (42210000 asset-not-found), so the
  Alpaca crypto route returns nothing, and the conversion
  grader's SeriesBook had no ENJ tape to price on.
- The grader counted only fills, and ENJ entries can never fill:
  they fail closed at the broker seam by name. The register's
  named step arms the stream as shadow on the live Kraken
  ENJ/USD tape and grades its entries, which exist only as
  dispatcher entry intents.

Cure (this landing): batch7._bars delegates to resolve_bars like
its siblings; warm.py persists the Kraken spot tape as
ENJ/USD|4Hour (KRAKEN_SPOT_FETCHES, fail-closed); the grader maps
ENJUSDT to the ENJ/USD tape, loads dispatcher entry intents as
shadow entries for arms declaring entry_source "intents", and
CONV-27 is registered as a FWD_GRADE arm with its falsifier and
kill rule byte-identical to its Conversion Register row. No ENJ
sleeve's signal logic, sizing, stops or thresholds change; the
feed serves data only.

Fail direction: on the pre-change tree at commit 53d7cd3 the
batch7 view test returns 0 bars, the warm Kraken tests error or
fail (no KRAKEN_SPOT_FETCHES, no parser), the SYMMAP and arm
tests fail, and the intent-loader tests error (no such loader).
"""
import json
import os
import shutil
import tempfile
import unittest

from desk3 import aster_batch7, conversion_shadow as cs, warm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BREAKOUT_FULLCASH = "aster_r19_enjusdt_breakout_base_fixed16_fullcash"
BREAKOUT_VOL1PCT = "aster_r19_enjusdt_breakout_base_fixed16_volume1pct"
REGISTER_FALSIFIER = "First 10 resolved shadow entries graded at fwd10."
REGISTER_KILL = ("Non-positive fwd10 excess over those entries "
                 "retires the lead.")


def _rows(n, close=0.02, start=1757000000):
    from datetime import datetime, timezone
    return [{"t": datetime.fromtimestamp(
                 start + 14400 * i, timezone.utc).strftime(
                     "%Y-%m-%dT%H:%M:%SZ"),
             "o": close, "h": close * 1.01,
             "l": close * 0.99, "c": close, "v": 1000.0}
            for i in range(n)]


class TestBatch7ResolvesTheServedTape(unittest.TestCase):
    def test_spot_form_view_resolves(self):
        rows = _rows(80)
        view = {"bars": {"ENJ/USD|4Hour": rows}}
        self.assertEqual(aster_batch7._bars(view, "ENJUSDT"), rows)

    def test_archive_key_still_wins(self):
        arch = _rows(70, close=0.03)
        view = {"bars": {"ENJUSDT|4Hour": arch,
                         "ENJ/USD|4Hour": _rows(80)}}
        self.assertEqual(aster_batch7._bars(view, "ENJUSDT"), arch)

    def test_missing_tape_fails_closed(self):
        self.assertEqual(aster_batch7._bars({}, "ENJUSDT"), [])
        self.assertEqual(aster_batch7._bars({"bars": {}}, "ENJUSDT"),
                         [])

    def test_breakout_parents_are_batch7_specs(self):
        self.assertIn(BREAKOUT_FULLCASH, aster_batch7.SPECS)
        self.assertIn(BREAKOUT_VOL1PCT, aster_batch7.SPECS)

    def test_breakout_signal_fires_on_a_breakout_bar(self):
        from datetime import datetime, timedelta, timezone
        rows = _rows(30, close=0.02)
        # Final bar closes above the prior 20 bars' high (the
        # family's _breakout rule); the view's now sits just after
        # that bar's close so the ENH freshness gate admits it.
        last = datetime.fromisoformat(
            rows[-1]["t"].replace("Z", "+00:00"))
        nxt = (last + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append({"t": nxt, "o": 0.021, "h": 0.026, "l": 0.0205,
                     "c": 0.025, "v": 5000.0})
        now = (last + timedelta(hours=8, seconds=60)).isoformat()
        view = {"bars": {"ENJ/USD|4Hour": rows}, "positions": [],
                "now": now,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        intents = aster_batch7.evaluate(BREAKOUT_FULLCASH, view, {})
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].kind, "enter")
        self.assertEqual(intents[0].side, "buy")
        self.assertEqual(intents[0].symbol, "ENJUSDT")


class TestWarmKrakenTape(unittest.TestCase):
    FIXTURE = {"error": [], "result": {"ENJUSD": [
        [1767225600, "0.10", "0.11", "0.09", "0.105", "0.10",
         "1234.5", 10],
        [1767240000, "0.105", "0.12", "0.10", "0.115", "0.11",
         "2222.0", 12]], "last": 1767240000}}

    def test_fetch_declared(self):
        hits = [f for f in warm.KRAKEN_SPOT_FETCHES
                if f[0] == "ENJ/USD" and f[2] == "4Hour"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][1], "ENJUSD")
        self.assertEqual(hits[0][3], 240)
        self.assertGreaterEqual(hits[0][4], 60)

    def test_parser_maps_the_family_record_form(self):
        rows = warm.parse_kraken_ohlc(self.FIXTURE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["t"], "2026-01-01T00:00:00Z")
        self.assertEqual(rows[0]["c"], 0.105)
        # Volume is candle index 6 (the VWAP field is index 5).
        self.assertEqual(rows[0]["v"], 1234.5)
        self.assertEqual(rows[1]["v"], 2222.0)

    def test_parser_fails_closed(self):
        self.assertEqual(warm.parse_kraken_ohlc(
            {"error": ["EGeneral:Invalid arguments"]}), [])
        self.assertEqual(warm.parse_kraken_ohlc(None), [])
        self.assertEqual(warm.parse_kraken_ohlc({"result": {}}), [])

    def test_fetch_all_persists_and_fails_closed(self):
        rows = [{"t": "2026-11-15T00:00:00Z", "o": 1.0, "h": 1.0,
                 "l": 1.0, "c": 1.0, "v": 1.0}]
        orig = (warm._fetch, warm._fetch_crypto,
                warm._fetch_kraken_spot)
        warm._fetch = lambda *a, **k: {}
        warm._fetch_crypto = lambda *a, **k: []
        try:
            warm._fetch_kraken_spot = lambda *a, **k: list(rows)
            bars = warm.fetch_all([], {}, now=None)
            self.assertEqual(bars.get("ENJ/USD|4Hour"), rows)

            def boom(*a, **k):
                raise RuntimeError("kraken down")
            warm._fetch_kraken_spot = boom
            bars = warm.fetch_all([], {}, now=None)
            self.assertNotIn("ENJ/USD|4Hour", bars)
        finally:
            (warm._fetch, warm._fetch_crypto,
             warm._fetch_kraken_spot) = orig


class TestGraderENJ(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.makedirs(os.path.join(self.tmp, "state"))

    def _write_warm(self, doc):
        with open(os.path.join(self.tmp, "state", "warm_bars.json"),
                  "w") as fh:
            json.dump({"bars": doc}, fh)

    def test_symmap_prices_enj_on_the_kraken_tape(self):
        self.assertEqual(cs.SYMMAP["ENJUSDT"], "ENJ/USD")
        self._write_warm({"ENJ/USD|4Hour": [
            {"t": "2026-11-14T00:00:00Z", "o": 1.0, "h": 1.0,
             "l": 1.0, "c": 0.020, "v": 1.0},
            {"t": "2026-11-14T04:00:00Z", "o": 1.0, "h": 1.0,
             "l": 1.0, "c": 0.022, "v": 1.0},
            {"t": "2026-11-15T00:00:00Z", "o": 1.0, "h": 1.0,
             "l": 1.0, "c": 0.021, "v": 1.0}]})
        book = cs.SeriesBook(self.tmp)
        series = book.daily("ENJUSDT")
        self.assertIsNotNone(series)
        self.assertEqual(series[1]["2026-11-15"], 0.021)

    def test_symmap_fails_closed_without_the_tape(self):
        self._write_warm({})
        book = cs.SeriesBook(self.tmp)
        self.assertIsNone(book.daily("ENJUSDT"))

    def test_conv27_arm_registered_in_its_own_form(self):
        reg = json.load(open(os.path.join(
            ROOT, "config", "conversion_shadow_20261115.json")))
        arms = [a for a in reg["arms"] if a["conv"] == "CONV-27"]
        self.assertEqual(len(arms), 1)
        arm = arms[0]
        self.assertEqual(arm["kind"], "FWD_GRADE")
        self.assertEqual(arm["entry_source"], "intents")
        self.assertEqual(arm["falsifier"], REGISTER_FALSIFIER)
        self.assertEqual(arm["kill_rule"], REGISTER_KILL)
        self.assertEqual(arm["parents"],
                         [BREAKOUT_FULLCASH, BREAKOUT_VOL1PCT])
        self.assertEqual(arm["decisive_horizons"], [10])
        self.assertEqual(arm["grade_n"], 10)
        self.assertEqual(arm["calendar"], "utc")


class TestIntentEntries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        sdir = os.path.join(self.tmp, "state", BREAKOUT_FULLCASH)
        os.makedirs(sdir)
        journal = [
            {"event": "intent", "intent_id": "i-good",
             "ts": "2026-11-20T14:00:00+00:00"},
            {"event": "intent", "intent_id": "i-noterminal",
             "ts": "2026-11-20T15:00:00+00:00"},
            {"event": "intent", "intent_id": "i-early",
             "ts": "2026-11-10T14:00:00+00:00"},
            {"event": "intent", "intent_id": "i-exit",
             "ts": "2026-11-20T16:00:00+00:00"},
        ]
        with open(os.path.join(sdir, "journal.jsonl"), "w") as fh:
            for r in journal:
                fh.write(json.dumps(r) + "\n")
        disp = [
            {"event": "broker_rejected_terminal", "kind": "entry",
             "intent_id": "i-good", "sleeve": BREAKOUT_FULLCASH,
             "symbol": "ENJ/USD", "side": "buy", "qty": 100},
            {"event": "broker_rejected_terminal", "kind": "entry",
             "intent_id": "i-early", "sleeve": BREAKOUT_FULLCASH,
             "symbol": "ENJ/USD", "side": "buy", "qty": 100},
            {"event": "broker_rejected_terminal", "kind": "exit",
             "intent_id": "i-exit", "sleeve": BREAKOUT_FULLCASH,
             "symbol": "ENJ/USD", "side": "sell", "qty": 100},
            {"event": "broker_unavailable", "kind": "entry",
             "intent_id": "i-noterminal", "sleeve": BREAKOUT_FULLCASH,
             "symbol": "ENJ/USD", "side": "buy", "qty": 100},
        ]
        with open(os.path.join(self.tmp, "state", "dispatcher.jsonl"),
                  "w") as fh:
            for r in disp:
                fh.write(json.dumps(r) + "\n")

    def test_only_terminal_entry_intents_in_window_count(self):
        ents = cs.load_intent_entries(self.tmp, "2026-11-16",
                                      {BREAKOUT_FULLCASH})
        self.assertEqual([e["intent_id"] for e in ents], ["i-good"])
        self.assertIsNone(ents[0]["price"])
        self.assertEqual(ents[0]["dir"], 1)
        self.assertEqual(ents[0]["date_utc"], "2026-11-20")

    def test_grade_fwd_prices_shadow_entries_on_the_tape(self):
        dates = ["2026-11-%02d" % d for d in range(16, 31)]
        closes = {d: 100.0 for d in dates}
        closes["2026-11-26"] = 110.0
        bench = (list(dates), {d: 200.0 for d in dates})
        series = (list(dates), closes)

        class Book:
            def daily(self, sym):
                return series if sym in ("ENJUSDT", "ENJ/USD") \
                    else None
        arm = {"conv": "CONV-27", "kind": "FWD_GRADE",
               "entry_source": "intents",
               "parents": [BREAKOUT_FULLCASH],
               "horizons": [10], "decisive_horizons": [10],
               "grade_n": 10, "calendar": "utc"}
        entry = {"sleeve": BREAKOUT_FULLCASH, "symbol": "ENJUSDT",
                 "dir": 1, "qty": 1.0, "price": None,
                 "ts": "2026-11-16T14:00:00+00:00",
                 "intent_id": "i-x", "date_et": "2026-11-16",
                 "date_utc": "2026-11-16"}
        res = cs.grade_fwd(Book(), bench, arm, [], [entry])
        self.assertEqual(res["entries_seen"], 1)
        self.assertEqual(res["horizons"]["10"]["raw"]["n"], 1)
        self.assertAlmostEqual(
            res["horizons"]["10"]["raw"]["mean_bp"], 1000.0)
        self.assertEqual(res["state"], "ACCRUING")

    def test_run_shows_conv27_accruing(self):
        self._write_warm_for_run()
        cfg = os.path.join(self.tmp, "config")
        os.makedirs(cfg)
        shutil.copy(os.path.join(
            ROOT, "config", "conversion_shadow_20261115.json"), cfg)
        _text, rows = cs.run(self.tmp)
        conv27 = [r for r in rows if r["conv"] == "CONV-27"]
        self.assertEqual(len(conv27), 1)
        self.assertEqual(conv27[0]["state"], "ACCRUING")
        # The fixture journals in this root carry one in-window
        # terminal entry intent (i-good, 2026-11-20): run() pools
        # it through the intent source end to end. It cannot
        # resolve at fwd10 on the fixture tape (which ends
        # 2026-11-28), so the arm stays ACCRUING.
        self.assertEqual(conv27[0]["entries_seen"], 1)

    def _write_warm_for_run(self):
        enj = [{"t": "2026-11-%02dT00:00:00Z" % d, "o": 1.0,
                "h": 1.0, "l": 1.0, "c": 0.02, "v": 1.0}
               for d in range(1, 29)]
        qqq = [{"t": "2026-11-%02dT00:00:00Z" % d, "o": 1.0,
                "h": 1.0, "l": 1.0, "c": 500.0, "v": 1.0}
               for d in range(1, 29)]
        with open(os.path.join(self.tmp, "state", "warm_bars.json"),
                  "w") as fh:
            json.dump({"bars": {"ENJ/USD|4Hour": enj,
                                "QQQ|1Day": qqq}}, fh)


if __name__ == "__main__":
    unittest.main()
