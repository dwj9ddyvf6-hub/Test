"""Prospective, unfunded original-method receipt collector; never submits orders.

Data received today is context for tomorrow, never a recreated historical trade.
The original specifications are references, not executable models in this module.
"""
from __future__ import annotations

import argparse
import asyncio
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import html
import json
import math
import os
import re
import signal
import sqlite3
import threading
import tempfile
import time
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

UTC = dt.timezone.utc
ROOT = Path(__file__).resolve().parents[1]
MAX_RECEIPT_BYTES = 2 * 1024 * 1024
MAX_STORED_BYTES = 25 * 1024 * 1024
METHODS = ("TRACE", "CRD", "UIR", "TCFT")
PINS = (
    ("UIR", "/workspace/five-strategy-inventions-2026-10-08/specs/01_information.json", "8bbbed035b727276b78c2a0c31069d7df5fba193cf7b9e022444959dba41d3be"),
    ("TRACE", "/workspace/five-strategy-inventions-2026-10-08/specs/02_paths.json", "dabb9a4942a458d93e35cf64c3c54dd46aa82cb83b1d9c54b9ee7d487e92c38d"),
    ("CRD", "/workspace/five-strategy-inventions-2026-10-08/specs/05_allocator.json", "d4ca0f82eed297bd1cd78d538a53a04ea2143a457727a218235fc56d92292b5f"),
    ("TCFT", "/workspace/five-strategy-inventions-r4-2026-10-08/strategies/flow/SPEC.json", "f114f5206bf942008454ed6420e2f1bf26a166b74019d3f8bc671d1c422469dc"),
    ("TRACE", "/workspace/ten-strategy-repair-review-r10-2026-10-09/strategies/trace/repair/trace_r10.py", "c8d668b4c4a2862b4d567f3beff15e0511b1a50b4ce45d347bc52b6d9bcaba73"),
    ("CRD", "/workspace/ten-strategy-repair-review-r10-2026-10-09/strategies/crd/repair/crd_r10.py", "d32209a85e78dfd540af5057a956987a66c0194304b16f719a57789ce0ceeb6a"),
    ("UIR", "/workspace/ten-strategy-repair-review-r10-2026-10-09/strategies/uir/repair_kernel.py", "0ab0b4dfb85b4116e68cbaeaf83e7f99040990ba411f8cc6e2509a027dfbdfc9"),
    ("TCFT", "/workspace/ten-strategy-repair-review-r10-2026-10-09/strategies/tcft/code/kernel.py", "33bda624ef595377678626b1410e24a16c71790bc8e2660915ab9928d5cc0671"),
    ("TRACE", "/workspace/tensor-forensic-edge-study-r11-2026-10-09/engine/frozen-v690/lib/anna-replica.mjs", "aa5c902509b9483b6b25cbb5a81c4978f434c7fb0bd58ec21874a3ffbe04ddb6"),
    ("TRACE", "/workspace/tensor-forensic-edge-study-r11-2026-10-09/engine/FROZEN_ENGINE_PROVENANCE.json", "a00c3564568046938801d7ad32affb204044434a44c81272a521823564ffd316"),
)
CONTROLS = {
    "version": "original-prospective-receipts-r15/1",
    "authority": "unfunded_research_only_no_orders_no_financial_simulation",
    "TRACE": ["exact_frozen_tensor", "sidecar_three_of_five", "B_only", "momentum_sector_momentum", "unresidualized_order", "eight_order_destroyed_placebos"],
    "CRD": ["current_only", "genuinely_emitted_persistence", "rank_only", "no_cost", "volatility_only", "drifted_hold"],
    "UIR": ["source_receiver_sector_macro_prices", "no_link", "shuffled_pre_event_links", "source_event_only"],
    "TCFT": ["announced_target_ADV_calendar", "time_relaxed_flow", "announcement_reaction", "held_core_four_leg_cost"],
    "TRACE_histories": {"1d": 252, "1wk": 72, "1h": 28, "feature_daily": 20, "feature_weekly": 12},
    "prospective_series": "new original CRD emissions only; no archive back-aging, no Tensor prediction substitution",
    "source_pins": [{"method": m, "path": p, "sha256": s} for m, p, s in PINS],
    "TCFT_calendar": {"preliminary_lists": "2026-11-13", "implementation_close": "2026-12-11", "effective_open": "2026-12-14", "target_changes_known": False},
}
PUBLIC_SOURCES = (
    ("UIR", "sec_submissions", "https://data.sec.gov/submissions/CIK0000789019.json"),
    ("UIR", "issuer_context", "https://www.microsoft.com/en-us/Investor/earnings/fy-2026-q4/press-release-webcast"),
    ("TCFT", "official_calendar", "https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-russell-announces-december-2026-russell-us-indexes-reconstitution-schedule"),
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(value).hexdigest()


CONTROL_SHA = digest(canonical(CONTROLS).encode())


def clock(value=None):
    if value is None:
        return dt.datetime.now(UTC)
    if isinstance(value, str):
        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, dt.datetime) or value.tzinfo is None:
        raise ValueError("Aware receipt timestamp required")
    return value.astimezone(UTC)


