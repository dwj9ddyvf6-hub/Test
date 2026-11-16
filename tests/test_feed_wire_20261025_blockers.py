"""FEED-WIRE-20261025 blockers — the two 403'd producers wired to the
feeds that answer on this account tier.

Proven by read-only probes 2026-10-25: Alpaca latest stock quotes
feed=sip -> HTTP 403, feed=delayed_sip -> 200 (consolidated SIP
quotes ~15 min delayed); options snapshots (v1beta1) feed=opra ->
HTTP 403, feed=indicative -> 200 (real bid/ask, NO greeks, NO
impliedVolatility). state/health.json producer_errors that night
listed quotes and options_chain as HTTP 403.

Pins:
  1. The fetchers REQUEST feed=delayed_sip (stocks) and
     feed=indicative (options) — captured at the _get_json seam.
  2. The products are STAMPED with the true feed names.
  3. Quote timestamps stay truthful: market_at/at are the quote's
     own timestamps, never re-stamped with received_at/now.
  4. Greeks-absent contract: a snapshot with no greeks yields
     delta None in BOTH consumer shapes (options chains and
     options_chain) — absent, never a fabricated 0.0 — and no
     impliedVolatility field is invented anywhere. A snapshot WITH
     greeks still carries its real delta.
  5. The named consumer refusal still fires: aster_batch3 contract
     selection on a greeks-absent chain raises
     no_qualified_delta_DTE_contract (fail closed, named) instead of
     selecting on a fabricated delta.

Fail direction: with the producer cure stashed, the feed/stamp/
greeks tests fail (feed=sip/feed=opra requested and stamped, chain
delta fabricated as 0.0 instead of None). Restored, all pass.
Test 5 is a contract pin, not a fail-direction proof: it pins that
the named refusal fires on the indicative-shaped chain the desk
will actually serve Monday.
"""
import json, os, shutil, sys, tempfile, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 26, 13, 37, tzinfo=timezone.utc)  # Mon 09:37 ET
QUOTE_T = "2026-10-26T13:22:00Z"  # ~15 min before NOW: the tier delay


def _capture_urls(payload, call):
    """Run call() with producers._get_json captured; return the URLs
    it requested (restores _get_json even on failure)."""
    import desk3.producers as P
    urls = []
    orig = P._get_json

    def fake(url, headers=None, timeout=30):
        urls.append(url)
        return payload
    P._get_json = fake
    try:
        call()
    finally:
        P._get_json = orig
    return urls


class TestRequestedFeeds(unittest.TestCase):
    def test_stock_quotes_request_delayed_sip(self):
        import desk3.producers as P
        urls = _capture_urls({"quotes": {}},
                             lambda: P.fetch_latest_quotes(["SPY"], {}))
        self.assertEqual(len(urls), 1)
        self.assertIn("feed=delayed_sip", urls[0])
        # and not the bare tier-forbidden value hiding beside it
        self.assertNotIn("feed=sip", urls[0].replace("delayed_sip", ""))

    def test_option_snapshots_request_indicative(self):
        import desk3.producers as P
        urls = _capture_urls(
            {"snapshots": {}},
            lambda: P.fetch_option_snapshots(["SPY261113C00118000"], {}))
        self.assertEqual(len(urls), 1)
        self.assertIn("feed=indicative", urls[0])
        self.assertNotIn("opra", urls[0])


class TestTruthfulStampsAndTimestamps(unittest.TestCase):
    def test_quotes_stamp_delayed_sip_and_keep_quote_time(self):
        from desk3.producers import StockQuotes
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "config"))
        with open(os.path.join(tmp, "config", "universes.json"), "w") as fh:
            json.dump({}, fh)
        raw = {"SPY": {"bp": 117.98, "ap": 118.02, "bs": 100, "as": 100,
                       "t": QUOTE_T}}
        p = StockQuotes(tmp, {}, fetcher=lambda syms, env: dict(raw))
        q = p({"now": NOW})["quotes"]["SPY"]
        self.assertEqual(q["feed"], "delayed_sip")
        # The delay is a property of the tier: the quote's own
        # timestamp survives untouched, never re-stamped as fresh.
        self.assertEqual(q["market_at"], QUOTE_T)
        self.assertEqual(q["at"], QUOTE_T)
        self.assertEqual(q["received_at"], NOW.isoformat())
        self.assertLess(q["market_at"], q["received_at"])


