"""Durable, fenced operational supervisor and explicitly installed paper rules.

Interval work remains due until completed. Exchange-session work carries an
expiry, so missed time-sensitive windows are recorded rather than replayed.
"""
import fcntl
import json
import math
import os
import shutil
import threading
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .providers import BAR_DAYS, BAR_INTERVALS, NY, Providers, utc_clock
from .store import DeskError, identifier, symbol


UTC = timezone.utc
PHASES = {"preopen", "open", "intraday", "close", "postclose"}
KINDS = {"operations", "strategies", "refresh", "reconcile", "lab", "desk_brief", "bars", "verify"}


class _WindowExpired(DeskError):
    pass


class _WorkPaused(DeskError):
    paused = True


class _FencedBroker:
    def __init__(self, broker, fence):
        self._broker, self._fence = broker, fence

    def __getattr__(self, name):
        value = getattr(self._broker, name)
        if name in {"submit", "cancel"}:
            def guarded(*args, **kwargs):
                self._fence()
                return value(*args, **kwargs)
            return guarded
        return value


class _FencedProviders:
    def __init__(self, provider, fence):
        self._provider = provider
        self._fence = fence
        self.execution_fence = fence
        self.broker = _FencedBroker(provider.broker, fence) if provider.broker is not None else None
        self.brokers = {name: _FencedBroker(broker, fence) for name, broker in getattr(provider, "brokers", {}).items()}

    def broker_for(self, connection_id="default"):
        if hasattr(self._provider, "broker_for"):
            broker = self._provider.broker_for(connection_id)
            return _FencedBroker(broker, self._fence) if broker is not None else None
        return self.broker if connection_id == "default" else None

    def __getattr__(self, name):
        return getattr(self._provider, name)


