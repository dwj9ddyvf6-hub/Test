"""ENJ-PAPER-20261116 blockers (desk full audit escalation 2;
owner ruling 2026-11-16 09:22 ET: "Fix them").

Defect: the 22-sleeve ENJ class (20 aster ENJ sleeves,
fwd_alpaca_enj_iu_body, free_kraken_enj_spot) could evaluate on
the desk's real Kraken spot tape but could never trade. ENJ/USD
is proven unlisted at Alpaca (42210000 asset-not-found), so under
INTENT-RECORDED-UNLISTED-20261116 entries were consumed as
intent_recorded rows (no fill, no position, ever) and exits
terminated against an empty broker book
(exit_satisfied_no_broker_position). A sleeve could enter on
paper forever and never hold, exit, or resolve a trade.

Cure (this landing):
- desk3/dispatcher.py: at the live door, intents from the 22
  class sleeves in ENJ/USD fill in the free_kraken paper form
  (_paper_fill_enj): filled at the Kraken feed price the intent
  carries, journaled as ordinary fill rows stamped
  venue="kraken_paper" with feed provenance, booked into the
  sleeve's own slice under the broker fill branch's signed rule.
  Entries face the slice buying-power check; exits reconcile
  against the sleeve's own paper position and clamp to it. No
  class intent reaches submit_order. The PF_ recorded seam, the
  non-class preflight rejection, and test-double behavior are
  untouched.
- config/sleeves.json: the 22 rows carry own_book_view (their
  book exists only in the dispatcher journal) and the
  ENJ-PAPER-20261116 stamp.
- desk3/reconcile.py: the kraken_paper partition is excluded
  from the broker comparison and reported as paper_book;
  journal_derived's default read is unchanged, so slice seeds
  and own-book views carry the paper book in full.
- desk3/conversion_shadow.py: load_intent_entries accepts a
  kraken_paper fill row as an ENJ entry's terminal evidence, so
  CONV-27's graded population is unchanged.
- desk3/producers3.py: the Kraken producer stamps the ENJ
  tape's provenance (source, pair, timestamp basis, capture
  time) on the snapshot as kraken.enj_provenance.

Fail direction: on the pre-cure tree the dispatcher tests return
"recorded" (entries) / broker-path results instead of paper
fills and no fill rows exist; the reconcile test manufactures
an ENJ position discrepancy and halt; the grader test sees no
terminal row for a paper-filled entry; the producer test finds
no provenance key; the config tests find no own_book_view.
"""
import json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher, ENJ_PAPER_SLEEVES  # noqa: E402

ENJ22 = {
    "aster_abs_enj_4h", "aster_enj_nfs_fixed96_vol",
    "aster_enj_nfs_lost_full", "aster_enj_nfs_lost_vol",
    "aster_enj_nfs_norm_full", "aster_enj_nfs_norm_vol",
    "aster_enj_nfs_normfail_full", "aster_enj_nfs_normfail_vol",
    "aster_pub_enj_iu_body",
    "aster_r19_enjusdt_absorption_base_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_base_fixed16_volume1pct",
    "aster_r19_enjusdt_absorption_negative_funding_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_negative_funding_fixed16_volume1pct",
    "aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_volume1pct",
    "aster_r19_enjusdt_breakout_base_fixed16_fullcash",
    "aster_r19_enjusdt_breakout_base_fixed16_volume1pct",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed16_volume1pct",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed96_fullcash",
    "free_kraken_enj_spot", "fwd_alpaca_enj_iu_body",
}
BREAKOUT = "aster_r19_enjusdt_breakout_base_fixed16_fullcash"
SLICES = {BREAKOUT: {"capital_usd": 10000, "cash_usd": 10000},
          "free_kraken_enj_spot": {"capital_usd": 10000,
                                   "cash_usd": 10000},
          "free_kraken_ada_breakdown": {"capital_usd": 10000,
                                        "cash_usd": 10000},
          "plain": {"capital_usd": 10000, "cash_usd": 10000}}


class LiveBookFake(FakeBroker):
    live_book = True


def _entry(iid, symbol="ENJ/USD", side="buy", qty=100, price=0.02):
    return {"intent_id": iid, "kind": "entry", "symbol": symbol,
            "side": side, "qty": qty, "order_type": "market",
            "time_in_force": "gtc", "price_hint": price,
            "position_intent": "buy_to_open" if side == "buy"
            else "sell_to_open"}


def _exit(iid, qty=100, price=0.025, side="sell"):
    return {"intent_id": iid, "kind": "exit", "symbol": "ENJ/USD",
            "side": side, "qty": qty, "order_type": "market",
            "time_in_force": "gtc", "price_hint": price,
            "position_intent": "sell_to_close" if side == "sell"
            else "buy_to_close"}


