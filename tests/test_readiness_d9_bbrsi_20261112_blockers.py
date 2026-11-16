"""READINESS-D9-20261112 blockers (ENTER-EXIT-CENSUS D9, remainder).

Defect: adapters/bb_rsi_divergence._symbols appended EVERY symbol
in ctx.positions to the sleeve's candidate universe. ctx.positions
is the broker account view: other sleeves' holdings — including
OCC option contracts from the options sleeves — became candidates
for a stock/ETF divergence sleeve whenever the v2 adapter was
reached without the v3 entrypoint's CR-4 position scoping (the
scoping cure's own fail-back path restores the account list), and
bars were fetched and signals evaluated for names the sleeve has
no business trading. (The cap-counting half of D9 was cured by
CR-4-CAP-SCOPE-20261112 at the v3 entrypoint.)

Cure: a position symbol joins the candidate universe only when
the row is attributable to THIS sleeve — its intent_id carries
the sleeve's prefix, the same attribution the CR-4 scoping uses.
Held names keep their bars for exit evaluation; foreign names,
OCC contracts included, never enter. The strategy file
(sleeves/bb_rsi_divergence.py, sha-pinned) is untouched.

Fail direction: proven on a worktree at the pre-cure HEAD — the
foreign equity and the OCC symbol both appear in _symbols.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class _Ctx:
    def __init__(self, positions):
        self.positions = positions
        self.params = {"extra": {}}


POSITIONS = [
    {"symbol": "SPY261218C00500000", "qty": 2,
     "intent_id": "leaps_momentum-20261112-1"},
    {"symbol": "ZZZZ", "qty": 10, "intent_id": "other_sleeve-20261112-2"},
    {"symbol": "QQQ", "qty": 3, "intent_id": None},
    {"symbol": "HELD1", "qty": 1,
     "intent_id": "bb_rsi_divergence-20261110-1"},
]


class TestUniverseScopedToOwnBook(unittest.TestCase):
    def test_foreign_symbols_never_enter(self):
        from adapters.bb_rsi_divergence import _symbols
        syms = _symbols(_Ctx(POSITIONS), {"plans": {}})
        self.assertNotIn("SPY261218C00500000", syms)
        self.assertNotIn("ZZZZ", syms)
        # (QQQ also sits in the fixture positions unattributed; it
        # is a member of the configured universe on its own, so it
        # proves nothing either way and is not asserted.)
        self.assertIn("HELD1", syms)   # own holding keeps its bars

    def test_configured_universe_intact(self):
        from adapters.bb_rsi_divergence import _symbols
        from sleeves.bb_rsi_divergence import UNIVERSE_12
        syms = _symbols(_Ctx([]), {"plans": {}})
        for s in UNIVERSE_12:
            self.assertIn(s, syms)


if __name__ == "__main__":
    unittest.main()
