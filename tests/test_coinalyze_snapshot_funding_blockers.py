"""R1 FUNDING SOURCE RULING blockers (MIDNA RULING, 2026-10-25).

Audit OPEN #2: Binance premiumIndex returns HTTP 451 (geo) from
this box, leaving 46 Aster crypto sleeves UNFED on a 24/7 product.
Ruling: Coinalyze is the source for the snapshot `funding` scalar
(those sleeves' declared input), mirroring the landed Coinalyze
history pattern in desk3/producers3.py — raw http.client with the
EXACT lowercase "api_key" header, percent values converted to
fractions at parse, source stamped in the snapshot record
("funding_source": "coinalyze"), ONE `funding` key (no parallel
source of truth), fail closed when the fetch fails and no cache
<= 3h old can serve, sleeve code untouched.

Live probe evidence (2026-10-25, in the R1 commit message):
GET /v1/funding-rate?symbols=ADAUSDT_PERP.A,ENJUSDT_PERP.A,
LINKUSDT_PERP.A -> 200 [{"symbol":"ADAUSDT_PERP.A","value":-0.00235,
"update":...}, ...]; value is PERCENT — -0.00235% == the history
series' -2.35e-05 fraction for the same hour.

Fail direction: pre-ruling, desk3.producers has no CoinalyzeFunding
/ parse_coinalyze_current / fetch_coinalyze_current (ImportError)
and register_all wires "binance_funding".
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

NOW = datetime(2026, 10, 25, 20, 0, 0, tzinfo=timezone.utc)

# Live-probed shape (values are PERCENT).
PAYLOAD = [
    {"symbol": "ADAUSDT_PERP.A", "value": -0.00235, "update": 1792959424410},
    {"symbol": "ENJUSDT_PERP.A", "value": 0.000548, "update": 1792959422366},
    {"symbol": "LINKUSDT_PERP.A", "value": -0.001837, "update": 1792959424392},
]
EXPECTED = {"ADAUSDT": -0.0000235, "ENJUSDT": 0.00000548,
            "LINKUSDT": -0.00001837}


def _mkroot():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    return root


def _write_cache(root, fetched_at, rates):
    path = os.path.join(root, "state", "coinalyze_funding_current.json")
    with open(path, "w") as fh:
        json.dump({"fetched_at": fetched_at.isoformat(),
                   "source": "coinalyze", "rates": rates}, fh)
    return path


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body


class FakeConn:
    def __init__(self, status=200, body=b"[]"):
        self.headers = []
        self.request = None
        self._status = status
        self._body = body

    def putrequest(self, method, path):
        self.request = (method, path)

    def putheader(self, name, value):
        self.headers.append((name, value))

    def endheaders(self):
        pass

    def getresponse(self):
        return FakeResponse(self._status, self._body)

    def close(self):
        pass


class TestParseAndFetch(unittest.TestCase):
    def test_coinalyze_payload_produces_the_scalar(self):
        # (a) a Coinalyze-shaped payload produces the scalar map the
        # sleeves read: {SYM: float fraction}, percent -> fraction.
        from desk3.producers import parse_coinalyze_current
        out = parse_coinalyze_current(PAYLOAD)
        self.assertEqual(set(out), set(EXPECTED))
        for sym, want in EXPECTED.items():
            self.assertAlmostEqual(out[sym], want, places=12)
            self.assertIsInstance(out[sym], float)

    def test_fetch_current_uses_exact_api_key_header_and_endpoint(self):
        from desk3.producers import fetch_coinalyze_current
        conn = FakeConn(200, json.dumps(PAYLOAD).encode())
        out = fetch_coinalyze_current("TESTKEY",
                                      conn_factory=lambda t: conn)
        self.assertEqual(conn.headers, [("api_key", "TESTKEY")])
        self.assertTrue(conn.request[1].startswith("/v1/funding-rate?"),
                        conn.request)
        self.assertIn("ADAUSDT_PERP.A", conn.request[1])
        self.assertIn("ENJUSDT_PERP.A", conn.request[1])
        self.assertIn("LINKUSDT_PERP.A", conn.request[1])
        self.assertAlmostEqual(out["ADAUSDT"], EXPECTED["ADAUSDT"],
                               places=12)

    def test_fetch_current_http_error_raises_named(self):
        from desk3.producers import fetch_coinalyze_current
        conn = FakeConn(401, b"{}")
        with self.assertRaises(RuntimeError) as cm:
            fetch_coinalyze_current("BAD", conn_factory=lambda t: conn)
        self.assertIn("401", str(cm.exception))


class TestProducer(unittest.TestCase):
    def test_producer_serves_funding_with_source_stamp(self):
        # (a) at the producer layer: ONE funding key + source stamp.
        from desk3.producers import CoinalyzeFunding, parse_coinalyze_current
        root = _mkroot()
        p = CoinalyzeFunding(
            root, fetcher=lambda syms: parse_coinalyze_current(PAYLOAD))
        out = p({"now": NOW})
        self.assertEqual(set(out), {"funding", "funding_source"})
        self.assertEqual(out["funding_source"], "coinalyze")
        self.assertAlmostEqual(out["funding"]["LINKUSDT"],
                               EXPECTED["LINKUSDT"], places=12)
        self.assertIsNone(p.last_error)
        # the fetch is cached for the fail-closed fallback path
        cache = json.load(open(os.path.join(
            root, "state", "coinalyze_funding_current.json")))
        self.assertEqual(cache["source"], "coinalyze")
        self.assertAlmostEqual(cache["rates"]["ADAUSDT"],
                               EXPECTED["ADAUSDT"], places=12)

    def test_per_symbol_isolation(self):
        # (c) one malformed / missing symbol never zeroes the others
        # (the B3 all-or-nothing defect, re-pinned on the new source).
        from desk3.producers import (CoinalyzeFunding,
                                     parse_coinalyze_current)
        payload = [PAYLOAD[0],
                   {"symbol": "ENJUSDT_PERP.A", "value": "not-a-number",
                    "update": 1},
                   {"symbol": "DOGEUSDT_PERP.A", "value": 0.5,
                    "update": 1}]  # unknown symbol: ignored
        parsed = parse_coinalyze_current(payload)
        self.assertEqual(set(parsed), {"ADAUSDT"})
        root = _mkroot()
        p = CoinalyzeFunding(root, fetcher=lambda syms: {
            "ADAUSDT": -0.01, "ENJUSDT": None, "LINKUSDT": "bad"})
        out = p({"now": NOW})
        self.assertEqual(out["funding"], {"ADAUSDT": -0.01})


class TestFailClosed(unittest.TestCase):
    def test_absent_key_fails_closed_and_names_error(self):
        # (b) no key, no cache: {} and last_error names the cause —
        # cycle.py surfaces last_error in producer_errors.
        import desk3.producers3 as p3
        from desk3.producers import CoinalyzeFunding
        root = _mkroot()
        p = CoinalyzeFunding(root)
        with mock.patch.object(p3, "_coinalyze_api_key",
                               lambda: None):
            out = p({"now": NOW})
        self.assertEqual(out, {})
        self.assertIn("coinalyze_key_missing", p.last_error)

    def test_fetch_failure_no_cache_fails_closed_named(self):
        from desk3.producers import CoinalyzeFunding
        root = _mkroot()

        def boom(syms):
            raise RuntimeError("HTTP 401 for coinalyze funding-rate")
        p = CoinalyzeFunding(root, fetcher=boom)
        self.assertEqual(p({"now": NOW}), {})
        self.assertIn("401", p.last_error)

    def test_stale_cache_fails_closed_and_names_stale(self):
        # (b) cache older than 3h must NOT serve when the fetch fails.
        from desk3.producers import CoinalyzeFunding
        root = _mkroot()
        _write_cache(root, NOW - timedelta(hours=4),
                     {"ADAUSDT": -0.001})

        def boom(syms):
            raise RuntimeError("HTTP 503")
        p = CoinalyzeFunding(root, fetcher=boom)
        self.assertEqual(p({"now": NOW}), {})
        self.assertIn("stale", p.last_error.lower())

    def test_fresh_cache_serves_on_fetch_failure(self):
        # Mirror of the landed history pattern: a <=3h cache may
        # serve when the live fetch fails (still one source: coinalyze).
        from desk3.producers import CoinalyzeFunding
        root = _mkroot()
        _write_cache(root, NOW - timedelta(hours=1),
                     {"ADAUSDT": -0.001, "LINKUSDT": 0.0002})

        def boom(syms):
            raise RuntimeError("HTTP 503")
        p = CoinalyzeFunding(root, fetcher=boom)
        out = p({"now": NOW})
        self.assertEqual(out["funding"],
                         {"ADAUSDT": -0.001, "LINKUSDT": 0.0002})
        self.assertEqual(out["funding_source"], "coinalyze")


class TestWiringAndSnapshot(unittest.TestCase):
    def test_register_all_wires_coinalyze_not_binance(self):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        from desk3.producers import register_all
        root = _mkroot()
        desk = Desk(root, broker=FakeBroker(), sleeve_path=root)
        register_all(desk, root, env={})
        try:
            # FUNDING-OKX-20261115 supersedes the registration
            # half of this pin: register_all now wires the OKX
            # history producer for the "funding" key (record
            # form; CoinalyzeFunding is retained unregistered).
            # The not-Binance half of the pin stands unchanged.
            self.assertIn("okx_funding", desk.producers)
            self.assertNotIn("binance_funding", desk.producers)
            spec = desk.registry.producers["okx_funding"]
            self.assertEqual(spec["outputs"], ("funding",))
        finally:
            desk.close()
        src = open(os.path.join(ROOT, "desk3", "producers.py")).read()
        self.assertNotIn("fapi.binance.com", src)
        self.assertNotIn("/fapi/v1/premiumIndex", src)
        self.assertNotIn("BinanceFunding", src)

    def test_snapshot_record_carries_source_stamp(self):
        # The stamp lands in the immutable snapshot itself (the
        # record sleeves are evaluated against), producer_errors clean.
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        from desk3.producers import CoinalyzeFunding, parse_coinalyze_current
        root = _mkroot()
        desk = Desk(root, broker=FakeBroker(), sleeve_path=root)
        desk.add_producer(
            "coinalyze_funding_current",
            CoinalyzeFunding(
                root,
                fetcher=lambda syms: parse_coinalyze_current(PAYLOAD)),
            ["funding"], 28800)
        try:
            roll = desk.run_cycle(now=NOW)
        finally:
            desk.close()
        self.assertEqual(roll["producer_errors"], {})
        data = desk._last_data
        self.assertEqual(data["funding_source"], "coinalyze")
        self.assertAlmostEqual(data["funding"]["ADAUSDT"],
                               EXPECTED["ADAUSDT"], places=12)
        snap_dir = os.path.join(root, "state", "snapshots")
        docs = [json.load(open(os.path.join(snap_dir, n)))
                for n in os.listdir(snap_dir) if n.endswith(".json")]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["data"]["funding_source"], "coinalyze")


if __name__ == "__main__":
    unittest.main()
