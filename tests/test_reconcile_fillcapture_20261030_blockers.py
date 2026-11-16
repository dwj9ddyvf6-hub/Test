"""RECONCILE-FILLCAPTURE-20261030 + DOOR-PREFLIGHT-20261030 blockers.

Root cause (RESEARCH-R1 B4, proven three ways): the dispatcher
recorded a fill only from ONE get_order_by_client_id read-back
issued immediately after submit, so every resting, pre-market or
post-restart fill was invisible to journal truth forever, and the
reconcile halt became self-sustaining (it fired on a FLAT broker
book on 2026-10-30, 275 rejects in one overnight window). The cure:
a pre-reconcile sweep imports the missing fills from the broker
(the system of record) exactly once, under original attribution;
journal_derived reads both journal generations like producers3;
halt reject rows carry their discrepancy context; the per-cycle
report persists to state/reconcile_last.json. Plus the door
pre-flight validator and the terminal-422 journal event.

Fail direction: on the pre-cure tree sweep_unjournaled_fills and
desk3/broker_dialect do not exist (import errors), journal_derived
ignores dispatcher.jsonl.1 (the split-generation test returns only
half the position), a late fill produces a DISCREPANCY reconcile
(the flat-book test), halt rows carry no discrepancies key, and a
"AG|1Hour" entry is submitted to the broker instead of being
rejected locally. Every test below fails there.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker
from desk3.dispatcher import Dispatcher
from desk3.journal import append_line, read_lines
from desk3.reconcile import journal_derived, reconcile, \
    sweep_unjournaled_fills


class LateFillBroker(FakeBroker):
    """Fills only on the SECOND read-back of an order: the exact
    shape that defeated the submit-time single read-back."""

    def __init__(self, prices=None):
        super().__init__(prices=prices or {}, fill_mode="pending")
        self.reads = {}

    def get_order_by_client_id(self, coid):
        self.reads[coid] = self.reads.get(coid, 0) + 1
        order = dict(self.orders[coid])
        if self.reads[coid] >= 2:
            order["status"] = "filled"
            order["filled_qty"] = order["qty"]
            order["filled_avg_price"] = self.prices.get(
                order["symbol"], 0.0)
            order["filled_at"] = "2026-10-30T14:00:00+00:00"
            if not order.get("_applied"):
                signed = float(order["qty"]) * (
                    1 if order["side"] == "buy" else -1)
                sym = order["symbol"]
                self.positions[sym] = self.positions.get(sym, 0.0) \
                    + signed
                if abs(self.positions[sym]) <= 1e-9:
                    del self.positions[sym]
                self.orders[coid]["_applied"] = True
        return order


def _root():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    return root


def _entry(iid, sym="AXTI", qty=10, **kw):
    d = {"intent_id": iid, "kind": "entry", "symbol": sym,
         "side": "buy", "qty": qty, "order_type": "market",
         "limit_price": None, "price_hint": 10.0,
         "time_in_force": "day", "position_intent": "buy_to_open"}
    d.update(kw)
    return d


SLICES = {"s1": {"capital_usd": 100000.0, "cash_usd": 100000.0}}


class TestSweepImportsLateFill(unittest.TestCase):
    def test_late_fill_imported_once_and_reconcile_clears(self):
        root = _root()
        broker = LateFillBroker(prices={"AXTI": 10.0})
        disp = Dispatcher(root, broker, slices=dict(SLICES),
                          price_lookup=lambda s: 10.0)
        r = disp.process_intent(_entry("late-1"), "s1")
        # Submit-time read-back: not yet filled, no fill row. This
        # is the pre-cure end state, permanently.
        self.assertEqual(r["status"], "submitted")
        self.assertEqual(
            [x for x in disp.journal_events()
             if x["event"] == "fill"], [])
        # The hole, proven the pre-cure way: reconcile disagrees.
        state = os.path.join(root, "state")
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "w") as fh:
            json.dump({"positions": {}, "cash_offset_usd": 0.0}, fh)
        rep0 = reconcile(state, {"AXTI": 10.0},
                         broker_cash=100000.0,
                         slice_capital={"s1": 100000.0})
        self.assertEqual(rep0["status"], "DISCREPANCY")
        # The sweep imports the fill from the broker, exactly once.
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out["imported_rows"], 1)
        self.assertEqual(out["errors"], [])
        fills = [x for x in read_lines(disp.djournal)
                 if x["event"] == "fill"]
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["qty"], 10.0)
        self.assertEqual(fills[0]["sleeve"], "s1")
        self.assertTrue(fills[0]["imported"])
        self.assertTrue(fills[0]["broker_order_id"])
        out2 = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out2["imported_rows"], 0)  # idempotent
        rep = reconcile(state, {"AXTI": 10.0},
                        broker_cash=99900.0,
                        slice_capital={"s1": 100000.0})
        self.assertEqual(rep["status"], "OK", rep)
        self.assertEqual(rep["halted_sleeves"], [])

    def test_partial_fill_journals_cumulative_deltas(self):
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal, {
            "event": "order_submitted", "intent_id": "p-1",
            "sleeve": "s1", "client_order_id": "v3-s1-p-1",
            "symbol": "AXTI"})
        broker = LateFillBroker(prices={"AXTI": 10.0})
        broker.orders["v3-s1-p-1"] = {
            "id": "ord-1", "client_order_id": "v3-s1-p-1",
            "symbol": "AXTI", "side": "buy", "qty": 100,
            "status": "partially_filled", "filled_qty": 40.0,
            "filled_avg_price": 10.0,
            "filled_at": "2026-10-30T14:00:00+00:00"}
        # Force the read-back to report the resting partial state
        # instead of the fixture's second-read fill.
        broker.get_order_by_client_id = lambda coid: dict(
            broker.orders[coid])
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out["imported_rows"], 1)
        broker.orders["v3-s1-p-1"]["filled_qty"] = 100.0
        broker.orders["v3-s1-p-1"]["status"] = "filled"
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out["imported_rows"], 1)
        qtys = [x["qty"] for x in read_lines(djournal)
                if x["event"] == "fill"]
        self.assertEqual(qtys, [40.0, 60.0])
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out["imported_rows"], 0)

    def test_flat_book_halt_clears_after_sweep(self):
        # The 2026-10-30 overnight shape: an exit fills late, the
        # broker book goes flat, journal truth stays stale, and the
        # halt fires on nothing. Sweep, then reconcile: OK.
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal, {
            "event": "fill", "intent_id": "open-1", "sleeve": "s1",
            "client_order_id": "v3-s1-open-1", "symbol": "AXTI",
            "side": "buy", "qty": 10.0, "price": 10.0,
            "ts": "2026-10-30T13:00:00+00:00"})
        append_line(djournal, {
            "event": "order_submitted", "intent_id": "close-1",
            "sleeve": "s1", "client_order_id": "v3-s1-close-1",
            "symbol": "AXTI"})
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "w") as fh:
            json.dump({"positions": {}, "cash_offset_usd": 0.0}, fh)
        broker = LateFillBroker(prices={"AXTI": 10.0})
        broker.orders["v3-s1-close-1"] = {
            "id": "ord-9", "client_order_id": "v3-s1-close-1",
            "symbol": "AXTI", "side": "sell", "qty": 10,
            "status": "accepted", "filled_qty": 0}
        broker.reads["v3-s1-close-1"] = 1  # next read fills it
        rep0 = reconcile(state, {}, broker_cash=None,
                         slice_capital=None)
        self.assertEqual(rep0["status"], "DISCREPANCY")
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out["imported_rows"], 1)
        rep = reconcile(state, {}, broker_cash=None,
                        slice_capital=None)
        self.assertEqual(rep["status"], "OK", rep)


class TestCashReconcile(unittest.TestCase):
    """CASH-RECONCILE-20261030: the cash leg had two proven defects
    beyond fill capture. (1) The formula used the LIVE roster slice
    sum against an offset recorded under the record-era roster:
    adding sleeves manufactured discrepancies (live proof: 23
    sleeves added after the 2026-10-26 baseline, +230,000.00 of
    phantom expected cash, exactly the observed residue less fees).
    (2) Broker regulatory fees (CAT/REG FEE activities, -223.71
    live this epoch) move cash without fills. Fail direction: on
    the pre-cure formula the roster-growth test halts on phantom
    cash, and the fees test has no parameter to pass (TypeError).
    """

    def _state_with_baseline(self, caps, cash):
        root = _root()
        state = os.path.join(root, "state")
        rep = reconcile(state, {}, broker_cash=cash,
                        slice_capital=caps, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED")
        return state

    def test_roster_growth_after_baseline_is_cash_neutral(self):
        state = self._state_with_baseline({"s1": 1000.0}, 1000.0)
        rep = reconcile(state, {}, broker_cash=1000.0,
                        slice_capital={"s1": 1000.0, "s2": 5000.0})
        self.assertEqual(rep["status"], "OK", rep)
        self.assertFalse(rep["cash_halt"])

    def test_broker_fees_enter_cash_expectation(self):
        state = self._state_with_baseline({"s1": 1000.0}, 1000.0)
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal, {
            "event": "fill", "intent_id": "f-1", "sleeve": "s1",
            "client_order_id": "c1", "symbol": "AXTI",
            "side": "buy", "qty": 10.0, "price": 10.0})
        # Broker cash = capital - spend - fees = 1000 - 100 - 2.50.
        rep = reconcile(state, {"AXTI": 10.0}, broker_cash=897.50,
                        slice_capital={"s1": 1000.0},
                        broker_fees_usd=-2.50)
        self.assertEqual(rep["status"], "OK", rep)
        rep2 = reconcile(state, {"AXTI": 10.0}, broker_cash=897.50,
                         slice_capital={"s1": 1000.0})
        self.assertTrue(rep2["cash_halt"])  # fees unexplained: halts

    def test_fees_unavailable_skips_cash_check_by_name(self):
        state = self._state_with_baseline({"s1": 1000.0}, 1000.0)
        rep = reconcile(state, {}, broker_cash=1.0,
                        slice_capital={"s1": 1000.0},
                        broker_fees_usd=None)
        self.assertFalse(rep["cash_halt"])
        self.assertEqual(rep["cash_check"], "skipped_fees_unavailable")
        self.assertEqual(
            [d for d in rep["discrepancies"] if d["kind"] == "cash"],
            [])


class TestPositionDialect(unittest.TestCase):
    """POSITION-DIALECT-20261030: the broker positions endpoint
    reports crypto as BTCUSD/LINKUSD (bare) while orders and the
    journal carry BTC/USD. Proven live in the first cured trading
    cycle (2026-10-31T02:58Z reconcile): one real position became
    two phantom discrepancies and the broker leg was attributed
    baseline_or_unknown. Fail direction: pre-cure, the equal-qty
    test below reports DISCREPANCY with two position rows."""

    def test_bare_broker_crypto_key_matches_journal_slash_key(self):
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal, {
            "event": "fill", "intent_id": "d-1", "sleeve": "s1",
            "client_order_id": "c1", "symbol": "LINK/USD",
            "side": "buy", "qty": 86.0, "price": 11.566})
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "w") as fh:
            json.dump({"positions": {}, "cash_offset_usd": 0.0}, fh)
        rep = reconcile(state, {"LINKUSD": 86.0}, broker_cash=None,
                        slice_capital=None)
        self.assertEqual(rep["status"], "OK", rep)

    def test_dialect_match_attributes_to_journal_sleeve(self):
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal, {
            "event": "fill", "intent_id": "d-2", "sleeve": "s1",
            "client_order_id": "c2", "symbol": "BTC/USD",
            "side": "buy", "qty": 0.064654274, "price": 77313.06})
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "w") as fh:
            json.dump({"positions": {}, "cash_offset_usd": 0.0}, fh)
        # The broker's net-of-in-kind-fee qty (0.25 percent, the
        # separate named item): the SYMBOL must now match, so the
        # one remaining discrepancy is attributed to the sleeve,
        # never baseline_or_unknown, and names BTC/USD.
        rep = reconcile(state, {"BTCUSD": 0.064492637},
                        broker_cash=None, slice_capital=None)
        self.assertEqual(len(rep["discrepancies"]), 1)
        d = rep["discrepancies"][0]
        self.assertEqual(d["symbol"], "BTC/USD")
        self.assertEqual(d["attribution"], "journal_sleeves")
        self.assertEqual(d["sleeves"], ["s1"])


class TestCryptoFeeInKind(unittest.TestCase):
    """CRYPTO-FEE-INKIND-20261030: the broker withholds the crypto
    taker fee in the asset on buys (live proof 2026-10-31: BTC
    0.064654274 filled vs 0.064492637 held, LINK 86 vs 85.785,
    dust value 14.99 equal to the whole cash gap). The sweep
    MEASURES journal-gross minus broker-net once the symbol's
    orders are all terminal and journals it as a named fee row;
    it never models a rate. Fail direction: pre-cure there is no
    fee row and the dust discrepancy stands forever."""

    def _fee_state(self):
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal, {
            "event": "order_submitted", "intent_id": "f-1",
            "sleeve": "s1", "client_order_id": "fc1",
            "symbol": "BTC/USD", "side": "buy", "qty": 0.064654274})
        append_line(djournal, {
            "event": "fill", "intent_id": "f-1", "sleeve": "s1",
            "client_order_id": "fc1", "symbol": "BTC/USD",
            "side": "buy", "qty": 0.064654274, "price": 77313.06,
            "ts": "2026-10-30T00:00:00+00:00"})
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "w") as fh:
            json.dump({"positions": {}, "cash_offset_usd": 0.0}, fh)
        broker = FakeBroker(prices={"BTC/USD": 77313.06},
                            fill_mode="filled")
        broker.orders = {"fc1": {
            "client_order_id": "fc1", "id": "fo1",
            "symbol": "BTC/USD", "side": "buy",
            "qty": 0.064654274, "_applied": True}}
        broker.positions = {"BTCUSD": 0.064492637}
        return state, broker

    def test_dust_measured_journaled_and_reconcile_clears(self):
        state, broker = self._fee_state()
        res = sweep_unjournaled_fills(state, broker)
        self.assertEqual(res["fee_adjustments"], 1, res)
        self.assertAlmostEqual(res["fee_dust"]["BTC/USD"],
                               0.000161637, places=9)
        rep = reconcile(state, {"BTCUSD": 0.064492637},
                        broker_cash=None, slice_capital=None)
        self.assertEqual(rep["status"], "OK", rep)
        # Idempotent: a second sweep measures nothing left.
        res2 = sweep_unjournaled_fills(state, broker)
        self.assertEqual(res2["fee_adjustments"], 0, res2)

    def test_live_order_symbol_is_never_dust_adjusted(self):
        state, broker = self._fee_state()
        broker.fill_mode = "resting"  # order reads back not-filled
        res = sweep_unjournaled_fills(state, broker)
        self.assertEqual(res["fee_adjustments"], 0, res)


class TestJournalReaderContract(unittest.TestCase):
    def test_fills_split_across_generations_reconcile(self):
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        append_line(djournal + ".1", {
            "event": "fill", "intent_id": "g-1", "sleeve": "s1",
            "client_order_id": "c1", "symbol": "AXTI",
            "side": "buy", "qty": 5.0, "price": 10.0})
        append_line(djournal, {
            "event": "fill", "intent_id": "g-2", "sleeve": "s1",
            "client_order_id": "c2", "symbol": "AXTI",
            "side": "buy", "qty": 7.0, "price": 10.0})
        positions, spend = journal_derived(djournal, epoch_start=False)
        self.assertEqual(positions, {"s1": {"AXTI": 12.0}})
        self.assertEqual(spend, {"s1": 120.0})


class TestHaltContext(unittest.TestCase):
    def test_reconcile_halt_row_names_the_discrepancy(self):
        root = _root()
        disp = Dispatcher(root, FakeBroker(), slices=dict(SLICES),
                          price_lookup=lambda s: 10.0)
        disp.halted_sleeves = {"s1"}
        disp.reconcile_report = {
            "status": "DISCREPANCY",
            "discrepancies": [{
                "kind": "position_qty", "symbol": "AXTI",
                "expected_qty": -7011.0, "broker_qty": -13414.0,
                "sleeves": ["s1"], "attribution": "journal_sleeves"}],
            "halted_sleeves": ["s1"], "cash_halt": False}
        r = disp.process_intent(_entry("h-1"), "s1")
        self.assertEqual(r["reason"], "reconcile_halt")
        rows = [x for x in disp.journal_events()
                if x["event"] == "intent_rejected"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "AXTI")
        self.assertEqual(rows[0]["discrepancies"][0]["expected_qty"],
                         -7011.0)
        self.assertEqual(rows[0]["discrepancies"][0]["broker_qty"],
                         -13414.0)
        self.assertFalse(rows[0]["cash_halt"])


class TestDoorPreflight(unittest.TestCase):
    def _disp(self, broker):
        return Dispatcher(_root(), broker, slices=dict(SLICES),
                          price_lookup=lambda s: 10.0)

    def test_timeframe_suffix_rejected_before_the_wire(self):
        broker = FakeBroker(prices={"AG": 10.0})
        disp = self._disp(broker)
        r = disp.process_intent(_entry("pf-1", sym="AG|1Hour"), "s1")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"],
                         "preflight_symbol_timeframe_suffix")
        self.assertEqual(broker.submit_count, 0)

    def test_market_with_limit_price_rejected(self):
        broker = FakeBroker()
        disp = self._disp(broker)
        r = disp.process_intent(
            _entry("pf-2", limit_price=10.0), "s1")
        self.assertEqual(r["reason"],
                         "preflight_market_with_limit_price")
        self.assertEqual(broker.submit_count, 0)

    def test_invalid_position_intent_rejected(self):
        broker = FakeBroker()
        disp = self._disp(broker)
        r = disp.process_intent(
            _entry("pf-3", position_intent="buy_to_party"), "s1")
        self.assertEqual(r["reason"],
                         "preflight_position_intent_invalid")
        self.assertEqual(broker.submit_count, 0)

    def test_untranslatable_dialect_rejected(self):
        broker = FakeBroker()
        disp = self._disp(broker)
        r = disp.process_intent(_entry("pf-4", sym="FOOUSDT"), "s1")
        self.assertEqual(r["reason"],
                         "preflight_symbol_untranslatable_dialect")
        self.assertEqual(broker.submit_count, 0)

    def test_kraken_perp_shape_is_not_a_pair_shape(self):
        # PF_ADAUSD is a Kraken perp contract symbol, not a crypto
        # pair dialect: the narrowed preflight passes it exactly as
        # pre-cure (the kraken e2e contract in
        # test_harden_cure_batch3_blockers dispatches it). Caught
        # by the first full gate run of this cure, narrowed same
        # pass; this blocker pins the narrowing.
        broker = FakeBroker(prices={"PF_ADAUSD": 1.01},
                            fill_mode="filled")
        disp = self._disp(broker)
        r = disp.process_intent(
            _entry("pf-6", sym="PF_ADAUSD", qty=1), "s1")
        self.assertEqual(r["status"], "filled")
        self.assertEqual(broker.submit_count, 1)

    def test_crypto_entry_normalized_and_submitted(self):
        broker = FakeBroker(prices={"ADA/USD": 10.0},
                            fill_mode="filled")
        disp = self._disp(broker)
        r = disp.process_intent(
            _entry("pf-5", sym="ADAUSDT", qty=5.0), "s1")
        self.assertEqual(r["status"], "filled")
        (order,) = list(broker.orders.values())
        self.assertEqual(order["symbol"], "ADA/USD")

    def test_historical_422_payloads_all_caught_locally(self):
        # The captured Oct 27 payloads replayed: suffixed equity,
        # dashed crypto with day TIF (translated, then clean), and
        # the Oct 29 ADAUSDT entry (translated, then clean). Only
        # the suffixed one may reject; the other two must reach the
        # wire in broker dialect.
        broker = FakeBroker(prices={"BTC/USD": 10.0, "ADA/USD": 10.0},
                            fill_mode="filled")
        disp = self._disp(broker)
        r1 = disp.process_intent(_entry("hx-1", sym="TE|1Week"), "s1")
        self.assertEqual(r1["status"], "rejected")
        r2 = disp.process_intent(
            _entry("hx-2", sym="BTC-USD", qty=0.5), "s1")
        self.assertEqual(r2["status"], "filled")
        r3 = disp.process_intent(
            _entry("hx-3", sym="ADAUSDT", qty=5.0), "s1")
        self.assertEqual(r3["status"], "filled")
        syms = sorted(o["symbol"] for o in broker.orders.values())
        self.assertEqual(syms, ["ADA/USD", "BTC/USD"])


class TestTerminal422Journal(unittest.TestCase):
    def test_422_gains_terminal_event_with_code_and_message(self):
        from desk3.netfetch import FetchError

        class Bad(FakeBroker):
            def submit_order(self, *a, **k):
                raise FetchError(
                    422, "https://paper-api.alpaca.markets/v2/orders",
                    body=json.dumps({"code": 42210000,
                                     "message": "asset not found"}))

        disp = Dispatcher(_root(), Bad(), slices=dict(SLICES),
                          price_lookup=lambda s: 10.0)
        r = disp.process_intent(_entry("t422-1", sym="ZZZZ9"), "s1")
        # READINESS-DSP1-20261112 supersession, named: the 422
        # verdict is consumed terminally (status "rejected",
        # never persisted to the pending store) instead of
        # "queued"; the terminal journal event this test exists
        # for is unchanged, asserted below.
        self.assertEqual(r["status"], "rejected")
        self.assertFalse(r["transient"])
        rows = disp.journal_events()
        term = [x for x in rows
                if x["event"] == "broker_rejected_terminal"]
        self.assertEqual(len(term), 1)
        self.assertEqual(term[0]["http_status"], 422)
        self.assertEqual(term[0]["broker_code"], 42210000)
        self.assertEqual(term[0]["broker_message"], "asset not found")
        # The drain-class contract is untouched: the
        # broker_unavailable row still exists for its readers.
        self.assertEqual(
            len([x for x in rows
                 if x["event"] == "broker_unavailable"]), 1)


class TestCanonicalTranslator(unittest.TestCase):
    def test_one_translator_for_door_and_aster_crypto(self):
        from desk3.broker_dialect import normalize_broker_symbol
        from desk3 import aster_crypto
        for spec in aster_crypto.SPECS.values():
            self.assertEqual(
                aster_crypto._broker_symbol(spec["sym"]),
                normalize_broker_symbol(spec["sym"]))
            self.assertTrue(
                normalize_broker_symbol(spec["sym"]).endswith("/USD"))
        self.assertEqual(normalize_broker_symbol("BTC-USD"), "BTC/USD")
        self.assertEqual(normalize_broker_symbol("ADAUSDT"), "ADA/USD")
        self.assertEqual(normalize_broker_symbol("ENJ/USD"), "ENJ/USD")
        self.assertEqual(normalize_broker_symbol("AXTI"), "AXTI")
        self.assertEqual(normalize_broker_symbol("BRK-B"), "BRK-B")


if __name__ == "__main__":
    unittest.main()
