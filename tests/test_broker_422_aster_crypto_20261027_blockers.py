"""BROKER-422-ASTER-CRYPTO-20261027 blockers: aster_native sleeves
must emit Alpaca trading-dialect crypto symbols with a crypto-valid
time_in_force. Live broker bodies captured 2026-10-27 against the
exact queued payload (BTC-USD, market, day, qty
0.06234923694976848, 84-char client_order_id):
  symbol BTC-USD -> 422 {"code":42210000,"message":
      "asset \\"BTC-USD\\" not found"}   (BTC/USD is the pair)
  BTC/USD + day  -> 422 {"code":42210000,"message":
      "invalid crypto time_in_force"}   (gtc is the equivalent)
  BTC/USD + gtc + the SAME 84-char coid + full-precision qty ->
      past all 422 validation (403 buying-power class only):
      client_order_id length and qty precision are PROVEN INNOCENT
      and are deliberately NOT changed.

Fail direction (proven at cure time by temporary revert): on the
old _intent the emitted symbol is "BTC-USD" with time_in_force
"day", and the position read-back test's exit never fires (the
broker-keyed "BTC/USD" position is invisible to the book); every
test below fails there.
"""
import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.aster_batch1 import _broker_symbol, _intent, evaluate

NOW = datetime(2026, 10, 27, 13, 21, 42, tzinfo=timezone.utc)
SID = "aster_native_btc_eth_sma200"


def _bars(closes):
    return [{"t": 1700000000.0 + i * 86400, "o": c, "h": c, "l": c,
             "c": c, "v": 1000.0} for i, c in enumerate(closes)]


def _rising(n=210):
    return [100.0 + i for i in range(n)]  # last close far above SMA200


def _view(positions=None, btc=True, eth=True):
    bars = {}
    if btc:
        bars["BTC-USD"] = _bars(_rising())
    if eth:
        bars["ETH-USD"] = _bars(_rising())
    return {"bars": bars, "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "now": NOW}


class TestBrokerSymbolTranslation(unittest.TestCase):
    def test_dashed_pairs_translate(self):
        self.assertEqual(_broker_symbol("BTC-USD"), "BTC/USD")
        self.assertEqual(_broker_symbol("ETH-USD"), "ETH/USD")

    def test_other_symbols_untouched(self):
        for sym in ("SPY", "ENJUSDT", "BTC/USD", "BRK-B"):
            self.assertEqual(_broker_symbol(sym), sym)

    def test_intent_crypto_symbol_and_tif(self):
        d = _intent(SID, "20261027T132142", 1, "entry", "BTC-USD",
                    "buy", 0.05, "x")
        self.assertEqual(d["symbol"], "BTC/USD")
        self.assertEqual(d["time_in_force"], "gtc")

    def test_intent_equity_symbol_and_tif_unchanged(self):
        d = _intent("aster_rsi2_1d", "20261027T132142", 1, "entry",
                    "SPY", "buy", 3, "x")
        self.assertEqual(d["symbol"], "SPY")
        self.assertEqual(d["time_in_force"], "day")


class TestNativeEvaluateBrokerShape(unittest.TestCase):
    def test_pair_entry_intents_carry_broker_symbols_and_gtc(self):
        out = evaluate(SID, _view(), {})
        self.assertTrue(out)
        for d in out:
            self.assertIn(d["symbol"], ("BTC/USD", "ETH/USD"))
            self.assertEqual(d["time_in_force"], "gtc")

    def test_single_leg_entry_when_other_leg_unfed(self):
        out = evaluate(SID, _view(eth=False), {})
        self.assertTrue(out)
        self.assertEqual({d["symbol"] for d in out}, {"BTC/USD"})
        self.assertTrue(all(d["time_in_force"] == "gtc" for d in out))

    def test_broker_keyed_position_is_seen_and_exited(self):
        # Price now BELOW SMA200 (falling series): the book must see
        # its broker-keyed BTC/USD position and emit the exit.
        falling = [400.0 - i for i in range(210)]
        view = _view(positions=[{"symbol": "BTC/USD", "qty": 0.05,
                                 "avg_price": 200.0}])
        view["bars"]["BTC-USD"] = _bars(falling)
        view["bars"]["ETH-USD"] = _bars(falling)
        out = evaluate(SID, view, {})
        exits = [d for d in out if d["kind"] == "exit"
                 and d["symbol"] == "BTC/USD"]
        self.assertTrue(exits, out)
        self.assertEqual(exits[0]["time_in_force"], "gtc")


if __name__ == "__main__":
    unittest.main()
