"""COINALYZE-1 blockers: Coinalyze funding-rate HISTORY wired at the
producer layer (desk3/producers3.py).

Pins:
- the auth header is named EXACTLY "api_key" (case-sensitive server;
  urllib would capitalize it and earn a 401) — asserted through a
  fake http.client connection, never the network;
- percent rates are converted to fractions at parse (0.003039% ->
  0.00003039), matching Kraken print / Binance scalar units;
- fail-closed: 401 / transport error / missing key / stale newest
  row all yield no history (producer serves {} => UNFED by name);
- merge-by-timestamp: Coinalyze history + Kraken live prints form
  ONE kraken.funding series, no duplicates, Kraken print wins its
  timestamp;
- the merged series fixture-drives a consuming sleeve
  (free_kraken_link_crowded, declared kraken.funding input) to an
  entry — the >=30-print gate the live-print collector alone could
  not satisfy for ~30 hours;
- cache: one batched fetch serves repeated loads inside the
  hourly refresh window.

Fail direction: pre-cure, desk3.producers3 has no Coinalyze symbols
(imports of the names below error) and KrakenProducer takes no
coinalyze_loader.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 24, 3, 0, tzinfo=timezone.utc)
NOW_S = int(NOW.timestamp())


def _mkroot():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    return root


def _hist_payload(base_c=0.01, n=48, latest_delta_h=1):
    """Coinalyze-shaped payload (percent values), hourly rows."""
    out = []
    for sym in ("ADAUSDT_PERP.A", "LINKUSDT_PERP.A", "ENJUSDT_PERP.A"):
        rows = []
        for i in range(n):
            t = NOW_S - (latest_delta_h + (n - 1 - i)) * 3600
            rows.append({"t": t, "o": base_c, "h": base_c,
                         "l": base_c, "c": base_c})
        out.append({"symbol": sym, "history": rows})
    return out


def _fetcher_returning(payload):
    def fetch(key, now, conn_factory=None):
        from desk3.producers3 import parse_coinalyze_history
        return parse_coinalyze_history(payload)
    return fetch


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body


class FakeConn:
    """Records the exact header names passed to putheader."""

    def __init__(self, status=200, body=b"[]"):
        self.headers = []
        self.request = None
        self._status = status
        self._body = body
        self.closed = False

    def putrequest(self, method, path):
        self.request = (method, path)

    def putheader(self, name, value):
        self.headers.append((name, value))

    def endheaders(self):
        pass

    def getresponse(self):
        return FakeResponse(self._status, self._body)

    def close(self):
        self.closed = True


class TestHeaderPin(unittest.TestCase):
    def test_exact_api_key_header_name(self):
        from desk3.producers3 import coinalyze_get
        conn = FakeConn(200, b"[]")
        status, body = coinalyze_get("/v1/funding-rate-history?x=1",
                                     "TESTKEY",
                                     conn_factory=lambda t: conn)
        self.assertEqual(status, 200)
        self.assertEqual(conn.headers, [("api_key", "TESTKEY")])
        self.assertNotIn("Api_key", [h[0] for h in conn.headers])
        self.assertNotIn("Api-Key", [h[0] for h in conn.headers])

    def test_fetch_uses_one_batched_call_all_symbols(self):
        from desk3.producers3 import fetch_coinalyze_history
        body = json.dumps(_hist_payload()).encode()
        conn = FakeConn(200, body)
        parsed = fetch_coinalyze_history(
            "K", NOW, conn_factory=lambda t: conn)
        self.assertEqual(set(parsed), {"ADAUSDT", "LINKUSDT", "ENJUSDT"})
        self.assertIn("ADAUSDT_PERP.A", conn.request[1])
        self.assertIn("LINKUSDT_PERP.A", conn.request[1])
        self.assertIn("ENJUSDT_PERP.A", conn.request[1])
        self.assertIn("interval=1hour", conn.request[1])


class TestParseUnits(unittest.TestCase):
    def test_percent_to_fraction_and_dedupe(self):
        from desk3.producers3 import parse_coinalyze_history
        payload = [{"symbol": "ADAUSDT_PERP.A", "history": [
            {"t": 1000, "o": 0.003039, "h": 0.003039, "l": 0.003039,
             "c": 0.003039},
            {"t": 1000, "o": 9.9, "h": 9.9, "l": 9.9, "c": 9.9},
            {"t": 2000, "o": 0.01, "h": 0.01, "l": 0.01, "c": 0.01}]}]
        rows = parse_coinalyze_history(payload)["ADAUSDT"]
        self.assertEqual(len(rows), 2)  # duplicate t collapsed
        self.assertAlmostEqual(rows[0]["c"], 9.9 / 100.0)  # last wins
        self.assertAlmostEqual(rows[1]["c"], 0.0001)


class TestFailClosed(unittest.TestCase):
    def test_http_401_yields_no_history(self):
        from desk3.producers3 import fetch_coinalyze_history
        conn = FakeConn(401, b"{}")
        self.assertIsNone(fetch_coinalyze_history(
            "BAD", NOW, conn_factory=lambda t: conn))

    def test_transport_error_yields_no_history(self):
        from desk3.producers3 import fetch_coinalyze_history

        def boom(timeout):
            raise OSError("connect failed")
        self.assertIsNone(fetch_coinalyze_history(
            "K", NOW, conn_factory=boom))

    def test_missing_key_producer_serves_empty(self):
        import desk3.producers3 as p3
        root = _mkroot()
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COINALYZE_API_KEY", None)
            with mock.patch.object(p3, "COINALYZE_KEY_FILE",
                                   os.path.join(root, "nope.key")):
                out = p3.CoinalyzeFundingProducer(root)({"now": NOW})
        self.assertEqual(out, {})

    def test_stale_history_producer_serves_empty(self):
        import desk3.producers3 as p3
        root = _mkroot()
        stale = _fetcher_returning(_hist_payload(latest_delta_h=10))
        out = p3.CoinalyzeFundingProducer(root, fetcher=stale)(
            {"now": NOW})
        self.assertEqual(out, {})


class TestMerge(unittest.TestCase):
    def test_merge_no_dupes_kraken_wins(self):
        from desk3.producers3 import merge_funding_series, _iso
        hist = [{"t": NOW_S - 7200, "o": 0.0, "h": 0.0, "l": 0.0,
                 "c": 0.0001},
                {"t": NOW_S - 3600, "o": 0.0, "h": 0.0, "l": 0.0,
                 "c": 0.0002}]
        kraken = [{"timestamp": _iso(NOW_S - 3600), "fundingRate": 0.5},
                  {"timestamp": _iso(NOW_S), "fundingRate": 0.0003}]
        merged = merge_funding_series(hist, kraken)
        stamps = [r["timestamp"] for r in merged]
        self.assertEqual(stamps, sorted(set(stamps)))
        self.assertEqual(len(merged), 3)
        by_t = {r["timestamp"]: r["fundingRate"] for r in merged}
        self.assertEqual(by_t[_iso(NOW_S - 3600)], 0.5)  # kraken wins
        self.assertEqual(by_t[_iso(NOW_S - 7200)], 0.0001)


class TestProducerAndCache(unittest.TestCase):
    def test_history_shape_and_single_fetch_cache(self):
        import desk3.producers3 as p3
        root = _mkroot()
        calls = []

        def counting(key, now, conn_factory=None):
            calls.append(1)
            return _fetcher_returning(_hist_payload())(key, now)
        prod = p3.CoinalyzeFundingProducer(root, fetcher=counting)
        out = prod({"now": NOW})
        hist = out["funding_history"]
        self.assertEqual(set(hist), {"ADAUSDT", "LINKUSDT", "ENJUSDT"})
        row = hist["ADAUSDT"][-1]
        self.assertAlmostEqual(row["rate"], 0.0001)  # 0.01% as fraction
        self.assertIn("timestamp", row)
        prod({"now": NOW + timedelta(minutes=30)})  # inside refresh
        self.assertEqual(len(calls), 1)  # cache served, no refetch


def _kraken_transport(url):
    import urllib.parse as up
    if "tickers" in url:
        return {"tickers": [
            {"symbol": "PF_ADAUSD", "bid": 1.0, "ask": 1.02,
             "fundingRate": 0.0002},
            {"symbol": "PF_LINKUSD", "bid": 1.49, "ask": 1.51,
             "fundingRate": 0.01}]}
    if "Depth" in url:
        return {"error": [], "result": {"ENJUSD": {
            "bids": [["0.10", "5", 1]], "asks": [["0.11", "5", 1]]}}}
    pair = up.parse_qs(up.urlparse(url).query).get("pair", [""])[0]
    if "charts" in url:
        candles = [{"time": (NOW - timedelta(hours=4 * (23 - i))).timestamp()
                    * 1000, "open": 1.0, "high": 1.1, "low": 0.9,
                    "close": 1.0, "volume": 10} for i in range(24)]
        return {"candles": candles}
    # spot OHLC
    rows = [[(NOW - timedelta(hours=4 * (23 - i))).timestamp(), "1.0",
             "1.1", "0.9", "1.0", "1.0", "10", 0] for i in range(24)]
    return {"error": [], "result": {pair: rows, "last": 0}}


class TestKrakenMergeE2E(unittest.TestCase):
    def test_merged_series_drives_link_crowded_entry(self):
        import desk3.producers3 as p3
        root = _mkroot()
        loader = lambda r, now: _fetcher_returning(_hist_payload())(
            "K", now)
        prod = p3.KrakenProducer(root, transport=_kraken_transport,
                                 coinalyze_loader=loader)
        out = prod({"now": NOW})
        series = out["kraken.funding"]["PF_LINKUSD"]
        self.assertGreaterEqual(len(series), 30)  # history backfill
        stamps = [r["timestamp"] for r in series]
        self.assertEqual(stamps, sorted(set(stamps)))  # no dupes
        # the live Kraken print (0.01 at NOW hour) wins its timestamp
        self.assertEqual(series[-1]["fundingRate"], 0.01)
        # fixture-drive the consuming sleeve on the merged series
        import desk3.sleeves.free_kraken_link_crowded as lc
        bars = []
        start = datetime(2026, 10, 19, tzinfo=timezone.utc)
        for i in range(24):
            c = 1.5 if i == 23 else 2.0
            lo = 1.4 if i == 23 else 1.9
            t = start + timedelta(hours=4 * i)
            bars.append({"t": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "o": 2.0, "h": 2.1, "l": lo, "c": c, "v": 100.0})
        view = {"now": NOW.isoformat(),
                "bars": {"PF_LINKUSD|4Hour": bars},
                "positions": [],
                "kraken_inputs": {"sleeves": {"free_kraken_link_basis":
                                    {"quote": {"bid": 1.49, "ask": 1.51}}}},
                "kraken.funding": out["kraken.funding"],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        intents = lc.evaluate(view, {"state_dir": _mkroot()})
        entries = [i for i in intents if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1, intents)
        self.assertEqual(entries[0]["side"], "sell")

    def test_kraken_without_loader_unchanged(self):
        import desk3.producers3 as p3
        root = _mkroot()
        out = p3.KrakenProducer(root, transport=_kraken_transport)(
            {"now": NOW})
        fund = out["kraken.funding"]["PF_LINKUSD"]
        self.assertEqual(len(fund), 1)  # live print only, as before
        self.assertEqual(fund[0]["fundingRate"], 0.01)


class TestWiring(unittest.TestCase):
    def test_run_live_registers_coinalyze(self):
        src = open(os.path.join(ROOT, "desk3", "run_live.py")).read()
        self.assertIn("CoinalyzeFundingProducer", src)
        self.assertIn('"funding_history"', src)

    def test_batch3_kraken_wired_with_loader(self):
        import desk3.producers3 as p3

        class FakeDesk:
            def __init__(self):
                self.prods = {}

            def add_producer(self, name, fn, outputs, sla):
                self.prods[name] = fn
        desk = FakeDesk()
        p3.register_batch3(desk, _mkroot())
        self.assertIsNotNone(desk.prods["kraken"].coinalyze_loader)


if __name__ == "__main__":
    unittest.main()
