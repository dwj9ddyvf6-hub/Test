"""Durable per-recipient delivery with opt-in external destinations.

Cursor contract: Midna 164be062 src/lib/alerts/{push,xpost}.ts. External
acceptance is a receipt, not proof of audience delivery. Ambiguous POSTs and
crashed sends remain unknown and are never automatically replayed.
"""
import base64
import fcntl
import hashlib
import json
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from .http_transport import ResponseTooLarge, bounded_http
from .providers import utc_clock
from .store import DeskError, identifier


UTC = timezone.utc
CHANNELS = {"in_app", "webhook", "webpush", "typefully"}
TYPEFULLY = "https://api.typefully.com"


class DeliveryFailure(RuntimeError):
    def __init__(self, message, status=None, *, retryable=False, ambiguous=False):
        self.status, self.retryable, self.ambiguous = status, retryable, ambiguous
        super().__init__(message)


def _http(method, url, payload=None, headers=None):
    data = payload if isinstance(payload, bytes) else json.dumps(payload).encode() if payload is not None else None
    try:
        status, raw = bounded_http(method, url, body=data, headers=headers, timeout_seconds=8, maximum_bytes=256000, follow_redirects=False)
        try:
            body = json.loads(raw) if raw else None
        except ValueError:
            body = None
        return {"status": status, "body": body}
    except ResponseTooLarge:
        raise DeliveryFailure("Delivery response exceeded its limit", ambiguous=method == "POST") from None
    except (httpx.HTTPError, TimeoutError, OSError):
        raise DeliveryFailure("Delivery transport failed", retryable=method in {"GET", "PUT"}, ambiguous=method == "POST") from None


class _BoundedPushSession:
    """Transport adapter; pywebpush retains encryption and VAPID signing."""
    def post(self, url, *, data=None, headers=None, timeout=None):
        from requests import Request, Response
        status, raw = bounded_http("POST", url, body=data, headers=dict(headers or {}), timeout_seconds=8, maximum_bytes=256000, follow_redirects=False)
        response = Response()
        response.status_code, response._content, response.url = status, raw, url
        response.reason = "Push provider response"
        response.request = Request("POST", url).prepare()
        return response


def _push(subscription, payload, private_key, subject):
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        raise DeliveryFailure("WebPush dependency is unavailable") from None
    try:
        response = webpush(subscription_info=subscription, data=json.dumps(payload), vapid_private_key=private_key, vapid_claims={"sub": subject}, timeout=8, requests_session=_BoundedPushSession())
        return {"status": response.status_code, "body": None}
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status:
            return {"status": status, "body": None}
        raise DeliveryFailure("Browser push delivery is ambiguous", ambiguous=True) from None
    except (ResponseTooLarge, httpx.HTTPError, TimeoutError, OSError):
        raise DeliveryFailure("Browser push delivery is ambiguous", ambiguous=True) from None