def iso(value):
    return clock(value).isoformat()


@contextmanager
def _readonly(path):
    path = Path(path).resolve()
    con = sqlite3.connect("file:" + urllib.parse.quote(str(path)) + "?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    try:
        yield con
    finally:
        con.close()


def default_path():
    return Path(os.environ.get("ASTER_ORIGINAL_RESEARCH_DB_PATH", ROOT / "data/original-research.sqlite"))


def source_lineage():
    rows = []
    materialized = ROOT / "strategies/original_research/lineage"
    try:
        binding = json.loads((materialized / "SOURCE_BINDING.json").read_text())["files"]
    except (OSError, ValueError, KeyError, TypeError):
        binding = []
    for i, (method, path, expected) in enumerate(PINS):
        local = materialized / f'{i:02d}-{method.lower()}-{Path(path).name}'
        selected = local if local.exists() else Path(path)
        bound = (len(binding) == len(PINS) and isinstance(binding[i], dict) and binding[i].get("canonical_origin_path") == path
                 and binding[i].get("materialized_file") == local.name and binding[i].get("sha256") == expected)
        try:
            raw = selected.read_bytes()
            actual, size = digest(raw), len(raw)
        except OSError:
            actual, size = None, None
        rows.append({"method": method, "path": path, "canonical_origin_path": path, "local_path": str(selected),
                     "materialized": selected == local, "binding_verified": bound, "expected_sha256": expected,
                     "actual_sha256": actual, "bytes": size, "matches": actual == expected and (not local.exists() or bound)})
    return rows


def _isolated(path, operating_path):
    path, operating_path = Path(path).resolve(), Path(operating_path).resolve()
    if path == operating_path or path.name == "aster.sqlite" or (path.exists() and operating_path.exists() and os.path.samefile(path, operating_path)):
        raise ValueError("Research journal must not be the operating ledger")
    if path.exists():
        with _readonly(path) as con:
            names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if any(n != "sqlite_sequence" and not n.startswith("original_") for n in names):
            raise ValueError("Research journal cannot contain another ledger")
    return path


class OriginalResearch:
    def __init__(self, db_path=None, operating_path=None, *, now=None):
        self.operating_path = Path(operating_path or os.environ.get("ASTER_DB_PATH", ROOT / "data/aster.sqlite")).resolve()
        self.path = _isolated(db_path or default_path(), self.operating_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._mutex = threading.Lock()
        self._lease_fd = None
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS original_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS original_receipts(id TEXT PRIMARY KEY,method TEXT NOT NULL,kind TEXT NOT NULL,source_key TEXT NOT NULL,
                  source_url TEXT,content_sha256 TEXT NOT NULL,body BLOB NOT NULL,first_received_at TEXT NOT NULL,publication_at TEXT,
                  usable_at TEXT NOT NULL,context_only INTEGER NOT NULL,details TEXT NOT NULL,UNIQUE(method,kind,source_key,content_sha256));
                CREATE TABLE IF NOT EXISTS original_events(id TEXT PRIMARY KEY,kind TEXT NOT NULL,created_at TEXT NOT NULL,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS original_panel_assessments(receipt_id TEXT PRIMARY KEY,symbol TEXT NOT NULL,frame TEXT NOT NULL,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS original_forecasts(id TEXT PRIMARY KEY,receipt_id TEXT NOT NULL,symbol TEXT NOT NULL,emitted_at TEXT NOT NULL,
                  observed_at TEXT NOT NULL,qualified INTEGER NOT NULL,reason TEXT NOT NULL,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS original_public_events(id TEXT PRIMARY KEY,receipt_id TEXT NOT NULL,publication_at TEXT,
                  first_received_at TEXT NOT NULL,context_only INTEGER NOT NULL,data TEXT NOT NULL);
            """)
            saved = dict(con.execute("SELECT key,value FROM original_meta"))
            if saved and (saved.get("controls_sha256") != CONTROL_SHA or saved.get("controls") != canonical(CONTROLS)):
                raise ValueError("Frozen control registry mismatch")
            con.execute("INSERT OR IGNORE INTO original_meta VALUES('controls_sha256',?)", (CONTROL_SHA,))
            con.execute("INSERT OR IGNORE INTO original_meta VALUES('controls',?)", (canonical(CONTROLS),))
            con.execute("INSERT OR IGNORE INTO original_meta VALUES('registered_at',?)", (iso(now),))
            con.execute("INSERT OR IGNORE INTO original_meta VALUES('lineage',?)", (canonical(source_lineage()),))

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            with con:
                yield con
        finally:
            con.close()

    def event(self, kind, payload, *, now=None):
        created = iso(now)
        identity = digest(canonical({"kind": kind, "at": created, "payload": payload}).encode())
        with self.connect() as con:
            con.execute("INSERT OR IGNORE INTO original_events VALUES(?,?,?,?)", (identity, kind, created, canonical(payload)))
        return identity

    def heartbeat(self, interval, state, *, now=None):
        if self._lease_fd is None:
            raise ValueError("Heartbeat requires this process's exclusive collector lease")
        if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not math.isfinite(interval) or interval < 60:
            raise ValueError("Research heartbeat interval must be at least 60 seconds")
        current = clock(now)
        value = {"pid": os.getpid(), "process_birth": process_birth(os.getpid()), "state": state,
                 "observed_at": current.isoformat(), "interval_seconds": interval,
                 "stale_after_seconds": max(2 * interval + 75, 120), "lease": "exclusive_flock_per_research_journal"}
        with self.connect() as con:
            con.execute("INSERT OR REPLACE INTO original_meta VALUES('worker_heartbeat',?)", (canonical(value),))
        return value

    def receive(self, method, kind, source_key, body, *, received_at=None, publication_at=None, source_url=None, context_only=True, details=None):
        if method not in METHODS or not isinstance(body, bytes) or len(body) > MAX_RECEIPT_BYTES:
            raise ValueError("Invalid or oversized original-method receipt")
        received = clock(received_at)
        publication = clock(publication_at) if publication_at is not None else None
        if publication and publication > received:
            raise ValueError("Future publication clock")
        identity = digest(canonical([method, kind, source_key, digest(body)]).encode())
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            old = con.execute("SELECT * FROM original_receipts WHERE id=?", (identity,)).fetchone()
            if old:
                return dict(old)  # immutable first receipt; a reread grants no fresh event
            stored = con.execute("SELECT COALESCE(SUM(length(body)),0) FROM original_receipts").fetchone()[0]
            if stored + len(body) > MAX_STORED_BYTES:
                raise ValueError("25 MiB capture budget exhausted; preserve prior receipts")
            con.execute("INSERT INTO original_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (identity, method, kind, source_key, source_url, digest(body), body, received.isoformat(),
                         publication.isoformat() if publication else None, received.isoformat(), int(context_only), canonical(details or {})))
            return dict(con.execute("SELECT * FROM original_receipts WHERE id=?", (identity,)).fetchone())

    def capture_operating(self, symbols=("AAPL", "MSFT"), *, received_at=None):
        """Snapshot qualified source rows read-only. Limited enrollment is explicit.

        Preserves original compressed BLOB bytes and row metadata. This does not
        attest that Yahoo's hourly slots or cross-frame adjustment are canonical TRACE.
        """
        received = clock(received_at)
        requested = sorted(set(str(s).upper() for s in symbols) | {"SPY", "XLK"})
        if len(requested) > 32 or any(not s.replace(".", "").replace("-", "").isalnum() for s in requested):
            raise ValueError("At most 32 explicit symbols required")
        report = {"read_only": True, "operating_path": str(self.operating_path), "symbols": requested, "panels": [], "source_schema": {}, "enrollment_complete": False}
        with _readonly(self.operating_path) as con:
            con.execute("BEGIN")
            schema = {r["name"]: r["sql"] for r in con.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")}
            selected_tables = ("a_tensor_candidates", "a_tensor_decisions", "a_tensor_coverage", "a_tensor_revision_receipts", "a_tensor_censuses")
            report["source_schema"] = {k: schema.get(k) for k in selected_tables}
            report["original_forecast_emitter_found"] = False
            for table in ("a_tensor_candidates", "a_tensor_decisions", "a_tensor_censuses"):
                if table not in schema:
                    continue
                columns = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
                order = "created_at DESC" if "created_at" in columns else "origin_ms DESC"
                limit = 5 if table == "a_tensor_censuses" else 100
                rows = [dict(r) for r in con.execute(f"SELECT * FROM {table} ORDER BY {order} LIMIT {limit}")]
                self.receive("TRACE", "operating_selection_context", table, canonical(rows).encode(), received_at=received,
                             details={"selection_or_tensor_prediction_is_not_original_CRD_forecast": True})
            if "a_tensor_coverage" in schema:
                placeholders = ",".join("?" for _ in requested)
                for row in con.execute(f"SELECT * FROM a_tensor_coverage WHERE symbol IN ({placeholders}) ORDER BY symbol,frame", requested):
                    raw = row["bars"]
                    if isinstance(raw, str):
                        raw = raw.encode()
                    meta = {k: row[k] for k in row.keys() if k != "bars"}
                    r = self.receive("TRACE", "native_panel_blob", f'{row["symbol"]}:{row["frame"]}:{row["revision_id"]}', raw,
                                     received_at=received, details={"operating_row": meta, "limited_collector_enrollment": requested})
                    first_meta = json.loads(r["details"])["operating_row"]
                    assessment = assess_panel(raw, row["frame"], r["first_received_at"], first_meta["observed_at"], first_meta["status"])
                    assessment.update({"receipt_id": r["id"], "symbol": row["symbol"], "frame": row["frame"]})
                    with self.connect() as own:
                        own.execute("INSERT OR IGNORE INTO original_panel_assessments VALUES(?,?,?,?)", (r["id"], row["symbol"], row["frame"], canonical(assessment)))
                    report["panels"].append(assessment)
            present = {(p["symbol"], p["frame"]) for p in report["panels"]}
            report["missing_panels"] = [{"symbol": symbol, "frame": frame} for symbol in requested
                                        for frame in ("1h", "1d", "1wk") if (symbol, frame) not in present]
        self.receive("TRACE", "operating_schema_context", "schemas-v1", canonical(report["source_schema"]).encode(), received_at=received)
        self.event("operating_snapshot", report, now=received)
        return report

    def ingest_forecast(self, payload, *, received_at=None):
        """Register genuine new observations, never synthesize aged forecasts.

        Qualification here means receipt-series admission, not model certification.
        Full canonical strategy remains input-blocked regardless of this field.
        """
        if not isinstance(payload, dict):
            raise ValueError("Forecast object required")
        received, emitted = clock(received_at), clock(payload["emitted_at"])
        if emitted > received:
            raise ValueError("Forecast emitted in the future")
        identity = payload.get("id")
        if not isinstance(identity, str) or not identity or len(identity) > 200:
            raise ValueError("Immutable forecast identity required")
        raw = canonical(payload).encode()
        with self.connect() as con:
            old = con.execute("SELECT * FROM original_forecasts WHERE id=?", (identity,)).fetchone()
            if old:
                if old["data"] != canonical(payload):
                    raise ValueError("Conflicting forecast identity")
                return dict(old)
            registered = clock(con.execute("SELECT value FROM original_meta WHERE key='registered_at'").fetchone()[0])
            reason = "newly_observed_source_bound_emission"
            if emitted < registered:
                reason = "pre_registration_context_no_back_aging"
            elif (received - emitted).total_seconds() > 300:
                reason = "late_historical_receipt_not_prospective_memory"
            elif (payload.get("method") != "CRD" or payload.get("original_model_source_sha256") != PINS[5][2]
                  or payload.get("controls_sha256") != CONTROL_SHA):
                reason = "not_original_CRD_emitter"
            elif not all(r["matches"] for r in source_lineage()):
                reason = "source_lineage_mismatch"
            elif (type(payload.get("calibration_origin_dates")) is not int or type(payload.get("effective_state_origin_dates")) is not int
                  or payload["calibration_origin_dates"] < 100 or payload["effective_state_origin_dates"] < 30):
                reason = "original_calibration_support_missing"
            else:
                refs = payload.get("input_receipt_ids")
                if not isinstance(refs, list) or not refs:
                    reason = "source_input_receipts_missing"
                else:
                    for ref in refs:
                        source = con.execute("SELECT usable_at,body,content_sha256 FROM original_receipts WHERE id=?", (ref,)).fetchone()
                        if source is None or clock(source[0]) > emitted or digest(source["body"]) != source["content_sha256"]:
                            reason = "source_input_unavailable_at_emission"
                            break
            for name in ("residual_forecast", "rank_only_forecast", "standard_error"):
                value = payload.get(name)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (name == "standard_error" and value < 0):
                    raise ValueError("Finite original forecast components required")
            if not isinstance(payload.get("symbol"), str) or not payload["symbol"]:
                raise ValueError("Forecast symbol required")
        qualified = reason == "newly_observed_source_bound_emission"
        r = self.receive("CRD", "forecast_emission", identity, raw, received_at=received, publication_at=emitted, context_only=not qualified,
                         details={"series_admission_only_not_validated_financial_model": True, "reason": reason})
        # A crash after receipt persistence cannot refresh first arrival or upgrade
        # a context-only receipt when the same payload is later replayed.
        qualified = qualified and not bool(r["context_only"])
        reason = json.loads(r["details"])["reason"]
        with self.connect() as con:
            con.execute("INSERT OR IGNORE INTO original_forecasts VALUES(?,?,?,?,?,?,?,?)",
                        (identity, r["id"], payload["symbol"], emitted.isoformat(), r["first_received_at"], int(qualified), reason, canonical(payload)))
            saved = dict(con.execute("SELECT * FROM original_forecasts WHERE id=?", (identity,)).fetchone())
            if saved["data"] != canonical(payload):
                raise ValueError("Conflicting forecast identity")
            return saved

    def capture_spy(self, *, fetcher=None):
        """Public GETs normalized in a disposable isolated Store, never Aster.

        Raw headers/body and first arrival bind native closure. SPY is a market
        factor ETF, not a member of the canonical ordinary-share universe.
        """
        from .providers import Providers
        from .store import Store
        from .tensor_runtime import canonical_native_bars
        reports = []
        with tempfile.TemporaryDirectory(prefix="aster-original-spy-") as directory:
            store = Store(Path(directory) / "normalizer.sqlite")
            captures = []

            def transport(method, url, payload, headers):
                if method != "GET" or payload is not None:
                    raise ValueError("SPY normalizer has public read-only GET authority")
                parsed = urllib.parse.urlsplit(url)
                if parsed.scheme != "https" or parsed.netloc != "query1.finance.yahoo.com" or parsed.path != "/v8/finance/chart/SPY":
                    raise ValueError("Only public SPY chart allowed")
                result = (fetcher or fetch_market)(url)
                r = self.receive("TRACE", "spy_raw_public_chart", "SPY:" + urllib.parse.parse_qs(parsed.query)["interval"][0],
                    result["body"], received_at=result["received_at"], source_url=url,
                    details={"response_headers": result.get("headers", {}), "http_status": result["status"], "factor_identity": "SPY ETF market factor only"})
                captures.append(r)
                if result["status"] != 200:
                    raise ValueError("SPY public chart HTTP failure")
                return json.loads(result["body"])

            providers = Providers(store, transport=transport)
            for frame, interval, period in (("1h", "60m", "1mo"), ("1d", "1d", "2y"), ("1wk", "1wk", "2y")):
                try:
                    content = providers._yahoo_bars("SPY", period, interval)
                    response = providers._save_bars("SPY", period, interval, content)
                    first = captures[-1]["first_received_at"]
                    response.update({"fetched_at": first, "observed_at": first})
                    diagnostics = []
                    bars = canonical_native_bars(response, frame, clock(first), expected_symbol="SPY", diagnostics=diagnostics)
                    raw = zlib.compress(canonical([vars(b) for b in bars]).encode(), 1)
                    r = self.receive("TRACE", "spy_native_factor_panel", f'SPY:{frame}:{response["revision_id"]}', raw,
                        received_at=first, details={"raw_receipt_id": captures[-1]["id"], "normalized_revision": response["revision_id"],
                            "factor_identity": "SPY ETF market factor only", "adjustment": response["adjustment"], "request_window": response.get("request_window"),
                            "diagnostics": diagnostics, "context_only_not_historical_opportunities": True})
                    assessment = assess_panel(raw, frame, r["first_received_at"], first, "ready")
                    assessment.update({"receipt_id": r["id"], "symbol": "SPY", "frame": frame, "factor_identity": "ETF_market_factor_not_candidate_stock"})
                    with self.connect() as con:
                        con.execute("INSERT OR IGNORE INTO original_panel_assessments VALUES(?,?,?,?)", (r["id"], "SPY", frame, canonical(assessment)))
                    reports.append(assessment)
                except Exception as exc:
                    report = {"symbol": "SPY", "frame": frame, "status": "blocked", "error": str(exc)}
                    self.event("SPY_factor_capture_failure", report)
                    reports.append(report)
        self.event("SPY_factor_capture", {"panels": reports, "operating_database_mutations": 0})
        return reports

    def collect_public(self, *, fetcher=None):
        outcomes = []
        for method, kind, url in PUBLIC_SOURCES:
            try:
                result = (fetcher or fetch_public)(url)
                received = clock(result["received_at"])
                success = result["status"] == 200
                body = result["body"]
                detail = {"http_status": result["status"], "content_type": result.get("content_type"), "final_url": result.get("final_url", url),
                          "successful_primary_document": success, "previous_filings_are_context": True}
                r = self.receive(method, kind, url, body, received_at=received, source_url=url, details=detail)
                if success and kind == "sec_submissions":
                    self._sec_events(r)
                if success and kind == "official_calendar":
                    text = html.unescape(re.sub(r"<[^>]+>", " ", body.decode("utf-8", "replace"))).lower()
                    # A fetched page binds the proposed schedule only if all three dates actually occur.
                    confirmed = all(re.search(pattern, text) for pattern in (
                        r"(?:november\s+13|13\s+november)", r"(?:december\s+11|11\s+december)", r"(?:december\s+14|14\s+december)"))
                    self.event("official_calendar_receipt", {"receipt_id": r["id"], "schedule_text_verified": confirmed,
                        "proposed_schedule": CONTROLS["TCFT_calendar"], "constituent_changes_observed": False,
                        "publication_date": "2026-09-01" if "september 01, 2026" in text else None,
                        "publication_clock_precision": "date_only_not_an_instant"}, now=received)
                if success and kind == "issuer_context":
                    text = html.unescape(re.sub(r"<[^>]+>", " ", body.decode("utf-8", "replace"))).lower()
                    self.event("issuer_publication_context", {"receipt_id": r["id"],
                        "publication_date": "2026-07-29" if "july 29, 2026" in text else None,
                        "publication_clock_precision": "date_only_not_an_instant", "context_only": True}, now=received)
                outcomes.append({"method": method, "kind": kind, "status": "received" if success else "http_failure_context", "receipt_id": r["id"], **detail})
            except Exception as exc:
                outcome = {"method": method, "kind": kind, "status": "failed", "error": str(exc), "url": url}
                self.event("public_capture_failure", outcome)
                outcomes.append(outcome)
        return outcomes

    def _sec_events(self, receipt):
        source = json.loads(receipt["body"])
        recent = source.get("filings", {}).get("recent", {})
        with self.connect() as con:
            registered = clock(con.execute("SELECT value FROM original_meta WHERE key='registered_at'").fetchone()[0])
            for i, accession in enumerate(recent.get("accessionNumber", [])[:100]):
                if recent.get("form", [])[i] not in ("10-Q", "10-K", "8-K"):
                    continue
                accepted = recent.get("acceptanceDateTime", [])[i]
                # SEC submissions acceptanceDateTime has an explicit UTC offset/Z.
                published = clock(accepted)
                if published > clock(receipt["first_received_at"]):
                    continue
                identity = f'sec:{source["cik"]}:{accession}'
                context = published < registered
                payload = {"accession": accession, "form": recent["form"][i], "primary_document": recent["primaryDocument"][i],
                           "publication_source": "SEC acceptanceDateTime", "first_seen_is_not_publication": True,
                           "filing_body_received": False, "UIR_event_model_qualified": False}
                con.execute("INSERT OR IGNORE INTO original_public_events VALUES(?,?,?,?,?,?)",
                            (identity, receipt["id"], published.isoformat(), receipt["first_received_at"], int(context), canonical(payload)))

    def once(self, symbols=("AAPL", "MSFT"), *, public=True):
        with self._mutex:
            lineage = source_lineage()
            if not all(r["matches"] for r in lineage):
                raise ValueError("Original source lineage changed or unavailable")
            report = {"operating": self.capture_operating(symbols), "SPY": self.capture_spy() if public else [], "public": self.collect_public() if public else [],
                      "financial_simulations": 0, "orders": 0, "funding": 0}
            self.event("cycle_completed", report)
            return report


def assess_panel(raw, frame, received_at, source_observed_at, status):
    result = {"valid_causal_bar_count": 0, "required_history": CONTROLS["TRACE_histories"].get(frame),
              "required_feature_window": {"1h": 28, "1d": 20, "1wk": 12}.get(frame), "canonical_TRACE_ready": False,
              "blockers": ["canonical_adjustment_and_hourly_slot_contract_unverified", "original_B_H_projection_and_fitted_outcome_model_missing",
                           "historical_issuer_sector_action_lineage_missing", "complete_canonical_enrollment_not_collected"]}
    try:
        if not isinstance(raw, bytes) or len(raw) > MAX_RECEIPT_BYTES:
            raise ValueError("panel bytes invalid")
        decoder = zlib.decompressobj()
        decoded = decoder.decompress(raw, MAX_RECEIPT_BYTES + 1)
        if len(decoded) > MAX_RECEIPT_BYTES or not decoder.eof or decoder.unused_data:
            raise ValueError("panel decode exceeds bound or has trailing bytes")
        rows = json.loads(decoded)
        if not isinstance(rows, list):
            raise ValueError("panel array required")
        observed, received = clock(source_observed_at), clock(received_at)
        if observed > received or status != "ready":
            raise ValueError("source not causally ready")
        ms = int(received.timestamp() * 1000)
        prior = -1
        for row in rows:
            for key in ("timestamp_ms", "completed_at_ms", "usable_at_ms"):
                if type(row.get(key)) is not int:
                    raise ValueError("noninteger native clock")
            if not prior < row["timestamp_ms"] < row["completed_at_ms"] <= row["usable_at_ms"] <= ms:
                raise ValueError("native clock order/finality violation")
            prior = row["timestamp_ms"]
            for key in ("open", "high", "low", "close", "volume"):
                value = row.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or (key != "volume" and value == 0):
                    raise ValueError("invalid native OHLCV")
            if row["high"] < max(row["open"], row["close"], row["low"]) or row["low"] > min(row["open"], row["close"], row["high"]):
                raise ValueError("inconsistent OHLC")
        result["valid_causal_bar_count"] = len(rows)
        result["source_observed_at"] = observed.isoformat()
        result["collector_first_received_at"] = received.isoformat()
        result["all_rows_context_received_now_not_historical_opportunities"] = True
        result["history_count_sufficient"] = bool(result["required_history"] and len(rows) >= result["required_history"])
        if not result["history_count_sufficient"]:
            result["blockers"].append("required_history_missing")
    except Exception as exc:
        result["history_count_sufficient"] = False
        result["blockers"].append(str(exc))
    return result


def fetch_public(url):
    if url not in {r[2] for r in PUBLIC_SOURCES}:
        raise ValueError("Only configured official public URLs allowed")
    result = _fetch_http(url, {"User-Agent": "AsterOriginalResearch/1 research-contact john@aster.invalid", "Accept": "application/json,text/html"})
    result["content_type"] = result["headers"].get("Content-Type")
    return result


def fetch_market(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "query1.finance.yahoo.com" or parsed.path != "/v8/finance/chart/SPY":
        raise ValueError("Only configured SPY public chart allowed")
    return _fetch_http(url, {"User-Agent": "Mozilla/5.0 AsterOriginalResearch/1", "Accept": "application/json"})


def _fetch_http(url, headers, *, timeout=10, maximum_bytes=MAX_RECEIPT_BYTES):
    """Absolute cancellable deadline across headers and streaming body."""
    import httpx
    from .http_transport import _io_loop
    async def get():
        async with asyncio.timeout(timeout):
            async with httpx.AsyncClient(timeout=timeout, trust_env=True, follow_redirects=True) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        body.extend(chunk)
                        if len(body) > maximum_bytes:
                            raise ValueError("Public response exceeds capture bound")
                    return {"body": bytes(body), "status": response.status_code, "received_at": iso(None), "final_url": str(response.url),
                        "headers": {name: response.headers.get(name) for name in ("Date", "Content-Type", "ETag", "Last-Modified", "Cache-Control")}}
    future = asyncio.run_coroutine_threadsafe(get(), _io_loop())
    try:
        return future.result(timeout=timeout)
    except FutureTimeout:
        future.cancel()
        raise TimeoutError("Public source exceeded absolute receipt deadline") from None


def read_status(db_path=None):
    """Read-only projection. Missing file stays missing; never constructs runtime."""
    path = Path(db_path or default_path()).resolve()
    base = {"status": "not_started", "registered": False, "db_path": str(path), "authority": CONTROLS["authority"], "funding": 0, "orders": 0,
            "financial_simulations": 0, "controls_sha256": CONTROL_SHA, "methods": {m: {"status": "input_blocked"} for m in METHODS}}
    if not path.is_file():
        return base
    try:
        with _readonly(path) as con:
            con.execute("BEGIN")
            meta = dict(con.execute("SELECT key,value FROM original_meta"))
            if meta.get("controls_sha256") != CONTROL_SHA or meta.get("controls") != canonical(CONTROLS):
                raise ValueError("Control registry mismatch")
            base.update({"status": "registered_unfunded_research", "registered": True, "registered_at": meta["registered_at"],
                "stored_receipt_bytes": con.execute("SELECT COALESCE(SUM(length(body)),0) FROM original_receipts").fetchone()[0],
                "receipt_count": con.execute("SELECT COUNT(*) FROM original_receipts").fetchone()[0],
                "event_count": con.execute("SELECT COUNT(*) FROM original_events").fetchone()[0],
                "lineage": json.loads(meta["lineage"]), "current_lineage_matches": all(x["matches"] for x in source_lineage())})
            worker = json.loads(meta["worker_heartbeat"]) if "worker_heartbeat" in meta else None
            if worker:
                age = (clock() - clock(worker["observed_at"])).total_seconds()
                worker["pid_birth_matches"] = worker["process_birth"] is not None and worker["process_birth"] == process_birth(worker["pid"])
                worker["lease_held"] = lease_held(path)
                worker["heartbeat_age_seconds"] = age
                worker["active"] = (worker["state"] != "stopped" and worker["pid_birth_matches"] and worker["lease_held"] and 0 <= age <= worker["stale_after_seconds"])
                if worker["active"]:
                    base["status"] = "collecting_unfunded_research"
            base["worker"] = worker
            panels = [json.loads(r[0]) for r in con.execute("SELECT data FROM original_panel_assessments ORDER BY symbol,frame")]
            base["methods"]["TRACE"].update({"panels": panels[-96:], "canonical_ready": False})
            base["methods"]["CRD"].update({"observed_forecast_count": con.execute("SELECT COUNT(*) FROM original_forecasts").fetchone()[0],
                "prospective_series_receipt_count": con.execute("SELECT COUNT(*) FROM original_forecasts WHERE qualified=1").fetchone()[0],
                "blockers": ["canonical_original_forecast_emitter_not_connected", "full_11_state_model_scenarios_and_held_context_missing"], "canonical_ready": False})
            base["methods"]["UIR"].update({"SEC_event_context_count": con.execute("SELECT COUNT(*) FROM original_public_events WHERE context_only=1").fetchone()[0],
                "new_SEC_first_arrival_count": con.execute("SELECT COUNT(*) FROM original_public_events WHERE context_only=0").fetchone()[0],
                "blockers": ["signed_pre_event_operating_exposure_graph_missing", "event_residual_model_and_receiver_absorption_missing"], "canonical_ready": False})
            base["methods"]["TCFT"].update({"known_upcoming_calendar": CONTROLS["TCFT_calendar"], "target_changes_observed": False,
                "blockers": ["announced_original_target_vintages_missing", "bounded_inventory_and_signed_physical_return_model_missing"], "canonical_ready": False})
            row = con.execute("SELECT payload FROM original_events WHERE kind='official_calendar_receipt' ORDER BY created_at DESC,id DESC LIMIT 1").fetchone()
            base["methods"]["TCFT"]["official_calendar_receipt"] = json.loads(row[0]) if row else None
    except Exception as exc:
        base["status"], base["error"] = "blocked_journal_error", str(exc)
    return base


def process_birth(pid):
    if type(pid) is not int or pid <= 0:
        return None
    try:
        # Linux stat command may contain spaces/parentheses; fields start after final ')'.
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


@contextmanager
def collector_lease(runtime):
    if runtime._lease_fd is not None:
        raise ValueError("Collector lease already owned by this runtime")
    path = Path(str(runtime.path) + ".collector.lock")
    if path.exists() and (os.path.samefile(path, runtime.path) or (runtime.operating_path.exists() and os.path.samefile(path, runtime.operating_path))):
        raise ValueError("Collector lease cannot alias its journal")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another collector owns this research journal") from None
        runtime._lease_fd = fd
        yield
    finally:
        runtime._lease_fd = None
        os.close(fd)


def lease_held(db_path):
    """Inspect existing OS lease without creating a lock or writing any file."""
    path = Path(str(db_path) + ".collector.lock")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        return False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)


def cycle_summary(report):
    return {"operating_panel_count": len(report["operating"]["panels"]),
            "SPY_panel_count": len([x for x in report["SPY"] if x.get("receipt_id")]),
            "public_capture_count": len(report["public"]), "financial_simulations": 0, "funding": 0, "orders": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "once", "serve", "ingest-forecast"))
    parser.add_argument("--db", type=Path, default=default_path())
    parser.add_argument("--operating-db", type=Path, default=ROOT / "data/aster.sqlite")
    parser.add_argument("--symbols", default="AAPL,MSFT")
    parser.add_argument("--no-public", action="store_true")
    parser.add_argument("--forecast-json", type=Path)
    parser.add_argument("--interval", type=float, default=3600)
    args = parser.parse_args(argv)
    if args.command == "status":
        print(canonical(read_status(args.db)))
        return
    runtime = OriginalResearch(args.db, args.operating_db)
    if args.command == "ingest-forecast":
        if args.forecast_json is None or args.forecast_json.stat().st_size > MAX_RECEIPT_BYTES:
            parser.error("Bounded --forecast-json file required")
        print(canonical(runtime.ingest_forecast(json.loads(args.forecast_json.read_text()))))
        return
    if not math.isfinite(args.interval) or args.interval < 60:
        parser.error("Serve interval must be finite and at least 60 seconds")
    if args.command == "once":
        with collector_lease(runtime):
            runtime.heartbeat(args.interval, "collecting")
            try:
                print(canonical(runtime.once(args.symbols.split(","), public=not args.no_public)))
            finally:
                runtime.heartbeat(args.interval, "stopped")
        return
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    with collector_lease(runtime):
        try:
            while not stopped.is_set():
                runtime.heartbeat(args.interval, "collecting")
                try:
                    print(canonical(cycle_summary(runtime.once(args.symbols.split(","), public=not args.no_public))), flush=True)
                except Exception as exc:
                    runtime.event("cycle_failure", {"error": str(exc)})
                runtime.heartbeat(args.interval, "sleeping")
                stopped.wait(args.interval)
        finally:
            runtime.heartbeat(args.interval, "stopped")


if __name__ == "__main__":
    main()
