"""BROKER-422-SMN-SYMBOL-20261027 blockers: the laz8 adapter must
never let a timeframe-suffixed bars key ("AG|1Hour", "TE|1Week")
reach a sleeve as a symbol. Live broker body captured 2026-10-27:
{"code":42210000,"message":"asset \\"AG|1Hour\\" not found"} — the
s_mn_vwap / s_mn_reversal 422 class. The sleeves are documented 1D
strategies over a plain-symbol bars map (their fixture contract);
desk3/warm.py additionally serves every symbol under suffixed
duplicate keys, and the raw map made each duplicate a phantom
symbol (reversal even ranked 21-week returns off "|1Week" keys).

Fail direction (proven at cure time by temporary revert): on the
old _normalize_bars the suffixed keys pass through untouched, the
evaluate-level tests emit intents with symbol "AG|1Hour" /
"TE|1Week", and every test below fails.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapters.laz8_common import _normalize_bars, make_evaluate

CTX = {"session": "2026-10-27", "now": "2026-10-27T13:21:42+00:00",
       "equity": 10000.0}


def _bars(closes, vol=100.0):
    return [{"t": 1700000000.0 + i * 86400, "o": c, "h": c, "l": c,
             "c": c, "v": vol} for i, c in enumerate(closes)]


class TestNormalizeBarsStripsSuffix(unittest.TestCase):
    def test_suffixed_duplicate_dropped_plain_kept(self):
        daily = _bars([10.0] * 25)
        hourly = _bars([99.0] * 25)
        out = _normalize_bars({"AG": daily, "AG|1Day": daily,
                               "AG|1Hour": hourly})
        self.assertEqual(sorted(out), ["AG"])
        self.assertEqual(out["AG"][0]["c"], 10.0)

    def test_symbol_served_only_suffixed_surfaces_plain(self):
        out = _normalize_bars({"TE|1Week": _bars([2.0] * 25)})
        self.assertEqual(sorted(out), ["TE"])


class TestEvaluateEmitsPlainSymbols(unittest.TestCase):
    def test_s_mn_vwap_entry_symbol_is_plain(self):
        # 23 flat bars then a jump: close crosses above rolling VWAP20.
        closes = [10.0] * 24 + [11.0]
        view = {"bars": {"AG|1Hour": _bars(closes)}, "positions": []}
        out = make_evaluate("s_mn_vwap", 1000.0)(view, dict(CTX))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "AG")
        self.assertNotIn("|", out[0]["symbol"])

    def test_s_mn_reversal_entry_symbol_is_plain(self):
        # 22 declining bars: worst 21-session return in its universe.
        closes = [100.0 - i for i in range(22)]
        view = {"bars": {"TE|1Week": _bars(closes)}, "positions": []}
        out = make_evaluate("s_mn_reversal", 3000.0)(view, dict(CTX))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "TE")
        self.assertNotIn("|", out[0]["symbol"])


if __name__ == "__main__":
    unittest.main()
