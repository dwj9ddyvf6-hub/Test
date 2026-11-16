"""CURE1-DESK-20261102 blockers, unlisted / foreign-venue emission class.

Live evidence (state/dispatcher.jsonl, 2026-10-31): s_mn_macd emitted
ENJ/USD and PF_LINKUSD; both reached the wire and came back as
broker_rejected_terminal 42210000 asset-not-found. ENJ/USD is proven
unlisted at Alpaca (BUGLOG ENJ-ASSET-NOT-LISTED-20261030; the owner
parked all 22 ENJ sleeves on that basis), yet multi-symbol sleeves
that are not ENJ sleeves (s_mn_macd, s_mn_vwap) still emit it.
PF_LINKUSD is a Kraken perp contract key leaking into the laz8
sleeves' shared bars map; the laz8 contract is plain symbols only
(BROKER-422-SMN-SYMBOL-20261027 cured the timeframe-suffix leak of
the same class at the same boundary).

Cures pinned here:
1. Door preflight rejects an ENTRY whose normalized symbol is the
   proven-unlisted ENJ/USD, locally, by name; exits are untouched.
2. adapters.laz8_common._normalize_bars drops PF_-prefixed keys.
3. Preservation: PF_ADAUSD through the dispatcher for a kraken
   contract still fills (the pinned kraken e2e shape is not a laz8
   emission and is not this class), and a listed crypto entry
   (LINK/USD) still fills.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher, _preflight_violation  # noqa: E402


def _entry(iid, sym, qty=1, kind="entry"):
    return {"intent_id": iid, "kind": kind, "symbol": sym,
            "side": "buy" if kind == "entry" else "sell",
            "qty": qty, "order_type": "market", "limit_price": None,
            "price_hint": 10.0,
            "time_in_force": "day", "reason": "cure1 fixture",
            "position_intent": "buy_to_open" if kind == "entry"
            else "sell_to_close"}


def _root():
    import tempfile
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    return root


def _disp(broker, sleeve="s_mn_macd"):
    return Dispatcher(_root(), broker,
                      slices={sleeve: {"capital_usd": 100000.0,
                                       "cash_usd": 100000.0}},
                      price_lookup=lambda s: 10.0)


class TestUnlistedPreflight(unittest.TestCase):
    def test_enj_usd_entry_is_preflight_rejected(self):
        self.assertEqual(
            _preflight_violation(_entry("u1", "ENJ/USD"), "s_mn_macd"),
            "preflight_symbol_asset_not_listed")

    def test_enj_usd_exit_is_not_blocked(self):
        intent = _entry("u2", "ENJ/USD", kind="exit")
        intent["position_intent"] = "sell_to_close"
        # the door translates crypto TIF (day -> gtc) before preflight
        intent["time_in_force"] = "gtc"
        self.assertIsNone(_preflight_violation(intent, "s_mn_macd"))

    def test_enj_entry_rejected_at_door_without_submit(self):
        broker = FakeBroker(prices={"ENJ/USD": 0.02},
                            fill_mode="filled")
        disp = _disp(broker)
        r = disp.process_intent(_entry("u3", "ENJ/USD", qty=10),
                                "s_mn_macd")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"],
                         "preflight_symbol_asset_not_listed")
        self.assertEqual(broker.submit_count, 0)

    def test_listed_crypto_entry_still_fills(self):
        broker = FakeBroker(prices={"LINK/USD": 11.0},
                            fill_mode="filled")
        disp = _disp(broker)
        r = disp.process_intent(_entry("u4", "LINK/USD", qty=1),
                                "s_mn_macd")
        self.assertEqual(r["status"], "filled")
        self.assertEqual(broker.submit_count, 1)

    def test_kraken_perp_dispatcher_shape_preserved(self):
        broker = FakeBroker(prices={"PF_ADAUSD": 1.01},
                            fill_mode="filled")
        disp = _disp(broker, sleeve="s1")
        r = disp.process_intent(_entry("u5", "PF_ADAUSD", qty=1), "s1")
        self.assertEqual(r["status"], "filled")
        self.assertEqual(broker.submit_count, 1)


class TestLaz8PerpKeyDrop(unittest.TestCase):
    def test_pf_keys_dropped_plain_keys_kept(self):
        from adapters.laz8_common import _normalize_bars
        bars = {"PF_LINKUSD": [{"t": 1, "c": 1.0}],
                "PF_ADAUSD": [{"t": 1, "c": 1.0}],
                "LINK/USD": [{"t": 1, "c": 1.0}],
                "ADA/USD": [{"t": 1, "c": 1.0}]}
        out = _normalize_bars(bars)
        self.assertEqual(sorted(out), ["ADA/USD", "LINK/USD"])


if __name__ == "__main__":
    unittest.main()