def _https(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        # Accessing port validates malformed ports and bracketed addresses.
        parsed.port
        return bool(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password and not parsed.fragment)
    except ValueError:
        return False


class NotificationDispatcher:
    MAX_ATTEMPTS = 5
    BATCH_START_BUDGET_SECONDS = 16

    def __init__(self, store, lab, transport=None, push_transport=None):
        self.store, self.lab = store, lab
        self.transport, self.push_transport = transport or _http, push_transport or _push
        self._mutex = threading.Lock()
        self.webhook_url = os.environ.get("ASTER_NOTIFICATION_WEBHOOK_URL", "").strip()
        self.webhook_token = os.environ.get("ASTER_NOTIFICATION_WEBHOOK_TOKEN", "")
        self.typefully_key = os.environ.get("ASTER_TYPEFULLY_API_KEY", "")
        self.social_set = os.environ.get("ASTER_TYPEFULLY_SOCIAL_SET_ID", "")
        self.vapid_public = os.environ.get("ASTER_VAPID_PUBLIC_KEY", "")
        self.vapid_private = os.environ.get("ASTER_VAPID_PRIVATE_KEY", "")
        self.vapid_subject = os.environ.get("ASTER_VAPID_SUBJECT", "")
        with store.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS n_channels(channel TEXT PRIMARY KEY,enabled INTEGER NOT NULL,cursor_id INTEGER NOT NULL,updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS n_subscriptions(id TEXT PRIMARY KEY,endpoint TEXT NOT NULL UNIQUE,keys TEXT NOT NULL,enabled INTEGER NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS n_outbox(id TEXT PRIMARY KEY,channel TEXT NOT NULL,event_id INTEGER NOT NULL,recipient TEXT NOT NULL,
                    payload TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,completed_at TEXT,error TEXT,UNIQUE(channel,event_id,recipient));
                CREATE TABLE IF NOT EXISTS n_receipts(id INTEGER PRIMARY KEY AUTOINCREMENT,item_id TEXT NOT NULL,attempted_at TEXT NOT NULL,
                    stage TEXT NOT NULL,state TEXT NOT NULL,http_status INTEGER,remote_id TEXT,error TEXT,detail TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS n_media(item_id TEXT PRIMARY KEY,content_base64 TEXT NOT NULL,content_sha256 TEXT NOT NULL,file_name TEXT NOT NULL,
                    alt_text TEXT NOT NULL,state TEXT NOT NULL,media_id TEXT,upload_url TEXT);
                CREATE INDEX IF NOT EXISTS n_outbox_due ON n_outbox(status,next_attempt_at);
                CREATE TABLE IF NOT EXISTS n_reader_cursors(reader TEXT PRIMARY KEY,through_event_id INTEGER NOT NULL,updated_at TEXT NOT NULL);
            """)
            con.execute("BEGIN IMMEDIATE")
            subscription_columns = {row[1] for row in con.execute("PRAGMA table_info(n_subscriptions)")}
            if "baseline_event_id" not in subscription_columns:
                # Existing recipients retain their pending delivery scope. New and
                # explicitly resumed recipients cover only future local events.
                con.execute("ALTER TABLE n_subscriptions ADD COLUMN baseline_event_id INTEGER NOT NULL DEFAULT 0")
            channel_columns = {row[1] for row in con.execute("PRAGMA table_info(n_channels)")}
            if "destination_binding" not in channel_columns:
                con.execute("ALTER TABLE n_channels ADD COLUMN destination_binding TEXT")
            maximum = con.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]
            for channel in sorted(CHANNELS):
                con.execute("INSERT OR IGNORE INTO n_channels(channel,enabled,cursor_id,updated_at) VALUES(?,?,?,?)", (channel, int(channel == "in_app"), maximum, datetime.now(UTC).isoformat()))
                prior = con.execute("SELECT * FROM n_channels WHERE channel=?", (channel,)).fetchone()
                binding = self._destination_binding(channel)
                # First migration binds the already configured receiver without
                # withdrawing existing enablement. Later receiver changes require
                # a new explicit enablement and cannot redirect pending history.
                if channel != "in_app" and prior["destination_binding"] is not None and prior["destination_binding"] != binding:
                    cancelled = con.execute("UPDATE n_outbox SET status='failed',error='Notification destination binding changed or was unavailable; explicitly enable the destination and queue a new message',completed_at=? WHERE channel=? AND status IN ('queued','retry')", (datetime.now(UTC).isoformat(), channel)).rowcount
                    if prior["enabled"] or cancelled:
                        self.store.event(con, "notification_destination_changed", "system", "Paused a changed notification destination; explicit enablement is required", {"channel": channel})
                    con.execute("UPDATE n_channels SET enabled=0 WHERE channel=?", (channel,))
                con.execute("UPDATE n_channels SET destination_binding=? WHERE channel=?", (binding, channel))

    def _destination_binding(self, channel):
        # Bind authorization to the receiver, allowing credentials to rotate.
        # The browser receiver is already a durable per-subscription endpoint.
        destination = self.webhook_url if channel == "webhook" else self.social_set if channel == "typefully" else channel
        return hashlib.sha256(json.dumps([channel, destination], separators=(",", ":")).encode()).hexdigest()

    def _configured(self, channel):
        if channel == "in_app":
            return True
        if channel == "webhook":
            return _https(self.webhook_url)
        if channel == "typefully":
            return bool(self.typefully_key and re.fullmatch(r"[1-9][0-9]*", self.social_set))
        return bool(self.vapid_public and self.vapid_private and (self.vapid_subject.startswith("mailto:") or _https(self.vapid_subject)))

    def configure(self, channel, enabled):
        if channel not in CHANNELS or not isinstance(enabled, bool):
            raise DeskError("A known notification channel and boolean enabled are required", 422)
        if enabled and not self._configured(channel):
            raise DeskError("Notification destination is not configured", 422)
        with self.store.transaction() as con:
            old = con.execute("SELECT * FROM n_channels WHERE channel=?", (channel,)).fetchone()
            cursor = old["cursor_id"]
            if enabled and not old["enabled"]:
                cursor = con.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]
            con.execute("UPDATE n_channels SET enabled=?,cursor_id=?,updated_at=?,destination_binding=? WHERE channel=?", (int(enabled), cursor, datetime.now(UTC).isoformat(), self._destination_binding(channel), channel))
            if not enabled:
                con.execute("UPDATE n_outbox SET status='failed',error='Channel disabled before delivery; enablement does not replay queued history',completed_at=? WHERE channel=? AND status IN ('queued','retry')", (datetime.now(UTC).isoformat(), channel))
            self.store.event(con, "notification_channel_configured", "operator", "Updated notification delivery; previous events are not replayed", {"channel": channel, "enabled": enabled})
        return self.status()

    def subscribe(self, payload):
        endpoint, keys = payload.get("endpoint", ""), payload.get("keys", {})
        if not isinstance(endpoint, str) or len(endpoint) > 3000 or not _https(endpoint) or not isinstance(keys, dict) or set(keys) != {"p256dh", "auth"} or any(not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_=-]{1,1000}", v) for v in keys.values()):
            raise DeskError("A complete HTTPS browser push subscription is required", 422)
        with self.store.transaction() as con:
            row = con.execute("SELECT id,enabled,baseline_event_id FROM n_subscriptions WHERE endpoint=?", (endpoint,)).fetchone()
            rid = row["id"] if row else identifier()
            baseline = row["baseline_event_id"] if row and row["enabled"] else con.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]
            con.execute("INSERT INTO n_subscriptions(id,endpoint,keys,enabled,created_at,baseline_event_id) VALUES(?,?,?,?,?,?) ON CONFLICT(endpoint) DO UPDATE SET keys=excluded.keys,enabled=1,baseline_event_id=excluded.baseline_event_id", (rid, endpoint, json.dumps(keys), 1, datetime.now(UTC).isoformat(), baseline))
            self.store.event(con, "push_subscription_saved", "operator", "Saved an explicit browser push subscription", {"subscription_id": rid})
        return {"id": rid, "enabled": True, "channel_enabled": self._channel_enabled("webpush")}

    def unsubscribe(self, rid):
        with self.store.transaction() as con:
            if not con.execute("SELECT 1 FROM n_subscriptions WHERE id=?", (rid,)).fetchone():
                raise DeskError("Subscription not found", 404)
            con.execute("UPDATE n_subscriptions SET enabled=0 WHERE id=?", (rid,))
            con.execute("UPDATE n_outbox SET status='failed',error='Browser subscription disabled before delivery',completed_at=? WHERE channel='webpush' AND recipient=? AND status IN ('queued','retry')", (datetime.now(UTC).isoformat(), rid))
            self.store.event(con, "push_subscription_disabled", "operator", "Disabled an explicit browser push subscription", {"subscription_id": rid})
        return {"id": rid, "enabled": False}

    def _channel_enabled(self, channel):
        with self.store.connect() as con:
            return bool(con.execute("SELECT enabled FROM n_channels WHERE channel=?", (channel,)).fetchone()[0])

    def _insert(self, con, channel, event_id, recipient, payload, clock):
        rid = identifier()
        con.execute("INSERT OR IGNORE INTO n_outbox(id,channel,event_id,recipient,payload,status,next_attempt_at,created_at) VALUES(?,?,?,?,?,'queued',?,?)", (rid, channel, event_id, recipient, json.dumps(payload), clock, clock))
        return con.execute("SELECT id FROM n_outbox WHERE channel=? AND event_id=? AND recipient=?", (channel, event_id, recipient)).fetchone()[0]

    def queue(self, payload):
        """Explicit operator message/media; no generated trading or media content."""
        channel = payload.get("channel", "in_app")
        title, body = payload.get("title", ""), payload.get("body", "")
        if not isinstance(channel, str) or channel not in CHANNELS or not isinstance(title, str) or not title.strip() or not isinstance(body, str) or len(title) > 200 or len(body) > 12000:
            raise DeskError("A known channel, title and bounded message are required", 422)
        if not self._channel_enabled(channel):
            raise DeskError("Enable the notification destination before queueing an explicit delivery")
        media = payload.get("media")
        if media is not None:
            if channel != "typefully" or not isinstance(media, dict):
                raise DeskError("Explicit PNG media is supported for Typefully", 422)
            try:
                content = base64.b64decode(media.get("content_base64", ""), validate=True)
            except (ValueError, TypeError):
                raise DeskError("Media must be base64 PNG data", 422) from None
            if not content.startswith(b"\x89PNG\r\n\x1a\n") or len(content) > 1_000_000:
                raise DeskError("Media must be a PNG up to one megabyte", 422)
        timestamp = datetime.now(UTC).isoformat()
        with self.store.transaction() as con:
            if not con.execute("SELECT enabled FROM n_channels WHERE channel=?", (channel,)).fetchone()[0]:
                raise DeskError("Enable the notification destination before queueing an explicit delivery")
            recipients = [r[0] for r in con.execute("SELECT id FROM n_subscriptions WHERE enabled=1")] if channel == "webpush" else ["channel"]
            if not recipients:
                raise DeskError("Subscribe a browser before queueing browser push", 422)
            self.store.event(con, "notification_explicit", "operator", title, {"channel": channel})
            event_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            ids = [self._insert(con, channel, event_id, recipient, {"title": title, "body": body, "source": "explicit operator notification", "event_id": event_id}, timestamp) for recipient in recipients]
            rid = ids[0]
            if media is not None:
                filename = re.sub(r"[^A-Za-z0-9_.-]", "_", str(media.get("file_name", "operator.png")))[:100]
                if not filename.endswith(".png"):
                    filename += ".png"
                con.execute("INSERT INTO n_media VALUES(?,?,?,?,?,'queued',NULL,NULL)", (rid, base64.b64encode(content).decode(), hashlib.sha256(content).hexdigest(), filename, str(media.get("alt_text", "Operator-supplied image"))[:1000]))
        return {"id": rid, "ids": ids, "status": "queued"}

    def read(self, reader, through_event_id):
        if not isinstance(reader, str) or not reader.strip() or len(reader) > 160 or isinstance(through_event_id, bool) or not isinstance(through_event_id, int) or through_event_id < 0:
            raise DeskError("Reader and a nonnegative event cursor are required", 422)
        with self.store.transaction() as con:
            maximum = con.execute("SELECT COALESCE(MAX(event_id),0) FROM n_outbox WHERE channel='in_app' AND status='delivered'").fetchone()[0]
            old = con.execute("SELECT through_event_id FROM n_reader_cursors WHERE reader=?", (reader,)).fetchone()
            undelivered = con.execute("SELECT 1 FROM n_outbox WHERE channel='in_app' AND status NOT IN ('delivered','failed') AND event_id<=?", (through_event_id,)).fetchone()
            if through_event_id > maximum or old and through_event_id < old[0] or undelivered:
                raise DeskError("Notification reader cannot skip pending or unknown events or move backwards")
            con.execute("INSERT INTO n_reader_cursors VALUES(?,?,?) ON CONFLICT(reader) DO UPDATE SET through_event_id=excluded.through_event_id,updated_at=excluded.updated_at", (reader, through_event_id, datetime.now(UTC).isoformat()))
        return {"reader": reader, "through_event_id": through_event_id}

    def _collect(self, con, timestamp):
        for channel in con.execute("SELECT * FROM n_channels WHERE enabled=1").fetchall():
            events = con.execute("SELECT * FROM events WHERE id>? ORDER BY id LIMIT 100", (channel["cursor_id"],)).fetchall()
            for event in events:
                if event["event_type"] not in {"peer_message", "operational_alert"}:
                    continue
                detail = json.loads(event["payload"])
                payload = {"event_id": event["id"], "title": event["message"], "body": event["message"], "timestamp": event["timestamp"], "source": "local desk event", "severity": detail.get("severity", "info")}
                if event["event_type"] == "peer_message":
                    row = con.execute("SELECT * FROM lab_messages WHERE id=?", (detail.get("message_id"),)).fetchone()
                    if row:
                        payload.update({"title": row["topic"], "body": row["body"][:12000], "sender": row["sender"], "recipient": row["recipient"], "source": row["source"]})
                recipients = [r[0] for r in con.execute("SELECT id FROM n_subscriptions WHERE enabled=1 AND baseline_event_id<?", (event["id"],))] if channel["channel"] == "webpush" else ["channel"]
                for recipient in recipients:
                    self._insert(con, channel["channel"], event["id"], recipient, payload, timestamp)
            if events:
                con.execute("UPDATE n_channels SET cursor_id=?,updated_at=? WHERE channel=?", (events[-1]["id"], timestamp, channel["channel"]))

    def _receipt(self, rid, stage, state, status=None, remote_id=None, error=None, detail=None, *, con=None):
        values = (rid, datetime.now(UTC).isoformat(), stage, state, status, remote_id, error, json.dumps(detail or {}))
        sql = "INSERT INTO n_receipts(item_id,attempted_at,stage,state,http_status,remote_id,error,detail) VALUES(?,?,?,?,?,?,?,?)"
        if con is not None:
            con.execute(sql, values)
        else:
            with self.store.transaction() as connection:
                connection.execute(sql, values)

    def _accepted(self, response, *, read=False, put=False):
        status = response.get("status")
        if status in ({200, 201, 204} if put else {200, 201, 202, 204}):
            return response.get("body") or {}
        if status == 429 or (read or put) and status in {500, 502, 503, 504}:
            raise DeliveryFailure("Provider deferred delivery", status, retryable=True)
        raise DeliveryFailure("Provider did not accept delivery", status, ambiguous=not read and not put and status in {500, 502, 503, 504})

    def _media(self, rid, headers):
        with self.store.connect() as con:
            row = con.execute("SELECT * FROM n_media WHERE item_id=?", (rid,)).fetchone()
        if not row:
            return None
        media = dict(row)
        if media["state"] in {"queued", "created"}:
            try:
                content = base64.b64decode(media["content_base64"], validate=True)
            except (ValueError, TypeError):
                raise DeliveryFailure("Stored media failed its content integrity check") from None
            if hashlib.sha256(content).hexdigest() != media["content_sha256"]:
                raise DeliveryFailure("Stored media failed its content integrity check")
        base = TYPEFULLY + "/v2/social-sets/" + self.social_set
        if media["state"] == "queued":
            response = self.transport("POST", base + "/media/upload", {"file_name": media["file_name"], "alt_text": media["alt_text"]}, headers)
            data = self._accepted(response)
            if response.get("status") != 201 or not data.get("media_id") or not _https(data.get("upload_url", "")):
                raise DeliveryFailure("Media creation response is incomplete", ambiguous=True)
            media.update({"media_id": str(data["media_id"]), "upload_url": data["upload_url"], "state": "created"})
            with self.store.transaction() as con:
                con.execute("UPDATE n_media SET media_id=?,upload_url=?,state='created' WHERE item_id=?", (media["media_id"], media["upload_url"], rid))
            self._receipt(rid, "media_create", "accepted", response["status"], media["media_id"], detail={"content_sha256": media["content_sha256"]})
        if media["state"] == "created":
            response = self.transport("PUT", media["upload_url"], content, {"Content-Type": "image/png"})
            self._accepted(response, put=True)
            with self.store.transaction() as con:
                con.execute("UPDATE n_media SET state='uploaded',upload_url=NULL WHERE item_id=?", (rid,))
            media["state"] = "uploaded"
            self._receipt(rid, "media_upload", "accepted", response["status"], media["media_id"])
        if media["state"] == "uploaded":
            response = self.transport("GET", base + "/media/" + quote(media["media_id"], safe=""), None, headers)
            status = self._accepted(response, read=True).get("status")
            self._receipt(rid, "media_process", str(status or "unknown"), response["status"], media["media_id"])
            if status == "failed":
                raise DeliveryFailure("Provider rejected the uploaded image")
            if status != "ready":
                raise DeliveryFailure("Uploaded image is still processing", retryable=True)
            with self.store.transaction() as con:
                con.execute("UPDATE n_media SET state='ready' WHERE item_id=?", (rid,))
        return media["media_id"]

    def _deliver(self, item):
        channel, payload = item["channel"], json.loads(item["payload"])
        if not self._configured(channel):
            raise DeliveryFailure("Delivery channel configuration is unavailable")
        with self.store.connect() as con:
            binding = con.execute("SELECT destination_binding FROM n_channels WHERE channel=?", (channel,)).fetchone()[0]
        if binding != self._destination_binding(channel):
            raise DeliveryFailure("Notification destination changed; explicit channel enablement is required")
        if channel == "in_app":
            return {"status": 200, "remote_id": item["id"], "detail": "Delivered to the durable in-app outbox; reader acknowledgement is separate"}
        if channel == "webhook":
            headers = {"Content-Type": "application/json", "Idempotency-Key": item["id"]}
            if self.webhook_token:
                headers["Authorization"] = "Bearer " + self.webhook_token
            response = self.transport("POST", self.webhook_url, {"id": item["id"], **payload}, headers)
            data = self._accepted(response)
            return {"status": response["status"], "remote_id": str(data.get("id", "")) if isinstance(data, dict) else "", "detail": "Webhook accepted the request; downstream handling is unverified"}
        if channel == "webpush":
            with self.store.connect() as con:
                subscription = con.execute("SELECT * FROM n_subscriptions WHERE id=? AND enabled=1", (item["recipient"],)).fetchone()
            if not subscription:
                raise DeliveryFailure("Browser subscription is disabled")
            response = self.push_transport({"endpoint": subscription["endpoint"], "keys": json.loads(subscription["keys"])}, {"id": item["id"], **payload}, self.vapid_private, self.vapid_subject)
            if response.get("status") in {404, 410}:
                self.unsubscribe(item["recipient"])
                raise DeliveryFailure("Browser subscription expired", response["status"])
            self._accepted(response)
            return {"status": response["status"], "remote_id": item["recipient"], "detail": "Push service accepted the message; browser display is unverified"}
        headers = {"Authorization": "Bearer " + self.typefully_key, "Content-Type": "application/json"}
        media_id = self._media(item["id"], headers)
        supplied_text = (payload["title"] + ". " + payload["body"]).replace("\n", " ")
        text = supplied_text[:280]
        post = {"text": text, **({"media_ids": [media_id]} if media_id else {})}
        response = self.transport("POST", TYPEFULLY + "/v2/social-sets/" + self.social_set + "/drafts", {"platforms": {"x": {"enabled": True, "posts": [post]}}, "publish_at": "now"}, headers)
        data = self._accepted(response)
        if response.get("status") not in {200, 201}:
            raise DeliveryFailure("Typefully draft acceptance is unconfirmed", ambiguous=True)
        detail = "Typefully accepted publish_at=now; X publication is unverified"
        if len(supplied_text) > len(text):
            detail += f"; supplied message truncated from {len(supplied_text)} to {len(text)} characters"
        return {"status": response["status"], "remote_id": str(data.get("id", data.get("draft_id", ""))), "detail": detail}

    def run_once(self, clock=None):
        fixed_clock = utc_clock(clock) if clock is not None else None
        current_clock = lambda: fixed_clock if fixed_clock is not None else utc_clock()
        if not self._mutex.acquire(blocking=False):
            return {"processed": 0, "busy": True}
        batch_deadline = monotonic() + self.BATCH_START_BUDGET_SECONDS
        lock = None
        try:
            lock = open(str(Path(self.store.path).resolve()) + ".notifications.lock", "a")
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return {"processed": 0, "busy": True}
            with self.store.transaction() as con:
                clock = current_clock()
                # A crash after external acceptance cannot authorize duplicate sends.
                con.execute("UPDATE n_outbox SET status=CASE WHEN channel='in_app' THEN 'queued' ELSE 'unknown' END,completed_at=CASE WHEN channel='in_app' THEN NULL ELSE ? END,error='Recovered interrupted delivery; external result must be reconciled' WHERE status='sending'", (clock.isoformat(),))
                self._collect(con, clock.isoformat())
                items = [dict(r) for r in con.execute("SELECT o.* FROM n_outbox o JOIN n_channels c ON c.channel=o.channel WHERE c.enabled=1 AND o.status IN ('queued','retry') AND o.next_attempt_at<=? ORDER BY o.created_at LIMIT 12", (clock.isoformat(),))]
            counts = {"processed": 0, "delivered": 0, "retrying": 0, "failed": 0, "unknown": 0, "budget_exhausted": False}
            for item in items:
                # Complete the current item's durable phases, then yield to
                # price/reconciliation work rather than beginning another slow
                # external delivery. Remaining items retain their due state.
                if monotonic() >= batch_deadline:
                    counts["budget_exhausted"] = True
                    break
                with self.store.transaction() as con:
                    clock = current_clock()
                    claimed = con.execute("UPDATE n_outbox SET status='sending',attempts=attempts+1,error=NULL WHERE id=? AND status IN ('queued','retry') AND next_attempt_at<=? AND EXISTS(SELECT 1 FROM n_channels WHERE channel=n_outbox.channel AND enabled=1)", (item["id"], clock.isoformat())).rowcount
                    if not claimed:
                        continue
                    # A pause, retry or subscription change can invalidate the
                    # earlier batch snapshot. Claim current state atomically.
                    item = dict(con.execute("SELECT * FROM n_outbox WHERE id=?", (item["id"],)).fetchone())
                try:
                    receipt = self._deliver(item)
                    state, error = "delivered", None
                    receipt_values = ("accepted", receipt["status"], receipt["remote_id"], None, {"scope": receipt["detail"]})
                except Exception as exc:
                    failure = exc if isinstance(exc, DeliveryFailure) else DeliveryFailure("Delivery failed without a trustworthy result", ambiguous=item["channel"] != "in_app")
                    attempts = item["attempts"]
                    state = "unknown" if failure.ambiguous else "retry" if failure.retryable and attempts < self.MAX_ATTEMPTS else "failed"
                    error = str(failure)
                    receipt_values = (state, failure.status, None, error, None)
                with self.store.transaction() as con:
                    clock = current_clock()
                    next_at = (clock + timedelta(seconds=min(300, 5 * 2 ** min(item["attempts"] - 1, 6)))).isoformat() if state == "retry" else clock.isoformat()
                    self._receipt(item["id"], "delivery", *receipt_values, con=con)
                    con.execute("UPDATE n_outbox SET status=?,next_attempt_at=?,completed_at=?,error=? WHERE id=?", (state, next_at, clock.isoformat() if state in {"delivered", "failed", "unknown"} else None, error, item["id"]))
                counts["processed"] += 1
                counts["delivered" if state == "delivered" else "retrying" if state == "retry" else state] += 1
            with self.store.connect() as con:
                counts["deferred_due"] = con.execute("SELECT COUNT(*) FROM n_outbox o JOIN n_channels c ON c.channel=o.channel WHERE c.enabled=1 AND o.status IN ('queued','retry') AND o.next_attempt_at<=?", (current_clock().isoformat(),)).fetchone()[0]
            return counts
        finally:
            try:
                if lock is not None:
                    lock.close()
            finally:
                self._mutex.release()

    def retry(self, rid):
        with self.store.transaction() as con:
            item = con.execute("SELECT * FROM n_outbox WHERE id=?", (rid,)).fetchone()
            if not item:
                raise DeskError("Notification not found", 404)
            if item["status"] not in {"failed", "retry"}:
                raise DeskError("Unknown delivery must be reconciled with the destination before retry; accepted deliveries cannot be replayed")
            con.execute("UPDATE n_outbox SET status='queued',attempts=0,next_attempt_at=?,error=NULL,completed_at=NULL WHERE id=?", (datetime.now(UTC).isoformat(), rid))
            self.store.event(con, "notification_retry_requested", "operator", "Requested a notification retry", {"item_id": rid})
        return {"id": rid, "status": "queued"}

    def resolve(self, rid, delivered, remote_id=""):
        if not isinstance(delivered, bool):
            raise DeskError("A factual delivered boolean is required", 422)
        with self.store.transaction() as con:
            item = con.execute("SELECT status FROM n_outbox WHERE id=?", (rid,)).fetchone()
            if not item or item[0] != "unknown":
                raise DeskError("Only unknown delivery results need destination reconciliation")
            state = "delivered" if delivered else "failed"
            con.execute("UPDATE n_outbox SET status=?,error=NULL,completed_at=? WHERE id=?", (state, datetime.now(UTC).isoformat(), rid))
            self._receipt(rid, "operator_reconciliation", state, remote_id=str(remote_id)[:160], detail={"source": "Explicit operator report; provider result was not independently verified"}, con=con)
        return {"id": rid, "status": state}

    def status(self):
        with self.store.connect() as con:
            channels = []
            for row in con.execute("SELECT * FROM n_channels ORDER BY channel"):
                latest = con.execute("SELECT status,completed_at,error FROM n_outbox WHERE channel=? ORDER BY created_at DESC LIMIT 1", (row["channel"],)).fetchone()
                public = {key: row[key] for key in row.keys() if key != "destination_binding"}
                channels.append({**public, "enabled": bool(row["enabled"]), "configured": self._configured(row["channel"]), "last_delivery": dict(latest) if latest else None})
            subscriptions = con.execute("SELECT COUNT(*) FROM n_subscriptions WHERE enabled=1").fetchone()[0]
            counts = {r[0]: r[1] for r in con.execute("SELECT status,COUNT(*) FROM n_outbox GROUP BY status")}
        return {"channels": channels, "active_subscriptions": subscriptions, "vapid_public_key": self.vapid_public or None, "counts": counts, "scope": "Delivered means durable in-app availability or external provider acceptance; audience receipt is unverified"}

    def snapshot(self):
        with self.store.connect() as con:
            cursors = [dict(r) for r in con.execute("SELECT * FROM n_reader_cursors")]
            items = []
            for row in con.execute("SELECT * FROM n_outbox ORDER BY created_at DESC LIMIT 200"):
                item = dict(row)
                item["payload"] = json.loads(item["payload"])
                item["receipts"] = []
                for receipt in con.execute("SELECT * FROM n_receipts WHERE item_id=? ORDER BY id", (row["id"],)):
                    data = dict(receipt)
                    data["detail"] = json.loads(data["detail"])
                    item["receipts"].append(data)
                items.append(item)
        return {"status": self.status(), "items": items, "reader_cursors": cursors}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChannelSetting(_Strict):
    enabled: bool


class ResolveSetting(_Strict):
    delivered: bool
    remote_id: str = ""


def notification_router(dispatcher):
    router = APIRouter(prefix="/api/notifications")
    router.add_api_route("", dispatcher.snapshot, methods=["GET"])
    @router.post("/channels/{channel}")
    def configure(channel: str, body: ChannelSetting):
        return dispatcher.configure(channel, body.enabled)
    @router.post("/subscribe")
    def subscribe(body: dict):
        return dispatcher.subscribe(body)
    @router.delete("/subscribe/{rid}")
    def unsubscribe(rid: str):
        return dispatcher.unsubscribe(rid)
    @router.post("/queue")
    def queue(body: dict):
        return dispatcher.queue(body)
    @router.post("/read")
    def read(body: dict):
        return dispatcher.read(body.get("reader"), body.get("through_event_id"))
    @router.post("/items/{rid}/retry")
    def retry(rid: str):
        return dispatcher.retry(rid)
    @router.post("/items/{rid}/resolve")
    def resolve(rid: str, body: ResolveSetting):
        return dispatcher.resolve(rid, body.delivered, body.remote_id)
    return router