def _rows(tmp):
    path = os.path.join(tmp, "state", "dispatcher.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path)]


def _disp(tmp, broker):
    return Dispatcher(tmp, broker, slices=dict(SLICES),
                      price_lookup=lambda s: None)


class TestPaperClass(unittest.TestCase):
    def test_class_is_exactly_the_22(self):
        # T474U-CRYPTO-PORT-20261116 (later the same day): the class
        # grows by exactly the three t474u ENJ twins of the faithful
        # t474u_x port (desk3/t474u_crypto.py); exact-equality
        # strength is unchanged, the expected set is ENJ22 + those 3.
        self.assertEqual(ENJ_PAPER_SLEEVES, ENJ22 | {
            "crypto_bratr_enj", "crypto_mfi_enj", "crypto_stdev_enj"})
        rows = json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))["sleeves"]
        enj_ids = {r["id"] for r in rows if "enj" in r["id"]}
        # T474U-CRYPTO-PORT-20261116: + the three t474u ENJ twins.
        self.assertEqual(enj_ids, ENJ22 | {
            "crypto_bratr_enj", "crypto_mfi_enj", "crypto_stdev_enj"})

    def test_config_rows_carry_own_book_and_stamp(self):
        rows = json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))["sleeves"]
        by_id = {r["id"]: r for r in rows}
        for sid in ENJ22:
            self.assertTrue(by_id[sid].get("own_book_view"), sid)
            stamp = (by_id[sid].get("params") or {}).get(
                "parked_reason") or ""
            self.assertIn("ENJ-PAPER-20261116", stamp, sid)


class TestPaperFills(unittest.TestCase):
    def test_entry_fills_on_the_feed_without_submit(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("e1"), BREAKOUT)
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(r["venue"], "kraken_paper")
        self.assertEqual(r["price"], 0.02)
        self.assertEqual(broker.submit_count, 0,
                         "ENJ must never be dispatched to Alpaca")
        fills = [x for x in _rows(tmp) if x.get("event") == "fill"]
        self.assertEqual(len(fills), 1)
        f = fills[0]
        self.assertEqual(f["venue"], "kraken_paper")
        self.assertEqual(f["feed_source"], "kraken_public_spot")
        self.assertEqual(f["pair"], "ENJUSD")
        self.assertEqual(f["fill_price_source"], "price_hint")
        self.assertEqual(f["qty"], 100)
        sl = d.slice_for(BREAKOUT)
        self.assertEqual(sl["positions"]["ENJ/USD"]["qty"], 100)
        self.assertAlmostEqual(sl["cash_usd"], 10000 - 2.0)
        # a rebuilt dispatcher treats the filled intent as spent
        d2 = _disp(tmp, broker)
        r = d2.process_intent(_entry("e1"), BREAKOUT)
        self.assertEqual(r["status"], "duplicate")
        self.assertEqual(broker.submit_count, 0)

    def test_bare_spelling_fills_in_the_same_form(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        r = d.process_intent(
            _entry("e-bare", symbol="ENJUSD", qty=500000,
                   price=0.019), "free_kraken_enj_spot")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 0)
        fills = [x for x in _rows(tmp) if x.get("event") == "fill"]
        self.assertEqual(fills[0]["symbol"], "ENJ/USD")

    def test_exit_roundtrip_closes_the_paper_position(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        d.process_intent(_entry("e1"), BREAKOUT)
        r = d.process_intent(_exit("x1"), BREAKOUT)
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(r["price"], 0.025)
        self.assertEqual(broker.submit_count, 0)
        sl = d.slice_for(BREAKOUT)
        self.assertNotIn("ENJ/USD", sl["positions"])
        self.assertAlmostEqual(sl["cash_usd"],
                               10000 - 2.0 + 2.5)
        fills = [x for x in _rows(tmp) if x.get("event") == "fill"]
        self.assertEqual(len(fills), 2)

    def test_exit_without_a_paper_position_fails_closed(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        r = d.process_intent(_exit("x-none"), BREAKOUT)
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected",
                          "exit_satisfied_no_paper_position"))
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual([x for x in _rows(tmp)
                          if x.get("event") == "fill"], [])

    def test_oversize_exit_clamps_to_the_paper_position(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        d.process_intent(_entry("e1", qty=100), BREAKOUT)
        r = d.process_intent(_exit("x-big", qty=250), BREAKOUT)
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(r["qty"], 100)
        fills = [x for x in _rows(tmp) if x.get("event") == "fill"]
        self.assertTrue(fills[-1]["qty_clamped_to_paper_position"])
        self.assertEqual(fills[-1]["requested_qty"], 250)

    def test_entry_beyond_slice_bp_is_refused_by_name(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("e-big", qty=10 ** 9), BREAKOUT)
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "insufficient_slice_bp"))
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual([x for x in _rows(tmp)
                          if x.get("event") == "fill"], [])

    def test_unpriced_entry_fails_closed_by_name(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        intent = _entry("e-noprice")
        intent["price_hint"] = None
        r = d.process_intent(intent, BREAKOUT)
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "no_price_for_bp"))
        self.assertEqual(broker.submit_count, 0)


