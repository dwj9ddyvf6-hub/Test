"""FEED80-PRZM-20261114 regression blockers.

Defect: przm_fade_edges sat parked because the options_chain
producer served delta-only rows — no gamma, no open interest —
so the sleeve's gamma_levels() could only return None
(WAITING_NO_GAMMA_LEVELS). The raw material existed: the Alpaca
contracts route carries open_interest (dropped when the producer
built its rows), and the desk already inverts IV from indicative
mids for its IV product.

Cure (desk3/producers.py build_options_payload): rows now carry
open_interest passed through from the contracts route, and a
gamma COMPUTED by BS at the IV inverted from the row's own mid
(puts via put-call parity), stamped gamma_source=
"bs_inverted_indicative_v1" so it is never mistaken for feed
greeks. Delta is deliberately NOT computed — the FEED-WIRE-
20261025 contract (absent stays absent) is pinned below.

Fail-first: pre-cure rows carried neither field, so every
enrichment assertion failed and gamma_levels returned None.
"""
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

NOW = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
SPOT = 600.0


def _contracts(und, env, ref, max_dte=62):
    return [
        {"symbol": "SPY261121C00600000", "strike_price": 600.0,
         "expiration_date": "2026-11-21", "open_interest": 12345},
        {"symbol": "SPY261121P00600000", "strike_price": 600.0,
         "expiration_date": "2026-11-21", "open_interest": 6789},
        {"symbol": "SPY261114C00600000", "strike_price": 600.0,
         "expiration_date": "2026-11-14", "open_interest": 111},
    ]


def _snaps(occs, env):
    return {o: {"latestQuote": {"bp": 5.0, "ap": 5.2, "bs": 10,
                                "as": 10, "t": "2026-11-14T15:00:00Z"}}
            for o in occs}


def _payload():
    from desk3.producers import build_options_payload
    return build_options_payload(
        ["SPY"], {}, NOW, contracts_fetcher=_contracts,
        snapshots_fetcher=_snaps, spot_hint={"SPY": SPOT})


class TestGammaOiEnrichment(unittest.TestCase):
    def test_chain_rows_carry_oi_and_computed_gamma(self):
        out = _payload()
        rows = {r["symbol"]: r for r in out["options_chain"]["SPY"]}
        call = rows["SPY261121C00600000"]
        self.assertEqual(call["open_interest"], 12345.0)
        self.assertIsNotNone(call["gamma"])
        self.assertGreater(call["gamma"], 0.0)
        self.assertEqual(call["gamma_source"],
                         "bs_inverted_indicative_v1")
        put = rows["SPY261121P00600000"]
        self.assertEqual(put["open_interest"], 6789.0)
        self.assertIsNotNone(put["gamma"])
        self.assertGreater(put["gamma"], 0.0)

    def test_zero_dte_gamma_stays_absent(self):
        out = _payload()
        rows = {r["symbol"]: r for r in out["options_chain"]["SPY"]}
        self.assertIsNone(rows["SPY261114C00600000"]["gamma"])
        self.assertNotIn("gamma_source", rows["SPY261114C00600000"])

    def test_delta_contract_untouched(self):
        """FEED-WIRE-20261025: absent feed greeks stay absent; the
        enrichment must not leak a computed delta into the rows."""
        out = _payload()
        for r in out["options_chain"]["SPY"]:
            self.assertIsNone(r["delta"])

    def test_gamma_levels_consumes_enriched_rows(self):
        """A multi-strike chain whose cumulative GEX changes sign
        (heavy put OI below spot, heavy call OI above) must yield
        levels; a single-strike chain correctly yields None (no
        sign change exists), which is why this fixture differs."""
        from desk3.producers import build_options_payload
        from sleeves.przm_fade_edges import gamma_levels

        def contracts(und, env, ref, max_dte=62):
            return [
                {"symbol": "SPY261121P00580000", "strike_price": 580.0,
                 "expiration_date": "2026-11-21", "open_interest": 90000},
                {"symbol": "SPY261121C00600000", "strike_price": 600.0,
                 "expiration_date": "2026-11-21", "open_interest": 1000},
                {"symbol": "SPY261121C00620000", "strike_price": 620.0,
                 "expiration_date": "2026-11-21", "open_interest": 90000},
            ]
        out = build_options_payload(
            ["SPY"], {}, NOW, contracts_fetcher=contracts,
            snapshots_fetcher=_snaps, spot_hint={"SPY": SPOT})
        levels = gamma_levels(out["options_chain"]["SPY"], SPOT)
        self.assertIsNotNone(levels)
        self.assertIn("magnet", levels)
        self.assertIn("flip", levels)


if __name__ == "__main__":
    unittest.main()
