"""VIRTUAL-BOOK live staging blockers (NO-PARTIALS DRIVE, 2026-11-11).

The shadow derivation (desk3/virtual_book.py) existed; the defect
stayed live because nothing in the live path read it. This file pins
the staged adoption in desk3/dispatcher.py + desk3/cycle.py:

- log mode: every exit is dual-read against the sleeve's own
  journal-derived book; divergences are journaled and censused;
  decisions are EXACTLY the pre-cure aggregate behaviour.
- canary mode: enforcement for the named sleeves only: an exit for a
  position the sleeve does not own terminates locally as
  exit_satisfied_no_sleeve_position and never reaches the broker
  (the 42210000 class at its source); an oversized exit is clamped
  to the sleeve's own quantity.
- fleet mode: the same enforcement for every sleeve.

Fail direction: against the pre-drive tree the Dispatcher takes no
virtual_book_mode argument (TypeError on construction), carries no
dual-read journal rows, and a canary sleeve's phantom exit reaches
the broker (submit_count 1 where the cured tree submits 0).
"""

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from desk3 import virtual_book  # noqa: E402
from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402


class LiveFakeBroker(FakeBroker):
    live_book = True


def _root_with_fills(fills):
    root = tempfile.mkdtemp(prefix="vbook-")
    state = os.path.join(root, "state")
    os.makedirs(state)
    with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
        for row in fills:
            fh.write(json.dumps(row) + "\n")
    return root


def _fill(sleeve, symbol, side, qty, iid):
    return {"event": "fill", "sleeve": sleeve, "symbol": symbol,
            "side": side, "qty": qty, "intent_id": iid,
            "client_order_id": "c-" + iid, "price": 100.0,
            "ts": "2026-11-11T15:00:00+00:00"}


def _exit(iid, symbol, side, qty, pintent):
    return {"intent_id": iid, "kind": "exit", "symbol": symbol,
            "side": side, "qty": qty, "order_type": "market",
            "position_intent": pintent, "time_in_force": "day",
            "limit_price": None, "stop_price": None, "price_hint": None}


def _journal_rows(root):
    path = os.path.join(root, "state", "dispatcher.jsonl")
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class TestDerivationFromJournals(unittest.TestCase):
    def test_streams_generations_and_skips_torn_lines(self):
        root = tempfile.mkdtemp(prefix="vbook-gen-")
        p_old = os.path.join(root, "dispatcher.jsonl.1")
        p_new = os.path.join(root, "dispatcher.jsonl")
        with open(p_old, "w") as fh:
            fh.write(json.dumps(_fill("a", "SPY", "buy", 10.0, "a-1")) + "\n")
            fh.write('{"event":"fill","sleeve":"a","sym')  # torn tail
        with open(p_new, "w") as fh:
            fh.write(json.dumps(_fill("a", "SPY", "sell", 4.0, "a-2")) + "\n")
            fh.write(json.dumps(_fill("b", "SPY", "buy", 13.0, "b-1")) + "\n")
        book = virtual_book.derive_book_from_journals([p_old, p_new])
        self.assertEqual(
            virtual_book.sleeve_positions(book, "a"), {"SPY": 6.0})
        self.assertEqual(
            virtual_book.sleeve_positions(book, "b"), {"SPY": 13.0})

    def test_exit_divergence_kinds(self):
        rows = [_fill("owner", "SPY", "buy", 6.0, "o-1"),
                _fill("short", "QQQ", "sell", 5.0, "s-1")]
        book = virtual_book.derive_book(rows)
        d = virtual_book.exit_divergence(book, "other", "SPY", 13.0)
        self.assertEqual(d["kind"], "no_sleeve_position")
        d = virtual_book.exit_divergence(book, "owner", "SPY", 13.0)
        self.assertEqual(d["kind"], "qty_differs")
        d = virtual_book.exit_divergence(book, "short", "QQQ", 5.0)
        self.assertEqual(d["kind"], "sign_mismatch")
        self.assertIsNone(
            virtual_book.exit_divergence(book, "owner", "SPY", 6.0))
        self.assertIsNone(
            virtual_book.exit_divergence(book, "other", "SPY", 0.0))