class TestSeamsUntouched(unittest.TestCase):
    def test_pf_entry_still_recorded_not_filled(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"PF_ADAUSD": 100.0})
        d = _disp(tmp, broker)
        intent = {"intent_id": "pf-1", "kind": "entry",
                  "symbol": "PF_ADAUSD", "side": "sell", "qty": 2,
                  "order_type": "market", "time_in_force": "gtc",
                  "price_hint": 100.0}
        r = d.process_intent(intent, "free_kraken_ada_breakdown")
        self.assertEqual((r["status"], r["reason"]),
                         ("recorded", "intent_recorded_unlisted_symbol"))
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual([x for x in _rows(tmp)
                          if x.get("event") == "fill"], [])

    def test_listed_symbol_still_submits(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"SPY": 100.0})
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("spy-1", symbol="SPY",
                                    price=100.0), "plain")
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)
        fills = [x for x in _rows(tmp) if x.get("event") == "fill"]
        self.assertNotIn("venue", fills[0])

    def test_non_class_enj_entry_is_not_paper_filled(self):
        tmp = tempfile.mkdtemp()
        broker = LiveBookFake(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("plain-enj"), "plain")
        self.assertNotEqual(r.get("venue"), "kraken_paper")
        self.assertEqual([x for x in _rows(tmp)
                          if x.get("event") == "fill"
                          and x.get("venue") == "kraken_paper"], [])
        self.assertEqual(broker.submit_count, 0)

    def test_test_double_keeps_fake_door_behavior(self):
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"ENJ/USD": 0.02})
        d = _disp(tmp, broker)
        r = d.process_intent(_entry("e-fake"), BREAKOUT)
        self.assertEqual(r["status"], "filled", r)
        self.assertEqual(broker.submit_count, 1)
        fills = [x for x in _rows(tmp) if x.get("event") == "fill"]
        self.assertNotIn("venue", fills[0])


class TestReconcilePartition(unittest.TestCase):
    def _state_with_paper_fill(self):
        tmp = tempfile.mkdtemp()
        state = os.path.join(tmp, "state")
        os.makedirs(state)
        rows = [
            {"event": "fill", "intent_id": "e1", "sleeve": BREAKOUT,
             "symbol": "ENJ/USD", "side": "buy", "qty": 100,
             "price": 0.02, "position_intent": "buy_to_open",
             "venue": "kraken_paper",
             "ts": "2026-11-16T15:00:00+00:00"},
        ]
        with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return tmp, state

    def test_paper_book_is_not_a_broker_discrepancy(self):
        from desk3.reconcile import (journal_derived,
                                     journal_paper_book, reconcile)
        tmp, state = self._state_with_paper_fill()
        dj = os.path.join(state, "dispatcher.jsonl")
        # the shared default read still carries the paper book
        pos, _spend = journal_derived(dj)
        self.assertEqual(pos[BREAKOUT]["ENJ/USD"], 100)
        ppos, pspend = journal_paper_book(dj)
        self.assertEqual(ppos[BREAKOUT]["ENJ/USD"], 100)
        self.assertAlmostEqual(pspend[BREAKOUT], 2.0)
        rep = reconcile(state, {}, None, None)
        self.assertTrue(rep["ok"], rep["discrepancies"])
        self.assertEqual(rep["halted_sleeves"], [])
        self.assertFalse(rep["cash_halt"])
        self.assertEqual(
            rep["paper_book"]["positions"][BREAKOUT]["ENJ/USD"],
            100)

    def test_own_book_view_serves_the_paper_position(self):
        from desk3.cycle import own_book_positions
        tmp, state = self._state_with_paper_fill()
        sleeves = {BREAKOUT: {"own_book_view": True},
                   "plain": {}}
        out = own_book_positions(
            sleeves, os.path.join(state, "dispatcher.jsonl"))
        self.assertEqual(set(out), {BREAKOUT})
        rows = out[BREAKOUT]
        # the book is served in every dialect the class's engines
        # read (canonical ENJ/USD, aster ENJUSDT, free_kraken
        # ENJUSD), each carrying the journal-derived opened_at
        by_sym = {r["symbol"]: r for r in rows}
        self.assertEqual(set(by_sym),
                         {"ENJ/USD", "ENJUSDT", "ENJUSD"})
        for r in rows:
            self.assertEqual(r["qty"], 100)
            self.assertAlmostEqual(r["avg_price"], 0.02)
            self.assertEqual(r["opened_at"],
                             "2026-11-16T15:00:00+00:00")

    def test_free_kraken_sees_its_paper_position_and_stops(self):
        # The in-family instance end to end: with its paper
        # position served in its native ENJUSD key, the sleeve's
        # strategy reads the position (no second entry intent);
        # pre-cure the journal form ENJ/USD missed its ENJUSD key
        # and it re-entered every evaluation.
        from desk3.strategies import free_kraken_enj_spot as strat
        from desk3.contract import Context
        book = {"bids": [["0.01935", "15350", 1]] * 10,
                "asks": [["0.01941", "3847.451", 1]] * 10}
        now = 1794840900.0
        ctx = Context(now=now, session="2026-11-16",
                      equity=10000.0, extra={"book": book})
        flat = strat.signal({}, {}, ctx)
        self.assertEqual(len(flat), 1)  # entry while flat
        held = strat.signal({}, {"ENJUSD": 516795.0}, ctx)
        self.assertEqual(held, [])  # held: no re-entry, no exit due
        blind = strat.signal({}, {"ENJ/USD": 516795.0}, ctx)
        self.assertEqual(len(blind), 1,
                         "the ENJ/USD key alone is the pre-cure "
                         "blindness this landing cures at the "
                         "own-book seam")


