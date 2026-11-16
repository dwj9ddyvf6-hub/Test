"""CURE2-ENJ-PREFLIGHT-SCOPE-20261102 blocker.

The cure 1 door rule (CURE1-UNLISTED-20261102) rejected every
ENJ/USD entry at the door. Its own stated root cause was narrower:
a multi-symbol sleeve that is NOT an ENJ sleeve (s_mn_macd,
s_mn_vwap) emitting ENJ into a symbol it does not own. As landed,
the rule also rejects entries from the 22 ENJ-domiciled sleeves,
which breaks their gate-wired e2e roundtrip blocker
(test_aster_batch7_blockers.test_e2e_roundtrip_fake_broker went
red in both the AUDIT1 gate and the Cure 2 solo gate) and would
keep rejecting them even after the owner's unpark condition
(Alpaca lists an ENJ pair) is met. ENJ-domiciled sleeves are
already parked at the roster level while ENJ is unlisted; the
door rule's job is only to stop NON-ENJ sleeves burning entries
on a symbol they do not own.

Pins:
1. Every ENJ-domiciled sleeve on the live roster (id carries
   "enj"; the owner's parked 22) passes the preflight for an
   ENJ/USD entry.
2. A non-ENJ sleeve's ENJ/USD entry is still rejected with
   preflight_symbol_asset_not_listed (the cure 1 behavior,
   preserved where its root cause lives).
3. ENJ/USD exits pass for any sleeve (unchanged).
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from desk3.dispatcher import _preflight_violation  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _entry(sym="ENJ/USD", kind="entry"):
    return {"symbol": sym, "kind": kind, "order_type": "market",
            "time_in_force": "gtc"}


class TestEnjPreflightScope(unittest.TestCase):
    def test_roster_enj_sleeves_pass_preflight(self):
        cfg = json.load(open(os.path.join(ROOT, "config",
                                          "sleeves.json")))
        enj = [r["id"] for r in cfg["sleeves"]
               if "enj" in r["id"].lower()]
        # T474U-CRYPTO-PORT-20261116: 22 -> 25 ENJ-domiciled rows
        # (the three t474u ENJ twins rostered live).
        self.assertEqual(len(enj), 25)
        for sid in enj:
            self.assertIsNone(
                _preflight_violation(_entry(), sid),
                f"ENJ-domiciled sleeve {sid} rejected at the door")

    def test_non_enj_sleeve_enj_entry_still_rejected(self):
        for sid in ("s_mn_macd", "s_mn_vwap"):
            self.assertEqual(
                _preflight_violation(_entry(), sid),
                "preflight_symbol_asset_not_listed")

    def test_enj_exit_passes_for_any_sleeve(self):
        intent = _entry(kind="exit")
        intent["position_intent"] = "sell_to_close"
        self.assertIsNone(_preflight_violation(intent, "s_mn_macd"))
        self.assertIsNone(_preflight_violation(
            intent, "aster_r19_enjusdt_breakout_base_fixed16_fullcash"))


if __name__ == "__main__":
    unittest.main()
