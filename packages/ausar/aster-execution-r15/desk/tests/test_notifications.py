import base64
import json
import os
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from backend.lab import Lab
from backend.http_transport import ResponseTooLarge, bounded_http
from backend.notifications import DeliveryFailure, NotificationDispatcher, TYPEFULLY, _http, _https, _push
from backend.store import DeskError, Store


UTC = timezone.utc


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "desk.sqlite")
        self.lab = Lab(self.store)
        self.env = patch.dict(os.environ, {"ASTER_NOTIFICATION_WEBHOOK_URL": "https://example.invalid/notify", "ASTER_NOTIFICATION_WEBHOOK_TOKEN": "private-webhook-token", "ASTER_TYPEFULLY_API_KEY": "private-typefully-key", "ASTER_TYPEFULLY_SOCIAL_SET_ID": "42", "ASTER_VAPID_PUBLIC_KEY": "public-vapid", "ASTER_VAPID_PRIVATE_KEY": "private-vapid", "ASTER_VAPID_SUBJECT": "mailto:desk@example.invalid"}, clear=True)
        self.env.start()
        self.calls = []
        self.reply = {"status": 200, "body": {"id": "remote-1"}}
        self.dispatcher = NotificationDispatcher(self.store, self.lab, self.http, self.push)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def http(self, method, url, payload, headers):
        self.calls.append((method, url, payload, headers))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply

    def push(self, *args):
        self.calls.append(args)
        return self.reply

    def message(self, body="Actual local handoff"):
        return self.lab.message({"sender": "accountant", "recipient": "chief", "topic": "Ledger health", "body": body, "source": "local ledger", "confidence": "high"})

    def channel_items(self, channel):
        return [i for i in self.dispatcher.snapshot()["items"] if i["channel"] == channel]

    def test_external_channels_are_off_and_in_app_delivers_once_with_reader_cursor(self):
        status = self.dispatcher.status()
        self.assertEqual([c["channel"] for c in status["channels"] if c["enabled"]], ["in_app"])
        self.message()
        result = self.dispatcher.run_once()
        self.assertEqual(result["delivered"], 1)
        self.assertFalse(self.calls)
        self.assertEqual(self.dispatcher.run_once()["processed"], 0)
        item = self.channel_items("in_app")[0]
        self.assertEqual(item["payload"]["body"], "Actual local handoff")
        self.assertEqual(item["receipts"][0]["state"], "accepted")
        self.dispatcher.read("operator", item["event_id"])
        with self.assertRaises(DeskError):
            self.dispatcher.read("operator", item["event_id"] - 1)
        self.assertNotIn("private-", json.dumps(self.dispatcher.snapshot()))

    def test_new_enablement_baselines_history_without_external_replay(self):
        self.message("Before destination enablement")
        self.dispatcher.configure("webhook", True)
        self.message("After destination enablement")
        self.dispatcher.run_once()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][2]["body"], "After destination enablement")
        self.assertTrue(self.calls[0][3]["Idempotency-Key"])
        rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        self.assertEqual(rebuilt.run_once()["processed"], 0)
        self.assertEqual(len(self.calls), 1)

    def test_definite_rate_limit_retries_but_ambiguous_post_never_replays(self):
        self.dispatcher.configure("webhook", True)
        self.message()
        clock = datetime.now(UTC)
        self.reply = {"status": 429, "body": None}
        self.dispatcher.run_once(clock)
        item = self.channel_items("webhook")[0]
        self.assertEqual(item["status"], "retry")
        self.reply = {"status": 200, "body": {"id": "accepted"}}
        self.dispatcher.run_once(clock + timedelta(seconds=4))
        self.assertEqual(len(self.calls), 1)
        self.dispatcher.run_once(clock + timedelta(seconds=5))
        self.assertEqual(self.channel_items("webhook")[0]["status"], "delivered")
        self.message("Next handoff")
        self.reply = DeliveryFailure("Timeout after POST", ambiguous=True)
        self.dispatcher.run_once(clock + timedelta(seconds=6))
        unknown = self.channel_items("webhook")[0]
        self.assertEqual(unknown["status"], "unknown")
        calls = len(self.calls)
        self.dispatcher.run_once(clock + timedelta(minutes=20))
        self.assertEqual(len(self.calls), calls)
        with self.assertRaises(DeskError):
            self.dispatcher.retry(unknown["id"])
        self.dispatcher.resolve(unknown["id"], True, "operator-verified-provider-id")
        self.assertEqual(self.channel_items("webhook")[0]["status"], "delivered")

    def test_interrupted_external_send_recovers_unknown_without_send(self):
        self.dispatcher.configure("webhook", True)
        queued = self.dispatcher.queue({"channel": "webhook", "title": "Explicit notice", "body": "Factual body"})
        with self.store.transaction() as con:
            con.execute("UPDATE n_outbox SET status='sending' WHERE id=?", (queued["id"],))
        rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        rebuilt.run_once()
        self.assertFalse(self.calls)
        self.assertEqual(self.channel_items("webhook")[0]["status"], "unknown")

    def test_webpush_expired_subscription_is_pruned_and_keys_hidden(self):
        self.dispatcher.configure("webpush", True)
        subscription = self.dispatcher.subscribe({"endpoint": "https://push.example.invalid/token", "keys": {"p256dh": "browser-public-key", "auth": "browser-auth-secret"}})
        self.message()
        self.reply = {"status": 410, "body": None}
        self.dispatcher.run_once()
        self.assertEqual(self.dispatcher.status()["active_subscriptions"], 0)
        self.assertEqual(self.channel_items("webpush")[0]["status"], "failed")
        exported = json.dumps(self.dispatcher.snapshot())
        self.assertNotIn("browser-auth-secret", exported)
        self.assertNotIn("push.example.invalid", exported)
        self.assertEqual(self.calls[0][0]["keys"]["auth"], "browser-auth-secret")

    def test_typefully_exact_contract_text_only_skips_media(self):
        self.dispatcher.configure("typefully", True)
        self.reply = {"status": 201, "body": {"id": "draft-1"}}
        self.dispatcher.queue({"channel": "typefully", "title": "Explicit operational notice", "body": "No trade recommendation"})
        self.dispatcher.run_once()
        self.assertEqual(len(self.calls), 1)
        method, url, payload, headers = self.calls[0]
        self.assertEqual((method, url), ("POST", TYPEFULLY + "/v2/social-sets/42/drafts"))
        self.assertEqual(payload["publish_at"], "now")
        self.assertNotIn("media_ids", payload["platforms"]["x"]["posts"][0])
        self.assertEqual(self.channel_items("typefully")[0]["status"], "delivered")
        self.assertIn("X publication is unverified", self.channel_items("typefully")[0]["receipts"][-1]["detail"]["scope"])

    def test_explicit_png_upload_processing_and_draft_have_durable_receipts(self):
        self.dispatcher.configure("typefully", True)
        def transport(method, url, payload, headers):
            self.calls.append((method, url, payload, headers))
            if url.endswith("/media/upload"):
                return {"status": 201, "body": {"media_id": "media-1", "upload_url": "https://upload.example.invalid/presigned-secret"}}
            if method == "PUT":
                return {"status": 201, "body": None}
            if method == "GET":
                return {"status": 200, "body": {"status": "ready"}}
            return {"status": 201, "body": {"id": "draft-media"}}
        self.dispatcher.transport = transport
        png = b"\x89PNG\r\n\x1a\nexplicit-fixture-image"
        queued = self.dispatcher.queue({"channel": "typefully", "title": "Operator supplied chart", "body": "Source-labelled data", "media": {"content_base64": base64.b64encode(png).decode(), "file_name": "receipt.png", "alt_text": "Explicit operator image"}})
        self.dispatcher.run_once()
        self.assertEqual([c[0] for c in self.calls], ["POST", "PUT", "GET", "POST"])
        self.assertEqual(self.calls[-1][2]["platforms"]["x"]["posts"][0]["media_ids"], ["media-1"])
        item = self.channel_items("typefully")[0]
        self.assertEqual([r["stage"] for r in item["receipts"]], ["media_create", "media_upload", "media_process", "delivery"])
        with self.store.connect() as con:
            media = con.execute("SELECT * FROM n_media WHERE item_id=?", (queued["id"],)).fetchone()
            self.assertEqual(media["state"], "ready")
            self.assertIsNone(media["upload_url"])
        self.assertNotIn("presigned-secret", json.dumps(self.dispatcher.snapshot()))

    def test_unconfigured_destination_cannot_be_enabled(self):
        self.dispatcher.typefully_key = ""
        with self.assertRaises(DeskError):
            self.dispatcher.configure("typefully", True)
        with self.assertRaises(DeskError):
            self.dispatcher.subscribe({"endpoint": "http://invalid", "keys": {}})

    def test_pause_resume_does_not_resurrect_cancelled_batch_items(self):
        self.dispatcher.configure("webhook", True)
        first = self.dispatcher.queue({"channel": "webhook", "title": "First", "body": "First explicit message"})
        second = self.dispatcher.queue({"channel": "webhook", "title": "Second", "body": "Cancelled before its turn"})
        def transport(*args):
            self.calls.append(args)
            self.dispatcher.configure("webhook", False)
            self.dispatcher.configure("webhook", True)
            return {"status": 200, "body": {"id": "accepted-first"}}
        self.dispatcher.transport = transport
        self.dispatcher.run_once()
        items = {i["id"]: i for i in self.channel_items("webhook")}
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(items[first["id"]]["status"], "delivered")
        self.assertEqual(items[second["id"]]["status"], "failed")
        self.assertEqual(items[second["id"]]["attempts"], 0)

    def test_new_subscription_baselines_uncollected_history(self):
        self.dispatcher.configure("webpush", True)
        self.message("Before subscription")
        subscription = self.dispatcher.subscribe({"endpoint": "https://push.example.invalid/new", "keys": {"p256dh": "public", "auth": "auth"}})
        self.message("After subscription")
        self.dispatcher.run_once()
        items = self.channel_items("webpush")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["recipient"], subscription["id"])
        self.assertEqual(items[0]["payload"]["body"], "After subscription")

    def test_unsubscribe_cancels_pending_deliveries_and_resubscribe_baselines(self):
        self.dispatcher.configure("webpush", True)
        payload = {"endpoint": "https://push.example.invalid/resume", "keys": {"p256dh": "public", "auth": "auth"}}
        subscription = self.dispatcher.subscribe(payload)
        old = self.dispatcher.queue({"channel": "webpush", "title": "Old", "body": "Queued before unsubscribe"})
        self.dispatcher.unsubscribe(subscription["id"])
        self.message("While unsubscribed")
        resumed = self.dispatcher.subscribe(payload)
        self.assertEqual(resumed["id"], subscription["id"])
        self.message("After resubscribe")
        self.dispatcher.run_once()
        items = {i["id"]: i for i in self.channel_items("webpush")}
        self.assertEqual(items[old["id"]]["status"], "failed")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1]["body"], "After resubscribe")

    def test_idempotent_media_upload_retries_server_failure_without_new_media(self):
        self.dispatcher.configure("typefully", True)
        uploaded = False
        def transport(method, url, payload, headers):
            nonlocal uploaded
            self.calls.append((method, url, payload, headers))
            if url.endswith("/media/upload"):
                return {"status": 201, "body": {"media_id": "media-retry", "upload_url": "https://upload.example.invalid/retry"}}
            if method == "PUT":
                if not uploaded:
                    uploaded = True
                    return {"status": 503, "body": None}
                return {"status": 204, "body": None}
            if method == "GET":
                return {"status": 200, "body": {"status": "ready"}}
            return {"status": 201, "body": {"id": "draft-retry"}}
        self.dispatcher.transport = transport
        queued = self.dispatcher.queue({"channel": "typefully", "title": "Retry", "body": "Explicit", "media": {"content_base64": base64.b64encode(b"\x89PNG\r\n\x1a\nfixture").decode()}})
        clock = datetime.now(UTC)
        self.dispatcher.run_once(clock)
        self.assertEqual(self.channel_items("typefully")[0]["status"], "retry")
        self.dispatcher.run_once(clock + timedelta(seconds=5))
        item = self.channel_items("typefully")[0]
        self.assertEqual(item["id"], queued["id"])
        self.assertEqual(item["status"], "delivered")
        self.assertEqual([call[0] for call in self.calls], ["POST", "PUT", "PUT", "GET", "POST"])

    def test_webhook_acceptance_does_not_require_json_object_response(self):
        self.dispatcher.configure("webhook", True)
        self.dispatcher.queue({"channel": "webhook", "title": "Accepted", "body": "Provider returns JSON array"})
        self.reply = {"status": 200, "body": ["accepted"]}
        self.dispatcher.run_once()
        self.assertEqual(self.channel_items("webhook")[0]["status"], "delivered")

    def test_reconciliation_receipt_and_state_are_atomic(self):
        self.dispatcher.configure("webhook", True)
        queued = self.dispatcher.queue({"channel": "webhook", "title": "Unknown", "body": "Needs a factual reconciliation"})
        with self.store.transaction() as con:
            con.execute("UPDATE n_outbox SET status='unknown' WHERE id=?", (queued["id"],))
        with patch.object(self.dispatcher, "_receipt", side_effect=OSError("simulated receipt persistence failure")):
            with self.assertRaises(OSError):
                self.dispatcher.resolve(queued["id"], True, "factual-id")
        self.assertEqual(self.channel_items("webhook")[0]["status"], "unknown")

    def test_lock_open_failure_releases_dispatch_mutex(self):
        with patch("backend.notifications.open", side_effect=OSError("temporary lock failure")):
            with self.assertRaises(OSError):
                self.dispatcher.run_once()
        self.message()
        self.assertEqual(self.dispatcher.run_once().get("delivered"), 1)

    def test_retry_backoff_starts_after_slow_attempt_completes(self):
        self.dispatcher.configure("webhook", True)
        queued = self.dispatcher.queue({"channel": "webhook", "title": "Slow", "body": "Delayed response"})
        started = datetime.now(UTC) + timedelta(seconds=1)
        current = started
        def clock(value=None):
            return current if value is None else value
        def transport(*args):
            nonlocal current
            current = started + timedelta(seconds=30)
            return {"status": 429, "body": None}
        self.dispatcher.transport = transport
        with patch("backend.notifications.utc_clock", side_effect=clock):
            self.dispatcher.run_once()
        item = self.channel_items("webhook")[0]
        self.assertEqual(item["id"], queued["id"])
        self.assertEqual(datetime.fromisoformat(item["next_attempt_at"]), started + timedelta(seconds=35))

    def test_slow_delivery_yields_before_claiming_next_item_and_resumes_next_pass(self):
        self.dispatcher.configure("webhook", True)
        first = self.dispatcher.queue({"channel": "webhook", "title": "Slow first", "body": "Complete this acceptance"})
        second = self.dispatcher.queue({"channel": "webhook", "title": "Waiting second", "body": "Preserve until the next pass"})
        elapsed = 0
        def transport(*args):
            nonlocal elapsed
            self.calls.append(args)
            elapsed += self.dispatcher.BATCH_START_BUDGET_SECONDS + 1
            return {"status": 200, "body": {"id": "accepted"}}
        self.dispatcher.transport = transport
        with patch("backend.notifications.monotonic", side_effect=lambda: elapsed):
            result = self.dispatcher.run_once()
            self.assertTrue(result["budget_exhausted"])
            self.assertEqual(result["processed"], 1)
            self.assertEqual(result["deferred_due"], 1)
            items = {i["id"]: i for i in self.channel_items("webhook")}
            self.assertEqual(items[first["id"]]["status"], "delivered")
            self.assertEqual(items[second["id"]]["status"], "queued")
            self.assertEqual(items[second["id"]]["attempts"], 0)
            resumed = self.dispatcher.run_once()
        self.assertEqual(resumed["processed"], 1)
        self.assertEqual(resumed["deferred_due"], 0)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(next(i for i in self.channel_items("webhook") if i["id"] == second["id"])["status"], "delivered")

    def test_invalid_channel_types_and_malformed_https_are_validation_errors(self):
        for channel in ([], {}, None, 123):
            with self.subTest(channel=channel), self.assertRaises(DeskError):
                self.dispatcher.queue({"channel": channel, "title": "Invalid", "body": "Input"})
        self.assertFalse(_https("https://[malformed"))
        self.assertFalse(_https("https://example.invalid:invalid/notify"))

    def test_local_cursor_passes_cancelled_notices_but_cannot_skip_pending(self):
        old = self.dispatcher.queue({"title": "Cancelled", "body": "Paused before local delivery"})
        self.dispatcher.configure("in_app", False)
        self.dispatcher.configure("in_app", True)
        delivered = self.dispatcher.queue({"title": "Delivered", "body": "Later available notice"})
        self.dispatcher.run_once()
        items = {i["id"]: i for i in self.channel_items("in_app")}
        self.assertEqual(items[old["id"]]["status"], "failed")
        self.dispatcher.read("operator", items[delivered["id"]]["event_id"])
        pending = self.dispatcher.queue({"title": "Pending", "body": "Do not skip this pending notice"})
        later = self.dispatcher.queue({"title": "Later", "body": "Simulate later durable availability"})
        with self.store.transaction() as con:
            con.execute("UPDATE n_outbox SET status='delivered' WHERE id=?", (later["id"],))
        items = {i["id"]: i for i in self.channel_items("in_app")}
        self.assertEqual(items[pending["id"]]["status"], "queued")
        with self.assertRaises(DeskError):
            self.dispatcher.read("operator", items[later["id"]]["event_id"])

    def test_accepted_receipt_and_final_status_roll_back_together(self):
        self.dispatcher.configure("webhook", True)
        queued = self.dispatcher.queue({"channel": "webhook", "title": "Acceptance", "body": "Crash before local status commit"})
        with self.store.transaction() as con:
            con.execute("CREATE TRIGGER simulate_finalization_failure BEFORE UPDATE OF status ON n_outbox WHEN NEW.status='delivered' BEGIN SELECT RAISE(ABORT, 'simulated commit failure'); END")
        with self.assertRaises(Exception):
            self.dispatcher.run_once()
        item = self.channel_items("webhook")[0]
        self.assertEqual(item["id"], queued["id"])
        self.assertEqual(item["status"], "sending")
        self.assertEqual(item["receipts"], [])
        with self.store.transaction() as con:
            con.execute("DROP TRIGGER simulate_finalization_failure")
        self.dispatcher.run_once()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.channel_items("webhook")[0]["status"], "unknown")

    def test_two_dispatchers_do_not_send_the_same_pending_item_concurrently(self):
        self.dispatcher.configure("webhook", True)
        self.dispatcher.queue({"channel": "webhook", "title": "Concurrent", "body": "One provider acceptance"})
        entered, release = threading.Event(), threading.Event()
        def transport(*args):
            self.calls.append(args)
            entered.set()
            if not release.wait(3):
                raise RuntimeError("test transport timed out")
            return {"status": 200, "body": {"id": "once"}}
        self.dispatcher.transport = transport
        alias = Path(self.temp.name) / "database-alias.sqlite"
        alias.symlink_to(self.store.path)
        alias_store = Store(alias)
        rebuilt = NotificationDispatcher(alias_store, Lab(alias_store), self.http, self.push)
        failures = []
        def run():
            try:
                self.dispatcher.run_once()
            except BaseException as exc:
                failures.append(exc)
        thread = threading.Thread(target=run)
        thread.start()
        try:
            self.assertTrue(entered.wait(3))
            self.assertTrue(rebuilt.run_once()["busy"])
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertFalse(failures)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.channel_items("webhook")[0]["attempts"], 1)

    def test_retry_budget_is_bounded_and_definite_failure_needs_operator_retry(self):
        self.dispatcher.configure("webhook", True)
        queued = self.dispatcher.queue({"channel": "webhook", "title": "Rate limited", "body": "Bounded automatic attempts"})
        self.reply = {"status": 429, "body": None}
        clock = datetime.now(UTC)
        for offset in (0, 5, 15, 35, 75):
            self.dispatcher.run_once(clock + timedelta(seconds=offset))
        item = self.channel_items("webhook")[0]
        self.assertEqual(item["status"], "failed")
        self.assertEqual(item["attempts"], self.dispatcher.MAX_ATTEMPTS)
        self.dispatcher.run_once(clock + timedelta(hours=1))
        self.assertEqual(len(self.calls), 5)
        self.dispatcher.retry(queued["id"])
        self.reply = {"status": 204, "body": None}
        self.dispatcher.run_once(clock + timedelta(hours=2))
        self.assertEqual(len(self.calls), 6)
        self.assertEqual(self.channel_items("webhook")[0]["attempts"], 1)

    def test_typefully_discloses_text_truncation(self):
        self.dispatcher.configure("typefully", True)
        self.reply = {"status": 201, "body": {"id": "draft-long"}}
        self.dispatcher.queue({"channel": "typefully", "title": "Long", "body": "x" * 500})
        self.dispatcher.run_once()
        self.assertEqual(len(self.calls[0][2]["platforms"]["x"]["posts"][0]["text"]), 280)
        self.assertIn("truncated from 506 to 280", self.channel_items("typefully")[0]["receipts"][-1]["detail"]["scope"])

    def test_typefully_rejects_changed_media_before_any_provider_effect(self):
        self.dispatcher.configure("typefully", True)
        queued = self.dispatcher.queue({"channel": "typefully", "title": "Image", "body": "Corrupted storage must not publish", "media": {"content_base64": base64.b64encode(b"\x89PNG\r\n\x1a\nfixture").decode()}})
        with self.store.transaction() as con:
            con.execute("UPDATE n_media SET content_base64=? WHERE item_id=?", (base64.b64encode(b"changed").decode(), queued["id"]))
        self.dispatcher.run_once()
        self.assertEqual(len(self.calls), 0)
        item = next(i for i in self.channel_items("typefully") if i["id"] == queued["id"])
        self.assertEqual(item["status"], "failed")
        self.assertIn("integrity check", item["error"])

    def test_queue_pause_race_does_not_append_an_unapproved_pending_item(self):
        self.dispatcher.configure("webhook", True)
        def enabled(channel):
            self.dispatcher.configure(channel, False)
            return True
        with patch.object(self.dispatcher, "_channel_enabled", side_effect=enabled):
            with self.assertRaises(DeskError):
                self.dispatcher.queue({"channel": "webhook", "title": "Raced pause", "body": "Do not queue"})
        self.assertEqual(self.channel_items("webhook"), [])

    def test_http_transport_preserves_status_and_retry_classification(self):
        with patch("backend.notifications.bounded_http", return_value=(503, b"provider error")) as transport:
            self.assertEqual(_http("POST", "https://example.invalid/notify", {"title": "test"})["status"], 503)
        self.assertEqual(transport.call_args.kwargs["timeout_seconds"], 8)
        self.assertFalse(transport.call_args.kwargs["follow_redirects"])
        for method, retryable, ambiguous in (("GET", True, False), ("PUT", True, False), ("POST", False, True)):
            for error in (TimeoutError("simulated deadline"), httpx.ConnectError("simulated unavailable transport")):
                with self.subTest(method=method, error=type(error).__name__), patch("backend.notifications.bounded_http", side_effect=error):
                    with self.assertRaises(DeliveryFailure) as failure:
                        _http(method, "https://example.invalid/notify", b"fixture")
                    self.assertEqual(failure.exception.retryable, retryable)
                    self.assertEqual(failure.exception.ambiguous, ambiguous)
        with patch("backend.notifications.bounded_http", side_effect=ResponseTooLarge("simulated size limit")):
            with self.assertRaises(DeliveryFailure) as failure:
                _http("POST", "https://example.invalid/notify", b"fixture")
        self.assertTrue(failure.exception.ambiguous)
        self.assertFalse(failure.exception.retryable)

    def test_real_loopback_dribbling_post_deadline_is_unknown_and_not_replayed(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                self.send_response(200)
                self.send_header("Content-Length", "100")
                self.end_headers()
                try:
                    for _ in range(100):
                        self.wfile.write(b"x")
                        self.wfile.flush()
                        time.sleep(.02)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            def log_message(self, *args):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        thread.start()
        def short_deadline(*args, **kwargs):
            kwargs["timeout_seconds"] = .15
            return bounded_http(*args, **kwargs)
        started = time.monotonic()
        try:
            with patch("backend.notifications.bounded_http", side_effect=short_deadline):
                with self.assertRaises(DeliveryFailure) as failure:
                    _http("POST", f"http://127.0.0.1:{server.server_port}/", {"body": "loopback-only fixture"})
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, .7)
            self.assertTrue(failure.exception.ambiguous)
            self.assertFalse(failure.exception.retryable)
            self.assertEqual(len(requests), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(1)

    def push_crypto_fixture(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        private = ec.generate_private_key(ec.SECP256R1())
        receiver = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        encoded = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
        return {"endpoint": "https://push.example.invalid/encrypted-fixture", "keys": {"p256dh": encoded(receiver), "auth": encoded(b"fixture-auth-1234")}}, encoded(private.private_numbers().private_value.to_bytes(32, "big"))

    def test_actual_webpush_encryption_and_signing_use_bounded_transport(self):
        subscription, private_key = self.push_crypto_fixture()
        with patch("backend.notifications.bounded_http", return_value=(201, b"")) as transport:
            self.assertEqual(_push(subscription, {"title": "Encrypted fixture"}, private_key, "mailto:test@example.invalid")["status"], 201)
        self.assertEqual(transport.call_args.args[:2], ("POST", subscription["endpoint"]))
        sent = transport.call_args.kwargs
        self.assertEqual(sent["timeout_seconds"], 8)
        self.assertEqual(sent["headers"]["content-encoding"], "aes128gcm")
        self.assertTrue({key.lower(): value for key, value in sent["headers"].items()}["authorization"].startswith("vapid "))
        self.assertIsInstance(sent["body"], bytes)
        self.assertNotIn(b"Encrypted fixture", sent["body"])
        with patch("backend.notifications.bounded_http", return_value=(410, b"expired")):
            self.assertEqual(_push(subscription, {"title": "Fixture"}, private_key, "mailto:test@example.invalid")["status"], 410)

    def test_webpush_deadline_and_oversized_response_remain_unknown(self):
        subscription, private_key = self.push_crypto_fixture()
        for error in (TimeoutError("deadline"), ResponseTooLarge("bounded response")):
            with self.subTest(error=type(error).__name__), patch("backend.notifications.bounded_http", side_effect=error) as transport:
                with self.assertRaises(DeliveryFailure) as failure:
                    _push(subscription, {"title": "Fixture"}, private_key, "mailto:test@example.invalid")
                self.assertTrue(failure.exception.ambiguous)
                self.assertFalse(failure.exception.retryable)
                self.assertEqual(transport.call_count, 1)

    def test_push_transport_known_expiry_and_missing_dependency_are_truthful(self):
        from pywebpush import WebPushException
        with patch("pywebpush.webpush", side_effect=WebPushException("Gone", response=SimpleNamespace(status_code=410))):
            self.assertEqual(_push({"endpoint": "https://push.example.invalid/test", "keys": {}}, {"title": "fixture"}, "fixture-key", "mailto:test@example.invalid")["status"], 410)
        with patch.dict("sys.modules", {"pywebpush": None}):
            with self.assertRaises(DeliveryFailure) as failure:
                _push({}, {}, "fixture-key", "mailto:test@example.invalid")
        self.assertIn("dependency is unavailable", str(failure.exception))
        self.assertFalse(failure.exception.ambiguous)

    def test_legacy_subscription_migration_preserves_existing_recipient_and_pending_scope(self):
        self.dispatcher.configure("webpush", True)
        with self.store.transaction() as con:
            con.execute("DROP TABLE n_subscriptions")
            con.execute("CREATE TABLE n_subscriptions(id TEXT PRIMARY KEY,endpoint TEXT NOT NULL UNIQUE,keys TEXT NOT NULL,enabled INTEGER NOT NULL,created_at TEXT NOT NULL)")
            con.execute("INSERT INTO n_subscriptions VALUES(?,?,?,?,?)", ("existing-browser", "https://push.example.invalid/existing", json.dumps({"p256dh": "public", "auth": "auth"}), 1, datetime.now(UTC).isoformat()))
        self.message("Pending for the existing recipient")
        rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        rebuilt.run_once()
        item = self.channel_items("webpush")[0]
        self.assertEqual(item["recipient"], "existing-browser")
        self.assertEqual(item["status"], "delivered")
        with self.store.connect() as con:
            row = con.execute("SELECT * FROM n_subscriptions").fetchone()
            self.assertEqual(row["id"], "existing-browser")
            self.assertEqual(row["baseline_event_id"], 0)

    def test_changed_webhook_destination_pauses_and_cannot_redirect_old_retry(self):
        self.dispatcher.configure("webhook", True)
        old = self.dispatcher.queue({"channel": "webhook", "title": "Old destination", "body": "Only approved for the original endpoint"})
        self.reply = {"status": 429, "body": None}
        self.dispatcher.run_once()
        self.assertEqual(self.channel_items("webhook")[0]["status"], "retry")
        with patch.dict(os.environ, {"ASTER_NOTIFICATION_WEBHOOK_URL": "https://other.example.invalid/new"}):
            rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        self.reply = {"status": 200, "body": {"id": "accepted-new"}}
        rebuilt.run_once(datetime.now(UTC) + timedelta(minutes=1))
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(next(c for c in rebuilt.status()["channels"] if c["channel"] == "webhook")["enabled"])
        item = next(i for i in rebuilt.snapshot()["items"] if i["id"] == old["id"])
        self.assertEqual(item["status"], "failed")
        rebuilt.configure("webhook", True)
        self.message("Future event after explicit new-destination enablement")
        rebuilt.run_once()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.calls[-1][1], "https://other.example.invalid/new")
        self.assertEqual(self.calls[-1][2]["body"], "Future event after explicit new-destination enablement")
        self.assertNotIn("other.example.invalid", json.dumps(rebuilt.snapshot()))

    def test_changed_typefully_social_set_cannot_publish_old_queued_message(self):
        self.dispatcher.configure("typefully", True)
        queued = self.dispatcher.queue({"channel": "typefully", "title": "Original social set", "body": "Approved receiver 42"})
        with patch.dict(os.environ, {"ASTER_TYPEFULLY_SOCIAL_SET_ID": "43"}):
            rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        rebuilt.run_once()
        self.assertFalse(self.calls)
        self.assertFalse(next(c for c in rebuilt.status()["channels"] if c["channel"] == "typefully")["enabled"])
        self.assertEqual(next(i for i in rebuilt.snapshot()["items"] if i["id"] == queued["id"])["status"], "failed")

    def test_credential_rotation_for_the_same_receiver_keeps_authorized_scope(self):
        self.dispatcher.configure("webhook", True)
        self.dispatcher.queue({"channel": "webhook", "title": "Same receiver", "body": "Only the credential rotates"})
        with patch.dict(os.environ, {"ASTER_NOTIFICATION_WEBHOOK_TOKEN": "rotated-token"}):
            rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        rebuilt.run_once()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][3]["Authorization"], "Bearer rotated-token")
        self.assertTrue(next(c for c in rebuilt.status()["channels"] if c["channel"] == "webhook")["enabled"])

    def test_initial_destination_binding_migration_keeps_existing_enablement(self):
        self.dispatcher.configure("webhook", True)
        self.dispatcher.queue({"channel": "webhook", "title": "Legacy queue", "body": "Preserve existing authorization"})
        with self.store.transaction() as con:
            con.execute("UPDATE n_channels SET destination_binding=NULL WHERE channel='webhook'")
        rebuilt = NotificationDispatcher(self.store, self.lab, self.http, self.push)
        rebuilt.run_once()
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(next(c for c in rebuilt.status()["channels"] if c["channel"] == "webhook")["enabled"])
        self.assertEqual(self.channel_items("webhook")[0]["status"], "delivered")


if __name__ == "__main__":
    unittest.main()
