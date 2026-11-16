"""FEED80-WARM-20261114 blockers: the warm layer must fetch and alias
the series three UNFED-by-granularity families were starved of.

- aster_native_eth_sma200 / aster_native_btc_eth_sma200 read snapshot
  bars under "ETH-USD|1Day" (the dashed Coinbase form the BTC alias
  precedent in fetch_all already writes for BTC/USD 1Day). No ETH
  series existed anywhere in the estate (verified 2026-11-14).
- donchian_crypto's adapter calls ctx.bars("SOLUSD", "15Min", 2000):
  snapshot key "SOLUSD|15Min". No SOL series existed.
- aster_r19_timing_overnight_25bp / _5bp read 30Min bars for every
  symbol in aster_batch15.UNIVERSE42; warm fetched 30Min for only
  SPY/QQQ/MDY/DIA.

Fail-first: every test below fails on the pre-cure warm.py (no ETH/SOL
crypto fetches, no aliases, 30Min universe of 4).
"""
import unittest

from desk3 import warm


class TestFeed80WarmFetches(unittest.TestCase):
    def test_eth_daily_crypto_fetch_declared(self):
        hits = [d for (s, tf, d) in warm.CRYPTO_FETCHES
                if s == "ETH/USD" and tf == "1Day"]
        self.assertTrue(hits and hits[0] >= 400,
                        "ETH/USD 1Day (>=400d for SMA200) not in CRYPTO_FETCHES")

    def test_sol_15min_crypto_fetch_declared(self):
        hits = [d for (s, tf, d) in warm.CRYPTO_FETCHES
                if s == "SOL/USD" and tf == "15Min"]
        self.assertTrue(hits, "SOL/USD 15Min not in CRYPTO_FETCHES")

    def test_overnight_30min_universe_complete(self):
        from desk3.aster_batch15 import UNIVERSE42
        have = {s for (s, tf, d) in warm.INTRADAY_FETCHES if tf == "30Min"}
        missing = [s for s in UNIVERSE42 if s not in have]
        self.assertEqual(missing, [],
                         f"30Min warm fetch missing UNIVERSE42 symbols: {missing}")


class TestFeed80WarmAliases(unittest.TestCase):
    def _run_fetch_all(self):
        rows = [{"t": "2026-11-13T00:00:00Z", "o": 1.0, "h": 1.0,
                 "l": 1.0, "c": 1.0, "v": 1.0}]
        orig_crypto = warm._fetch_crypto
        orig_fetch = warm._fetch
        # ENJ-FEED-CONV27-20261115: stub the Kraken spot fetch too
        # so this suite stays hermetic (fetch_all gained the
        # KRAKEN_SPOT_FETCHES loop on that landing).
        orig_kraken = warm._fetch_kraken_spot
        warm._fetch_crypto = lambda *a, **k: list(rows)
        warm._fetch = lambda *a, **k: []
        warm._fetch_kraken_spot = lambda *a, **k: []
        try:
            return warm.fetch_all([], {}, now=None)
        finally:
            warm._fetch_crypto = orig_crypto
            warm._fetch = orig_fetch
            warm._fetch_kraken_spot = orig_kraken

    def test_eth_dashed_alias_written(self):
        bars = self._run_fetch_all()
        self.assertIn("ETH/USD|1Day", bars)
        self.assertIn("ETH-USD|1Day", bars,
                      "native engines read the dashed form ETH-USD|1Day")

    def test_sol_bare_alias_written(self):
        bars = self._run_fetch_all()
        self.assertIn("SOL/USD|15Min", bars)
        self.assertIn("SOLUSD|15Min", bars,
                      "donchian_crypto reads the bare form SOLUSD|15Min")

    def test_btc_alias_preserved(self):
        bars = self._run_fetch_all()
        self.assertIn("BTC-USD|1Day", bars)
        self.assertIn("BTC-USD", bars)


if __name__ == "__main__":
    unittest.main()


class TestHedgeInstrument(unittest.TestCase):
    """FEED80-HEDGE-20261114: TZA (s_mn_hedge's instrument) must be
    in the warm symbol union; pre-cure it was absent estate-wide."""

    def test_tza_in_desk_symbols(self):
        from desk3.warm import desk_symbols
        self.assertIn("TZA", desk_symbols("."))


class TestOvernightDepth(unittest.TestCase):
    """FEED80-WARM-DEPTH-20261114: the r19 overnight percentile gate
    needs 126 sessions of 30Min history; the first cure fetched 30
    days, which left the gate unable to fire even though the
    sleeves evaluated. Every UNIVERSE42 30Min entry must request
    >= 126 days."""

    def test_universe42_30min_depth_covers_gate(self):
        from desk3.warm import INTRADAY_FETCHES
        from desk3.aster_batch15 import UNIVERSE42
        ent = {s: d for s, tf, d in INTRADAY_FETCHES if tf == "30Min"}
        for sym in UNIVERSE42:
            self.assertIn(sym, ent)
            self.assertGreaterEqual(ent[sym], 126, sym)