OCC1 = "SPY261113C00118000"   # SPY 2026-11-13 call 118
OCC2 = "SPY261113C00123000"   # SPY 2026-11-13 call 123


def _contracts(und, env, ref):
    if und != "SPY":
        return []
    return [{"symbol": OCC1, "expiration_date": "2026-11-13",
             "strike_price": "118.0"},
            {"symbol": OCC2, "expiration_date": "2026-11-13",
             "strike_price": "123.0"}]


def _snapshots_no_greeks(occs, env):
    # The indicative shape: latestQuote only — no "greeks" key, no
    # "impliedVolatility" key, exactly as the tier serves it.
    rows = {OCC1: {"latestQuote": {"bp": 2.90, "ap": 3.00, "bs": 10,
                                   "as": 10, "t": QUOTE_T}},
            OCC2: {"latestQuote": {"bp": 1.10, "ap": 1.20, "bs": 10,
                                   "as": 10, "t": QUOTE_T}}}
    return {o: rows[o] for o in occs if o in rows}


def _snapshots_with_greeks(occs, env):
    rows = _snapshots_no_greeks(occs, env)
    rows[OCC1] = {**rows[OCC1], "greeks": {"delta": 0.55}}
    return rows


def _payload(snapshots_fetcher):
    from desk3.producers import build_options_payload
    return build_options_payload(
        ["SPY"], {}, NOW, contracts_fetcher=_contracts,
        snapshots_fetcher=snapshots_fetcher,
        spot_hint={"SPY": 118.0})


class TestOptionsStampsAndGreeksAbsent(unittest.TestCase):
    def test_options_quotes_stamp_indicative(self):
        out = _payload(_snapshots_no_greeks)
        q = out["options_quotes"][OCC1]
        self.assertEqual(q["feed"], "indicative")
        self.assertEqual((q["bid"], q["ask"]), (2.90, 3.00))
        self.assertEqual(q["market_at"], QUOTE_T)

    def test_absent_greeks_stay_absent_never_zero(self):
        out = _payload(_snapshots_no_greeks)
        full = out["options"]["SPY"]["chains"]["SPY"]
        chain = out["options_chain"]["SPY"]
        self.assertEqual(len(full), 2)
        self.assertEqual(len(chain), 2)
        for row in full + chain:
            self.assertIsNone(row["delta"], row)
            self.assertNotIn("impliedVolatility", row)
            self.assertNotIn("iv", row)
        for q in out["options_quotes"].values():
            self.assertNotIn("impliedVolatility", q)
            self.assertNotIn("delta", q)

    def test_present_greeks_still_carried(self):
        out = _payload(_snapshots_with_greeks)
        full = {r["symbol"]: r for r in out["options"]["SPY"]["chains"]["SPY"]}
        chain = {r["symbol"]: r for r in out["options_chain"]["SPY"]}
        self.assertEqual(full[OCC1]["delta"], 0.55)
        self.assertEqual(chain[OCC1]["delta"], 0.55)
        self.assertIsNone(full[OCC2]["delta"])
        self.assertIsNone(chain[OCC2]["delta"])


class TestConsumerRefusesAbsentGreeksByName(unittest.TestCase):
    def test_batch3_selection_fails_closed_named(self):
        # aster_batch3._select_contracts must refuse a greeks-absent
        # chain by name — never select on a fabricated delta. The
        # underlying quote is hand-built at the sleeve's own sip
        # contract (its gate, unchanged); only the chain comes from
        # the producer.
        from desk3 import aster_batch3
        out = _payload(_snapshots_no_greeks)
        view = {"options_chain": out["options_chain"],
                "quotes": {"SPY": {"symbol": "SPY", "feed": "sip",
                                   "bid": 117.98, "ask": 118.02,
                                   "market_at": NOW.isoformat(),
                                   "received_at": NOW.isoformat()}}}
        spec = dict(aster_batch3.SPECS["aster_rec_rsi2_vertical_fixed_a"])
        with self.assertRaises(ValueError) as cm:
            aster_batch3._select_contracts(view, spec, "SPY", NOW)
        self.assertEqual(str(cm.exception),
                         "no_qualified_delta_DTE_contract")


if __name__ == "__main__":
    unittest.main()
