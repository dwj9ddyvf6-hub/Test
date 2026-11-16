"""A1-SEED-20261114 blockers: the dispatcher's derived (virtual)
book seeds from the durable fill ledger, not the rotating journal.

Founding evidence (VB-ENDGAME-20261114): Friday 2026-11-13's 425
dual-read divergence rows classify as 210 shared-book close
artifacts, 212 netting artifacts, 3 unjournaled-fill drift rows,
with per-symbol residuals (QQQ +14, SPY -12, CVNA +6, WDC +1,
NBIS +1, BTC/USD -0.0699) between the journal-derived aggregate
and the broker book. The derived book was built from the five
surviving dispatcher journal generations; fills that rotate out
silently shrink it. The durable fill ledger (immutable segments,
hash-verified manifest) is the same fills in durable form.

Cure: Dispatcher._virtual_book seeds via _vb_seed_raw from
state/fill_ledger when its manifest verifies, falling back to the
journal generations (the pre-A1 source) when it does not.

Fail direction: pre-cure, _vb_seed_raw does not exist and a book
whose journal generations have rotated away derives EMPTY; the
rotation-survival test fails. Cured: the book survives rotation,
matches the journal-derived book while both sources exist, and a
corrupt ledger falls back to the journals.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.broker import FakeBroker
from desk3.dispatcher import Dispatcher
from desk3.fill_ledger import build_ledger


def _fill(sid, sym, side, qty, px, iid, ts):
    return {"event": "fill", "intent_id": iid,
            "broker_order_id": f"bo-{iid}", "sleeve": sid,
            "symbol": sym, "side": side, "qty": qty, "price": px,
            "ts": ts}


FILLS = [
    _fill("s1", "TEST", "buy", 10, 100.0, "a", "2026-11-12T15:00:00Z"),
    _fill("s1", "TEST", "sell", 4, 101.0, "b", "2026-11-12T16:00:00Z"),
    _fill("s2", "TEST", "sell", 6, 100.0, "c", "2026-11-12T17:00:00Z"),
]


def _root_with_journal():
    root = tempfile.mkdtemp()
    state = os.path.join(root, "state")
    os.makedirs(state)
    with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
        for r in FILLS:
            fh.write(json.dumps(r) + "\n")
    return root, state


class TestA1Seed(unittest.TestCase):
    def test_book_matches_journal_derivation_when_both_exist(self):
        root, state = _root_with_journal()
        build_ledger([os.path.join(state, "dispatcher.jsonl")],
                     os.path.join(state, "fill_ledger"))
        disp = Dispatcher(root, FakeBroker(prices={"TEST": 100.0}))
        book = disp._virtual_book()
        self.assertAlmostEqual(book[("s1", "TEST")]["qty"], 6.0)
        self.assertAlmostEqual(book[("s2", "TEST")]["qty"], -6.0)

    def test_book_survives_journal_rotation(self):
        root, state = _root_with_journal()
        build_ledger([os.path.join(state, "dispatcher.jsonl")],
                     os.path.join(state, "fill_ledger"))
        # rotation: the journal generations are gone entirely
        os.remove(os.path.join(state, "dispatcher.jsonl"))
        disp = Dispatcher(root, FakeBroker(prices={"TEST": 100.0}))
        book = disp._virtual_book()
        self.assertAlmostEqual(book[("s1", "TEST")]["qty"], 6.0)
        self.assertAlmostEqual(book[("s2", "TEST")]["qty"], -6.0)

    def test_corrupt_ledger_falls_back_to_journals(self):
        root, state = _root_with_journal()
        ledger = os.path.join(state, "fill_ledger")
        build_ledger([os.path.join(state, "dispatcher.jsonl")], ledger)
        seg = os.path.join(ledger, "fills-000001.jsonl")
        with open(seg, "a") as fh:
            fh.write('{"event": "fill", "sleeve": "s9", "symbol": '
                     '"TEST", "side": "buy", "qty": 999}\n')
        disp = Dispatcher(root, FakeBroker(prices={"TEST": 100.0}))
        book = disp._virtual_book()
        self.assertNotIn(("s9", "TEST"), book)
        self.assertAlmostEqual(book[("s1", "TEST")]["qty"], 6.0)


if __name__ == "__main__":
    unittest.main()
