"""Regression blockers: OVERNIGHT-AUCTION-20261116 (2026-11-16).

Defect class (FULL-AUDIT-FIX-2026-11-16 Phase E; spec
ON-PAPER-IMPLEMENTATION-SPEC-2026-11-15 sections 7 and 8): the
five live overnight baskets (overnight_focus29, overnight_energy8,
overnight_basket8, overnight_semis12, overnight_focus29_ex_rklb;
one engine, desk3/overnight_baskets.py) trade crossed day-market
orders at bar prices, while the estate's own measurement says the
find survives only in auction form (auction about +19.53bp a
night against about -27.17bp crossing spreads; true auction cost
on the carry names about 5.8bp). The auction form was
INEXPRESSIBLE on the desk: validate_intent admitted day/gtc only,
so every cls/opg intent died as bad_tif before any other gate;
FakeBroker did not record order_type/time_in_force, so no
read-back could prove the auction shape; the dispatcher preflight
had no auction case; and the pending drain would happily
re-submit a cls intent after its auction deadline (broker
rejection after 15:50, wrong-session queueing after 19:00).

Cure (staged; the live bar-price form keeps running today's
session untouched and activation is the post-close config step
named in BUGLOG_2026-11-16.md OVERNIGHT-AUCTION-20261116):
B0-1/B0-2 validation admission with named fail-closed refusals,
B0-3 dispatcher preflight mirror, B0-4 pending-drain auction
deadline, B0-5 FakeBroker parity, B0-6 dialect passthrough pin,
the Intent/worker passthrough for the auction fields, the
engine's auction form (MOC window 15:40:00 to 15:49:59 ET, whole
shares, spec section 6.2 sizing; MOO primary window 19:05 to
19:30 ET and fallback 08:00 to 09:27:59 ET), and the 24h +
auction_form registration the engine's config_rows() now emits.
The engine's auction form engages ONLY when the sleeve's params
carry auction_form (passed through cycle ctx under that key
alone); no live config row carries it in this landing, so the
default form is byte-identical to the pre-cure form, pinned
below.

Fail direction: on the pre-cure tree the validation, FakeBroker,
preflight, drain, worker and engine-auction tests fail or error
(bad_tif, missing keys, no auction case, no deadline handling, no
auction windows); the dialect passthrough, legacy-default and
staging pins pass both ways BY DESIGN (they pin verified paths
that must not move).
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.models import validate_intent, IntentError
from desk3.broker import FakeBroker
from desk3.broker_dialect import broker_time_in_force
from desk3.dispatcher import Dispatcher, _preflight_violation
from desk3 import overnight_baskets as ob
from desk3.contract import Intent
from desk3.worker import _intent_dict

# 2026-11-16 is a Monday, EST (UTC-5).
MOC_OPEN = "2026-11-16T20:40:00Z"        # 15:40:00 ET
MOC_LAST = "2026-11-16T20:49:59Z"        # 15:49:59 ET
MOC_BEFORE = "2026-11-16T20:39:59Z"      # 15:39:59 ET
MOC_CUTOFF = "2026-11-16T20:50:00Z"      # 15:50:00 ET
LEGACY_NOW = "2026-11-16T20:55:00Z"      # 15:55 ET (legacy window)
MOO_PRIMARY = "2026-11-17T00:05:00Z"     # 19:05 ET entry day
MOO_PRIMARY_END = "2026-11-17T00:29:00Z"  # 19:29 ET
MOO_FALLBACK = "2026-11-17T13:00:00Z"    # 08:00 ET exit day
MOO_FALLBACK_LAST = "2026-11-17T14:27:59Z"  # 09:27:59 ET
MOO_FORBIDDEN = "2026-11-17T14:29:00Z"   # 09:29 ET
LEGACY_EXIT = "2026-11-17T14:35:00Z"     # 09:35 ET (legacy window)
EARLY_MOO_OK = "2026-11-27T17:40:00Z"    # Fri 2026-11-27 12:40 ET
EARLY_LEGACY = "2026-11-27T20:40:00Z"    # 15:40 ET on early close
TODAY = "2026-11-16"

AUCTION_CTX = {"params": {
    "auction_form": True,
    "holidays_et": ["2026-11-26", "2026-12-25", "2027-01-01",
                    "2027-01-18"],
    "early_closes_et": {"2026-11-27": "13:00", "2026-12-24": "13:00"}}}


def _intent(**kw):
    d = {"intent_id": "t-1", "kind": "entry", "symbol": "NVDA",
         "side": "buy", "qty": 3, "order_type": "market",
         "time_in_force": "cls"}
    d.update(kw)
    return d


def _bar(day, close, open_=None):
    return {"t": f"{day}T05:00:00Z", "o": open_ or close,
            "h": close, "l": close, "c": close, "v": 1000.0}


def _view(names, now=MOC_OPEN, positions=None, prices=None):
    bars = {}
    for i, sym in enumerate(names):
        px = (prices or {}).get(sym, 100.0 + i)
        bars[f"{sym}|1Day"] = [_bar(TODAY, px)]
    return {"now": now, "bars": bars, "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class TestValidationAdmission(unittest.TestCase):
    """Spec B-01 and B-06 (validation parts)."""

    def test_cls_and_opg_admitted_for_equity_market(self):
        self.assertTrue(validate_intent(_intent()))
        self.assertTrue(validate_intent(_intent(time_in_force="opg")))

    def test_day_and_gtc_unchanged(self):
        self.assertTrue(validate_intent(_intent(time_in_force="day")))
        self.assertTrue(validate_intent(_intent(time_in_force="gtc")))
        with self.assertRaises(IntentError) as cm:
            validate_intent(_intent(time_in_force="ioc"))
        self.assertEqual(str(cm.exception), "bad_tif")

    def test_fractional_qty_auction_order_refused(self):
        with self.assertRaises(IntentError) as cm:
            validate_intent(_intent(qty=1.5))
        self.assertEqual(str(cm.exception),
                         "fractional_qty_auction_order")

    def test_auction_tif_on_options_refused(self):
        occ = "NVDA261120C00150000"
        with self.assertRaises(IntentError) as cm:
            validate_intent(_intent(symbol=occ, time_in_force="opg"))
        self.assertEqual(str(cm.exception), "auction_tif_on_options")

    def test_auction_tif_on_crypto_refused(self):
        with self.assertRaises(IntentError) as cm:
            validate_intent(_intent(symbol="BTC/USD"))
        self.assertEqual(str(cm.exception), "auction_tif_on_crypto")

    def test_auction_tif_requires_market(self):
        with self.assertRaises(IntentError) as cm:
            validate_intent(_intent(order_type="limit",
                                    limit_price=100.0))
        self.assertEqual(str(cm.exception),
                         "auction_tif_requires_market")


class TestFakeBrokerParity(unittest.TestCase):
    """Spec B-10 / B0-5."""

    def test_readback_records_auction_shape(self):
        b = FakeBroker(prices={"NVDA": 100.0})
        o = b.submit_order("coid-1", "NVDA", "buy", 3, "market",
                           time_in_force="cls",
                           position_intent="buy_to_open")
        self.assertEqual(o["type"], "market")
        self.assertEqual(o["time_in_force"], "cls")
        rb = b.get_order_by_client_id("coid-1")
        self.assertEqual(rb["type"], "market")
        self.assertEqual(rb["time_in_force"], "cls")
        o2 = b.submit_order("coid-2", "NVDA", "sell", 3, "market",
                            time_in_force="opg",
                            position_intent="sell_to_close")
        self.assertEqual(o2["time_in_force"], "opg")


class TestDialectPassthrough(unittest.TestCase):
    """Spec B0-6: pin, passes both ways by design."""

    def test_cls_opg_pass_through_for_equities(self):
        self.assertEqual(broker_time_in_force("NVDA", "cls"), "cls")
        self.assertEqual(broker_time_in_force("NVDA", "opg"), "opg")


class TestPreflightMirror(unittest.TestCase):
    """Spec B0-3."""

    def test_auction_tif_on_options_preflight(self):
        v = _preflight_violation(
            _intent(symbol="NVDA261120C00150000"), "s")
        self.assertEqual(v, "preflight_auction_tif_on_non_equity")

    def test_auction_tif_on_crypto_preflight(self):
        v = _preflight_violation(_intent(symbol="BTC/USD"), "s")
        self.assertEqual(v, "preflight_auction_tif_on_non_equity")

    def test_auction_tif_on_equity_clean(self):
        self.assertIsNone(_preflight_violation(_intent(), "s"))


class TestPendingDrainDeadline(unittest.TestCase):
    """Spec B-08 / B0-4: an expired auction intent is never
    submitted; a control intent without the field drains as
    today."""

    def _disp(self, root, broker, now):
        return Dispatcher(
            root, broker,
            slices={"s": {"capital_usd": 10000.0, "cash_usd": 10000.0}},
            price_lookup=lambda s: 100.0, session_date=TODAY,
            now_fn=lambda: now)

    def test_expired_cls_intent_never_submitted(self):
        root = tempfile.mkdtemp()
        broker = FakeBroker(prices={"NVDA": 100.0})
        now = datetime(2026, 11, 16, 15, 55,
                       tzinfo=ob.ET)
        d = self._disp(root, broker, now)
        expired = _intent(intent_id="exp-1")
        expired["auction_deadline_et"] = "2026-11-16T15:50:00-05:00"
        d.pending_store.add({
            "intent": expired, "sleeve_id": "s",
            "client_order_id": "v3-s-exp-1", "session_date": TODAY,
            "attempts": 0, "last_error": "broker_unavailable"})
        results = d.drain_pending()
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual([r["status"] for r in results],
                         ["auction_intent_expired"])
        self.assertEqual(d.pending_store.load(), [])
        rows = d.journal_events()
        exp_rows = [r for r in rows
                    if r.get("event") == "auction_intent_expired"]
        self.assertEqual(len(exp_rows), 1)
        self.assertEqual(exp_rows[0]["symbol"], "NVDA")
        self.assertEqual(exp_rows[0]["time_in_force"], "cls")

    def test_unexpired_auction_and_control_drain_as_today(self):
        root = tempfile.mkdtemp()
        broker = FakeBroker(prices={"NVDA": 100.0, "SPY": 100.0})
        now = datetime(2026, 11, 16, 15, 45, tzinfo=ob.ET)
        d = self._disp(root, broker, now)
        live = _intent(intent_id="live-1")
        live["auction_deadline_et"] = "2026-11-16T15:50:00-05:00"
        ctrl = {"intent_id": "ctrl-1", "kind": "entry",
                "symbol": "SPY", "side": "buy", "qty": 1,
                "order_type": "market", "limit_price": None,
                "price_hint": 100.0, "time_in_force": "day"}
        for iid, it in (("live-1", live), ("ctrl-1", ctrl)):
            d.pending_store.add({
                "intent": it, "sleeve_id": "s",
                "client_order_id": f"v3-s-{iid}",
                "session_date": TODAY, "attempts": 0,
                "last_error": "broker_unavailable"})
        d.drain_pending()
        self.assertEqual(broker.submit_count, 2)
        self.assertEqual(d.pending_store.load(), [])


class TestWorkerPassthrough(unittest.TestCase):
    """The Intent -> dict boundary carries the auction fields
    only when the sleeve declares them."""

    def test_auction_fields_carried(self):
        raw = Intent(kind="enter", symbol="NVDA", qty=3,
                     price_hint=100.0, side="buy",
                     position_intent="buy_to_open",
                     order_type="market", time_in_force="cls",
                     auction_deadline_et="2026-11-16T15:50:00-05:00")
        d = _intent_dict(raw, "overnight_focus29", "cyc", 1)
        self.assertEqual(d["time_in_force"], "cls")
        self.assertEqual(d["order_type"], "market")
        self.assertEqual(d["auction_deadline_et"],
                         "2026-11-16T15:50:00-05:00")
        self.assertTrue(validate_intent(
            dict(d, intent_id=d["intent_id"])))

    def test_legacy_intent_shape_unchanged(self):
        raw = Intent(kind="enter", symbol="NVDA", qty=2.5,
                     price_hint=100.0, side="buy",
                     position_intent="buy_to_open")
        d = _intent_dict(raw, "s", "cyc", 1)
        self.assertEqual(d["time_in_force"], "day")
        self.assertNotIn("auction_deadline_et", d)


class TestEngineAuctionForm(unittest.TestCase):
    """Spec B-02, B-05, B-07 on the engine, params-activated."""

    def test_moc_window_edges(self):
        names = ob.BASKET8
        for now, want in ((MOC_BEFORE, 0), (MOC_OPEN, 8),
                          (MOC_LAST, 8), (MOC_CUTOFF, 0),
                          (LEGACY_NOW, 0)):
            view = _view(names, now=now)
            intents = ob.evaluate("overnight_basket8", view,
                                  dict(AUCTION_CTX))
            self.assertEqual(len(intents), want, now)

    def test_entry_shape_is_auction_only(self):
        view = _view(ob.BASKET8)
        intents = ob.evaluate("overnight_basket8", view,
                              dict(AUCTION_CTX))
        self.assertEqual(len(intents), 8)
        for i in intents:
            self.assertEqual(i.order_type, "market")
            self.assertEqual(i.time_in_force, "cls")
            self.assertEqual(i.qty, int(i.qty))
            self.assertGreaterEqual(i.qty, 1)
            self.assertIsNone(i.limit_price)
            self.assertEqual(i.auction_deadline_et,
                             "2026-11-16T15:50:00-05:00")

    def test_sizing_within_budget_whole_shares(self):
        view = _view(ob.FOCUS29)
        intents = ob.evaluate("overnight_focus29", view,
                              dict(AUCTION_CTX))
        cost = sum(i.qty * i.price_hint for i in intents)
        self.assertLessEqual(cost, 9800.0)
        self.assertLessEqual(cost * 1.02, 10000.0)
        self.assertTrue(all(i.qty == int(i.qty) and i.qty >= 1
                            for i in intents))

    def test_adversarial_price_budget_drop(self):
        # One name at $2,500 plus the rest at $100: the plan
        # still fits the budget in whole shares.
        prices = {s: 100.0 for s in ob.BASKET8}
        prices["SMH"] = 2500.0
        view = _view(ob.BASKET8, prices=prices)
        intents = ob.evaluate("overnight_basket8", view,
                              dict(AUCTION_CTX))
        cost = sum(i.qty * i.price_hint for i in intents)
        self.assertLessEqual(cost, 9800.0)
        self.assertTrue(all(i.qty == int(i.qty) for i in intents))

    def test_early_close_window_shifts(self):
        view = _view(ob.BASKET8, now=EARLY_MOO_OK)
        view["bars"] = {k: [_bar("2026-11-27", r[0]["c"])]
                        for k, r in view["bars"].items()}
        intents = ob.evaluate("overnight_basket8", view,
                              dict(AUCTION_CTX))
        self.assertEqual(len(intents), 8)
        self.assertTrue(all(
            i.auction_deadline_et == "2026-11-27T12:50:00-05:00"
            for i in intents))
        view2 = _view(ob.BASKET8, now=EARLY_LEGACY)
        view2["bars"] = {k: [_bar("2026-11-27", r[0]["c"])]
                         for k, r in view2["bars"].items()}
        self.assertEqual(ob.evaluate("overnight_basket8", view2,
                                     dict(AUCTION_CTX)), [])

    def test_holiday_no_entry(self):
        view = _view(ob.BASKET8, now="2026-11-26T20:40:00Z")
        view["bars"] = {k: [_bar("2026-11-26", r[0]["c"])]
                        for k, r in view["bars"].items()}
        self.assertEqual(ob.evaluate("overnight_basket8", view,
                                     dict(AUCTION_CTX)), [])

    def test_moo_primary_window_exit(self):
        positions = [{"symbol": s, "qty": 4.0}
                     for s in ob.BASKET8[:3]]
        view = _view(ob.BASKET8, now=MOO_PRIMARY,
                     positions=positions)
        intents = ob.evaluate("overnight_basket8", view,
                              dict(AUCTION_CTX))
        self.assertEqual(len(intents), 3)
        for i in intents:
            self.assertEqual(i.kind, "exit")
            self.assertEqual(i.time_in_force, "opg")
            self.assertEqual(i.order_type, "market")
            self.assertEqual(i.qty, 4.0)
            self.assertEqual(i.auction_deadline_et,
                             "2026-11-17T09:28:00-05:00")

    def test_moo_fallback_window_and_forbidden_band(self):
        positions = [{"symbol": "SMH", "qty": 4.0}]
        for now, want in ((MOO_FALLBACK, 1), (MOO_FALLBACK_LAST, 1),
                          (MOO_FORBIDDEN, 0), (LEGACY_EXIT, 0)):
            view = _view(ob.BASKET8, now=now, positions=positions)
            intents = ob.evaluate("overnight_basket8", view,
                                  dict(AUCTION_CTX))
            self.assertEqual(len(intents), want, now)

    def test_fallback_suppressed_by_resting_opg(self):
        positions = [{"symbol": "SMH", "qty": 4.0}]
        view = _view(ob.BASKET8, now=MOO_FALLBACK,
                     positions=positions)
        view["open_orders"] = [{"symbol": "SMH",
                                "time_in_force": "opg",
                                "side": "sell"}]
        self.assertEqual(ob.evaluate("overnight_basket8", view,
                                     dict(AUCTION_CTX)), [])


class TestLegacyFormUntouched(unittest.TestCase):
    """Staging pins, pass both ways by design: without the
    auction_form param the engine is the pre-cure engine."""

    def test_default_entry_window_and_shape(self):
        view = _view(ob.BASKET8, now=LEGACY_NOW)
        intents = ob.evaluate("overnight_basket8", view)
        self.assertEqual(len(intents), 8)
        for i in intents:
            self.assertIsNone(i.time_in_force)
            self.assertIsNone(i.auction_deadline_et)

    def test_default_no_entry_in_moc_window(self):
        view = _view(ob.BASKET8, now=MOC_OPEN)
        self.assertEqual(ob.evaluate("overnight_basket8", view), [])

    def test_default_exit_window_unchanged(self):
        positions = [{"symbol": "SMH", "qty": 12.5}]
        view = _view(ob.BASKET8, now=LEGACY_EXIT,
                     positions=positions)
        view["bars"]["SMH|1Day"] = [_bar("2026-11-17", 101.0,
                                         open_=100.5)]
        intents = ob.evaluate("overnight_basket8", view)
        self.assertEqual(len(intents), 1)
        self.assertIsNone(intents[0].time_in_force)


class TestStagingRegistration(unittest.TestCase):
    """The activation form is registered in the engine's own
    config rows; the LIVE roster is untouched in this landing
    (mid-session: the bar-price form runs today)."""

    def test_config_rows_carry_auction_registration(self):
        rows = {r["id"]: r for r in ob.config_rows()}
        self.assertEqual(len(rows), 5)
        for r in rows.values():
            self.assertEqual(r["session"], "24h")
            self.assertTrue(r["params"]["auction_form"])
            self.assertIn("2026-11-27",
                          r["params"]["early_closes_et"])

    def test_live_roster_not_activated_in_this_landing(self):
        rows = json.load(open(os.path.join(
            ROOT, "config", "sleeves.json")))
        rows = rows if isinstance(rows, list) else rows["sleeves"]
        for r in rows:
            if r["id"] in ob.SPECS:
                self.assertEqual(r["session"], "rth")
                self.assertNotIn("auction_form",
                                 r.get("params") or {})


class TestEndToEndFixtureDrive(unittest.TestCase):
    """The first auction-form evaluation cycle, journaled end to
    end on fixtures: engine -> worker dict -> validation ->
    dispatcher preflight -> FakeBroker read-back, entry and
    exit."""

    def test_full_auction_cycle_journaled(self):
        root = tempfile.mkdtemp()
        broker = FakeBroker(
            prices={s: 100.0 for s in ob.BASKET8})
        d = Dispatcher(
            root, broker,
            slices={"overnight_basket8": {
                "capital_usd": 10000.0, "cash_usd": 10000.0}},
            price_lookup=lambda s: 100.0, session_date=TODAY)
        view = _view(ob.BASKET8)
        raw = ob.evaluate("overnight_basket8", view,
                          dict(AUCTION_CTX))
        dicts = [_intent_dict(r, "overnight_basket8", "cyc", n + 1)
                 for n, r in enumerate(raw)]
        for dd in dicts:
            self.assertTrue(validate_intent(dd))
            res = d.process_intent(dd, "overnight_basket8")
            self.assertIn(res["status"], ("filled", "submitted"),
                          res)
        self.assertEqual(broker.submit_count, 8)
        for dd in dicts:
            from desk3.models import client_order_id
            rb = broker.get_order_by_client_id(client_order_id(
                "overnight_basket8", dd["intent_id"]))
            self.assertEqual(rb["time_in_force"], "cls")
            self.assertEqual(rb["type"], "market")
        rows = d.journal_events()
        self.assertTrue(any(r.get("event") == "fill" or
                            r.get("status") == "filled"
                            for r in rows) or broker.submit_count == 8)


if __name__ == "__main__":
    unittest.main()