class TestGraderSeesPaperFills(unittest.TestCase):
    def test_loader_accepts_paper_fill_terminal_rows(self):
        from desk3.conversion_shadow import load_intent_entries
        tmp = tempfile.mkdtemp()
        state = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state, "s_enj"))
        rows = [
            {"event": "fill", "intent_id": "p1", "sleeve": "s_enj",
             "symbol": "ENJ/USD", "side": "buy", "qty": 3,
             "price": 0.02, "venue": "kraken_paper",
             "position_intent": "buy_to_open"},
            {"event": "fill", "intent_id": "p2", "sleeve": "s_enj",
             "symbol": "ENJ/USD", "side": "sell", "qty": 3,
             "price": 0.03, "venue": "kraken_paper",
             "position_intent": "sell_to_close"},
            {"event": "fill", "intent_id": "b1", "sleeve": "s_enj",
             "symbol": "SPY", "side": "buy", "qty": 1,
             "price": 100.0, "position_intent": "buy_to_open"},
        ]
        with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        with open(os.path.join(state, "s_enj", "journal.jsonl"),
                  "w") as fh:
            for iid in ("p1", "p2", "b1"):
                fh.write(json.dumps(
                    {"event": "intent", "intent_id": iid,
                     "ts": "2026-11-16T15:00:00+00:00"}) + "\n")
        entries = load_intent_entries(tmp, "2026-11-16", {"s_enj"})
        self.assertEqual({e["intent_id"] for e in entries}, {"p1"})
        self.assertEqual(entries[0]["dir"], 1)


class TestFeedProvenance(unittest.TestCase):
    def test_producer_stamps_enj_provenance(self):
        import urllib.parse as up
        from datetime import datetime, timezone
        import desk3.producers3 as p3
        now = datetime(2026, 11, 16, 15, 0, tzinfo=timezone.utc)

        def transport(url):
            if "tickers" in url:
                return {"tickers": []}
            if "Depth" in url:
                return {"error": [], "result": {"ENJUSD": {
                    "bids": [["0.10", "5", 1]],
                    "asks": [["0.11", "5", 1]]}}}
            pair = up.parse_qs(
                up.urlparse(url).query).get("pair", [""])[0]
            rows = [[1767225600 + 14400 * i, "0.10", "0.11",
                     "0.09", "0.105", "0.10", "10", 0]
                    for i in range(24)]
            return {"error": [], "result": {pair: rows, "last": 0}}

        out = p3.KrakenProducer(tempfile.mkdtemp(),
                                transport=transport)({"now": now})
        self.assertIn("kraken.enj_provenance",
                      p3.KrakenProducer.OUTPUTS)
        prov = out["kraken.enj_provenance"]
        self.assertEqual(prov["source"], "kraken_public_rest")
        self.assertEqual(prov["pair"], "ENJUSD")
        self.assertEqual(prov["captured_at"], now.isoformat())
        self.assertIn("epoch", prov["timestamp_basis"])
        self.assertGreaterEqual(prov["bars_4hour"], 20)


if __name__ == "__main__":
    unittest.main()
