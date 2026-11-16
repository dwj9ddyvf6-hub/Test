"""SLEEVE-VIRTUAL-BOOK-DIVERGENCE blockers (2026-11-11, FIX-ALL WAVE).

The defect: sleeves read the AGGREGATE broker book as their own. On
Tue 2026-11-10 six sleeves each submitted sell_to_close for the same
13 SPY (42210000, 27 terminal rejections across 15 sleeves; 3,094
exit-guard firings). First increment landed as a shadow read:
desk3/virtual_book.py derives each sleeve's book from its own
journal fills ONLY. Nothing live imports it yet; the register row
closes when a sleeve reads its derived book in a live cycle.

These tests pin the derivation semantics against the burst shape:
a sleeve with no fills in a symbol derives ZERO there even when the
aggregate book is nonzero (reading the aggregate as its own is the
defect being cured), two sleeves' books in the same symbol stay
separate, and positions the aggregate nets to zero are surfaced.

Fail direction: against a derivation that returns the aggregate for
every sleeve (the live defect's semantics), the burst test fails.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from desk3 import virtual_book  # noqa: E402


def fill(sleeve, symbol, side, qty, intent):
    return {
        "event": "fill",
        "sleeve": sleeve,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "intent_id": intent,
        "broker_order_id": "bo-" + intent,
        "ts": "2026-11-10T15:58:00Z",
    }


class TestVirtualBookShadow(unittest.TestCase):
    def test_burst_shape_only_the_owner_derives_the_position(self):
        # The 2026-11-10 15:58Z shape: the broker book holds 13 SPY,
        # owned by one sleeve's fills. Five other sleeves never filled
        # SPY. Under the defect they each read 13 as their own.
        rows = [fill("owner_sleeve", "SPY", "buy", 13.0, "own-1")]
        rows += [
            {"event": "intent_rejected", "sleeve": s, "symbol": "SPY"}
            for s in ("s1", "s2", "s3", "s4", "s5")
        ]
        book = virtual_book.derive_book(rows)
        self.assertEqual(virtual_book.aggregate_book(book), {"SPY": 13.0})
        self.assertEqual(
            virtual_book.sleeve_positions(book, "owner_sleeve"), {"SPY": 13.0}
        )
        for other in ("s1", "s2", "s3", "s4", "s5"):
            self.assertEqual(virtual_book.sleeve_positions(book, other), {})

    def test_two_sleeves_same_symbol_stay_separate(self):
        rows = [
            fill("a", "QQQ", "buy", 10.0, "a-1"),
            fill("b", "QQQ", "buy", 5.0, "b-1"),
            fill("a", "QQQ", "sell", 4.0, "a-2"),
        ]
        book = virtual_book.derive_book(rows)
        self.assertEqual(virtual_book.sleeve_positions(book, "a"), {"QQQ": 6.0})
        self.assertEqual(virtual_book.sleeve_positions(book, "b"), {"QQQ": 5.0})
        self.assertEqual(virtual_book.aggregate_book(book), {"QQQ": 11.0})

    def test_non_fill_rows_never_move_a_book(self):
        rows = [
            {"event": "order_submitted", "sleeve": "a", "symbol": "SPY"},
            {"event": "intent_rejected", "sleeve": "a", "symbol": "SPY"},
            fill("a", "SPY", "buy", 2.0, "a-1"),
        ]
        book = virtual_book.derive_book(rows)
        self.assertEqual(book[("a", "SPY")]["qty"], 2.0)
        self.assertEqual(book[("a", "SPY")]["fills"], 1)

    def test_netted_positions_surface_as_divergences(self):
        rows = [
            fill("long_sleeve", "USAR", "buy", 3.0, "l-1"),
            fill("short_sleeve", "USAR", "sell", 3.0, "s-1"),
        ]
        book = virtual_book.derive_book(rows)
        self.assertEqual(virtual_book.aggregate_book(book), {"USAR": 0.0})
        divs = virtual_book.netted_divergences(book)
        self.assertEqual(
            {(d["sleeve"], d["derived_qty"]) for d in divs},
            {("long_sleeve", 3.0), ("short_sleeve", -3.0)},
        )

    def test_fill_rows_missing_identity_are_skipped_not_guessed(self):
        rows = [
            {"event": "fill", "symbol": "SPY", "side": "buy", "qty": 9.0},
            {"event": "fill", "sleeve": "a", "side": "buy", "qty": 9.0},
            fill("a", "SPY", "buy", 1.0, "a-1"),
        ]
        book = virtual_book.derive_book(rows)
        self.assertEqual(book, {("a", "SPY"): {"qty": 1.0, "fills": 1}})


if __name__ == "__main__":
    unittest.main()
