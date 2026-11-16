"""CR-4 cap-scope blockers (2026-11-12, Firing Line follow-up).

Defect (CR4-REPLAY.md, replay-proven): bb_rsi_divergence's v2
adapter builds slice_state, and therefore its concurrency cap,
from ctx.positions, which the snapshot fills with the WHOLE
broker account (15 positions on the replayed snapshot). The
sleeve has never held a position (0 fills, 0 intents in 2,364
adapter_eval stamps), yet the cap read 3 - 15 = -12: 785 of 2,364
stamps state blocked_concurrency_cap, two sessions were blocked
in 100% of evaluations, and the only divergence signal the
sleeve ever printed (NBIS long, 2026-10-26) was killed by the
cap before its gates were tested.

Cure: the v3 worker entrypoint (adapters3/bb_rsi_divergence.py,
v3-native glue, not the hash-pinned port) scopes sctx.positions
to the sleeve's own journal-derived book (desk3.virtual_book,
the same derivation the dispatcher's dual-read uses) before
delegating. The cap of 3 is untouched; what is counted changes.
On derivation failure the account list is left as it was.

Fail direction: pre-cure the entrypoint has no scoping; these
tests fail on the missing helper and the unscoped context.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters3 import bb_rsi_divergence as entry  # noqa: E402
from adapters3._snapshot_ctx import SnapshotSleeveContext  # noqa: E402

NOW = "2026-11-12T15:00:00+00:00"
ACCOUNT = [{"symbol": s, "qty": 1.0, "avg_price": 10.0}
           for s in ("SPY", "QQQ", "AAPL", "NVDA", "MSFT", "AMZN",
                     "GOOGL", "META", "TSLA", "AMD", "NFLX", "AVGO",
                     "COST", "PEP", "ADBE")]


def _mkroot(fills=()):
    root = tempfile.mkdtemp()
    state = os.path.join(root, "state")
    os.makedirs(os.path.join(state, "bb_rsi_divergence"),
                exist_ok=True)
    with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
        for f in fills:
            fh.write(json.dumps(f) + "\n")
    return root


def _ctx(root, positions):
    view = {"now": NOW, "positions": positions, "bars": {}}
    ctx = {"now": NOW,
           "state_dir": os.path.join(root, "state",
                                     "bb_rsi_divergence")}
    return SnapshotSleeveContext("bb_rsi_divergence", view, ctx)


def _fill(sleeve, symbol, side, qty):
    return {"event": "fill", "sleeve": sleeve, "symbol": symbol,
            "side": side, "qty": qty}


class TestOwnPositionsFilter(unittest.TestCase):

    def test_no_own_book_drops_everything(self):
        self.assertEqual(entry.own_positions(ACCOUNT, {}), [])

    def test_own_rows_preserved_with_broker_fields(self):
        account = ACCOUNT + [{"symbol": "NBIS", "qty": 25.0,
                              "avg_price": 42.5,
                              "opened_at": "2026-10-26T18:06:00Z"}]
        out = entry.own_positions(account, {"NBIS": 25.0})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "NBIS")
        self.assertEqual(out[0]["avg_price"], 42.5)

    def test_intent_id_attribution_keeps_the_row(self):
        # The batch-1 exit_drive contract: a position row whose
        # intent_id names this sleeve is the sleeve's own, even
        # with no journal fill in the fixture's generations.
        account = [{"symbol": "SPY", "qty": 5.0,
                    "intent_id": "bb_rsi_divergence-20261026T200100-1"},
                   {"symbol": "QQQ", "qty": 3.0,
                    "intent_id": "other_sleeve-20261026T200100-1"}]
        out = entry.own_positions(account, {})
        self.assertEqual([p["symbol"] for p in out], ["SPY"])

    def test_plan_attribution_keeps_the_row(self):
        account = [{"symbol": "SPY", "qty": 5.0},
                   {"symbol": "QQQ", "qty": 3.0}]
        out = entry.own_positions(account, {}, planned_syms={"SPY"})
        self.assertEqual([p["symbol"] for p in out], ["SPY"])


class TestEntrypointScoping(unittest.TestCase):

    def test_fifteen_unrelated_positions_scope_to_zero(self):
        # The replayed snapshot's shape: 15 account positions,
        # none of them this sleeve's (it has never filled).
        root = _mkroot(fills=[_fill("other_sleeve", "SPY",
                                    "buy", 13.0)])
        sctx = _ctx(root, list(ACCOUNT))
        entry._scope_positions_to_own_book(sctx)
        self.assertEqual(sctx.positions, [])

    def test_own_fill_keeps_only_the_owned_row(self):
        root = _mkroot(fills=[
            _fill("bb_rsi_divergence", "NBIS", "buy", 25.0),
            _fill("other_sleeve", "SPY", "buy", 13.0)])
        account = ACCOUNT + [{"symbol": "NBIS", "qty": 25.0,
                              "avg_price": 42.5}]
        sctx = _ctx(root, account)
        entry._scope_positions_to_own_book(sctx)
        self.assertEqual([p["symbol"] for p in sctx.positions],
                         ["NBIS"])

    def test_closed_own_position_scopes_out(self):
        root = _mkroot(fills=[
            _fill("bb_rsi_divergence", "NBIS", "buy", 25.0),
            _fill("bb_rsi_divergence", "NBIS", "sell", 25.0)])
        sctx = _ctx(root, [{"symbol": "NBIS", "qty": 25.0}])
        entry._scope_positions_to_own_book(sctx)
        self.assertEqual(sctx.positions, [])

    def test_entrypoint_scopes_before_delegating(self):
        src = open(os.path.join(
            ROOT, "adapters3", "bb_rsi_divergence.py")).read()
        self.assertIn("_scope_positions_to_own_book(sctx)", src)
        self.assertLess(src.index("_scope_positions_to_own_book(sctx)"),
                        src.index("importlib.import_module"))


if __name__ == "__main__":
    unittest.main()
