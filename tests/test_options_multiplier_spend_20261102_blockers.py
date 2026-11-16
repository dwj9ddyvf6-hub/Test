"""OPTIONS-MULTIPLIER-SPEND-20261102 regression blockers.

Root cause (Cure 2, round 2, 2026-11-02): journal_derived's spend
fold counted options fills at qty x price, but an OCC fill's price
is the per-share premium and its qty is contracts: the cash that
moved is qty x price x 100. On 2026-11-02 the desk's first options
round trips (SPY/QQQ Dec puts) summed to raw spend +60.75 against
true cash spend +6,075.00, understating spend by 6,014.25 and
manufacturing 6,014.25 of the 6,021.61 reconcile cash discrepancy
(5,809.12 of it unexplained after the D1-CFEE known item).
Position quantities are contracts on both sides and must NOT be
multiplied. Equity and crypto fills stay x1.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.reconcile import journal_derived  # noqa: E402


def _write_journal(rows):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return path


def _fill(sleeve, symbol, side, qty, price):
    return {"event": "fill", "sleeve": sleeve, "symbol": symbol,
            "side": side, "qty": qty, "price": price,
            "ts": "2026-11-02T14:30:00+00:00"}


class OptionsMultiplierSpend(unittest.TestCase):
    def test_option_buy_spend_counts_contract_multiplier(self):
        path = _write_journal([
            _fill("opt_sleeve", "SPY261204P00756000", "buy", 1, 11.33)])
        try:
            positions, spend = journal_derived(path, epoch_start=False)
        finally:
            os.unlink(path)
        # cash out is 1 contract x $11.33 premium x 100 shares
        self.assertAlmostEqual(spend["opt_sleeve"], 1133.00, places=2)
        # position qty stays in contracts (broker dialect)
        self.assertAlmostEqual(
            positions["opt_sleeve"]["SPY261204P00756000"], 1.0)

    def test_option_round_trip_spend_is_true_cash(self):
        path = _write_journal([
            _fill("opt_sleeve", "QQQ261204P00690000", "buy", 2, 17.03),
            _fill("opt_sleeve", "QQQ261204P00690000", "sell", 2, 18.00)])
        try:
            positions, spend = journal_derived(path, epoch_start=False)
        finally:
            os.unlink(path)
        self.assertAlmostEqual(
            spend["opt_sleeve"], (2 * 17.03 - 2 * 18.00) * 100, places=2)
        self.assertNotIn("QQQ261204P00690000",
                         positions.get("opt_sleeve", {}))

    def test_equity_and_crypto_spend_unchanged(self):
        path = _write_journal([
            _fill("eq", "AAPL", "buy", 10, 200.0),
            _fill("cx", "BTC/USD", "buy", 0.5, 70000.0)])
        try:
            _, spend = journal_derived(path, epoch_start=False)
        finally:
            os.unlink(path)
        self.assertAlmostEqual(spend["eq"], 2000.0, places=2)
        self.assertAlmostEqual(spend["cx"], 35000.0, places=2)


if __name__ == "__main__":
    unittest.main()