class TestDualReadLogMode(unittest.TestCase):
    def test_log_mode_journals_divergence_and_changes_nothing(self):
        # The burst shape: broker holds 13 SPY owned by "owner";
        # "other" exits 13 against the aggregate, as sleeves did.
        root = _root_with_fills([_fill("owner", "SPY", "buy", 13.0, "o-1")])
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"SPY": 13.0}
        d = Dispatcher(root, b, slices={}, virtual_book_mode="log")
        r = d.process_intent(
            _exit("x-1", "SPY", "sell", 13.0, "sell_to_close"), "other")
        # Pre-cure behaviour preserved in log mode: the exit submits.
        self.assertEqual(r["status"], "submitted")
        self.assertEqual(b.submit_count, 1)
        dual = [row for row in _journal_rows(root)
                if row.get("event") == "virtual_book_dual_read"]
        self.assertEqual(len(dual), 1)
        self.assertEqual(dual[0]["kind"], "no_sleeve_position")
        self.assertEqual(dual[0]["sleeve"], "other")
        census = d.virtual_book_census()
        self.assertEqual(census["mode"], "log")
        self.assertEqual(census["dual_read_divergences"], 1)


class TestCanaryEnforcement(unittest.TestCase):
    def test_canary_sleeve_phantom_exit_never_reaches_broker(self):
        root = _root_with_fills([_fill("owner", "SPY", "buy", 13.0, "o-1")])
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"SPY": 13.0}
        d = Dispatcher(root, b, slices={}, virtual_book_mode="canary",
                       virtual_book_canaries={"other"})
        r = d.process_intent(
            _exit("x-1", "SPY", "sell", 13.0, "sell_to_close"), "other")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_satisfied_no_sleeve_position")
        self.assertEqual(b.submit_count, 0)

    def test_non_canary_sleeve_keeps_aggregate_behaviour(self):
        root = _root_with_fills([_fill("owner", "SPY", "buy", 13.0, "o-1")])
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"SPY": 13.0}
        d = Dispatcher(root, b, slices={}, virtual_book_mode="canary",
                       virtual_book_canaries={"someone_else"})
        r = d.process_intent(
            _exit("x-1", "SPY", "sell", 13.0, "sell_to_close"), "other")
        self.assertEqual(r["status"], "submitted")
        self.assertEqual(b.submit_count, 1)

    def test_canary_exit_clamped_to_the_sleeves_own_quantity(self):
        # Owner derived 6 of the aggregate 13; its exit for 13 is
        # clamped to its own 6 on the wire.
        root = _root_with_fills([_fill("owner", "SPY", "buy", 6.0, "o-1"),
                                 _fill("other", "SPY", "buy", 7.0, "t-1")])
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"SPY": 13.0}
        d = Dispatcher(root, b, slices={}, virtual_book_mode="canary",
                       virtual_book_canaries={"owner"})
        r = d.process_intent(
            _exit("x-1", "SPY", "sell", 13.0, "sell_to_close"), "owner")
        self.assertEqual(r["status"], "submitted")
        order = list(b.orders.values())[0]
        self.assertEqual(order["qty"], 6.0)

    def test_fleet_mode_enforces_for_every_sleeve(self):
        root = _root_with_fills([_fill("owner", "SPY", "buy", 13.0, "o-1")])
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"SPY": 13.0}
        d = Dispatcher(root, b, slices={}, virtual_book_mode="fleet")
        r = d.process_intent(
            _exit("x-1", "SPY", "sell", 13.0, "sell_to_close"), "other")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_satisfied_no_sleeve_position")
        self.assertEqual(b.submit_count, 0)


class TestCycleWiring(unittest.TestCase):
    def test_cycle_reads_control_config_and_censuses_the_roll(self):
        import textwrap
        from datetime import datetime, timezone
        from desk3.cycle import Desk
        root = tempfile.mkdtemp(prefix="vbook-cycle-")
        os.makedirs(os.path.join(root, "config"))
        with open(os.path.join(root, "config", "virtual_book.json"),
                  "w") as fh:
            json.dump({"mode": "log", "canary_sleeves": []}, fh)
        fixdir = os.path.join(root, "fix")
        os.makedirs(fixdir)
        with open(os.path.join(fixdir, "good.py"), "w") as fh:
            fh.write(textwrap.dedent('''
                def evaluate(view, ctx):
                    return []
            '''))
        desk = Desk(root, broker=FakeBroker(prices={"SPY": 100.0}),
                    sleeve_path=fixdir, timeout_s=10.0)
        desk.add_producer(
            "bars",
            lambda ctx: {"bars": {"SPY": [
                {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
            outputs=("bars",), freshness_sla_s=3600)
        desk.add_sleeve("fed1", "good", inputs=("bars",), cadence_s=60,
                        slice_usd=10000.0)
        roll = desk.run_cycle(
            now=datetime(2026, 11, 11, 15, 0, tzinfo=timezone.utc))
        self.assertIn("virtual_book", roll)
        self.assertEqual(roll["virtual_book"]["mode"], "log")
        self.assertEqual(roll["virtual_book"]["dual_read_divergences"], 0)


if __name__ == "__main__":
    unittest.main()
