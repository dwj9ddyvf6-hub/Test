"""FEE-INKIND-CASH-TIMING-20261031 blockers.

Root cause (proven live 2026-10-31, deep-dive remainders round 2):
journal_derived folded a crypto_fee_in_kind row into SPEND the
moment the sweep journaled it. But the broker's cash does not move
for the in-kind fee while the position is open: the restarted
runner's first BTC/USD buy (fill 0.064759838 at 77089.154067275,
journaled fee dust 0.0001619 at the weighted buy price 77218.28,
value 12.5016) produced a live cash discrepancy of exactly the
dust's value across cycles 2 and 3 (expected 1072781.21 vs broker
1072793.73, cash_halt true), while the broker's own FILL
activities for that order sum to exactly the fill row's value
(4992.28, the entire cycle-over-cycle cash delta) and no FEE
activity exists. The three earlier fee rows sit on positions that
had fully CLOSED, and with them folded the same derivation tied
to the cent (cycle-1 reconcile OK, broker 1077786.01 vs expected
1077786.00). So the dust's cash value is real in the closed state
and a double count in the open state: the position fold (the
broker credits the net qty at fill time) stays immediate; the
spend fold lands only once the symbol's aggregate journal
position has fully closed.

Fail direction: on the pre-cure tree the open-position tests fail
(the fee's value is folded into spend at once, so the derived
spend overstates the broker's cash debit by the dust's value and
the reconcile cash leg halts); the closed-position test passes
there too (preservation: closed dust was, and stays, counted).
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.journal import append_line
from desk3.reconcile import journal_derived, reconcile


def _root():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    return root


def _fill(djournal, sleeve, side, qty, price, ts):
    append_line(djournal, {
        "event": "fill", "intent_id": "t-1", "sleeve": sleeve,
        "client_order_id": "tc", "symbol": "BTC/USD",
        "side": side, "qty": qty, "price": price, "ts": ts})


def _fee(djournal, sleeve, qty, price, ts):
    append_line(djournal, {
        "event": "crypto_fee_in_kind", "sleeve": sleeve,
        "symbol": "BTC/USD", "qty": qty, "price": price,
        "ts": ts, "imported": True})


class TestFeeCashTiming(unittest.TestCase):
    def test_open_position_fee_counts_position_not_spend(self):
        root = _root()
        djournal = os.path.join(root, "state", "dispatcher.jsonl")
        _fill(djournal, "s1", "buy", 0.064759838, 77089.154067275,
              "2026-10-31T04:47:40+00:00")
        _fee(djournal, "s1", 0.0001619, 77218.27870772722,
             "2026-10-31T04:53:44+00:00")
        positions, spend = journal_derived(djournal,
                                           epoch_start=False)
        # Position is net of the dust at once (the broker credits
        # the net qty at fill time).
        self.assertAlmostEqual(positions["s1"]["BTC/USD"],
                               0.064597938, places=9)
        # Spend is the fill's cash value only: the broker debited
        # exactly filled_qty x price (FILL activities, proven).
        self.assertAlmostEqual(spend["s1"], 4992.2811, places=4)

    def test_closed_position_fee_counts_spend(self):
        root = _root()
        djournal = os.path.join(root, "state", "dispatcher.jsonl")
        _fill(djournal, "s1", "buy", 0.064654274, 77313.06,
              "2026-10-31T02:55:31+00:00")
        _fill(djournal, "s2", "sell", 0.064492637, 77224.673747068,
              "2026-10-31T03:04:36+00:00")
        _fee(djournal, "s1", 0.000161637, 77313.06,
             "2026-10-31T03:10:42+00:00")
        positions, spend = journal_derived(djournal,
                                           epoch_start=False)
        total_pos = sum(p.get("BTC/USD", 0.0)
                        for p in positions.values())
        self.assertAlmostEqual(total_pos, 0.0, places=9)
        # Closed: the dust's value is part of net spend, as the
        # live derivation proved when it tied to the cent with
        # these rows folded (cycle-1, 2026-10-31T04:43Z).
        self.assertAlmostEqual(
            sum(spend.values()),
            0.064654274 * 77313.06 + 0.000161637 * 77313.06
            - 0.064492637 * 77224.673747068,
            places=6)

    def test_mixed_generations_same_symbol(self):
        # The live 2026-10-31 shape: one BTC/USD generation fully
        # closed (its fee counts), a second generation open in the
        # same symbol (its fee does not count yet). A symbol-level
        # final-state rule gets this wrong in both directions.
        root = _root()
        djournal = os.path.join(root, "state", "dispatcher.jsonl")
        _fill(djournal, "s1", "buy", 0.064654274, 77313.06,
              "2026-10-31T02:55:31+00:00")
        _fill(djournal, "s2", "sell", 0.064492637, 77224.673747068,
              "2026-10-31T03:04:36+00:00")
        _fee(djournal, "s1", 0.000161637, 77313.06,
             "2026-10-31T03:10:42+00:00")
        _fill(djournal, "s1", "buy", 0.064759838, 77089.154067275,
              "2026-10-31T04:47:40+00:00")
        _fee(djournal, "s1", 0.0001619, 77218.27870772722,
             "2026-10-31T04:53:44+00:00")
        positions, spend = journal_derived(djournal,
                                           epoch_start=False)
        total_pos = sum(p.get("BTC/USD", 0.0)
                        for p in positions.values())
        self.assertAlmostEqual(total_pos, 0.064597938, places=9)
        self.assertAlmostEqual(
            sum(spend.values()),
            0.064654274 * 77313.06 + 0.000161637 * 77313.06
            - 0.064492637 * 77224.673747068
            + 0.064759838 * 77089.154067275,
            places=6)

    def test_open_position_reconcile_cash_leg_ties(self):
        root = _root()
        state = os.path.join(root, "state")
        djournal = os.path.join(state, "dispatcher.jsonl")
        _fill(djournal, "s1", "buy", 0.064759838, 77089.154067275,
              "2026-10-31T04:47:40+00:00")
        _fee(djournal, "s1", 0.0001619, 77218.27870772722,
             "2026-10-31T04:53:44+00:00")
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "w") as fh:
            json.dump({"positions": {}, "cash_offset_usd": 0.0}, fh)
        # Broker cash = capital - the fill's cash value exactly;
        # the in-kind fee never moved cash (activities, proven).
        rep = reconcile(state, {"BTCUSD": 0.064597938},
                        broker_cash=10000.0 - 4992.2811,
                        slice_capital={"s1": 10000.0},
                        broker_fees_usd=0.0)
        self.assertEqual(rep["status"], "OK", rep)
        self.assertFalse(rep["cash_halt"], rep)


if __name__ == "__main__":
    unittest.main()
