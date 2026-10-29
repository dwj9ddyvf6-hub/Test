import copy
import datetime as dt
import hashlib
import json
import sqlite3
import tempfile
import unittest
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.original_research_runtime import (OriginalResearch, PINS, PUBLIC_SOURCES,
    MAX_RECEIPT_BYTES, CONTROL_SHA, assess_panel, clock, read_status, fetch_public)

UTC = dt.timezone.utc
START = dt.datetime(2026, 10, 9, 19, 0, tzinfo=UTC)


def blob(n=252):
    rows = []
    origin = int((START - dt.timedelta(days=365)).timestamp() * 1000)
    for i in range(n):
        t = origin + i * 60_000
        rows.append(dict(timestamp_ms=t, completed_at_ms=t + 30_000, usable_at_ms=t + 40_000,
                         open=10., high=12., low=9., close=11., volume=100., executable_at_ms=None))
    return zlib.compress(json.dumps(rows).encode())


class OriginalResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.operating = self.base / "operating.sqlite"
        self.path = self.base / "research.sqlite"
        with sqlite3.connect(self.operating) as con:
            con.executescript("""
              CREATE TABLE a_tensor_coverage(frame TEXT,symbol TEXT,revision_id TEXT,observed_at TEXT,bars BLOB,status TEXT,error TEXT,updated_at TEXT);
              CREATE TABLE a_tensor_candidates(installation_id TEXT,origin_ms INTEGER,symbol TEXT,data TEXT);
              CREATE TABLE a_tensor_decisions(id TEXT,installation_id TEXT,symbol TEXT,origin_ms INTEGER,role TEXT,status TEXT,reason TEXT,data TEXT,intent_id TEXT,created_at TEXT);
              CREATE TABLE a_tensor_censuses(id TEXT,installation_id TEXT,origin_ms INTEGER,content_sha256 TEXT,data TEXT,created_at TEXT);
            """)
            for frame, n in (("1h", 28), ("1d", 252), ("1wk", 72)):
                con.execute("INSERT INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", (frame, "MSFT", frame, START.isoformat(), blob(n), "ready", None, START.isoformat()))
            con.execute("INSERT INTO a_tensor_candidates VALUES('tensor',1,'MSFT','{\"prediction\":99}')")
        self.runtime = OriginalResearch(self.path, self.operating, now=START)

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, now=START):
        return self.runtime.receive("CRD", "new_input", "input", b"observed input", received_at=now)

    def forecast(self, ref, **changes):
        value = dict(id="actual-emission-1", method="CRD", symbol="MSFT", emitted_at=(START + dt.timedelta(seconds=1)).isoformat(),
                     original_model_source_sha256=PINS[5][2], controls_sha256=CONTROL_SHA, calibration_origin_dates=100,
                     effective_state_origin_dates=30, input_receipt_ids=[ref], residual_forecast=.01,
                     rank_only_forecast=.003, standard_error=.002)
        value.update(changes)
        return value

    def test_missing_status_does_not_create_file_or_parent(self):
        path = self.base / "missing-parent" / "missing.sqlite"
        self.assertEqual(read_status(path)["status"], "not_started")
        self.assertFalse(path.parent.exists())

    def test_no_orders_funding_or_operating_tables_in_own_journal(self):
        with self.runtime.connect() as con:
            names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        self.assertTrue(all(n.startswith("original_") for n in names))
        self.assertEqual(read_status(self.path)["funding"], 0)

    def test_operating_same_path_symlink_and_hardlink_rejected(self):
        import os
        for path in (self.operating, self.base / "link.sqlite", self.base / "hard.sqlite"):
            if path.name == "link.sqlite":
                path.symlink_to(self.operating)
            elif path.name == "hard.sqlite":
                os.link(self.operating, path)
            with self.assertRaises(ValueError):
                OriginalResearch(path, self.operating)

    def test_foreign_ledger_rejected(self):
        with self.assertRaises(ValueError):
            OriginalResearch(self.operating, self.base / "other.sqlite")

    def test_snapshot_preserves_actual_blob_and_operating_bytes(self):
        before = hashlib.sha256(self.operating.read_bytes()).hexdigest()
        result = self.runtime.capture_operating(["MSFT"], received_at=START + dt.timedelta(seconds=2))
        self.assertEqual(before, hashlib.sha256(self.operating.read_bytes()).hexdigest())
        self.assertEqual(len(result["panels"]), 3)
        self.assertFalse(result["original_forecast_emitter_found"])
        self.assertEqual(read_status(self.path)["methods"]["CRD"]["observed_forecast_count"], 0)
        with self.runtime.connect() as con:
            panel = con.execute("SELECT body FROM original_receipts WHERE kind='native_panel_blob' AND source_key LIKE 'MSFT:1d:%'").fetchone()[0]
        self.assertEqual(panel, blob(252))

    def test_required_histories_do_not_claim_canonical_model(self):
        result = self.runtime.capture_operating(["MSFT"], received_at=START)
        for panel in result["panels"]:
            self.assertTrue(panel["history_count_sufficient"])
            self.assertFalse(panel["canonical_TRACE_ready"])
        daily = next(p for p in result["panels"] if p["frame"] == "1d")
        self.assertEqual((daily["required_history"], daily["required_feature_window"]), (252, 20))

    def test_missing_spy_sector_are_visible_not_invented(self):
        result = self.runtime.capture_operating(["MSFT"], received_at=START)
        self.assertEqual(result["symbols"], ["MSFT", "SPY", "XLK"])
        self.assertFalse(result["enrollment_complete"])
        self.assertEqual({p["symbol"] for p in result["panels"]}, {"MSFT"})

    def test_reread_preserves_first_receipt_and_assessment_clocks(self):
        first = self.runtime.capture_operating(["MSFT"], received_at=START)
        second = self.runtime.capture_operating(["MSFT"], received_at=START + dt.timedelta(days=2))
        self.assertEqual(first["panels"], second["panels"])
        self.assertEqual(len({p["receipt_id"] for p in first["panels"]}), 3)

    def test_duplicate_raw_receipt_idempotent_with_immutable_clock(self):
        a = self.source()
        b = self.source(START + dt.timedelta(days=4))
        self.assertEqual(a, b)
        self.assertEqual(a["usable_at"], START.isoformat())

    def test_oversize_and_future_publication_rejected_before_receipt(self):
        for body, pub in ((b"a" * (MAX_RECEIPT_BYTES + 1), None), (b"a", START + dt.timedelta(seconds=1))):
            with self.assertRaises(ValueError):
                self.runtime.receive("UIR", "x", "x", body, received_at=START, publication_at=pub)
        self.assertEqual(read_status(self.path)["receipt_count"], 0)

    def test_new_forecast_admitted_only_as_source_bound_series(self):
        source = self.source()
        row = self.runtime.ingest_forecast(self.forecast(source["id"]), received_at=START + dt.timedelta(seconds=2))
        self.assertEqual(row["qualified"], 1)
        self.assertFalse(read_status(self.path)["methods"]["CRD"]["canonical_ready"])

    def test_old_archive_forecast_is_context_never_back_aged(self):
        source = self.source()
        row = self.runtime.ingest_forecast(self.forecast(source["id"], emitted_at=(START - dt.timedelta(days=10)).isoformat()), received_at=START)
        self.assertEqual(row["qualified"], 0)
        self.assertEqual(row["reason"], "pre_registration_context_no_back_aging")

    def test_late_new_emission_cannot_become_slow_memory(self):
        source = self.source()
        row = self.runtime.ingest_forecast(self.forecast(source["id"]), received_at=START + dt.timedelta(minutes=10))
        self.assertEqual(row["qualified"], 0)
        self.assertEqual(row["reason"], "late_historical_receipt_not_prospective_memory")

    def test_tensor_or_proxy_forecast_not_original_emission(self):
        source = self.source()
        row = self.runtime.ingest_forecast(self.forecast(source["id"], original_model_source_sha256="tensor"), received_at=START + dt.timedelta(seconds=2))
        self.assertEqual(row["qualified"], 0)

    def test_absent_or_later_source_blocks_emission(self):
        for ref in ("missing", self.source(START + dt.timedelta(seconds=3))["id"]):
            with self.subTest(ref=ref):
                p = self.forecast(ref, id=ref)
                r = self.runtime.ingest_forecast(p, received_at=START + dt.timedelta(seconds=4))
                self.assertEqual(r["qualified"], 0)

    def test_calibration_bool_and_insufficient_support_block_series(self):
        source = self.source()
        for i, count in enumerate((True, 99)):
            p = self.forecast(source["id"], id=str(i), calibration_origin_dates=count)
            self.assertEqual(self.runtime.ingest_forecast(p, received_at=START + dt.timedelta(seconds=2))["qualified"], 0)

    def test_future_forecast_invalid_numeric_and_conflicting_id_fail(self):
        source = self.source()
        for changes in ({"emitted_at": (START + dt.timedelta(hours=1)).isoformat()}, {"standard_error": True}, {"residual_forecast": float("inf")}):
            with self.assertRaises(ValueError):
                self.runtime.ingest_forecast(self.forecast(source["id"], **changes), received_at=START + dt.timedelta(seconds=2))
        p = self.forecast(source["id"])
        self.runtime.ingest_forecast(p, received_at=START + dt.timedelta(seconds=2))
        p["residual_forecast"] = .02
        with self.assertRaises(ValueError):
            self.runtime.ingest_forecast(p, received_at=START + dt.timedelta(seconds=3))

    def test_same_forecast_replay_and_restart_keep_first_receipt(self):
        source = self.source()
        p = self.forecast(source["id"])
        first = self.runtime.ingest_forecast(p, received_at=START + dt.timedelta(seconds=2))
        second = OriginalResearch(self.path, self.operating, now=START + dt.timedelta(days=3)).ingest_forecast(p, received_at=START + dt.timedelta(days=4))
        self.assertEqual(first, second)

    def test_concurrent_identical_emissions_have_single_series_row(self):
        source = self.source()
        payload = self.forecast(source["id"])
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.runtime.ingest_forecast(payload, received_at=START + dt.timedelta(seconds=2)), range(3)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(read_status(self.path)["methods"]["CRD"]["observed_forecast_count"], 1)

    def test_panel_invalid_future_clock_bool_and_decompression_bomb_fail(self):
        rows = json.loads(zlib.decompress(blob(1)))
        cases = []
        for field, value in (("timestamp_ms", True), ("usable_at_ms", int((START + dt.timedelta(days=1)).timestamp() * 1000)), ("low", 30)):
            data = copy.deepcopy(rows); data[0][field] = value; cases.append(zlib.compress(json.dumps(data).encode()))
        cases.append(zlib.compress(b" " * (MAX_RECEIPT_BYTES + 1)))
        for raw in cases:
            with self.subTest():
                self.assertEqual(assess_panel(raw, "1d", START, START.isoformat(), "ready")["valid_causal_bar_count"], 0)

    def test_sec_previous_filings_context_new_first_arrival_not_trade(self):
        sec = {"cik": "789019", "filings": {"recent": {"accessionNumber": ["old", "new"], "form": ["10-Q", "8-K"],
               "acceptanceDateTime": [(START - dt.timedelta(days=10)).isoformat(), (START + dt.timedelta(seconds=1)).isoformat()], "primaryDocument": ["old.htm", "new.htm"]}}}
        def fetch(url):
            body = json.dumps(sec).encode() if "submissions" in url else b"November 13 December 11 December 14"
            return dict(body=body, status=200, received_at=(START + dt.timedelta(seconds=2)).isoformat())
        result = self.runtime.collect_public(fetcher=fetch)
        self.assertEqual(len(result), 3)
        status = read_status(self.path)
        self.assertEqual(status["methods"]["UIR"]["SEC_event_context_count"], 1)
        self.assertEqual(status["methods"]["UIR"]["new_SEC_first_arrival_count"], 1)
        self.assertFalse(status["methods"]["UIR"]["canonical_ready"])
        self.assertFalse(status["methods"]["TCFT"]["target_changes_observed"])
        self.runtime.collect_public(fetcher=fetch)
        self.assertEqual(read_status(self.path)["methods"]["UIR"]["new_SEC_first_arrival_count"], 1)

    def test_http_failure_bodies_saved_as_failure_not_primary_evidence(self):
        result = self.runtime.collect_public(fetcher=lambda _: dict(body=b"not found", status=404, received_at=START.isoformat()))
        self.assertTrue(all(r["status"] == "http_failure_context" and not r["successful_primary_document"] for r in result))
        self.assertEqual(read_status(self.path)["methods"]["UIR"]["new_SEC_first_arrival_count"], 0)

    def test_actual_fetch_driver_request_and_bound_with_isolated_mock(self):
        from unittest.mock import patch
        with patch("backend.original_research_runtime._fetch_http", return_value={"body": b'{}', "headers": {"Content-Type": "application/json"}}) as opener:
            result = fetch_public(PUBLIC_SOURCES[0][2])
            self.assertEqual(result["body"], b'{}')
            self.assertEqual(result["content_type"], "application/json")
            self.assertEqual(opener.call_args.args[0], PUBLIC_SOURCES[0][2])
        with self.assertRaises(ValueError):
            fetch_public("https://unconfigured.invalid")

    def test_http_driver_absolute_slow_stream_deadline_and_headers(self):
        from backend.original_research_runtime import _fetch_http
        import http.server, threading, time
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "20" if self.path == "/slow" else "2"); self.end_headers()
                try:
                    if self.path == "/slow":
                        for _ in range(20):
                            self.wfile.write(b"x"); self.wfile.flush(); time.sleep(.08)
                    else:
                        self.wfile.write(b'{}')
                except (BrokenPipeError, ConnectionResetError):
                    pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            result = _fetch_http(url + "/ok", {}, timeout=2)
            self.assertEqual(result["body"], b'{}')
            self.assertEqual(result["headers"]["Content-Type"], "application/json")
            before = time.monotonic()
            with self.assertRaises(TimeoutError):
                _fetch_http(url + "/slow", {}, timeout=.3)
            self.assertLess(time.monotonic() - before, 1)
        finally:
            server.shutdown(); server.server_close()

    def test_spy_real_calendar_forming_periods_excluded_and_raw_clocks_preserved(self):
        import urllib.parse
        def fetch(url):
            interval = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["interval"][0]
            times = {"60m": ["2026-10-09T14:30:00+00:00", "2026-10-09T18:30:00+00:00"],
                     "1d": ["2026-10-08T13:30:00+00:00", "2026-10-09T13:30:00+00:00"],
                     "1wk": ["2026-09-28T13:30:00+00:00", "2026-10-05T13:30:00+00:00"]}[interval]
            data = {"chart": {"result": [{"meta": {"symbol": "SPY", "dataGranularity": interval},
                    "timestamp": [int(clock(t).timestamp()) for t in times], "indicators": {"quote": [dict(open=[10,10], high=[12,12], low=[9,9], close=[11,11], volume=[100,100])]}}], "error": None}}
            return dict(body=json.dumps(data).encode(), status=200, received_at=START.isoformat(), headers={"Date": "Fri, 09 Oct 2026 19:00:00 GMT"})
        before = self.operating.read_bytes()
        first = self.runtime.capture_spy(fetcher=fetch)
        self.assertEqual(self.operating.read_bytes(), before)
        self.assertEqual([p["valid_causal_bar_count"] for p in first], [1, 1, 1])
        self.assertTrue(all(p["factor_identity"] == "ETF_market_factor_not_candidate_stock" for p in first))
        second = self.runtime.capture_spy(fetcher=fetch)
        self.assertTrue(all(p["collector_first_received_at"] == START.isoformat() for p in second))
        with self.runtime.connect() as con:
            rows = con.execute("SELECT * FROM original_receipts WHERE kind='spy_raw_public_chart'").fetchall()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(json.loads(r["details"])["response_headers"]["Date"] for r in rows))

    def test_spy_http_failures_never_create_native_factor_panels(self):
        result = self.runtime.capture_spy(fetcher=lambda _: dict(body=b"failure", status=404, received_at=START.isoformat()))
        self.assertTrue(all(r["status"] == "blocked" for r in result))
        with self.runtime.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM original_receipts WHERE kind='spy_native_factor_panel'").fetchone()[0], 0)

    def test_official_calendar_day_month_and_publication_precision(self):
        body = b"September 01, 2026 Friday 13 November Friday 11 December Monday 14 December"
        self.runtime.collect_public(fetcher=lambda _: dict(body=body, status=200, received_at=START.isoformat()))
        # SEC parsing failure is kept as an acquisition error; the genuine calendar branch still proceeds.
        row = read_status(self.path)["methods"]["TCFT"]["official_calendar_receipt"]
        self.assertTrue(row["schedule_text_verified"])
        self.assertEqual(row["publication_clock_precision"], "date_only_not_an_instant")

    def test_registered_projection_and_real_lease_birth_heartbeat(self):
        from backend.original_research_runtime import collector_lease
        status = read_status(self.path)
        self.assertTrue(status["registered"])
        self.assertIsNone(status["worker"])
        with self.assertRaises(ValueError):
            self.runtime.heartbeat(300, "collecting")
        with collector_lease(self.runtime):
            self.runtime.heartbeat(300, "collecting")
            status = read_status(self.path)
            self.assertEqual(status["status"], "collecting_unfunded_research")
            self.assertTrue(status["worker"]["lease_held"])
            self.assertTrue(status["worker"]["pid_birth_matches"])
            self.assertEqual(status["worker"]["stale_after_seconds"], 675)
            other = OriginalResearch(self.path, self.operating)
            with self.assertRaises(ValueError):
                with collector_lease(other):
                    pass
        self.assertFalse(read_status(self.path)["worker"]["active"])

    def test_heartbeat_stopped_stale_and_wrong_birth_not_active(self):
        from backend.original_research_runtime import collector_lease
        with collector_lease(self.runtime):
            self.runtime.heartbeat(300, "stopped")
            self.assertFalse(read_status(self.path)["worker"]["active"])
            self.runtime.heartbeat(300, "collecting", now=START)
            self.assertFalse(read_status(self.path)["worker"]["active"])
            self.runtime.heartbeat(300, "collecting")
            with self.runtime.connect() as con:
                row = json.loads(con.execute("SELECT value FROM original_meta WHERE key='worker_heartbeat'").fetchone()[0])
                row["process_birth"] = "wrong"
                con.execute("UPDATE original_meta SET value=? WHERE key='worker_heartbeat'", (json.dumps(row),))
            self.assertFalse(read_status(self.path)["worker"]["active"])

    def test_materialized_reference_bytes_bind_canonical_original_pins(self):
        from backend.original_research_runtime import source_lineage
        rows = source_lineage()
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(r["materialized"] and r["binding_verified"] and r["matches"] for r in rows))
        self.assertTrue(all(r["canonical_origin_path"].startswith("/workspace/") for r in rows))

    def test_tampered_control_registry_blocks_restart_and_status(self):
        with self.runtime.connect() as con:
            con.execute("UPDATE original_meta SET value='bad' WHERE key='controls_sha256'")
        with self.assertRaises(ValueError):
            OriginalResearch(self.path, self.operating)
        self.assertEqual(read_status(self.path)["status"], "blocked_journal_error")

    def test_control_object_tampering_and_source_body_mismatch_fail_closed(self):
        source = self.source()
        with self.runtime.connect() as con:
            con.execute("UPDATE original_receipts SET body='changed' WHERE id=?", (source["id"],))
        # SQLite may return TEXT for a malicious type change: no memory admission.
        with self.assertRaises((TypeError, ValueError)):
            self.runtime.ingest_forecast(self.forecast(source["id"]), received_at=START + dt.timedelta(seconds=2))
        with self.runtime.connect() as con:
            con.execute("UPDATE original_meta SET value='{}' WHERE key='controls'")
        with self.assertRaises(ValueError):
            OriginalResearch(self.path, self.operating)
        self.assertEqual(read_status(self.path)["status"], "blocked_journal_error")


if __name__ == "__main__":
    unittest.main()
