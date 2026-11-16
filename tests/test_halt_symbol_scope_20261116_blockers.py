"""HALT-SYMBOL-SCOPE-20261116 blocker.

Live defect, Sunday 2026-11-15: the BTC/USD position_qty reconcile
row (expected 0.136601008 against broker 0.132675707) halted six
sleeves, and the dispatcher enforced that halt per SLEEVE, not per
symbol. The day's 46 reconcile_halt rejects were all SPY and QQQ
entries from aster_etf_qqq_monthly_m150 and aster_etf_spy_monthly_
m150 (23 each, counted from the dispatcher journal by intent-id
date): entries in symbols with no discrepancy of their own, frozen
by a BTC/USD divergence tied to an Alpaca-side stuck order.

Cure: reconcile reports halted_scopes as (sleeve, symbol) pairs;
the dispatcher halts an entry only when its own symbol is in its
sleeve's scope. Cash halts stay desk-wide. A halt set with no
scope information keeps the legacy sleeve-wide halt.

Fail direction: on the pre-cure tree the report carries no
halted_scopes and the scoped dispatcher's SPY entry from a
BTC-halted sleeve is rejected reconcile_halt.
"""
import os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SLICES = {"s_etf": {"capital_usd": 100000, "cash_usd": 100000},
          "s_btc": {"capital_usd": 100000, "cash_usd": 100000}}


def _entry(iid, symbol, sleeve_qty_price=100.0):
    return {"intent_id": iid, "kind": "entry", "symbol": symbol,
            "side": "buy", "qty": 1, "order_type": "market",
            "price_hint": sleeve_qty_price}


class TestHaltSymbolScope(unittest.TestCase):
    def _desk_with_btc_discrepancy(self, tmp):
        """Baseline on an empty journal, then one BTC fill for
        s_etf and one for s_btc; the broker read-back is short, so
        BTC/USD is discrepant for exactly those two sleeves."""
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        from desk3.reconcile import reconcile
        broker = FakeBroker(prices={"BTC/USD": 100.0, "SPY": 100.0,
                                    "QQQ": 100.0})
        state = os.path.join(tmp, "state")
        os.makedirs(state, exist_ok=True)
        caps = {"s_etf": 100000.0, "s_btc": 100000.0}
        reconcile(state, {}, slice_capital=caps, record_baseline=True)
        d = Dispatcher(tmp, broker, slices=dict(SLICES),
                       price_lookup=lambda s: 100.0)
        for sid in ("s_etf", "s_btc"):
            r = d.process_intent(_entry(f"{sid}-btc", "BTC/USD"), sid)
            assert r["status"] == "filled", r
        short = dict(broker.get_positions())
        short["BTC/USD"] = short.get("BTC/USD", 0.0) - 0.5
        rep = reconcile(state, short, slice_capital=caps)
        return broker, rep

    def test_report_carries_exact_scopes(self):
        tmp = tempfile.mkdtemp()
        _, rep = self._desk_with_btc_discrepancy(tmp)
        self.assertEqual(rep["halted_sleeves"], ["s_btc", "s_etf"])
        self.assertEqual(
            rep["halted_scopes"],
            [{"sleeve": "s_btc", "symbol": "BTC/USD"},
             {"sleeve": "s_etf", "symbol": "BTC/USD"}])

    def test_scoped_halt_blocks_only_the_discrepant_symbol(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        tmp = tempfile.mkdtemp()
        broker, rep = self._desk_with_btc_discrepancy(tmp)
        d = Dispatcher(tmp, broker, slices=dict(SLICES),
                       price_lookup=lambda s: 100.0)
        d.halted_sleeves = set(rep["halted_sleeves"])
        scopes = {}
        for row in rep["halted_scopes"]:
            scopes.setdefault(row["sleeve"], set()).add(row["symbol"])
        d.halted_scopes = scopes
        # The Sunday shape: the ETF sleeve's SPY and QQQ entries
        # must reach the broker; its BTC entry stays halted.
        r = d.process_intent(_entry("etf-spy", "SPY"), "s_etf")
        self.assertEqual(r["status"], "filled", r)
        r = d.process_intent(_entry("etf-qqq", "QQQ"), "s_etf")
        self.assertEqual(r["status"], "filled", r)
        r = d.process_intent(_entry("etf-btc", "BTC/USD"), "s_etf")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))
        # The bare broker-dialect spelling of the same symbol is
        # the same scope.
        r = d.process_intent(_entry("btc-bare", "BTCUSD"), "s_btc")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))
        # Exits always pass, even in the discrepant symbol.
        r = d.process_intent(
            {"intent_id": "etf-exit", "kind": "exit", "symbol": "BTC/USD",
             "side": "sell", "qty": 1, "order_type": "market",
             "price_hint": 100.0}, "s_etf")
        self.assertEqual(r["status"], "filled", r)

    def test_scopeless_halt_keeps_legacy_sleeve_wide_behavior(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"SPY": 100.0})
        d = Dispatcher(tmp, broker, slices=dict(SLICES),
                       price_lookup=lambda s: 100.0)
        d.halted_sleeves = {"s_etf"}
        r = d.process_intent(_entry("legacy-spy", "SPY"), "s_etf")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))


if __name__ == "__main__":
    unittest.main()