class AutonomyRuntime:
    LEASE_SECONDS = 120
    SESSION_CATCHUP_DAYS = 7
    DEFAULTS = {"running": True, "refresh_seconds": 60, "brief_seconds": 900, "minimum_free_bytes": 10_000_000}

    def __init__(self, store, trading, lab, reasoning, providers=None):
        self.store, self.trading, self.lab, self.reasoning = store, trading, lab, reasoning
        self.providers = providers or Providers(store)
        self.owner = identifier()
        self.thread = None
        self.stop_event = threading.Event()
        self._mutex = threading.Lock()
        self.last_error = None
        self._calendar = None
        self._refresh_cursor = 0
        self._held_cursor = 0
        self._intent_cursor = 0
        self.notifications = None
        self.strategies = None
        self.actions = None
        with store.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS a_runtime_config(id INTEGER PRIMARY KEY CHECK(id=1),data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_runtime_lock(id INTEGER PRIMARY KEY CHECK(id=1),owner TEXT,expires REAL NOT NULL);
                INSERT OR IGNORE INTO a_runtime_lock VALUES(1,NULL,0);
                CREATE TABLE IF NOT EXISTS a_runtime_health(id INTEGER PRIMARY KEY CHECK(id=1),data TEXT NOT NULL);
                INSERT OR IGNORE INTO a_runtime_health VALUES(1,'{}');
                CREATE TABLE IF NOT EXISTS a_schedules(id TEXT PRIMARY KEY,label TEXT NOT NULL,kind TEXT NOT NULL,cadence TEXT NOT NULL,
                    interval_seconds INTEGER,phase TEXT,enabled INTEGER NOT NULL,payload TEXT NOT NULL,next_due REAL,
                    last_success_at TEXT,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_jobs(id TEXT PRIMARY KEY,schedule_id TEXT NOT NULL,due_at REAL NOT NULL,expires_at REAL,
                    status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at REAL NOT NULL,owner TEXT,lease_until REAL,
                    started_at TEXT,completed_at TEXT,result TEXT,error TEXT,UNIQUE(schedule_id,due_at));
                CREATE INDEX IF NOT EXISTS a_jobs_due ON a_jobs(status,next_attempt_at);
                CREATE TABLE IF NOT EXISTS a_session_cursors(schedule_id TEXT PRIMARY KEY,through_at REAL NOT NULL);
            """)
            con.execute("INSERT OR IGNORE INTO a_runtime_config VALUES(1,?)", (json.dumps(self.DEFAULTS),))
            timestamp = datetime.now(UTC).isoformat()
            con.execute("INSERT OR IGNORE INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        ("default-operations", "Autonomous operations", "operations", "interval", 60, None, 1, "{}", 0, None, timestamp))
            con.execute("INSERT OR IGNORE INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        ("default-brief", "Configured model desk brief", "desk_brief", "interval", 900, None, int(bool(reasoning.configured)), "{}", 0, None, timestamp))
            con.execute("INSERT OR IGNORE INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        ("benchmark-history", "QQQ and S&P 500 proxy history", "bars", "interval", 3600, None, int(getattr(self.providers, "kind", "yahoo") != "manual"), json.dumps({"symbols": ["QQQ", "SPY"], "range": "1y", "interval": "1d"}), 0, None, timestamp))
            nightly = datetime.now(UTC).replace(hour=1, minute=0, second=0, microsecond=0)
            if nightly <= datetime.now(UTC):
                nightly += timedelta(days=1)
            con.execute("INSERT OR IGNORE INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        ("nightly-verification", "Nightly journal and broker verification", "verify", "interval", 86400, None, 1, "{}", nightly.timestamp(), None, timestamp))
            for phase in sorted(PHASES):
                con.execute("INSERT OR IGNORE INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                            ("session-" + phase, "Exchange " + phase, "verify" if phase == "postclose" else "operations", "session", 1800 if phase == "intraday" else None, phase, 1, "{}", None, None, timestamp))

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, name="aster-autonomous-supervisor", daemon=True)
        self.thread.start()

    def bind_notifications(self, dispatcher):
        self.notifications = dispatcher

    def ensure_strategy_schedule(self):
        """Create the bounded fast strategy poll only after explicit installation."""
        with self.store.transaction() as con:
            con.execute("INSERT OR IGNORE INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        ("tensor-strategies", "Frozen Tensor paper sleeves", "strategies", "interval", 1, None, 1, "{}", 0, None, datetime.now(UTC).isoformat()))
        return "tensor-strategies"

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=20)
        if not self.thread or not self.thread.is_alive():
            with self.store.transaction() as con:
                con.execute("UPDATE a_runtime_lock SET owner=NULL,expires=0 WHERE owner=?", (self.owner,))

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                self.run_once()
                self.last_error = None
            except Exception:
                self.last_error = "Autonomous supervisor encountered a storage or runtime error"
            self.stop_event.wait(1)

    def _config(self, con):
        return json.loads(con.execute("SELECT data FROM a_runtime_config WHERE id=1").fetchone()[0])

    def _health(self, con, **values):
        health = json.loads(con.execute("SELECT data FROM a_runtime_health WHERE id=1").fetchone()[0])
        health.update(values)
        con.execute("UPDATE a_runtime_health SET data=? WHERE id=1", (json.dumps(health),))

    def configure(self, payload):
        unknown = set(payload) - {"running", "refresh_seconds", "brief_seconds", "brief_enabled", "minimum_free_bytes"}
        if unknown:
            raise DeskError("Unknown autonomous runtime setting", 422)
        for field in ("running", "brief_enabled"):
            if field in payload and not isinstance(payload[field], bool):
                raise DeskError(field + " must be a boolean", 422)
        for field, minimum, maximum in (("refresh_seconds", 5, 86400), ("brief_seconds", 60, 86400), ("minimum_free_bytes", 1_000_000, 10_000_000_000)):
            if field in payload and (isinstance(payload[field], bool) or not isinstance(payload[field], int) or not minimum <= payload[field] <= maximum):
                raise DeskError(field + " is outside its allowed range", 422)
        with self.store.transaction() as con:
            config = self._config(con)
            config.update({k: v for k, v in payload.items() if k != "brief_enabled"})
            con.execute("UPDATE a_runtime_config SET data=? WHERE id=1", (json.dumps(config),))
            if "refresh_seconds" in payload:
                self._set_interval(con, "default-operations", payload["refresh_seconds"])
            if "brief_seconds" in payload:
                self._set_interval(con, "default-brief", payload["brief_seconds"])
            if "brief_enabled" in payload:
                con.execute("UPDATE a_schedules SET enabled=? WHERE id='default-brief'", (int(payload["brief_enabled"]),))
            self.store.event(con, "autonomy_configured", "operator", "Updated autonomous operating settings", payload)
        return self.status()

    @staticmethod
    def _set_interval(con, rid, seconds):
        schedule = con.execute("SELECT * FROM a_schedules WHERE id=?", (rid,)).fetchone()
        next_due = utc_clock(schedule["last_success_at"]).timestamp() + seconds if schedule["last_success_at"] and schedule["cadence"] == "interval" else schedule["next_due"]
        con.execute("UPDATE a_schedules SET interval_seconds=?,next_due=? WHERE id=?", (seconds, next_due, rid))

    def schedule(self, payload):
        kind = payload.get("kind", "operations")
        cadence = payload.get("cadence", "interval")
        if not isinstance(kind, str) or kind not in KINDS or not isinstance(cadence, str) or cadence not in {"interval", "session"}:
            raise DeskError("Unsupported operational schedule", 422)
        phase = payload.get("phase")
        seconds = payload.get("interval_seconds", 60 if cadence == "interval" else None)
        if cadence == "session" and (not isinstance(phase, str) or phase not in PHASES):
            raise DeskError("Session schedule requires a known exchange phase", 422)
        if cadence == "interval" and phase is not None:
            raise DeskError("An interval schedule cannot have an exchange phase", 422)
        if cadence == "interval" or phase == "intraday":
            seconds = 1800 if seconds is None else seconds
            if isinstance(seconds, bool) or not isinstance(seconds, int) or not 5 <= seconds <= 86400:
                raise DeskError("Schedule interval must be 5 to 86400 seconds", 422)
        enabled = payload.get("enabled", True)
        if not isinstance(enabled, bool):
            raise DeskError("Schedule enabled must be a boolean", 422)
        params = payload.get("payload", {})
        if not isinstance(params, dict) or set(params) - {"symbols", "range", "interval", "instructions"} or len(json.dumps(params)) > 4000:
            raise DeskError("Schedule payload supports only symbols, bar range/interval and brief instructions", 422)
        if "symbols" in params and (not isinstance(params["symbols"], list) or len(params["symbols"]) > 16 or any(not isinstance(s, str) for s in params["symbols"])):
            raise DeskError("A schedule supports at most 16 explicit symbols", 422)
        params = dict(params)
        if "symbols" in params:
            params["symbols"] = sorted({symbol(s) for s in params["symbols"]})
        if "range" in params and (not isinstance(params["range"], str) or params["range"] not in BAR_DAYS):
            raise DeskError("Unsupported scheduled bar range", 422)
        if "interval" in params and (not isinstance(params["interval"], str) or params["interval"] not in BAR_INTERVALS):
            raise DeskError("Unsupported scheduled bar interval", 422)
        if "instructions" in params and params["instructions"] is not None and not isinstance(params["instructions"], str):
            raise DeskError("Scheduled brief instructions must be text", 422)
        rid = payload.get("id") or identifier()
        if not isinstance(rid, str) or not 1 <= len(rid) <= 160:
            raise DeskError("A schedule ID must be text of at most 160 characters", 422)
        label = str(payload.get("label") or kind.replace("_", " ").title())[:160]
        with self.store.transaction() as con:
            old = con.execute("SELECT * FROM a_schedules WHERE id=?", (rid,)).fetchone()
            if old and any(con.execute("SELECT 1 FROM a_jobs WHERE schedule_id=? AND status IN ('pending','running','retry')", (rid,))):
                # Updating cadence never reinterprets an unfinished job's meaning.
                if (old["kind"], old["cadence"], old["phase"], old["payload"]) != (kind, cadence, phase, json.dumps(params)):
                    raise DeskError("Finish the schedule's due jobs before changing its operation")
            con.execute("INSERT INTO a_schedules VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET label=excluded.label,kind=excluded.kind,cadence=excluded.cadence,interval_seconds=excluded.interval_seconds,phase=excluded.phase,enabled=excluded.enabled,payload=excluded.payload",
                        (rid, label, kind, cadence, seconds, phase, int(enabled), json.dumps(params), 0 if cadence == "interval" else None, None, datetime.now(UTC).isoformat()))
            if old and cadence == "interval" and old["interval_seconds"] != seconds:
                self._set_interval(con, rid, seconds)
            if cadence == "session" and (not old or not old["enabled"] and enabled):
                con.execute("DELETE FROM a_session_cursors WHERE schedule_id=?", (rid,))
            self.store.event(con, "schedule_saved", "operator", "Saved an operational schedule", {"schedule_id": rid, "kind": kind})
            return self._schedule_public(con.execute("SELECT * FROM a_schedules WHERE id=?", (rid,)).fetchone())

    def retry_job(self, rid):
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM a_jobs WHERE id=?", (rid,)).fetchone()
            if row is None:
                raise DeskError("Job not found", 404)
            if row["status"] in {"running", "succeeded", "skipped"}:
                raise DeskError("Only pending or retrying jobs can be retried")
            con.execute("UPDATE a_jobs SET status='pending',next_attempt_at=0,error=NULL WHERE id=?", (rid,))
            self.store.event(con, "job_retry_requested", "operator", "Requested a durable job retry", {"job_id": rid})
            return self._job_public(con.execute("SELECT * FROM a_jobs WHERE id=?", (rid,)).fetchone())

    def _claim(self):
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM a_runtime_lock WHERE id=1").fetchone()
            if row["owner"] not in {None, self.owner} and row["expires"] > time.time():
                return False
            self._recovered = bool(row["owner"] and row["expires"] <= time.time())
            if self._recovered:
                self.store.event(con, "runtime_lease_recovered", "supervisor", "Recovered expired autonomous worker ownership")
            con.execute("UPDATE a_runtime_lock SET owner=?,expires=? WHERE id=1", (self.owner, time.time() + self.LEASE_SECONDS))
            return True

    def _fence(self, con=None):
        if con is None:
            with self.store.transaction() as writer:
                self._fence(writer)
            return
        row = con.execute("SELECT * FROM a_runtime_lock WHERE id=1").fetchone()
        if row["owner"] != self.owner or row["expires"] <= time.time():
            raise DeskError("Autonomous worker lost its execution fence")
        con.execute("UPDATE a_runtime_lock SET expires=? WHERE id=1", (time.time() + self.LEASE_SECONDS,))
        self._health(con, heartbeat_at=datetime.now(UTC).isoformat(), last_progress_at=datetime.now(UTC).isoformat())

    def _renew(self, stopped):
        # Network reads have bounded timeouts, but a collection can take longer
        # than one lease. Renewal maintains liveness without inventing progress.
        while not stopped.wait(15):
            try:
                with self.store.transaction() as con:
                    if stopped.is_set():
                        return
                    row = con.execute("SELECT * FROM a_runtime_lock WHERE id=1").fetchone()
                    if row["owner"] != self.owner or row["expires"] <= time.time():
                        return
                    con.execute("UPDATE a_runtime_lock SET expires=? WHERE id=1", (time.time() + self.LEASE_SECONDS,))
                    self._health(con, heartbeat_at=datetime.now(UTC).isoformat())
            except Exception:
                # A failed heartbeat is visible as stale; never overwrite truth.
                return

    def _session_slots(self, schedule, calendar):
        if not calendar["is_session"]:
            return []
        opened, closed = utc_clock(calendar["open_at"]), utc_clock(calendar["close_at"])
        phase = schedule["phase"]
        if phase == "intraday":
            interval = schedule["interval_seconds"] or 1800
            slots = []
            timestamp = opened + timedelta(seconds=interval)
            while timestamp < closed:
                slots.append((timestamp, min(timestamp + timedelta(minutes=5), closed)))
                timestamp += timedelta(seconds=interval)
            return slots
        timestamp = {"preopen": opened - timedelta(minutes=5), "open": opened, "close": closed, "postclose": closed + timedelta(minutes=5)}[phase]
        return [(timestamp, timestamp + timedelta(minutes=5 if phase != "postclose" else 30))]

    def _materialize(self, con, clock, calendar):
        epoch = clock.timestamp()
        session_backlogs = []
        today = clock.astimezone(NY).date()
        calendars = {today: calendar}
        for schedule in con.execute("SELECT * FROM a_schedules").fetchall():
            if schedule["cadence"] == "interval":
                if not schedule["enabled"]:
                    continue
                # One unresolved occurrence at a time; failures do not advance due time.
                pending = con.execute("SELECT 1 FROM a_jobs WHERE schedule_id=? AND status IN ('pending','running','retry')", (schedule["id"],)).fetchone()
                if not pending and (schedule["next_due"] or 0) <= epoch:
                    due = schedule["next_due"] or epoch
                    con.execute("INSERT OR IGNORE INTO a_jobs(id,schedule_id,due_at,status,next_attempt_at) VALUES(?,?,?,'pending',?)", (identifier(), schedule["id"], due, due))
            else:
                cursor = con.execute("SELECT through_at FROM a_session_cursors WHERE schedule_id=?", (schedule["id"],)).fetchone()
                # First observation establishes desk availability. It cannot
                # invent windows from before this schedule was observed.
                after = min(cursor[0], epoch) if cursor else epoch
                if not schedule["enabled"]:
                    con.execute("INSERT OR REPLACE INTO a_session_cursors VALUES(?,?)", (schedule["id"], epoch))
                    continue
                day = datetime.fromtimestamp(after, UTC).astimezone(NY).date()
                end = min(today, day + timedelta(days=self.SESSION_CATCHUP_DAYS - 1))
                while day <= end:
                    if day not in calendars:
                        calendars[day] = self.providers.calendar(datetime.combine(day, datetime.min.time(), NY) + timedelta(hours=12))
                    for due, expiry in self._session_slots(schedule, calendars[day]):
                        if after <= due.timestamp() <= epoch or cursor is None and due <= clock < expiry:
                            con.execute("INSERT OR IGNORE INTO a_jobs(id,schedule_id,due_at,expires_at,status,next_attempt_at) VALUES(?,?,?,?,'pending',?)", (identifier(), schedule["id"], due.timestamp(), expiry.timestamp(), due.timestamp()))
                    day += timedelta(days=1)
                through = epoch if end == today else datetime.combine(end + timedelta(days=1), datetime.min.time(), NY).timestamp()
                con.execute("INSERT OR REPLACE INTO a_session_cursors VALUES(?,?)", (schedule["id"], through))
                if end < today:
                    session_backlogs.append({"schedule_id": schedule["id"], "covered_through": datetime.fromtimestamp(through, UTC).isoformat(), "remaining_calendar_days": (today - end).days})
        self._health(con, session_catchup={"maximum_calendar_days_per_pass": self.SESSION_CATCHUP_DAYS, "backlog": session_backlogs, "complete": not session_backlogs, "scope": "Known schedules only; first observation establishes availability, expired windows are recorded without execution"})

    def _symbols(self, extra_observations=None):
        from .trading import TERMINAL
        held, instructions = set(), set()
        with self.store.connect() as con:
            observations = {r[0] for r in con.execute("SELECT symbol FROM watchlist")} | set(extra_observations or [])
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='p_positions'").fetchone():
                held.update(r["symbol"] for r in con.execute("SELECT symbol,quantity FROM p_positions") if Decimal(r["quantity"]) != 0)
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='p_intents'").fetchone():
                for row in con.execute("SELECT symbol,status,parent_id FROM p_intents"):
                    if row["status"] not in TERMINAL:
                        (held if row["parent_id"] else instructions).add(row["symbol"])
        maximum = getattr(self.providers, "MAX_SYMBOLS", 16)
        def take(values, count, cursor):
            values = sorted(values)
            if count <= 0 or not values:
                return []
            if len(values) <= count:
                return values
            start = getattr(self, cursor) % len(values)
            selected = (values + values)[start:start + count]
            setattr(self, cursor, (start + count) % len(values))
            return selected
        selected = take(held, maximum, "_held_cursor")
        selected += take(instructions - held, maximum - len(selected), "_intent_cursor")
        selected += take(observations - held - instructions, maximum - len(selected), "_refresh_cursor")
        critical = held | instructions
        deferred = critical - set(selected)
        coverage = {"maximum_per_pass": maximum, "held_or_protective_symbols": len(held), "active_symbols": len(critical), "observational_symbols": len(observations - critical), "selected_symbols": selected, "deferred_active_symbols": sorted(deferred)[:32], "deferred_active_count": len(deferred), "capacity_limited": bool(deferred), "policy": "Held positions and active protection first, then active instructions; rotate only remaining capacity. Over-capacity tiers rotate with an explicit warning."}
        with self.store.transaction() as con:
            self._health(con, quote_coverage=coverage)
        if deferred:
            self._alert("runtime-quote-capacity", "warning", "Active market-data coverage exceeds per-pass capacity; fresh-quote gates remain enforced", coverage)
        elif self.lab is not None and hasattr(self.lab, "resolve_key"):
            self.lab.resolve_key("runtime-quote-capacity")
        return selected

    def _alert(self, key, severity, message, payload=None):
        if self.lab is not None:
            self.lab.alert(key, severity, message, payload)

    def _check_result(self, result):
        if isinstance(result, dict) and result.get("errors"):
            raise DeskError("An operational read or reconciliation failed; retry remains due")
        return result

    def _execute(self, job, schedule, clock, force=False):
        kind = schedule["kind"]
        payload = json.loads(schedule["payload"])
        result = {}
        def fence(con=None):
            if self.stop_event.is_set():
                exc = _WorkPaused("Supervisor shutdown was requested")
                exc.receipt = result
                raise exc
            if con is None:
                with self.store.transaction() as writer:
                    fence(writer)
                return
            self._fence(con)
            enabled = con.execute("SELECT enabled FROM a_schedules WHERE id=?", (schedule["id"],)).fetchone()
            paused = not self._config(con)["running"] and not force
            if paused or not enabled or not enabled[0]:
                exc = _WorkPaused("Operator paused the runtime or disabled this schedule")
                exc.receipt = result
                raise exc
        provider = _FencedProviders(self.providers, fence)
        if kind == "verify" and hasattr(self.store, "verify_ledger"):
            fence()
            result["journal_integrity"] = self.store.verify_ledger()
        if kind in {"operations", "refresh"}:
            fence()
            symbols = self._symbols(payload.get("symbols")) if kind == "operations" else payload["symbols"] if "symbols" in payload else self._symbols()
            result["refresh"] = self.providers.refresh(symbols)
            if hasattr(self.providers, "capture_quotes"):
                self.providers.capture_quotes()
            if kind == "refresh":
                self._check_result(result["refresh"])
        if kind in {"operations", "reconcile", "verify"}:
            fence()
            result["reconcile"] = self.trading.reconcile(provider, clock)
            if kind != "operations":
                self._check_result(result["reconcile"])
        if kind in {"operations", "strategies"}:
            fence()
            if job["expires_at"] is not None and utc_clock(clock).timestamp() >= job["expires_at"]:
                exc = _WindowExpired("Exchange window expired during operational reads; no execution or replay")
                exc.receipt = result
                raise exc
            # TradingDesk gates each broker book on its own reconciliation truth.
            # One failed account must not strand a healthy independent book.
            integrity = self.store.ledger_status() if hasattr(self.store, "ledger_status") else {"status": "ok"}
            if self.actions is not None and integrity.get("status") == "ok":
                result["corporate_actions"] = self.actions.run_once(clock=clock, fence=fence, max_symbols=16)
            if self.strategies is not None and integrity.get("status") == "ok":
                # Service already-observed exits first, before any unrelated
                # held-name or full-universe historical-data acquisition.
                result["matured_exits"] = self.strategies.service_exits(
                    clock=clock, transaction_guard=fence, providers=provider,
                    acquire_native_clocks=False,
                )
                result["matured_exit_process"] = self.trading.process(provider, clock)
                # A twentieth native bar may have just closed. Acquire only
                # held-name clocks, then cross the same public fill boundary.
                result["held_exits"] = self.strategies.service_exits(
                    clock=clock, transaction_guard=fence, providers=provider,
                )
                result["held_exit_process"] = self.trading.process(provider, clock)
            if kind == "strategies" and self.strategies is not None and integrity.get("status") == "ok":
                # Production decisions use the actual post-acquisition clock.
                # Injected clocks remain deterministic in supervisor tests.
                result["strategies"] = self.strategies.run_once(clock=clock, transaction_guard=fence, providers=provider)
            result["process"] = self.trading.process(provider, clock) if integrity.get("status") == "ok" else {"errors": ["Journal integrity is not verified; financial execution is blocked"]}
        if kind in {"operations", "lab", "verify"} and self.lab is not None:
            fence()
            result["lab"] = self.lab.operate(trading_snapshot=self.trading.snapshot(), runtime_status=self.status(), clock=utc_clock(clock))
        if kind in {"operations", "strategies"}:
            if self.notifications is not None:
                fence()
                result["notifications"] = self.notifications.run_once(clock=clock)
            try:
                for component in ("refresh", "reconcile", "matured_exit_process", "held_exit_process", "process"):
                    self._check_result(result.get(component))
            except DeskError as exc:
                exc.receipt = result
                raise
        if kind == "verify" and result.get("journal_integrity", {}).get("status") == "failed":
            exc = DeskError("Journal verification failed; financial execution is blocked")
            exc.receipt = result
            raise exc
        if kind == "bars":
            result["bars"] = []
            for sym in payload["symbols"] if "symbols" in payload else self._symbols():
                fence()
                result["bars"].append(self.providers.bars(sym, payload.get("range", "1mo"), payload.get("interval", "1d")))
            if any(b.get("stale_cache") for b in result["bars"]):
                raise DeskError("Historical refresh failed; retry remains due")
            if schedule["id"] == "benchmark-history":
                result["benchmarks"] = []
                for history in result["bars"]:
                    bars = history.get("bars", [])
                    adjusted = bool(bars and all(b.get("adjusted_close") is not None for b in bars))
                    field = "adjusted_close" if adjusted else "close"
                    start, end = (float(bars[0][field]), float(bars[-1][field])) if len(bars) >= 2 else (None, None)
                    change = (end / start - 1) * 100 if start and end else None
                    finite = change is not None and math.isfinite(change)
                    result["benchmarks"].append({"symbol": history["symbol"], "label": "S&P 500 ETF proxy (SPY)" if history["symbol"] == "SPY" else "Nasdaq-100 ETF (QQQ)", "return_pct": change if finite else None, "return_status": "available" if finite else "withheld", "return_reason": None if finite else "At least two positive prices and a finite representable return are required", "from_at": bars[0]["timestamp"] if bars else None, "through_at": bars[-1]["timestamp"] if bars else None, "scope": "vendor adjusted close return" if adjusted else history.get("return_scope", "raw close price return; excludes dividend adjustments"), "source": history.get("source"), "provider_asof": history.get("provider_asof"), "revision_id": history.get("revision_id"), "delayed": True})
            result["bars"] = [{k: v for k, v in history.items() if k != "bars"} | {"bar_count": len(history.get("bars", []))} for history in result["bars"]]
        if kind == "desk_brief":
            if not self.reasoning.configured:
                raise DeskError("Model reasoning is not configured; scheduled brief remains due")
            title = "Scheduled operational brief " + job["id"]
            with self.store.connect() as con:
                existing = con.execute("SELECT id FROM tasks WHERE kind='desk_brief' AND title=?", (title,)).fetchone()
            fence()
            task = {"id": existing["id"]} if existing else self.store.enqueue("desk_brief", title, payload.get("instructions"))
            result["task_id"] = task["id"]
            result["delivery"] = "Queued for the independently fenced reasoning worker; model completion is recorded on the task"
        return result

    def run_once(self, clock=None, force=False):
        injected_clock = utc_clock(clock) if clock is not None else None
        clock = utc_clock(injected_clock)
        if not self._mutex.acquire(blocking=False):
            return False
        lock_file = None
        renewal_stop = threading.Event()
        renewal_thread = None
        try:
            lock_file = open(str(self.store.path) + ".autonomy.lock", "a")
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return False
            if not self._claim():
                return False
            if self._recovered:
                self._alert("runtime-worker-recovered", "warning", "Recovered the autonomous supervisor after an expired worker lease")
            renewal_thread = threading.Thread(target=self._renew, args=(renewal_stop,), name="aster-runtime-heartbeat", daemon=True)
            renewal_thread.start()
            with self.store.connect() as con:
                config = self._config(con)
                sqlite_ok = con.execute("PRAGMA quick_check(1)").fetchone()[0] == "ok"
            disk = shutil.disk_usage(self.store.path.parent)
            if not sqlite_ok or disk.free < config["minimum_free_bytes"]:
                with self.store.transaction() as con:
                    self._health(con, sqlite_status="ok" if sqlite_ok else "failed", disk_free_bytes=disk.free, last_error="Storage health gate blocks execution")
                self._alert("runtime-storage", "critical", "Storage health gate blocks autonomous execution")
                return False
            self._fence()
            clock = utc_clock(injected_clock)
            calendar = self.providers.calendar(clock)
            self._calendar = calendar
            with self.store.transaction() as con:
                self._health(con, sqlite_status="ok", disk_free_bytes=disk.free, last_error=None)
                if not config["running"] and not force:
                    return False
                # A crashed job becomes due again; file and database fences exclude its old worker.
                con.execute("UPDATE a_jobs SET status='retry',next_attempt_at=?,owner=NULL,lease_until=NULL,error='Recovered after expired execution lease' WHERE status='running' AND (lease_until IS NULL OR lease_until<=?)", (clock.timestamp(), time.time()))
                self._materialize(con, clock, calendar)
                expired = con.execute("SELECT id FROM a_jobs WHERE status IN ('pending','retry') AND expires_at IS NOT NULL AND expires_at<=?", (clock.timestamp(),)).fetchall()
                if expired:
                    con.execute("UPDATE a_jobs SET status='skipped',completed_at=?,error='Exchange window expired; no replay',owner=NULL,lease_until=NULL WHERE status IN ('pending','retry') AND expires_at IS NOT NULL AND expires_at<=?", (clock.isoformat(), clock.timestamp()))
                    self.store.event(con, "job_windows_missed", "supervisor", "Recorded missed exchange windows without replay", {"count": len(expired), "job_ids": [r["id"] for r in expired[:24]]})
                if force:
                    # An explicit operator cycle also works when interval work is not due.
                    pending = con.execute("SELECT 1 FROM a_jobs WHERE schedule_id='default-operations' AND status IN ('pending','running','retry')").fetchone()
                    if not pending:
                        con.execute("INSERT OR IGNORE INTO a_jobs(id,schedule_id,due_at,status,next_attempt_at) VALUES(?,'default-operations',?,'pending',?)", (identifier(), clock.timestamp(), clock.timestamp()))
                jobs = con.execute("SELECT j.*,s.enabled FROM a_jobs j JOIN a_schedules s ON s.id=j.schedule_id WHERE j.status IN ('pending','retry') AND j.next_attempt_at<=? AND s.enabled=1 ORDER BY j.due_at LIMIT 12", (clock.timestamp(),)).fetchall()
            if expired:
                self._alert("runtime-missed-windows", "warning", "Exchange windows were missed; stale work was not replayed", {"count": len(expired)})
            did_work = False
            successful_alert_keys = []
            for row in jobs:
                self._fence()
                clock = utc_clock(injected_clock)
                job = dict(row)
                with self.store.transaction() as con:
                    schedule = dict(con.execute("SELECT * FROM a_schedules WHERE id=?", (job["schedule_id"],)).fetchone())
                    if self.stop_event.is_set() or not self._config(con)["running"] and not force:
                        break
                    if not schedule["enabled"]:
                        continue
                    if job["expires_at"] is not None and clock.timestamp() >= job["expires_at"]:
                        con.execute("UPDATE a_jobs SET status='skipped',completed_at=?,error='Exchange window expired; no replay' WHERE id=?", (clock.isoformat(), job["id"]))
                        self.store.event(con, "job_window_missed", "supervisor", "Recorded a missed exchange window without replay", {"job_id": job["id"], "phase": schedule["phase"]})
                        continue
                    con.execute("UPDATE a_jobs SET status='running',attempts=attempts+1,owner=?,lease_until=?,started_at=?,error=NULL WHERE id=?", (self.owner, time.time() + self.LEASE_SECONDS, clock.isoformat(), job["id"]))
                    self._health(con, active_job_id=job["id"], active_job_started_at=datetime.now(UTC).isoformat())
                try:
                    # None preserves TradingDesk's production per-intent and
                    # pre-transport clock checks after bounded external reads.
                    result = self._execute(job, schedule, injected_clock, force=force)
                    self._fence()
                    clock = utc_clock(injected_clock)
                    with self.store.transaction() as con:
                        lock = con.execute("SELECT * FROM a_runtime_lock WHERE id=1").fetchone()
                        if lock["owner"] != self.owner or lock["expires"] <= time.time():
                            raise DeskError("Completion lost its execution fence")
                        encoded = json.dumps(result, default=str)
                        if len(encoded) > 100000:
                            encoded = json.dumps({"summary": "Completed bounded operational work; detailed truth remains in component records", "components": list(result), "benchmarks": result.get("benchmarks", [])})
                        con.execute("UPDATE a_jobs SET status='succeeded',completed_at=?,result=?,owner=NULL,lease_until=NULL,error=NULL WHERE id=? AND owner=?", (clock.isoformat(), encoded, job["id"], self.owner))
                        current_schedule = con.execute("SELECT * FROM a_schedules WHERE id=?", (schedule["id"],)).fetchone()
                        next_due = clock.timestamp() + (current_schedule["interval_seconds"] or 60) if current_schedule["cadence"] == "interval" else None
                        con.execute("UPDATE a_schedules SET last_success_at=?,next_due=? WHERE id=?", (clock.isoformat(), next_due, schedule["id"]))
                        self._health(con, last_cycle_at=clock.isoformat(), last_success_at=clock.isoformat(), last_error=None, active_job_id=None, active_job_started_at=None)
                        self.store.event(con, "autonomous_job_completed", "supervisor", "Completed operational work", {"job_id": job["id"], "kind": schedule["kind"], "components": list(result), "task_id": result.get("task_id")})
                    did_work = True
                    successful_alert_keys.append("runtime-job-" + job["id"])
                except Exception as exc:
                    clock = utc_clock(injected_clock)
                    error = "Operational job failed: " + type(exc).__name__
                    with self.store.transaction() as con:
                        # A stale worker cannot overwrite a newer worker's receipt.
                        lock = con.execute("SELECT * FROM a_runtime_lock WHERE id=1").fetchone()
                        if lock["owner"] != self.owner or lock["expires"] <= time.time():
                            raise
                        attempts = con.execute("SELECT attempts FROM a_jobs WHERE id=?", (job["id"],)).fetchone()[0]
                        delay = min(300, 5 * 2 ** min(attempts - 1, 6))
                        receipt = json.dumps(getattr(exc, "receipt", {}), default=str)
                        if len(receipt) > 100000:
                            receipt = json.dumps({"summary": "Partial pass receipts remain in component records"})
                        if isinstance(exc, _WorkPaused):
                            con.execute("UPDATE a_jobs SET status='pending',next_attempt_at=?,owner=NULL,lease_until=NULL,error=NULL,result=? WHERE id=? AND owner=?", (clock.timestamp(), receipt, job["id"], self.owner))
                            self.store.event(con, "autonomous_job_paused", "supervisor", "Preserved due work after an operator pause", {"job_id": job["id"]})
                        elif isinstance(exc, _WindowExpired):
                            con.execute("UPDATE a_jobs SET status='skipped',completed_at=?,owner=NULL,lease_until=NULL,error='Exchange window expired during reads; no replay',result=? WHERE id=? AND owner=?", (clock.isoformat(), receipt, job["id"], self.owner))
                            self.store.event(con, "job_window_missed", "supervisor", "Exchange window expired during reads; execution was skipped", {"job_id": job["id"]})
                        else:
                            con.execute("UPDATE a_jobs SET status='retry',next_attempt_at=?,owner=NULL,lease_until=NULL,error=?,result=? WHERE id=? AND owner=?", (clock.timestamp() + delay, error, receipt, job["id"], self.owner))
                        self._health(con, last_error=None if isinstance(exc, _WorkPaused) else error, active_job_id=None, active_job_started_at=None)
                        if not isinstance(exc, (_WindowExpired, _WorkPaused)):
                            self.store.event(con, "autonomous_job_retry", "supervisor", "Operational work remains due for retry", {"job_id": job["id"], "retry_seconds": delay, "error": error})
                    if not isinstance(exc, _WorkPaused):
                        self._alert("runtime-job-" + job["id"], "warning", error, {"job_id": job["id"], "kind": schedule["kind"]})
            if self.lab is not None and hasattr(self.lab, "resolve_key"):
                self.lab.resolve_key("runtime-storage")
                for key in successful_alert_keys:
                    self.lab.resolve_key(key)
            return did_work
        finally:
            renewal_stop.set()
            if renewal_thread:
                renewal_thread.join(timeout=2)
            if lock_file:
                lock_file.close()
            self._mutex.release()

    @staticmethod
    def _schedule_public(row):
        result = dict(row)
        result["enabled"] = bool(result["enabled"])
        result["payload"] = json.loads(result["payload"])
        next_due = result.pop("next_due")
        result["next_due_at"] = datetime.fromtimestamp(next_due, UTC).isoformat() if next_due else None
        return result

    @staticmethod
    def _job_public(row):
        result = dict(row)
        for field in ("due_at", "expires_at", "next_attempt_at"):
            result[field] = datetime.fromtimestamp(result[field], UTC).isoformat() if result.get(field) is not None else None
        result.pop("owner", None)
        result.pop("lease_until", None)
        result["result"] = json.loads(result["result"]) if result.get("result") else None
        return result

    def status(self):
        with self.store.connect() as con:
            config = self._config(con)
            health = json.loads(con.execute("SELECT data FROM a_runtime_health WHERE id=1").fetchone()[0])
            lock = con.execute("SELECT * FROM a_runtime_lock WHERE id=1").fetchone()
            pending = con.execute("SELECT COUNT(*) FROM a_jobs WHERE status IN ('pending','running','retry')").fetchone()[0]
            retrying = con.execute("SELECT COUNT(*) FROM a_jobs WHERE status='retry'").fetchone()[0]
        heartbeat = health.get("heartbeat_at")
        age = (datetime.now(UTC) - utc_clock(heartbeat)).total_seconds() if heartbeat else None
        progress = health.get("last_progress_at")
        progress_age = (datetime.now(UTC) - utc_clock(progress)).total_seconds() if progress else None
        progress_stale = bool(health.get("active_job_id") and progress_age is not None and progress_age > 300)
        active = bool(lock["owner"] != self.owner or (self.thread and self.thread.is_alive()) or self._mutex.locked())
        alive = bool(active and lock["owner"] and lock["expires"] > time.time() and age is not None and age < self.LEASE_SECONDS)
        running = config["running"]
        integrity = self.store.ledger_status() if hasattr(self.store, "ledger_status") else {"status": "ok"}
        return {**config, **health, "journal_integrity": integrity, "worker_alive": alive, "worker_stale": bool(running and not alive), "progress_stale": progress_stale, "healthy": bool((not running or alive) and not progress_stale and not health.get("quote_coverage", {}).get("capacity_limited") and health.get("session_catchup", {}).get("complete", True) and integrity.get("status") == "ok" and health.get("sqlite_status") == "ok" and not health.get("last_error") and not retrying),
                "heartbeat_age_seconds": age, "pending_jobs": pending, "retrying_jobs": retrying, "failed_jobs": retrying,
                "providers": self.providers.status(), "calendar": self.providers.calendar(),
                "reasoning": self.reasoning.status(), "automation": "deterministic operational workers; optional configured read-only models", "last_error": self.last_error or health.get("last_error")}

    def snapshot(self):
        result = self.status()
        with self.store.connect() as con:
            result["schedules"] = [self._schedule_public(r) for r in con.execute("SELECT * FROM a_schedules ORDER BY created_at,id")]
            result["jobs"] = [self._job_public(r) for r in con.execute("SELECT * FROM a_jobs ORDER BY due_at DESC LIMIT 200")]
            benchmark = con.execute("SELECT result FROM a_jobs WHERE schedule_id='benchmark-history' AND status='succeeded' ORDER BY completed_at DESC LIMIT 1").fetchone()
            result["benchmarks"] = json.loads(benchmark[0]).get("benchmarks", []) if benchmark else []
        return result
