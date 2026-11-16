"""BROKER-422-BODY-20261027 blockers: the broker door must journal
the HTTP error response BODY (Alpaca's 422 body names the failing
field). Before the cure, netfetch.fetch_bytes read the body and
discarded it, FetchError carried only the status, and the
dispatcher's broker_unavailable journal row held a bare
"FetchError:HTTP 422 for ..." string: the failing field was
unknowable from desk records (STAGE-C-PROGRESS diagnostic note,
2026-10-26).

Fail direction (proven at cure time by temporary revert): on the old
netfetch, FetchError has no .body and str() carries no body text;
on the old dispatcher the journal row has no error_body/payload
keys. Every test below fails there.
"""
import http.server
import json
import os
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BODY = json.dumps({"code": 42210000,
                   "message": "invalid symbol: AG|1Hour"})


class TestFetchErrorCarriesBody(unittest.TestCase):
    def test_fetch_error_body_in_message_and_attribute(self):
        from desk3.netfetch import FetchError
        e = FetchError(422, "https://paper-api.alpaca.markets/v2/orders",
                       body=BODY)
        self.assertEqual(e.status, 422)
        self.assertEqual(e.body, BODY)
        self.assertIn("invalid symbol", str(e))

    def test_fetch_error_without_body_keeps_old_shape(self):
        from desk3.netfetch import FetchError
        e = FetchError(422, "https://example.invalid/x")
        self.assertIsNone(e.body)
        self.assertEqual(str(e), "HTTP 422 for https://example.invalid/x")

    def test_live_http_422_body_reaches_caller(self):
        from desk3.netfetch import fetch_json, FetchError

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                data = BODY.encode()
                self.send_response(422)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        env = {k: v for k, v in os.environ.items()
               if k.lower() not in ("http_proxy", "https_proxy")}
        try:
            with mock.patch.dict(os.environ, env, clear=True):
                with self.assertRaises(FetchError) as cm:
                    fetch_json(
                        f"http://127.0.0.1:{srv.server_address[1]}/v2/orders",
                        method="POST", body=b"{}")
        finally:
            srv.shutdown()
        self.assertEqual(cm.exception.status, 422)
        self.assertIn("invalid symbol", cm.exception.body or "")
        self.assertIn("invalid symbol", str(cm.exception))


class TestDispatcherJournalsBodyAndPayload(unittest.TestCase):
    def _intent(self):
        # DOOR-PREFLIGHT-20261030 supersession, named: the original
        # fixture symbol "AG|1Hour" is now rejected locally by the
        # door pre-flight validator before it can reach the wire
        # (covered by test_reconcile_fillcapture_20261030_blockers),
        # so this body-capture fixture uses the wire-clean "AG" and
        # the 422 arrives from the broker double, as before. Every
        # body and payload assertion below is unchanged.
        return {"intent_id": "i-422", "kind": "entry", "symbol": "AG",
                "side": "buy", "qty": 67, "order_type": "market",
                "limit_price": None, "price_hint": 14.87,
                "time_in_force": "day", "position_intent": "buy_to_open"}

    def test_broker_unavailable_row_carries_body_and_payload(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        from desk3.netfetch import FetchError

        class Bad(FakeBroker):
            def submit_order(self, *a, **k):
                raise FetchError(
                    422, "https://paper-api.alpaca.markets/v2/orders",
                    body=BODY)

        disp = Dispatcher(tempfile.mkdtemp(), Bad(),
                          slices={"s": {"capital_usd": 10000.0,
                                        "cash_usd": 10000.0}},
                          price_lookup=lambda s: 100.0)
        r = disp.process_intent(self._intent(), "s")
        # READINESS-DSP1-20261112 supersession, named: a 422 is a
        # deterministic verdict and is now consumed TERMINALLY in
        # process_intent (status "rejected", never persisted to the
        # pending store — persisting it made the drain submit the
        # identical payload a second time). The pre-cure form of
        # this test pinned "queued" plus a durable pending entry;
        # that was the DSP-1 defect, and the pin is amended here.
        # Every body and payload assertion below is unchanged: the
        # broker_unavailable row still carries the body and the
        # exact submitted payload.
        self.assertEqual(r["status"], "rejected")
        self.assertIn("invalid symbol", r["last_error"])
        rows = [json.loads(l) for l in open(disp.djournal) if l.strip()]
        bu = [x for x in rows if x["event"] == "broker_unavailable"]
        self.assertEqual(len(bu), 1)
        self.assertIn("invalid symbol", bu[0]["error_body"] or "")
        self.assertEqual(bu[0]["symbol"], "AG")
        self.assertEqual(bu[0]["qty"], 67)
        self.assertEqual(bu[0]["order_type"], "market")
        self.assertEqual(bu[0]["time_in_force"], "day")
        # No durable pending entry: the verdict already consumed
        # the intent (READINESS-DSP1-20261112).
        self.assertEqual(disp.pending_entries(), [])


if __name__ == "__main__":
    unittest.main()
