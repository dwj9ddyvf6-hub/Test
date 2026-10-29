"""Causal, persistent execution of four explicitly installed local paper sleeves.

This manager originates only frozen, deterministic rules. It has no broker order
interface, cannot fund books, and does not install anything at construction. Bar
labels, desk observation times, decisions and observed quote fills remain distinct.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from functools import lru_cache
import hashlib
import gzip
import json
import math
from pathlib import Path
import re
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

from .providers import NY, _nyse, utc_clock
from .store import DeskError, cents, symbol
from .trading import ACTIVE

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]
FRAMES = {"H1STATE": "1h", "WSTATE": "1wk", "D20PV": "1d", "D20TENSOR": "1d"}
ALIASES = {"H1_STATE_REPAIR": "H1STATE", "W_STATE_REPAIR": "WSTATE", "D20_PV": "D20PV", "D20_TENSOR": "D20TENSOR"}
INTERVAL = {"1h": "60m", "1d": "1d", "1wk": "1wk"}


class NativeIneligible(DeskError):
    """A known warmup/ineligible symbol, distinct from an unknown data failure."""


def _dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _plain(value):
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return asdict(value) if is_dataclass(value) else dict(value)


def _ms(value):
    return int(utc_clock(value).timestamp() * 1000)


def _dt(value):
    return datetime.fromtimestamp(value / 1000, UTC)


@lru_cache(maxsize=12000)
def _session(day):
    cal = _nyse()
    if not cal.is_session(day):
        return None
    return (_ms(cal.session_open(day).to_pydatetime()), _ms(cal.session_close(day).to_pydatetime()))


def _sessions(start, end):
    return [str(v.date()) for v in _nyse().sessions_in_range(start, end)]


@lru_cache(maxsize=120000)
def _native_period(timestamp_ms, frame):
    """Return exchange opening/completion without modifying the vendor label."""
    stamp = _dt(timestamp_ms)
    local = stamp.astimezone(NY)
    day = local.date().isoformat()
    if frame == "1wk":
        # Preserve the explicit provider UTC-Monday or NY-Monday week. Never
        # turn UTC Monday midnight into the preceding New York Sunday week.
        source_midnight = stamp.weekday() == 0 and stamp.time().replace(tzinfo=None) == datetime.min.time()
        exchange_midnight = local.weekday() == 0 and local.time().replace(tzinfo=None) == datetime.min.time()
        if source_midnight:
            monday = stamp.date()
        elif local.weekday() == 0 and local.time().replace(tzinfo=None) == datetime.min.time():
            monday = local.date()
        else:
            monday = local.date() - timedelta(days=local.weekday())
        days = _sessions(monday.isoformat(), (monday + timedelta(days=6)).isoformat())
        if not days:
            raise DeskError("Weekly exchange period has no sessions", 422)
        if not source_midnight and not exchange_midnight and timestamp_ms != _session(days[0])[0]:
            raise DeskError("Unsupported weekly source label; no nearest-week relabelling", 422)
        return _session(days[0])[0], _session(days[-1])[1]
    if frame == "1d" and stamp.time().replace(tzinfo=None) == datetime.min.time():
        day = stamp.date().isoformat()
    boundaries = _session(day)
    if not boundaries:
        raise DeskError("Bar label is outside an XNYS session", 422)
    opened, closed = boundaries
    if frame == "1d":
        # A daily vendor date is a label, never a midnight executable open.
        utc_midnight = stamp.time().replace(tzinfo=None) == datetime.min.time()
        ny_midnight = local.time().replace(tzinfo=None) == datetime.min.time()
        if not utc_midnight and not ny_midnight and timestamp_ms != opened:
            raise DeskError("Unsupported daily vendor clock; no relabelling", 422)
        return opened, closed
    if not opened <= timestamp_ms < closed or (timestamp_ms - opened) % 3_600_000:
        raise DeskError("Hourly source is not the regular XNYS 09:30 hourly grid", 422)
    return timestamp_ms, min(timestamp_ms + 3_600_000, closed)


def _next_open(frame, completion_ms):
    cal = _nyse()
    day = _dt(completion_ms).astimezone(NY).date().isoformat()
    opened, closed = _session(day)
    if frame == "1h" and completion_ms < closed:
        return completion_ms
    following = cal.next_session(day)
    if frame == "1wk":
        week = _dt(completion_ms).astimezone(NY).date()
        next_monday = week + timedelta(days=7 - week.weekday())
        following = cal.date_to_session(next_monday.isoformat(), direction="next")
    return _ms(cal.session_open(following).to_pydatetime())


def latest_native_clock(frame, as_of):
    """Latest actually completed exchange period; no price observations implied."""
    clock = utc_clock(as_of)
    now_ms = _ms(clock)
    local_day = clock.astimezone(NY).date()
    days = _sessions((local_day - timedelta(days=18)).isoformat(), local_day.isoformat())
    periods = []
    if frame == "1wk":
        mondays = sorted({datetime.fromisoformat(day).date() - timedelta(days=datetime.fromisoformat(day).weekday()) for day in days})
        for monday in mondays:
            label = datetime.combine(monday, datetime.min.time(), NY)
            opening, closing = _native_period(_ms(label), frame)
            if closing <= now_ms:
                periods.append((_ms(label), opening, closing))
    else:
        for day in days:
            opened, closed = _session(day)
            if frame == "1d":
                label = _ms(datetime.combine(datetime.fromisoformat(day).date(), datetime.min.time(), NY))
                if closed <= now_ms:
                    periods.append((label, opened, closed))
            else:
                start = opened
                while start < closed:
                    end = min(start + 3_600_000, closed)
                    if end <= now_ms:
                        periods.append((start, start, end))
                    start += 3_600_000
    if not periods:
        raise DeskError("No completed native exchange period is available")
    label, opened, completed = periods[-1]
    return {"timestamp_ms": label, "executable_at_ms": opened, "completed_at_ms": completed,
            "next_open_ms": _next_open(frame, completed)}


def canonical_native_bars(payload, frame, as_of, *, expected_symbol=None, diagnostics=None):
    """Validate one immutable provider observation and exclude unfinished bars.

    Observation time is a desk knowledge clock, not historical publication time.
    Full-response provenance is required; an unsupported fallback never changes
    prices or timestamp semantics to impersonate the research source.
    """
    from .tensor_engine import NativeBar
    clock_ms = _ms(as_of)
    if not isinstance(payload, dict) or not payload.get("revision_id") or not payload.get("content_sha256"):
        raise DeskError("An immutable, timestamped provider revision is required")
    if payload.get("revision_id") != payload.get("content_sha256") or not re.fullmatch(r"[a-f0-9]{64}", payload["revision_id"]):
        raise DeskError("Provider revision identity is inconsistent")
    if expected_symbol is not None and payload.get("symbol") != expected_symbol:
        raise DeskError("Provider revision symbol does not match enrollment")
    if payload.get("interval") != INTERVAL[frame]:
        raise DeskError("Provider revision interval does not match native frame")
    if not payload.get("observed_at") or not payload.get("fetched_at"):
        raise DeskError("Provider revision has no explicit knowledge-time receipt")
    observed_ms, fetched_ms = _ms(payload["observed_at"]), _ms(payload["fetched_at"])
    if observed_ms > clock_ms or fetched_ms > clock_ms:
        raise DeskError("Provider revision was observed after the decision clock")
    if observed_ms > fetched_ms:
        raise DeskError("Provider first observation follows its actual fetch receipt")
    if payload.get("provider_asof") and _ms(payload["provider_asof"]) > clock_ms:
        raise DeskError("Provider revision contains a future source clock")
    if payload.get("truncated") or payload.get("stale_cache"):
        raise DeskError("Incomplete or stale provider coverage cannot authorize an entry")
    completeness = payload.get("completeness", {})
    omitted_count = payload.get("omitted_rows", 0)
    omissions = payload.get("omitted_bar_rows", [])
    if type(omitted_count) is not int or omitted_count < 0 or not isinstance(omissions, list) or len(omissions) != omitted_count:
        raise DeskError("Omitted provider rows have no exact source evidence")
    if omitted_count:
        if payload.get("provider") != "yahoo" or completeness.get("status") != "bounded_partial":
            raise DeskError("Provider omissions cannot be proved unfinished")
        if type(payload.get("source_row_count")) is not int or payload["source_row_count"] != len(payload.get("bars", [])) + omitted_count:
            raise DeskError("Omitted provider row count differs from the exact source response")
        indices, omitted_stamps = [], []
        for omitted in omissions:
            if not isinstance(omitted, dict) or type(omitted.get("row_index")) is not int or not 0 <= omitted["row_index"] < len(payload.get("bars", [])) + omitted_count or not omitted.get("timestamp") or not all(k in omitted for k in ("open", "high", "low", "close", "volume")):
                raise DeskError("Omitted provider row identity is incomplete")
            stamp = _ms(omitted["timestamp"])
            try:
                o, h, low, c, volume = [float(omitted[k]) for k in ("open", "high", "low", "close", "volume")]
                invalid = not all(math.isfinite(v) for v in (o, h, low, c, volume)) or min(o, h, low, c) <= 0 or volume < 0 or low > min(o, c) or h < max(o, c)
            except (ValueError, TypeError, OverflowError):
                invalid = True
            if not invalid:
                raise DeskError("Omitted-row evidence does not show invalid or missing native OHLCV")
            if stamp > fetched_ms or stamp > clock_ms:
                raise DeskError("An omitted native period has a future source clock")
            reason, complete = "quarantined_proved_unfinished_vendor_omission", None
            try:
                _, complete = _native_period(stamp, frame)
            except DeskError:
                marker = payload.get("vendor_regular_market_timestamp")
                if frame != "1wk" or omitted["row_index"] != payload["source_row_count"] - 1 or not marker or stamp != _ms(marker):
                    raise
                reason = "quarantined_yahoo_weekly_regular_market_supplement_omission"
            if complete is not None and (complete <= fetched_ms or complete <= clock_ms):
                raise DeskError("An omitted native period is already completed")
            indices.append(omitted["row_index"])
            omitted_stamps.append(stamp)
            if diagnostics is not None:
                diagnostics.append({"reason": reason, "row_index": omitted["row_index"], "timestamp_ms": stamp,
                    "completed_at_ms": complete, "actual_fetched_at_ms": fetched_ms, "native_bar_admitted": False,
                    "raw_row_preserved_in_provider_revision": True})
        if indices != sorted(set(indices)) or omitted_stamps != sorted(set(omitted_stamps)):
            raise DeskError("Omitted provider row identities are duplicated or unordered")
        if any(_ms(v["timestamp"]) in set(omitted_stamps) for v in payload.get("bars", [])):
            raise DeskError("A provider period is both admitted and omitted")
    elif completeness.get("status") not in {None, "complete_vendor_response"}:
        raise DeskError("Provider response coverage is incomplete")
    adjustment = payload.get("adjustment", "")
    if payload.get("provider") not in {"yahoo", "alpaca", "fixture"} or not adjustment or "unspecified" in adjustment.lower():
        raise DeskError("Provider adjustment policy is unavailable or ambiguous")
    if payload.get("vendor_interval") not in {INTERVAL[frame], "1h" if frame == "1h" else INTERVAL[frame]}:
        raise DeskError("Vendor silently changed the requested native interval")
    rows, seen, previous = [], set(), -1
    source_rows = payload.get("bars", [])
    for row_index, value in enumerate(source_rows):
        stamp = _ms(value["timestamp"])
        if stamp in seen or stamp <= previous or stamp > clock_ms:
            raise DeskError("Native source timestamps are duplicated, unordered or future")
        seen.add(stamp)
        previous = stamp
        period_error = None
        try:
            opened, completed = _native_period(stamp, frame)
        except DeskError as exc:
            period_error = exc
        if period_error is None and (completed > clock_ms or completed > fetched_ms):
            if diagnostics is not None:
                diagnostics.append({"timestamp_ms": stamp, "reason": "quarantined_unfinished_native_period", "completed_at_ms": completed,
                    "actual_fetched_at_ms": fetched_ms, "native_bar_admitted": False, "raw_row_preserved_in_provider_revision": True})
            continue
        try:
            fields = [float(value[k]) for k in ("open", "high", "low", "close", "volume")]
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            raise DeskError("Native source OHLCV is invalid") from exc
        o, h, low, c, volume = fields
        if not all(math.isfinite(v) for v in fields) or min(o, h, low, c) <= 0 or volume < 0 or low > min(o, c) or h < max(o, c):
            raise DeskError("Native source OHLCV is invalid")
        if period_error is not None:
            bounds = _session(_dt(stamp).astimezone(NY).date().isoformat())
            # Yahoo weekly charts can append the current day's OHLCV aggregate
            # at their explicitly reported regular-market timestamp. This is
            # a supplemental vendor row, not a weekly period. Exact metadata
            # identity and final-row position are required; no nearest-week
            # mapping or price-shape inference is permitted.
            supplemental = payload.get("vendor_regular_market_timestamp")
            point_quote = volume == 0 and o == h == low == c
            exact_yahoo_tail = payload.get("provider") == "yahoo" and row_index == len(source_rows) - 1 and supplemental and stamp == _ms(supplemental) and stamp <= fetched_ms
            if frame == "1h" and exact_yahoo_tail and point_quote:
                if diagnostics is not None:
                    diagnostics.append({"timestamp_ms": stamp, "reason": "quarantined_yahoo_hourly_regular_market_point_quote", "vendor_regular_market_timestamp": supplemental,
                        "native_bar_admitted": False, "raw_row_preserved_in_provider_revision": True})
                continue
            if frame == "1wk" and exact_yahoo_tail:
                if diagnostics is not None:
                    diagnostics.append({"timestamp_ms": stamp, "reason": "quarantined_yahoo_weekly_regular_market_supplement", "vendor_regular_market_timestamp": supplemental,
                        "native_bar_admitted": False, "raw_row_preserved_in_provider_revision": True})
                continue
            # Legacy injected fixtures retain their exact close-point shape;
            # live Yahoo quarantine always requires its explicit tail marker.
            if payload.get("provider") == "fixture" and frame in {"1h", "1wk"} and point_quote and bounds and 0 <= stamp - bounds[1] <= 1000:
                if diagnostics is not None:
                    diagnostics.append({"timestamp_ms": stamp, "reason": "quarantined_vendor_session_close_quote_stub", "native_bar_admitted": False})
                continue
            raise period_error
        # A cached partial candle cannot become a final observation merely
        # because the decision clock advances. Require an actual post-close
        # read, even if its unchanged content reuses an older revision ID.
        rows.append(NativeBar(timestamp_ms=stamp, completed_at_ms=completed,
                    usable_at_ms=max(completed, observed_ms, fetched_ms), executable_at_ms=opened,
                    open=o, high=h, low=low, close=c, volume=volume))
    if not rows:
        raise DeskError("No completed native source bars are available")
    return tuple(rows)


def historical_state_cooldown(rows, before_index):
    """Reconstruct the frozen greedy opportunity clock, never old orders.

    This examines only already observed native measurements. Missed deployment
    periods still consume their original 20-bar opportunity cooldown, exactly
    as R11 dedup(mask, 20), irrespective of cash or fills.
    """
    after, latest, count = -1, None, 0
    channels = ("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave")
    for i in range(233, min(before_index, len(rows))):
        if i < after:
            continue
        current, previous = rows[i], rows[i - 3]
        try:
            if int(current["bar_index"]) != i or float(current["close"]) < 5 or float(current["dollar_volume20"]) < 1_000_000 or float(current["atr14"]) <= 0:
                continue
            if not all(math.isfinite(float(current[k])) for k in ("close", "dollar_volume20", "atr14")):
                continue
            if int(current["total_votes"]) != 7 or int(previous["total_votes"]) != 7:
                continue
            balance = float(current["bullish_votes"]) - float(current["bearish_votes"])
            old_balance = float(previous["bullish_votes"]) - float(previous["bearish_votes"])
            if balance - old_balance < 2:
                continue
            turns = 0
            for channel in channels:
                for j in range(i - 2, i + 1):
                    a, b = rows[j - 1].get("vote_" + channel), rows[j].get("vote_" + channel)
                    if a is not None and b is not None and float(b) > float(a):
                        turns += 1
                        break
            if turns >= 2:
                latest, after, count = i, i + 20, count + 1
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    return {"next_eligible_bar_index": after, "last_consumed_origin_index": latest,
            "historical_opportunities": count, "last_scanned_index": before_index - 1,
            "orders_created": 0}


class TensorRuntime:
    """Explicit installation, bounded acquisition, atomic decisions and exits."""

    def __init__(self, store, trading, providers, *, feature_extractor=None, daily_evaluator=None, policy_factory=None):
        self.store, self.trading, self.providers = store, trading, providers
        self.feature_extractor, self.daily_evaluator, self.policy_factory = feature_extractor, daily_evaluator, policy_factory
        self._mutex = threading.Lock()
        self._seed_manifests = {}
        self._eligibility_manifests = {}
        self.actions = None
        with store.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS a_tensor_installations(id TEXT PRIMARY KEY,sleeve TEXT NOT NULL,book_id TEXT NOT NULL UNIQUE,
                  enabled INTEGER NOT NULL,config TEXT NOT NULL,config_sha256 TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_tensor_cycles(frame TEXT PRIMARY KEY,origin_ms INTEGER NOT NULL,next_open_ms INTEGER NOT NULL,
                  expires_ms INTEGER NOT NULL,cursor INTEGER NOT NULL,universe TEXT NOT NULL,status TEXT NOT NULL,updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_tensor_coverage(frame TEXT NOT NULL,symbol TEXT NOT NULL,revision_id TEXT NOT NULL,
                  observed_at TEXT NOT NULL,bars BLOB NOT NULL,status TEXT NOT NULL,error TEXT,updated_at TEXT NOT NULL,PRIMARY KEY(frame,symbol));
                CREATE TABLE IF NOT EXISTS a_tensor_coverage_tails(frame TEXT NOT NULL,symbol TEXT NOT NULL,revision_id TEXT NOT NULL,
                  blob_sha256 TEXT NOT NULL,bar_count INTEGER NOT NULL,last_timestamp_ms INTEGER NOT NULL,last_completed_ms INTEGER NOT NULL,
                  last_usable_ms INTEGER NOT NULL,metadata_sha256 TEXT NOT NULL,PRIMARY KEY(frame,symbol));
                CREATE TABLE IF NOT EXISTS a_tensor_cycle_reads(frame TEXT NOT NULL,origin_ms INTEGER NOT NULL,symbol TEXT NOT NULL,
                  status TEXT NOT NULL,error TEXT,PRIMARY KEY(frame,origin_ms,symbol));
                CREATE TABLE IF NOT EXISTS a_tensor_candidates(installation_id TEXT NOT NULL,origin_ms INTEGER NOT NULL,symbol TEXT NOT NULL,
                  data TEXT NOT NULL,PRIMARY KEY(installation_id,origin_ms,symbol));
                CREATE TABLE IF NOT EXISTS a_tensor_decisions(id TEXT PRIMARY KEY,installation_id TEXT NOT NULL,symbol TEXT NOT NULL,
                  origin_ms INTEGER NOT NULL,role TEXT NOT NULL,status TEXT NOT NULL,reason TEXT NOT NULL,data TEXT NOT NULL,intent_id TEXT,
                  created_at TEXT NOT NULL,UNIQUE(installation_id,symbol,origin_ms,role));
                CREATE TABLE IF NOT EXISTS a_tensor_cooldowns(installation_id TEXT NOT NULL,symbol TEXT NOT NULL,next_index INTEGER NOT NULL,
                  origin_ms INTEGER NOT NULL,PRIMARY KEY(installation_id,symbol));
                CREATE TABLE IF NOT EXISTS a_tensor_position_state(installation_id TEXT NOT NULL,symbol TEXT NOT NULL,entry_fill_id TEXT NOT NULL,
                  fill_at TEXT NOT NULL,entry_open_ms INTEGER NOT NULL,status TEXT NOT NULL,PRIMARY KEY(installation_id,symbol));
                CREATE TABLE IF NOT EXISTS a_tensor_cursors(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_tensor_revision_receipts(frame TEXT NOT NULL,symbol TEXT NOT NULL,revision_id TEXT NOT NULL,
                  observed_at TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(frame,symbol,revision_id));
                CREATE TABLE IF NOT EXISTS a_tensor_censuses(id TEXT PRIMARY KEY,installation_id TEXT NOT NULL,origin_ms INTEGER NOT NULL,
                  content_sha256 TEXT NOT NULL,data TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_tensor_observed_periods(frame TEXT NOT NULL,symbol TEXT NOT NULL,opening_ms INTEGER NOT NULL,
                  completed_ms INTEGER NOT NULL,observed_at TEXT NOT NULL,revision_id TEXT NOT NULL,PRIMARY KEY(frame,symbol,opening_ms));
                CREATE TABLE IF NOT EXISTS a_tensor_prefix_bindings(frame TEXT NOT NULL,symbol TEXT NOT NULL,seed_sha256 TEXT NOT NULL,
                  original_rows INTEGER NOT NULL,first_timestamp_ms INTEGER NOT NULL,last_timestamp_ms INTEGER NOT NULL,last_opening_ms INTEGER NOT NULL,
                  verified_at TEXT NOT NULL,PRIMARY KEY(frame,symbol));
            """)
        # Initialize legacy coverage once before resident acquisition begins.
        # This cache chooses only the vendor query range; it grants no signal,
        # completed-period observation, execution clock or entry permission.
        self.prime_coverage_tails()

    @staticmethod
    def _guard(con, guard):
        if guard is not None:
            try:
                guard(con)
            except Exception as exc:
                setattr(exc, "tensor_fence_failure", True)
                raise

    def bind_actions(self, actions):
        self.actions = actions

    def install(self, config):
        if not isinstance(config, dict):
            raise DeskError("Strategy installation must be an object", 422)
        config = dict(config)
        sleeve = config.get("sleeve", config.get("strategy_id"))
        sleeve = ALIASES.get(sleeve, sleeve)
        if sleeve not in FRAMES:
            raise DeskError("Select one of H1STATE, WSTATE, D20PV or D20TENSOR", 422)
        rid = config.get("id", config.get("installation_id", "tensor-" + sleeve.lower()))
        if not isinstance(rid, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", rid):
            raise DeskError("Invalid installation identity", 422)
        symbols = config.get("symbols", config.get("universe"))
        if config.get("universe_file"):
            path = (ROOT / config["universe_file"]).resolve()
            if ROOT not in path.parents or not path.is_file():
                raise DeskError("Enrollment manifest must be a shipped repository file", 422)
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if config.get("universe_sha256") and config["universe_sha256"] != digest:
                raise DeskError("Enrollment manifest does not match its frozen identity")
            manifest = json.loads(raw)
            symbols = manifest if isinstance(manifest, list) else manifest.get("symbols", manifest.get("universe"))
            config["universe_sha256"] = digest
        if not isinstance(symbols, list) or not 1 <= len(symbols) <= 3000:
            raise DeskError("A fixed enrollment of 1 to 3000 symbols is required", 422)
        original_enrollment_count = len(symbols)
        symbols = sorted({symbol(v) for v in symbols})
        if len(symbols) != original_enrollment_count:
            raise DeskError("Enrollment contains duplicate symbols", 422)
        if {"SPY", "QQQ", "B", "GOLD"} & set(symbols):
            raise DeskError("Benchmarks and quarantined symbols cannot be enrolled", 422)
        enabled = config.get("enabled", False)
        budget = config.get("max_fetch_per_run", 256)
        window = config.get("opening_window_seconds", 300)
        if type(enabled) is not bool or type(budget) is not int or not 1 <= budget <= 256 or type(window) is not int or not 1 <= window <= 300:
            raise DeskError("Invalid enabled flag, bounded acquisition budget or opening window", 422)
        normalized = {**config, "id": rid, "sleeve": sleeve, "frame": FRAMES[sleeve], "symbols": symbols,
                      "enabled": enabled, "max_fetch_per_run": budget, "opening_window_seconds": window,
                      "history_range": config.get("history_range", "2y" if sleeve == "H1STATE" else "max"),
                      "hold_native_bars": 20, "maximum_slots": 10, "entry_cap_equity": .10, "entry_cap_native_dv": .01}
        normalized["forward_revision_policy"] = config.get("forward_revision_policy", "retain_frozen_prefix_audit_minor")
        if normalized["forward_revision_policy"] not in {"reject_any_revision", "retain_frozen_prefix_audit_minor"}:
            raise DeskError("Unknown forward data revision policy", 422)
        normalized["missing_data_policy"] = config.get("missing_data_policy", "require_complete_enrollment")
        if normalized["missing_data_policy"] not in {"require_complete_enrollment", "exclude_unavailable_with_census_receipts"}:
            raise DeskError("Unknown point-in-time missing-data admission policy", 422)
        if normalized.get("expected_bar_provider") not in {None, "yahoo", "alpaca", "fixture"}:
            raise DeskError("Unknown required native bar provider", 422)
        if normalized["history_range"] not in {"2y", "5y", "max"}:
            raise DeskError("Full native history requires 2y, 5y or max range", 422)
        digest = hashlib.sha256(_dump(normalized).encode()).hexdigest()
        with self.store.transaction() as con:
            existing = con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (rid,)).fetchone()
            if existing:
                if existing["config_sha256"] != digest:
                    raise DeskError("An installation identity already binds a different frozen configuration")
                return self._installation(con, existing)
            self.trading.claim_strategy_book(normalized.get("book_id"), rid, con=con)
            stamp = datetime.now(UTC).isoformat()
            con.execute("INSERT INTO a_tensor_installations VALUES(?,?,?,?,?,?,?,?)",
                (rid, sleeve, normalized["book_id"], int(enabled), _dump(normalized), digest, stamp, stamp))
            self.store.event(con, "tensor_strategy_installed", "operator", "Installed a frozen local paper strategy sleeve",
                             {"installation_id": rid, "sleeve": sleeve, "book_id": normalized["book_id"], "config_sha256": digest, "enrollment_count": len(symbols)})
            return self._installation(con, con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (rid,)).fetchone())

    def set_enabled(self, installation_id, enabled):
        if type(enabled) is not bool:
            raise DeskError("enabled must be a boolean", 422)
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (installation_id,)).fetchone()
            if not row:
                raise DeskError("Tensor installation not found", 404)
            con.execute("UPDATE a_tensor_installations SET enabled=?,updated_at=? WHERE id=?", (int(enabled), datetime.now(UTC).isoformat(), installation_id))
            self.store.event(con, "tensor_strategy_enabled", "operator", "Changed strategy entry enablement; owned exits continue",
                             {"installation_id": installation_id, "enabled": enabled})
            return self._installation(con, con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (installation_id,)).fetchone())

    def _installation(self, con, row):
        config = json.loads(row["config"])
        covered = con.execute("SELECT COUNT(*) FROM a_tensor_coverage WHERE frame=? AND status='ready' AND symbol IN (%s)" % ",".join("?" for _ in config["symbols"]), [config["frame"], *config["symbols"]]).fetchone()[0]
        cycle = con.execute("SELECT * FROM a_tensor_cycles WHERE frame=?", (config["frame"],)).fetchone()
        failures = [dict(r) for r in con.execute("SELECT symbol,error FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND status='failed' ORDER BY symbol LIMIT 20", (config["frame"], cycle["origin_ms"]))] if cycle else []
        failed_count = con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND status='failed'", (config["frame"], cycle["origin_ms"])).fetchone()[0] if cycle else 0
        warming = con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND status='ineligible'", (config["frame"], cycle["origin_ms"])).fetchone()[0] if cycle else 0
        census = con.execute("SELECT data FROM a_tensor_censuses WHERE installation_id=? ORDER BY rowid DESC LIMIT 1", (row["id"],)).fetchone()
        held = [dict(r) for r in con.execute("SELECT * FROM a_tensor_position_state WHERE installation_id=? AND status='held'", (row["id"],))]
        pending = con.execute("SELECT COUNT(*) FROM p_intents WHERE book_id=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (row["book_id"],)).fetchone()[0]
        return {**dict(row), "enabled": bool(row["enabled"]), "config": config,
                "readiness": {"enrollment_count": len(config["symbols"]), "native_coverage": covered,
                    "status": "ready" if cycle and cycle["status"] == "complete" else "degraded" if cycle and cycle["status"] == "degraded" else "awaiting_complete_native_cycle",
                    "failed_reads": failed_count, "errors": failures, "known_ineligible": warming,
                    "provider": getattr(self.providers, "kind", "unconfigured"),
                    "entry_eligibility": json.loads(census[0]) if census else None,
                    "cycle": dict(cycle) if cycle else None}, "owned_positions": held, "pending_intents": pending,
                "execution": "dedicated local quote paper fills; no broker order submission"}

    def snapshot(self):
        with self.store.connect() as con:
            con.execute("BEGIN")
            installations = [self._installation(con, r) for r in con.execute("SELECT * FROM a_tensor_installations ORDER BY id")]
            decisions = [{**dict(r), "data": json.loads(r["data"])} for r in con.execute("SELECT * FROM a_tensor_decisions ORDER BY created_at DESC,id LIMIT 200")]
            return {"enabled": any(r["enabled"] for r in installations), "strategy_count": len(installations),
                    "installations": installations, "decisions": decisions, "registry": installations,
                    "status": "installed" if installations else "empty",
                    "definitions": [{"id": name, "sleeve": name, "frame": frame, "hold_native_bars": 20,
                        "maximum_slots": 10, "execution": "local paper", "requires_explicit_installation": True} for name, frame in FRAMES.items()],
                    "scope": "Four frozen sleeves in independent local paper books; no combined backtest alpha claim",
                    "entry_timing": "Latest completed native bar, bounded next opening, observed quote fill",
                    "exit_timing": "20 observed native bars from actual filled entry; exits survive disabled entries"}

    @staticmethod
    def _pack(bars):
        # NativeBar is immutable and contains only scalar values. Avoid
        # copying/sorting every field and spending the opening on compression.
        # Field values and decoder semantics remain exactly the same; the
        # persisted tail hash binds the resulting physical BLOB identity.
        raw = json.dumps([vars(v) for v in bars], separators=(",", ":"), allow_nan=False).encode()
        return zlib.compress(raw, 1)

    @staticmethod
    def _unpack(value):
        from .tensor_engine import NativeBar
        return tuple(NativeBar(**v) for v in json.loads(zlib.decompress(value)))

    @staticmethod
    def _tail_identity(frame, sym, revision, blob, bars):
        if not bars:
            raise DeskError("Native coverage has no tail")
        tail = bars[-1]
        _, completed = _native_period(tail.timestamp_ms, frame)
        if completed != tail.completed_at_ms or tail.usable_at_ms < completed:
            raise DeskError("Native coverage tail clock is inconsistent")
        return {"frame": frame, "symbol": sym, "revision_id": revision,
                "blob_sha256": hashlib.sha256(blob).hexdigest(), "bar_count": len(bars),
                "last_timestamp_ms": tail.timestamp_ms, "last_completed_ms": completed,
                "last_usable_ms": tail.usable_at_ms}

    @staticmethod
    def _valid_tail(frame, sym, revision, blob, tail):
        if tail is None or not isinstance(blob, (bytes, bytearray, memoryview)):
            return False
        try:
            data = {k: tail[k] for k in ("frame", "symbol", "revision_id", "blob_sha256", "bar_count", "last_timestamp_ms", "last_completed_ms", "last_usable_ms")}
            if data["frame"] != frame or data["symbol"] != sym or data["revision_id"] != revision or data["blob_sha256"] != hashlib.sha256(blob).hexdigest():
                return False
            if any(type(data[k]) is not int for k in ("bar_count", "last_timestamp_ms", "last_completed_ms", "last_usable_ms")):
                return False
            if tail["metadata_sha256"] != hashlib.sha256(_dump(data).encode()).hexdigest():
                return False
            return data["bar_count"] > 0 and _native_period(data["last_timestamp_ms"], frame)[1] == data["last_completed_ms"] and data["last_usable_ms"] >= data["last_completed_ms"]
        except (DeskError, KeyError, TypeError, ValueError, OverflowError):
            return False

    def _write_tail(self, con, frame, sym, revision, blob, bars=None):
        if not isinstance(blob, (bytes, bytearray, memoryview)):
            raise DeskError("Native coverage BLOB has an invalid SQLite storage type")
        data = self._tail_identity(frame, sym, revision, blob, bars if bars is not None else self._unpack(blob))
        con.execute("INSERT OR REPLACE INTO a_tensor_coverage_tails VALUES(?,?,?,?,?,?,?,?,?)",
                    (*data.values(), hashlib.sha256(_dump(data).encode()).hexdigest()))
        return data["last_completed_ms"]

    def _write_coverage(self, con, frame, sym, response, bars, clock):
        blob = self._pack(bars)
        con.execute("INSERT OR REPLACE INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)",
                    (frame, sym, response["revision_id"], response["observed_at"], blob,
                     "ready" if len(bars) >= 234 else "warming", None, clock.isoformat()))
        self._write_tail(con, frame, sym, response["revision_id"], blob, bars)

    def prime_coverage_tails(self, transaction_guard=None):
        """Bind legacy scalar query hints to exact persisted coverage, without scoring."""
        initialized, failures = 0, []
        with self.store.transaction() as con:
            self._guard(con, transaction_guard)
            for row in con.execute("SELECT frame,symbol,revision_id,bars FROM a_tensor_coverage"):
                tail = con.execute("SELECT * FROM a_tensor_coverage_tails WHERE frame=? AND symbol=?", (row["frame"], row["symbol"])).fetchone()
                if not self._valid_tail(row["frame"], row["symbol"], row["revision_id"], row["bars"], tail):
                    try:
                        self._write_tail(con, row["frame"], row["symbol"], row["revision_id"], row["bars"])
                        initialized += 1
                    except Exception as exc:
                        # Preserve the original research evidence and isolate a
                        # damaged cache name; healthy books and risk service
                        # must still start. Normal acquisition withholds it.
                        con.execute("DELETE FROM a_tensor_coverage_tails WHERE frame=? AND symbol=?", (row["frame"], row["symbol"]))
                        failure = {"frame": row["frame"], "symbol": row["symbol"], "revision_id": row["revision_id"],
                                   "blob_sha256": hashlib.sha256(row["bars"]).hexdigest() if isinstance(row["bars"], (bytes, bytearray, memoryview)) else None,
                                   "storage_type": type(row["bars"]).__name__, "error": str(exc)}
                        if failure["blob_sha256"] is None:
                            failure["stored_value_sha256"] = hashlib.sha256(_dump({"storage_type": failure["storage_type"], "value_repr": repr(row["bars"])}).encode()).hexdigest()
                        failures.append(failure)
                        self.store.event(con, "tensor_coverage_tail_initialization_failed", "data_steward", "Preserved malformed legacy coverage and withheld its query hint", failure)
        return {"initialized": initialized, "failed": len(failures), "errors": failures[:100],
                "scope": "exact coverage-bound query range hints; no decisions or orders"}

    def _coverage_tail(self, frame, sym, guard):
        with self.store.connect() as con:
            con.execute("BEGIN")
            coverage = con.execute("SELECT revision_id,bars FROM a_tensor_coverage WHERE frame=? AND symbol=?", (frame, sym)).fetchone()
            tail = con.execute("SELECT * FROM a_tensor_coverage_tails WHERE frame=? AND symbol=?", (frame, sym)).fetchone()
            if coverage is None:
                return None
            if self._valid_tail(frame, sym, coverage["revision_id"], coverage["bars"], tail):
                return tail["last_completed_ms"]
        # A stale or externally replaced BLOB is never trusted. Re-read its
        # identity under the writer transaction before deriving a new hint.
        with self.store.transaction() as con:
            self._guard(con, guard)
            coverage = con.execute("SELECT revision_id,bars FROM a_tensor_coverage WHERE frame=? AND symbol=?", (frame, sym)).fetchone()
            if coverage is None:
                return None
            tail = con.execute("SELECT * FROM a_tensor_coverage_tails WHERE frame=? AND symbol=?", (frame, sym)).fetchone()
            if self._valid_tail(frame, sym, coverage["revision_id"], coverage["bars"], tail):
                return tail["last_completed_ms"]
            return self._write_tail(con, frame, sym, coverage["revision_id"], coverage["bars"])

    def _extract(self, sym, frame, bars, clock):
        if self.feature_extractor:
            return self.feature_extractor(sym, frame, bars, _ms(clock))
        from .tensor_engine import extract_native_feature_rows, extract_state_feature_rows
        extractor = extract_native_feature_rows if frame == "1d" else extract_state_feature_rows
        return extractor(sym, frame, bars, as_of_ms=_ms(clock))

    def _policy(self, frame, manifest):
        if self.policy_factory:
            return self.policy_factory(frame, manifest)
        from .tensor_strategy import StateRepairPolicy
        return StateRepairPolicy(frame, source_manifest_sha256=manifest)

    def _daily(self, sym, rows, clock):
        if self.daily_evaluator:
            return self.daily_evaluator(sym, rows, _ms(clock))
        from .tensor_daily_models import evaluate_daily20
        return evaluate_daily20(sym, rows, as_of_ms=_ms(clock))

    def _state_cooldown_proof(self, con, frame, sym, bars, installs, origin, clock, manifest, prior_bound, diagnostics):
        """Prove a new opportunity impossible without recomputing its features."""
        if frame not in {"1h", "1wk"} or self.feature_extractor is not None or self.policy_factory is not None or not prior_bound or not manifest:
            return None
        if any(d.get("reason") == "restored_exact_pinned_native_prefix" for d in diagnostics):
            return None
        current, cooldowns = len(bars) - 1, {}
        for install in installs:
            config = install["settings"]
            if not config.get("seed_directory") or not config.get("seed_manifest_file") or config.get("engine_source_manifest_sha256") != manifest:
                return None
            row = con.execute("SELECT next_index,origin_ms FROM a_tensor_cooldowns WHERE installation_id=? AND symbol=?", (install["id"], sym)).fetchone()
            if row is None or type(row["next_index"]) is not int or type(row["origin_ms"]) is not int or not current < row["next_index"] <= current + 20 or not 0 < row["origin_ms"] <= origin:
                return None
            cooldowns[install["id"]] = dict(row)
        from .tensor_engine import _normalize_bars
        _normalize_bars(bars, _ms(clock))  # Same complete-history causal/input gate as the actual engine.
        return {"reason": "persisted_state_cooldown_proves_no_new_opportunity", "current_bar_index": current,
                "source_bar_count": len(bars), "source_origin_timestamp_ms": bars[0].timestamp_ms,
                "source_manifest_sha256": manifest, "validated_at_ms": _ms(clock), "cooldowns": cooldowns,
                "full_native_input_validated": True, "native_features_recomputed": False,
                "existing_same_origin_candidates_preserved": True}

    def _record(self, con, install, sym, origin, role, status, reason, data, intent_id=None):
        rid = hashlib.sha256(f"{install['id']}|{sym}|{origin}|{role}".encode()).hexdigest()
        con.execute("INSERT OR IGNORE INTO a_tensor_decisions VALUES(?,?,?,?,?,?,?,?,?,?)",
            (rid, install["id"], sym, origin, role, status, reason, _dump(data), intent_id, datetime.now(UTC).isoformat()))
        return rid

    def _merge(self, con, frame, sym, bars, configs, *, diagnostics=None):
        old = con.execute("SELECT * FROM a_tensor_coverage WHERE frame=? AND symbol=?", (frame, sym)).fetchone()
        baseline = self._unpack(old["bars"]) if old else self._seed(frame, sym, configs, bars[-1].usable_at_ms)
        seed_config = next((c for c in configs if c.get("seed_directory") and c.get("seed_manifest_file")), None)
        if seed_config:
            group = self._seed_group(seed_config, frame, sym)
            binding = con.execute("SELECT * FROM a_tensor_prefix_bindings WHERE frame=? AND symbol=?", (frame, sym)).fetchone()
            if not group:
                raise DeskError("Pinned native prefix is unavailable")
            if binding and binding["seed_sha256"] != group["sha256"]:
                raise DeskError("Native prefix binding differs from the installed seed")
            if not binding:
                seed = self._seed(frame, sym, configs, bars[-1].usable_at_ms) if old else baseline
                fields = ("timestamp_ms", "executable_at_ms", "completed_at_ms", "open", "high", "low", "close", "volume")
                prefix = tuple(b for b in baseline if b.executable_at_ms <= seed[-1].executable_at_ms)
                same = len(prefix) == len(seed) and all(all(getattr(a, f) == getattr(b, f) for f in fields) for a, b in zip(prefix, seed))
                if not same:
                    affected = [dict(r) for r in con.execute("SELECT * FROM a_tensor_installations") if json.loads(r["config"])["frame"] == frame and sym in json.loads(r["config"])["symbols"]]
                    for install in affected:
                        if con.execute("SELECT 1 FROM p_fills WHERE book_id=? AND symbol=? LIMIT 1", (install["book_id"], sym)).fetchone() or con.execute("SELECT 1 FROM p_intents WHERE book_id=? AND symbol=? AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested') LIMIT 1", (install["book_id"], sym)).fetchone():
                            raise DeskError("Native prefix ordinal repair requires explicit review after financial execution")
                        con.execute("DELETE FROM a_tensor_candidates WHERE installation_id=? AND symbol=?", (install["id"], sym))
                        con.execute("DELETE FROM a_tensor_cooldowns WHERE installation_id=? AND symbol=?", (install["id"], sym))
                    con.execute("DELETE FROM a_tensor_cycle_reads WHERE frame=? AND symbol=?", (frame, sym))
                    seed_openings = {s.executable_at_ms for s in seed}
                    repair = {"reason": "restored_exact_pinned_native_prefix", "frame": frame, "symbol": sym, "seed_sha256": group["sha256"],
                        "original_rows": len(seed), "old_prefix_rows": len(prefix), "removed_nonseed_periods_ms": [b.executable_at_ms for b in prefix if b.executable_at_ms not in seed_openings][:20],
                        "forward_periods_retained": sum(b.executable_at_ms > seed[-1].executable_at_ms for b in baseline), "ordinal_dependent_state_invalidated": True,
                        "financial_execution_rewritten": False}
                    if diagnostics is not None:
                        diagnostics.append(repair)
                    self.store.event(con, "tensor_native_prefix_repair", "data_steward", "Restored the exact pinned research prefix before any financial execution", repair)
                baseline = (prefix if same else seed) + tuple(b for b in baseline if b.executable_at_ms > seed[-1].executable_at_ms)
                con.execute("INSERT INTO a_tensor_prefix_bindings VALUES(?,?,?,?,?,?,?,?)", (frame, sym, group["sha256"], len(seed), seed[0].timestamp_ms, seed[-1].timestamp_ms, seed[-1].executable_at_ms, _dt(bars[-1].usable_at_ms).isoformat()))
            else:
                prefix = tuple(b for b in baseline if b.executable_at_ms <= binding["last_opening_ms"])
                if len(prefix) != binding["original_rows"] or not prefix or prefix[0].timestamp_ms != binding["first_timestamp_ms"] or prefix[-1].timestamp_ms != binding["last_timestamp_ms"]:
                    raise DeskError("Cached native prefix no longer matches its verified original ordinals")
        merged = {b.executable_at_ms: b for b in baseline}
        if baseline and any(b.executable_at_ms > baseline[-1].executable_at_ms for b in bars):
            supplied = {b.executable_at_ms for b in bars}
            if not supplied & set(merged):
                raise DeskError("Forward native history has no verified overlap with the frozen prefix")
            after = _next_open(frame, baseline[-1].completed_at_ms)
            through = max(b.executable_at_ms for b in bars)
            while after <= through:
                if after not in supplied:
                    raise DeskError("Forward native history omits a completed exchange period; no ordinal compression")
                _, complete = _native_period(after, frame)
                after = _next_open(frame, complete)
        retained, backfilled = [], []
        forward = all(c.get("forward_revision_policy") == "retain_frozen_prefix_audit_minor" for c in configs)
        # Previously observed completed values remain immutable. The explicit
        # forward policy audits small same-basis vendor corrections and retains
        # the old known prefix; large price-basis changes still fail closed.
        for b in bars:
            prior = merged.get(b.executable_at_ms)
            different = [f for f in ("open", "high", "low", "close", "volume", "completed_at_ms") if prior and getattr(prior, f) != getattr(b, f)]
            if different:
                price_change = max(abs(getattr(b, f) / getattr(prior, f) - 1) for f in ("open", "high", "low", "close"))
                if not forward or "completed_at_ms" in different or price_change > .05:
                    raise DeskError("Completed native history was revised beyond the explicit forward policy; entries paused pending price-basis review")
                retained.append({"original_timestamp_ms": prior.timestamp_ms, "vendor_timestamp_ms": b.timestamp_ms,
                                 "executable_at_ms": prior.executable_at_ms, "changed_fields": different,
                                 "maximum_ohlc_relative_change": price_change,
                                 "before": {f: getattr(prior, f) for f in different}, "later_vendor": {f: getattr(b, f) for f in different}})
            if not prior:
                if baseline and b.executable_at_ms <= baseline[-1].executable_at_ms:
                    backfilled.append({"timestamp_ms": b.timestamp_ms, "executable_at_ms": b.executable_at_ms})
                else:
                    merged[b.executable_at_ms] = b
        values = tuple(merged[k] for k in sorted(merged))
        anchor = None
        for config in configs:
            raw_anchor = (config.get("source_origins") or {}).get(sym)
            if raw_anchor is not None:
                value = raw_anchor if isinstance(raw_anchor, int) else _ms(raw_anchor)
                if anchor is not None and anchor != value:
                    raise DeskError("Sleeves disagree on immutable native source anchor")
                anchor = value
        if frame == "1d" and not self.daily_evaluator:
            from .tensor_daily_models import anchor_for
            a = anchor_for(sym)
            daily_anchor = a.first_timestamp_ms
            if daily_anchor is None:
                raise DeskError("Frozen daily model has no usable source anchor")
            if anchor is not None and anchor != daily_anchor:
                raise DeskError("Configured daily source anchor differs from the frozen model")
            anchor = daily_anchor
        if anchor is not None:
            values = tuple(b for b in values if b.timestamp_ms >= anchor)
            if not values or values[0].timestamp_ms != anchor:
                raise DeskError("Required original native history prefix is missing; no phase rebasing")
        if diagnostics is not None and retained:
            diagnostics.append({"reason": "later_vendor_minor_revisions_audited_original_prefix_retained", "changed_native_periods": len(retained),
                "maximum_ohlc_relative_change": max(r["maximum_ohlc_relative_change"] for r in retained), "examples": retained[:20],
                "example_limit": 20, "all_vendor_rows_preserved_in_provider_revision": True, "historical_values_rewritten": False})
        if diagnostics is not None and backfilled:
            diagnostics.append({"reason": "quarantined_vendor_backfill_inside_immutable_native_prefix", "quarantined_periods": len(backfilled), "examples": backfilled[:20],
                "example_limit": 20, "raw_rows_preserved_in_provider_revision": True, "historical_ordinals_shifted": False})
        return values

    def _source_basis_action(self, con, install, sym, clock):
        """A forward split needs a new declared basis, never a mixed prefix."""
        config = install["settings"]
        if not config.get("seed_manifest_file"):
            return None
        group = self._seed_group(config, config["frame"], sym)
        if not group or not group.get("last_completed_at"):
            raise DeskError("Frozen source basis endpoint is unavailable")
        cutoff = _dt(int(group["last_completed_at"]) * 1000).isoformat()
        event = con.execute("SELECT id,effective_at,definition_sha256,source,observed_at FROM a_strategy_actions WHERE book_id=? AND symbol=? AND kind='split' AND effective_at>? AND effective_at<=? AND observed_at<=? ORDER BY effective_at,id LIMIT 1",
            (install["book_id"], sym, cutoff, clock.isoformat(), clock.isoformat())).fetchone()
        return {"source_basis_endpoint": cutoff, **dict(event)} if event else None

    def _verified_ineligible(self, sym, configs, clock):
        for config in configs:
            filename = config.get("verified_ineligible_file")
            if not filename:
                continue
            path = Path(filename)
            path = path if path.is_absolute() else ROOT / path
            expected = config.get("verified_ineligible_sha256")
            stat = path.stat()
            key = (str(path), expected, stat.st_size, stat.st_mtime_ns)
            if key not in self._eligibility_manifests:
                raw = path.read_bytes()
                if not expected or hashlib.sha256(raw).hexdigest() != expected:
                    raise DeskError("Operational asset-status evidence differs from its pinned manifest")
                self._eligibility_manifests[key] = json.loads(raw)
            manifest = self._eligibility_manifests[key]
            if _ms(manifest["retrieved_at"]) > _ms(clock):
                raise DeskError("Operational asset-status evidence was observed after this decision")
            for record in manifest.get("records", []):
                asset = record.get("asset", {})
                if asset.get("symbol") == sym and asset.get("status") == "inactive" and asset.get("tradable") is False:
                    return {"reason": "verified_inactive_nontradable_asset", "asset": asset, "evidence_observed_at": manifest["retrieved_at"],
                            "evidence_manifest_sha256": expected, "response_sha256": record.get("response_sha256"), "enrollment_preserved": True}
        return None

    def _seed(self, frame, sym, configs, receipt_ms):
        """Read one original gzip member, hash pinned before decoding.

        These old prices become known to this operational installation now;
        their stipulated research usableAt is not a claimed desk receipt.
        """
        from .tensor_engine import NativeBar
        config = next((c for c in configs if c.get("seed_directory") and c.get("seed_manifest_file")), None)
        if not config:
            return ()
        group = self._seed_group(config, frame, sym)
        if group is None or group.get("identity_quarantined"):
            raise NativeIneligible("Symbol has no unquarantined original native research seed")
        directory = Path(config["seed_directory"])
        if not directory.is_absolute():
            directory = ROOT / directory
        relative = Path(group["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise DeskError("Invalid research seed member path")
        path = directory / relative
        encoded = path.read_bytes()
        if len(encoded) != group["bytes"] or hashlib.sha256(encoded).hexdigest() != group["sha256"]:
            raise DeskError("Original native research seed member differs from its manifest")
        source = json.loads(gzip.decompress(encoded))
        if source["symbol"] != sym or source["interval"] != frame or len(source["bars"]) != group["accepted_bars"]:
            raise DeskError("Research seed identity or original ordinal count differs")
        result = []
        for b in source["bars"]:
            stamp, complete = int(b["timestamp"]) * 1000, int(b["completedAt"]) * 1000
            opened, verified_complete = _native_period(stamp, frame)
            if complete != verified_complete or complete > receipt_ms:
                raise DeskError("Research seed completion clock differs from XNYS or is future")
            result.append(NativeBar(timestamp_ms=stamp, completed_at_ms=complete, usable_at_ms=max(receipt_ms, complete),
                executable_at_ms=opened, **{k: float(b[k]) for k in ("open", "high", "low", "close", "volume")}))
        return tuple(result)

    def _seed_group(self, config, frame, sym):
        manifest_path = Path(config["seed_manifest_file"])
        if not manifest_path.is_absolute():
            manifest_path = ROOT / manifest_path
        expected = config.get("seed_manifest_sha256")
        stat = manifest_path.stat()
        cache_key = (str(manifest_path), expected, stat.st_size, stat.st_mtime_ns)
        if cache_key not in self._seed_manifests:
            raw = manifest_path.read_bytes()
            if not expected or hashlib.sha256(raw).hexdigest() != expected:
                raise DeskError("Research seed manifest differs from its frozen pin")
            manifest = json.loads(raw)
            self._seed_manifests[cache_key] = {(g["interval"], g["symbol"]): g for source in manifest["sources"] for g in source["groups"]}
        return self._seed_manifests[cache_key].get((frame, sym))

    def run_once(self, clock=None, transaction_guard=None, providers=None):
        if not self._mutex.acquire(blocking=False):
            return {"status": "busy", "acquired": 0, "entries": 0, "exits": 0}
        try:
            return self._run_once(utc_clock(clock), transaction_guard, providers or self.providers, dynamic_clock=clock is None)
        finally:
            self._mutex.release()

    def service_exits(self, clock=None, transaction_guard=None, providers=None, *, acquire_native_clocks=True):
        """Bounded held-only risk service before the normal fill boundary.

        The supervisor processes this outbox before starting broad research.
        No feature computation, universe acquisition, or private fill occurs.
        """
        if not self._mutex.acquire(blocking=False):
            return {"status": "busy", "exits": 0, "observed_periods": 0, "errors": []}
        try:
            dynamic = clock is None
            current = utc_clock(clock)
            providers = providers or self.providers
            result = {"status": "ok", "exits": 0, "observed_periods": 0, "errors": []}
            with self.store.transaction() as con:
                self._guard(con, transaction_guard)
                installs = [dict(r) for r in con.execute("SELECT * FROM a_tensor_installations ORDER BY id")]
                for install in installs:
                    install["settings"] = json.loads(install["config"])
                    self._bind_fill_anchors(con, install)
                targets, needs = set(), {}
                for install in installs:
                    frame = install["settings"]["frame"]
                    states = con.execute("SELECT s.* FROM a_tensor_position_state s JOIN p_positions p ON p.book_id=? AND p.symbol=s.symbol WHERE s.installation_id=? AND s.status='held' AND CAST(p.quantity AS REAL)>0", (install["book_id"], install["id"]))
                    for state in states:
                        # An already observed matured hold does not need an
                        # unrelated feed roundtrip before its owed exit.
                        known_periods = self._held_periods(con, install, state, current)
                        mature = len(known_periods) >= 20 and state["entry_open_ms"] in known_periods
                        if mature:
                            if self._exit_opening(install, current) is not None and _ms(current) >= _next_open(frame, known_periods[sorted(known_periods)[19]]):
                                targets.add(state["symbol"])
                            continue
                        if not acquire_native_clocks:
                            continue
                        latest_completion = latest_native_clock(frame, current)["completed_at_ms"]
                        cached = con.execute("SELECT bars FROM a_tensor_coverage WHERE frame=? AND symbol=?", (frame, state["symbol"])).fetchone()
                        known_latest = max([*known_periods.values(), self._unpack(cached[0])[-1].completed_at_ms if cached else 0])
                        if known_latest >= latest_completion and (not known_periods or state["entry_open_ms"] in known_periods):
                            continue  # No new completed source period exists yet.
                        key = "risk-attempt:" + frame + ":" + state["symbol"]
                        if (frame, state["symbol"]) in needs:
                            needs[(frame, state["symbol"])].append(dict(state))
                            continue
                        last = con.execute("SELECT value FROM a_tensor_cursors WHERE key=?", (key,)).fetchone()
                        prior = json.loads(last[0]) if last else None
                        if prior and prior["completion_ms"] == latest_completion and 0 <= _ms(current) - prior["at_ms"] < 30_000:
                            continue
                        needs.setdefault((frame, state["symbol"]), []).append(dict(state))
                        con.execute("INSERT OR REPLACE INTO a_tensor_cursors VALUES(?,?)", (key, _dump({"completion_ms": latest_completion, "at_ms": _ms(current)})))
            def read(key):
                frame, sym = key
                try:
                    with self.store.connect() as con:
                        cached = con.execute("SELECT bars FROM a_tensor_coverage WHERE frame=? AND symbol=?", key).fetchone()
                    earliest_entry = min(v["entry_open_ms"] for v in needs[key])
                    tail = min(self._unpack(cached[0])[-1].completed_at_ms, earliest_entry) if cached else earliest_entry
                    now = utc_clock() if dynamic else current
                    days = (_ms(now) - tail) / 86_400_000
                    period = "5d" if frame != "1wk" and days <= 3 else next((name for name, span in (("1mo", 25), ("3mo", 80), ("6mo", 160), ("1y", 340), ("2y", 700)) if days <= span), "max")
                    response = providers.bars(sym, period, INTERVAL[frame])
                    now = utc_clock() if dynamic else current
                    bars = canonical_native_bars(response, frame, now, expected_symbol=sym)
                    return key, response, bars, None
                except Exception as exc:
                    if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                        raise
                    return key, None, (), exc.detail if isinstance(exc, DeskError) else "Held native observations unavailable"
            with ThreadPoolExecutor(max_workers=min(16, len(needs) or 1)) as pool:
                reads = list(pool.map(read, needs))
            for (frame, sym), response, bars, error in reads:
                if error:
                    result["errors"].append({"frame": frame, "symbol": sym, "reason": error})
                    continue
                anchor = min(v["entry_open_ms"] for v in needs[(frame, sym)])
                rows = [(frame, sym, b.executable_at_ms, b.completed_at_ms, _dt(b.usable_at_ms).isoformat(), response["revision_id"]) for b in bars if b.executable_at_ms >= anchor]
                with self.store.transaction() as con:
                    self._guard(con, transaction_guard)
                    con.executemany("INSERT OR IGNORE INTO a_tensor_observed_periods VALUES(?,?,?,?,?,?)", rows)
                    for state in needs[(frame, sym)]:
                        install = next(i for i in installs if i["id"] == state["installation_id"])
                        periods = self._held_periods(con, install, state, utc_clock() if dynamic else current)
                        if len(periods) >= 20 and state["entry_open_ms"] in periods and self._exit_opening(install, utc_clock() if dynamic else current) is not None:
                            targets.add(sym)
                result["observed_periods"] += len(rows)
            if targets and hasattr(providers, "refresh"):
                def quote(sym):
                    try:
                        providers.refresh([sym])
                    except Exception as exc:
                        if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                            raise
                        return {"symbol": sym, "reason": "Held execution quote unavailable"}
                with ThreadPoolExecutor(max_workers=min(8, len(targets))) as pool:
                    result["errors"].extend(e for e in pool.map(quote, sorted(targets)) if e)
            if dynamic:
                current = utc_clock()
            if targets and self.actions is not None:
                self.actions.probe_symbols(sorted(targets), clock=None if dynamic else current, fence=transaction_guard, max_symbols=64)
            if dynamic:
                current = utc_clock()
            for install in installs:
                result["exits"] += self._exits(install, current, transaction_guard, providers)
            if result["errors"]:
                result["status"] = "degraded"
            return result
        finally:
            self._mutex.release()

    def _run_once(self, clock, guard, providers, *, dynamic_clock=False):
        result = {"status": "ok", "acquired": 0, "entries": 0, "exits": 0, "errors": []}
        with self.store.connect() as con:
            installations = [dict(r) for r in con.execute("SELECT * FROM a_tensor_installations ORDER BY id")]
        if not installations:
            return {**result, "status": "empty"}
        groups = {}
        for row in installations:
            row["settings"] = json.loads(row["config"])
            groups.setdefault(row["settings"]["frame"], []).append(row)
        # Owed reductions get their own first pass and quotes before broad
        # entry research. A second pass below uses newly verified native clocks.
        with self.store.connect() as con:
            owned_books = [r["book_id"] for r in installations]
            held = sorted({r["symbol"] for r in con.execute("SELECT symbol,quantity FROM p_positions WHERE book_id IN (%s)" % ",".join("?" for _ in owned_books), owned_books) if Decimal(r["quantity"]) > 0})[:40]
        if hasattr(providers, "refresh") and held:
            with ThreadPoolExecutor(max_workers=min(8, len(held))) as pool:
                list(pool.map(lambda sym: providers.refresh([sym]), held))
        if dynamic_clock:
            clock = utc_clock()
        for install in installations:
            result["exits"] += self._exits(install, clock, guard, providers)
        for frame in sorted(groups, key=lambda value: {"1h": 0, "1d": 1, "1wk": 2}[value]):
            installs = groups[frame]
            try:
                if dynamic_clock:
                    clock = utc_clock()
                if frame != "1h" and "1h" in groups and self._h1_window_priority(groups["1h"], clock):
                    self._cached_frame_cycle(frame, installs, clock, guard, providers, result, dynamic_clock)
                    result.setdefault("acquisition_deferred_frames", []).append(frame)
                    continue
                self._frame_cycle(frame, installs, clock, guard, providers, result, dynamic_clock=dynamic_clock)
            except Exception as exc:
                if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                    raise
                message = exc.detail if isinstance(exc, DeskError) else "Native strategy data or computation unavailable"
                result["errors"].append({"frame": frame, "reason": message})
        # Data/feature failures never remove the last verified clocks or the
        # actual fill anchor needed to continue a scheduled risk-reducing exit.
        for install in installations:
            try:
                if dynamic_clock:
                    clock = utc_clock()
                result["exits"] += self._exits(install, clock, guard, providers)
            except Exception as exc:
                if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                    raise
                result["errors"].append({"installation_id": install["id"], "reason": exc.detail if isinstance(exc, DeskError) else "Owned exit processing unavailable"})
        with self.store.connect() as con:
            cycles = [dict(r) for r in con.execute("SELECT frame,status,cursor,origin_ms,expires_ms FROM a_tensor_cycles ORDER BY frame")]
        result["cycles"] = cycles
        if result["errors"] or any(c["status"] == "incomplete" for c in cycles):
            result["status"] = "data_blocked"
        elif any(c["status"] == "degraded" for c in cycles):
            result["status"] = "degraded"
        elif any(c["status"] == "collecting" for c in cycles):
            result["status"] = "collecting"
        return result

    def _h1_window_priority(self, installs, clock):
        """Protect the bounded hourly opening from unrelated acquisition."""
        latest = latest_native_clock("1h", clock)
        stamp, opening = _ms(clock), latest["next_open_ms"]
        window = min(i["settings"]["opening_window_seconds"] for i in installs) * 1000
        if opening - 60_000 <= stamp < opening:
            return True
        if opening <= stamp < opening + window:
            return True  # Queued hourly BUYs still need the normal fill phase.
        bounds = _session(clock.astimezone(NY).date().isoformat())
        if bounds and bounds[0] <= stamp < bounds[1]:
            current_open = bounds[0] + (stamp - bounds[0]) // 3_600_000 * 3_600_000
            close = min(current_open + 3_600_000, bounds[1])
            following = _next_open("1h", close)
            return following == close and 0 < following - stamp <= 60_000
        return False

    def _cached_frame_cycle(self, frame, installs, clock, guard, providers, result, dynamic_clock):
        """Admit a ready overnight census without acquiring unrelated data."""
        latest = latest_native_clock(frame, clock)
        universe = sorted({s for i in installs for s in i["settings"]["symbols"]})
        with self.store.connect() as con:
            cycle = con.execute("SELECT * FROM a_tensor_cycles WHERE frame=?", (frame,)).fetchone()
            count = con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=?", (frame, latest["timestamp_ms"])).fetchone()[0]
        if not cycle or cycle["origin_ms"] != latest["timestamp_ms"] or json.loads(cycle["universe"]) != universe or count < len(universe):
            return
        window = min(i["settings"]["opening_window_seconds"] for i in installs) * 1000
        self._finish_cycle(frame, installs, latest["timestamp_ms"], latest["next_open_ms"], window, cycle["cursor"], [], universe, clock, guard, providers, result, dynamic_clock)

    def _unverified_prefix_barrier(self, con, frame, installs, origin, universe):
        """Old ready census rows cannot bypass newly required seed binding."""
        seeded = {s for i in installs if i["settings"].get("seed_directory") and i["settings"].get("seed_manifest_file") for s in i["settings"]["symbols"]}
        if not seeded:
            return None
        unbound = {r["symbol"] for r in con.execute("SELECT c.symbol,r.status FROM a_tensor_coverage c LEFT JOIN a_tensor_prefix_bindings b ON b.frame=c.frame AND b.symbol=c.symbol LEFT JOIN a_tensor_cycle_reads r ON r.frame=c.frame AND r.symbol=c.symbol AND r.origin_ms=? WHERE c.frame=? AND b.symbol IS NULL", (origin, frame)) if r["symbol"] in seeded and r["status"] in {None, "ready"}}
        if not unbound:
            return None
        con.executemany("DELETE FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND symbol=?", [(frame, origin, sym) for sym in sorted(unbound)])
        earliest = min(universe.index(sym) for sym in unbound)
        con.execute("UPDATE a_tensor_cycles SET cursor=MIN(cursor,?),status='collecting' WHERE frame=? AND origin_ms=?", (earliest, frame, origin))
        return earliest

    def _frame_cycle(self, frame, installs, clock, guard, providers, result, *, dynamic_clock=False):
        latest = latest_native_clock(frame, clock)
        origin, opening = latest["timestamp_ms"], latest["next_open_ms"]
        universe = sorted({sym for i in installs for sym in i["settings"]["symbols"]})
        window = min(i["settings"]["opening_window_seconds"] for i in installs) * 1000
        with self.store.transaction() as con:
            self._guard(con, guard)
            cycle = con.execute("SELECT * FROM a_tensor_cycles WHERE frame=?", (frame,)).fetchone()
            if cycle is None or cycle["origin_ms"] != origin or json.loads(cycle["universe"]) != universe:
                if cycle is not None:
                    old_candidates = list(con.execute("SELECT c.*,i.config,i.sleeve,i.book_id FROM a_tensor_candidates c JOIN a_tensor_installations i ON i.id=c.installation_id WHERE c.origin_ms=?", (cycle["origin_ms"],)))
                    for old in old_candidates:
                        installation = {"id": old["installation_id"], "sleeve": old["sleeve"], "book_id": old["book_id"]}
                        self._record(con, installation, old["symbol"], old["origin_ms"], "entry", "expired", "prior_native_cycle_expired_without_late_replay", json.loads(old["data"]))
                con.execute("INSERT OR REPLACE INTO a_tensor_cycles VALUES(?,?,?,?,?,?,?,?)",
                    (frame, origin, opening, opening + window, 0, _dump(universe), "collecting", clock.isoformat()))
                cycle = con.execute("SELECT * FROM a_tensor_cycles WHERE frame=?", (frame,)).fetchone()
            self._unverified_prefix_barrier(con, frame, installs, origin, universe)
            cursor = con.execute("SELECT cursor FROM a_tensor_cycles WHERE frame=?", (frame,)).fetchone()[0]
        budget = min(i["settings"]["max_fetch_per_run"] for i in installs)
        manifest = None
        if frame in {"1h", "1wk"} and self.feature_extractor is None and self.policy_factory is None:
            from .tensor_engine import source_manifest_sha256
            manifest = source_manifest_sha256()  # Verify the actual pinned closure, never an input-supplied hash.
        with self.store.transaction() as con:
            self._guard(con, guard)
            books = [i["book_id"] for i in installs]
            held = sorted({r["symbol"] for r in con.execute("SELECT symbol,quantity FROM p_positions WHERE book_id IN (%s)" % ",".join("?" for _ in books), books) if Decimal(r["quantity"]) > 0})
            previous = con.execute("SELECT value FROM a_tensor_cursors WHERE key=?", ("held:" + frame,)).fetchone()
            if previous and previous[0] in held:
                offset = held.index(previous[0]) + 1
                held = held[offset:] + held[:offset]
            priority = held[:min(8, budget // 2)]
            if priority:
                con.execute("INSERT OR REPLACE INTO a_tensor_cursors VALUES(?,?)", ("held:" + frame, priority[-1]))
        with self.store.transaction() as con:
            self._guard(con, guard)
            failed_symbols = [r[0] for r in con.execute("SELECT symbol FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND status='failed' ORDER BY symbol", (frame, origin))]
            assessed_symbols = {r[0] for r in con.execute("SELECT symbol FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=?", (frame, origin))}
            all_assessed = set(universe).issubset(assessed_symbols)
            previous = con.execute("SELECT value FROM a_tensor_cursors WHERE key=?", ("retry:" + frame,)).fetchone()
            if previous and previous[0] in failed_symbols:
                offset = failed_symbols.index(previous[0]) + 1
                failed_symbols = failed_symbols[offset:] + failed_symbols[:offset]
            # Preserve first-attempt progress, then use the configured width
            # to recover an already assessed census after a provider repair.
            retry_width = max(0, budget - len(priority)) if all_assessed else min(8, max(1, budget // 4), max(0, budget - len(priority) - 1))
            retry = failed_symbols[:retry_width]
            if retry:
                con.execute("INSERT OR REPLACE INTO a_tensor_cursors VALUES(?,?)", ("retry:" + frame, retry[-1]))
        if all_assessed:
            cursor = len(universe)
        # Staged coverage can survive an interruption before its assessment.
        # Revisit those missing names even if a prior cycle cursor reached end;
        # an immutable prefix binding is not a completed scoring assessment.
        offset = cursor % len(universe)
        ordered = universe[offset:] + universe[:offset]
        missing = [sym for sym in ordered if sym not in assessed_symbols and sym not in priority]
        cycle_batch = missing[:max(0, budget - len(priority) - len(retry))]
        batch = list(dict.fromkeys(priority + retry + cycle_batch))
        def read(sym):
            relevant = [i for i in installs if sym in i["settings"]["symbols"]]
            try:
                status_evidence = self._verified_ineligible(sym, [i["settings"] for i in relevant], utc_clock() if dynamic_clock else clock)
                if status_evidence:
                    return {"_verified_ineligible": status_evidence}
                last_complete = self._coverage_tail(frame, sym, guard)
                seeded = last_complete is not None
                if last_complete is None and relevant[0]["settings"].get("seed_directory"):
                    group = self._seed_group(relevant[0]["settings"], frame, sym)
                    last_complete = int(group["last_completed_at"]) * 1000 if group else None
                if last_complete is None:
                    period = relevant[0]["settings"]["history_range"]
                else:
                    gap_days = (_ms(utc_clock() if dynamic_clock else clock) - last_complete) / 86_400_000
                    period = "5d" if seeded and frame != "1wk" and gap_days <= 3 else next((name for name, span in (("1mo", 25), ("3mo", 80), ("6mo", 160), ("1y", 340), ("2y", 700)) if gap_days <= span), "max")
                return providers.bars(sym, period, INTERVAL[frame])
            except Exception as exc:
                if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                    raise
                return exc
        # Stream bounded independent reads into native calculation instead of
        # waiting for every network response before any computation can begin.
        # Source commit order and full-census ranking remain deterministic.
        responses = []
        prepared = {}
        def compute(sym, bars, observed_clock):
            history = self._extract(sym, frame, bars, observed_clock)
            rows = history.rows if hasattr(history, "rows") else history.get("rows", ())
            decision_clock = utc_clock() if dynamic_clock else observed_clock
            if dynamic_clock and frame == "1d" and rows:
                remaining = (max(int(row["usable_at"]) for row in rows) * 1000 - _ms(decision_clock)) / 1000
                if remaining > 0:
                    time.sleep(min(remaining, 1))
                    decision_clock = utc_clock()
            daily = self._daily(sym, rows, decision_clock) if frame == "1d" else None
            return history, daily, decision_clock
        with ThreadPoolExecutor(max_workers=min(32, len(batch) or 1)) as readers, ThreadPoolExecutor(max_workers=min(8, len(batch) or 1)) as engines:
            pending_reads = [readers.submit(read, sym) for sym in batch]
            # Bar validation/storage preserves deterministic source order;
            # native calculation is independent and has no write interface.
            for sym, pending_read in zip(batch, pending_reads):
                response = pending_read.result()
                responses.append(response)
                relevant = [i for i in installs if sym in i["settings"]["symbols"]]
                try:
                    observed_clock = utc_clock() if dynamic_clock else clock
                    if isinstance(response, Exception):
                        raise response
                    if response.get("_verified_ineligible"):
                        error = NativeIneligible("verified_inactive_nontradable_asset")
                        error.evidence = response["_verified_ineligible"]
                        raise error
                    diagnostics = []
                    bars = canonical_native_bars(response, frame, observed_clock, expected_symbol=sym, diagnostics=diagnostics)
                    # Actual observed calendar periods are a risk-service tape,
                    # independent of source price-basis/feature readiness. They
                    # never authorize entries. Preserve only held-period clocks
                    # plus a small current tail, rather than duplicating all
                    # historical seed rows into another database table.
                    with self.store.transaction() as con:
                        self._guard(con, guard)
                        anchor = con.execute("SELECT MIN(entry_open_ms) FROM a_tensor_position_state WHERE symbol=? AND status='held' AND installation_id IN (%s)" % ",".join("?" for _ in relevant), [sym, *[i["id"] for i in relevant]]).fetchone()[0]
                        clocks = [b for b in bars if anchor is not None and b.executable_at_ms >= anchor] if anchor is not None else bars[-4:]
                        con.executemany("INSERT OR IGNORE INTO a_tensor_observed_periods VALUES(?,?,?,?,?,?)", [(frame, sym, b.executable_at_ms, b.completed_at_ms, _dt(b.usable_at_ms).isoformat(), response["revision_id"]) for b in clocks])
                    if any(i["settings"].get("expected_bar_provider") and response.get("provider") != i["settings"]["expected_bar_provider"] for i in relevant):
                        raise DeskError("Native bar provider differs from the installed price and volume source basis")
                    if bars[-1].completed_at_ms != latest["completed_at_ms"]:
                        raise DeskError("Latest completed native bar is missing")
                    with self.store.transaction() as con:
                        self._guard(con, guard)
                        if any(self._source_basis_action(con, install, sym, observed_clock) for install in relevant):
                            raise DeskError("Observed post-seed split requires explicit native source-basis review; immutable prefix was not adjusted")
                        prior_bound = con.execute("SELECT 1 FROM a_tensor_prefix_bindings WHERE frame=? AND symbol=?", (frame, sym)).fetchone() is not None
                        bars = self._merge(con, frame, sym, bars, [i["settings"] for i in relevant], diagnostics=diagnostics)
                        prior_read = con.execute("SELECT status FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND symbol=?", (frame, origin, sym)).fetchone()
                        proof = self._state_cooldown_proof(con, frame, sym, bars, relevant, origin, observed_clock, manifest, prior_bound, diagnostics) if len(bars) >= 234 else None
                        self._write_coverage(con, frame, sym, response, bars, observed_clock)
                        receipt = {"frame": frame, "symbol": sym, "revision_id": response["revision_id"], "observed_at": response["observed_at"],
                            "revision_first_observed_at": response["observed_at"], "fetched_at": response["fetched_at"], "latest_native_usable_at_ms": bars[-1].usable_at_ms,
                            "provider": response["provider"], "adjustment": response["adjustment"], "native_source_bar_count": len(bars),
                            "canonical_source_origin_timestamp_ms": bars[0].timestamp_ms, "diagnostics": diagnostics,
                            "forward_revision_policy": relevant[0]["settings"].get("forward_revision_policy", "reject_any_revision")}
                        wrote = con.execute("INSERT OR IGNORE INTO a_tensor_revision_receipts VALUES(?,?,?,?,?)", (frame, sym, response["revision_id"], response["observed_at"], _dump(receipt)))
                        if diagnostics and wrote.rowcount:
                            self.store.event(con, "tensor_forward_source_receipt", "data_steward", "Recorded quarantined vendor rows or retained historical source revisions", receipt)
                    skip = prior_read and prior_read[0] in {"ready", "ineligible"}
                    future = None if skip or proof or len(bars) < 234 else engines.submit(compute, sym, bars, observed_clock)
                    prepared[sym] = (bars, future, proof or bool(skip))
                except Exception as exc:
                    if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                        raise
                    prepared[sym] = exc
            for sym, response in zip(batch, responses):
                self._finish_symbol(sym, response, prepared[sym], frame, installs, origin, opening, window, clock, guard, result)
        if dynamic_clock:
            clock = utc_clock()
        self._finish_cycle(frame, installs, origin, opening, window, cursor, cycle_batch, universe, clock, guard, providers, result, dynamic_clock)

    def _finish_symbol(self, sym, response, prepared, frame, installs, origin, opening, window, clock, guard, result):
        relevant = [i for i in installs if sym in i["settings"]["symbols"]]
        try:
            if isinstance(prepared, Exception):
                raise prepared
            bars, future, skipped = prepared
            if isinstance(skipped, dict):
                with self.store.transaction() as con:
                    self._guard(con, guard)
                    for install in relevant:
                        self._record(con, install, sym, origin, "signal", "no_opportunity", "cooldown", skipped)
                    con.execute("INSERT OR REPLACE INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", (frame, origin, sym, "ready", None))
                result["acquired"] += 1
                return
            if skipped:
                result["acquired"] += 1
                return
            if len(bars) < 234:
                with self.store.transaction() as con:
                    self._guard(con, guard)
                    con.execute("INSERT OR REPLACE INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", (frame, origin, sym, "ineligible", "native_history_warming"))
                    for install in relevant:
                        self._record(con, install, sym, origin, "signal", "no_opportunity", "native_history_warming", {"observed_bars": len(bars)})
                result["acquired"] += 1
                return
            history, daily, clock = future.result()
            snapshot = history.snapshot if hasattr(history, "snapshot") else history["snapshot"]
            rows = history.rows if hasattr(history, "rows") else history.get("rows", ())
            manifest = snapshot.source_manifest_sha256 if hasattr(snapshot, "source_manifest_sha256") else snapshot["source_manifest_sha256"]
            if any(i["settings"].get("engine_source_manifest_sha256") and i["settings"]["engine_source_manifest_sha256"] != manifest for i in relevant):
                raise DeskError("Native source manifest differs from the installed engine pin")
            with self.store.transaction() as con:
                self._guard(con, guard)
                for install in relevant:
                    cooldown = con.execute("SELECT next_index FROM a_tensor_cooldowns WHERE installation_id=? AND symbol=?", (install["id"], sym)).fetchone()
                    if frame == "1d":
                        selected = next(d for d in daily if ALIASES.get(_plain(d).get("sleeve_id"), _plain(d).get("sleeve_id")) == install["sleeve"])
                        data = _plain(selected)
                        signal = data if data.get("selected") else None
                        reason = data.get("reason", "not_selected")
                        if signal:
                            data["origin_bar_index"] = data["bar_index"]
                            data["next_eligible_bar_index"] = data["bar_index"] + 20
                            data["score"] = data.get("predicted_net_qqq_excess", data.get("score"))
                    else:
                        bootstrap = historical_state_cooldown(rows, len(bars) - 1) if rows else None
                        if bootstrap and (cooldown is None or bootstrap["next_eligible_bar_index"] > cooldown[0]):
                            con.execute("INSERT OR REPLACE INTO a_tensor_cooldowns VALUES(?,?,?,?)", (install["id"], sym, bootstrap["next_eligible_bar_index"], origin))
                            cooldown = (bootstrap["next_eligible_bar_index"],)
                            self._record(con, install, sym, origin, "cooldown_bootstrap", "reconstructed", "full_prefix_opportunities_without_historical_orders", bootstrap)
                        decision = self._policy(frame, manifest).evaluate(sym, snapshot, as_of_ms=_ms(clock), next_eligible_bar_index=cooldown[0] if cooldown else None)
                        signal = decision.signal
                        reason = decision.reason
                        data = _plain(signal) if signal else {"reason": reason}
                    if signal:
                        if frame == "1d" and cooldown and data["bar_index"] < cooldown[0]:
                            self._record(con, install, sym, origin, "signal", "no_opportunity", "cooldown", data)
                            continue
                        data.update({"origin_ms": origin, "next_open_ms": opening, "expires_ms": opening + window,
                                     "revision_id": response["revision_id"], "observed_at": _dt(bars[-1].usable_at_ms).isoformat(),
                                     "revision_first_observed_at": response["observed_at"], "fetched_at": response["fetched_at"], "source_manifest_sha256": manifest})
                        con.execute("INSERT OR REPLACE INTO a_tensor_candidates VALUES(?,?,?,?)", (install["id"], origin, sym, _dump(data)))
                        con.execute("INSERT OR REPLACE INTO a_tensor_cooldowns VALUES(?,?,?,?)", (install["id"], sym, data["next_eligible_bar_index"], origin))
                    else:
                        self._record(con, install, sym, origin, "signal", "no_opportunity", reason, data)
                con.execute("INSERT OR REPLACE INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", (frame, origin, sym, "ready", None))
            result["acquired"] += 1
        except Exception as exc:
            if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                raise
            reason = exc.detail if isinstance(exc, DeskError) else str(exc) if isinstance(exc, (ValueError, KeyError)) else "Native history or deterministic computation unavailable"
            with self.store.transaction() as con:
                self._guard(con, guard)
                con.execute("INSERT OR REPLACE INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", (frame, origin, sym, "ineligible" if isinstance(exc, NativeIneligible) else "failed", reason[:500]))
                for install in relevant:
                    self._record(con, install, sym, origin, "signal", "known_ineligible" if isinstance(exc, NativeIneligible) else "data_denied", reason[:500], getattr(exc, "evidence", {}))
    def _finish_cycle(self, frame, installs, origin, opening, window, cursor, cycle_batch, universe, clock, guard, providers, result, dynamic_clock):
        # Price observations are acquired after score ranking, outside the
        # accounting transaction. They cannot become historical bar-open fills.
        if opening <= _ms(clock) < opening + window and hasattr(providers, "refresh"):
            with self.store.connect() as reader:
                ready = reader.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=?", (frame, origin)).fetchone()[0] == len(universe)
                candidates = []
                if ready:
                    candidates = [json.loads(r[0]) for i in installs for r in reader.execute("SELECT data FROM a_tensor_candidates WHERE installation_id=? AND origin_ms=?", (i["id"], origin))]
                candidates.sort(key=lambda d: (-d["score"], d["symbol"]))
                books = [i["book_id"] for i in installs]
                refresh = sorted({r["symbol"] for r in reader.execute("SELECT symbol,quantity FROM p_positions WHERE book_id IN (%s)" % ",".join("?" for _ in books), books) if Decimal(r["quantity"]) > 0})[:32]
                for candidate in candidates:
                    if candidate["symbol"] not in refresh:
                        try:
                            q = self.trading._raw_quote(reader, candidate["symbol"], clock)
                            if _ms(q["as_of"]) >= opening:
                                continue
                        except DeskError:
                            pass
                        refresh.append(candidate["symbol"])
                    if len(refresh) >= 32:
                        break
            with ThreadPoolExecutor(max_workers=min(8, len(refresh) or 1)) as pool:
                list(pool.map(lambda sym: providers.refresh([sym]), refresh))
            if dynamic_clock:
                clock = utc_clock()
        if self.actions is not None:
            from .tensor_actions import _required_probe_at
            with self.store.connect() as reader:
                cutoff = _required_probe_at(clock)
                probes = {r["symbol"]: dict(r) for r in reader.execute("SELECT * FROM a_strategy_action_probes")}
                books = [i["book_id"] for i in installs]
                targets = sorted({r["symbol"] for r in reader.execute("SELECT symbol,quantity FROM p_positions WHERE book_id IN (%s)" % ",".join("?" for _ in books), books) if Decimal(r["quantity"]) > 0})
                for install in installs:
                    if not reader.execute("SELECT enabled FROM a_tensor_installations WHERE id=?", (install["id"],)).fetchone()[0]:
                        continue
                    ranked = [json.loads(r[0]) for r in reader.execute("SELECT data FROM a_tensor_candidates WHERE installation_id=? AND origin_ms=?", (install["id"], origin))]
                    ranked.sort(key=lambda d: (-d["score"], d["symbol"]))
                    targets.extend(d["symbol"] for d in ranked[:32])
                targets = list(dict.fromkeys(targets))
                needed = [sym for sym in targets if sym not in probes or probes[sym]["status"] != "ok" or probes[sym]["checked_at"] < cutoff or utc_clock(probes[sym]["checked_at"]) > clock][:64]
            if needed:
                self.actions.probe_symbols(needed, clock=None if dynamic_clock else clock, fence=guard, max_symbols=64)
            if dynamic_clock:
                clock = utc_clock()
        for install in installs:
            result["exits"] += self._exits(install, clock, guard, providers)
        with self.store.transaction() as con:
            self._guard(con, guard)
            unverified = self._unverified_prefix_barrier(con, frame, installs, origin, universe)
            next_cursor = min(len(universe), cursor + len(cycle_batch))
            if unverified is not None:
                next_cursor = min(next_cursor, unverified)
            con.execute("UPDATE a_tensor_cycles SET cursor=?,updated_at=? WHERE frame=? AND origin_ms=?", (next_cursor, clock.isoformat(), frame, origin))
            failed = con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=? AND status='failed'", (frame, origin)).fetchone()[0]
            count = con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=?", (frame, origin)).fetchone()[0]
            status = "collecting" if count < len(universe) else "degraded" if failed and (len(universe) - failed) / len(universe) >= .99 else "incomplete" if failed else "complete"
            con.execute("UPDATE a_tensor_cycles SET status=? WHERE frame=?", (status, frame))
            if count < len(universe):
                return
            for install in installs:
                read_rows = {r["symbol"]: dict(r) for r in con.execute("SELECT * FROM a_tensor_cycle_reads WHERE frame=? AND origin_ms=?", (frame, origin)) if r["symbol"] in install["settings"]["symbols"]}
                bad = sorted(sym for sym, r in read_rows.items() if r["status"] == "failed")
                pool = sorted(sym for sym, r in read_rows.items() if r["status"] == "ready")
                assessed = len(read_rows)
                total = len(install["settings"]["symbols"])
                known_fraction = (assessed - len(bad)) / total
                allowed = assessed == total and (not bad or install["settings"]["missing_data_policy"] == "exclude_unavailable_with_census_receipts" and known_fraction >= .99)
                census = {"enrollment_count": total, "assessed_count": assessed, "known_valid_or_ineligible": assessed - len(bad),
                    "known_fraction": known_fraction, "minimum_forward_known_fraction": .99, "policy": install["settings"]["missing_data_policy"],
                    "unknown_entry_blocked_symbols": bad, "rankable_native_symbols": pool, "rankable_count": len(pool),
                    "all_intended_symbols_attempted": assessed == total, "entries_admissible": allowed,
                    "partial_batch_ranking": False, "forward_live_census_differs_from_r11_idealized_complete_roster": bool(bad)}
                digest = hashlib.sha256(_dump(census).encode()).hexdigest()
                census_id = hashlib.sha256(f"{install['id']}|{origin}|{digest}".encode()).hexdigest()
                con.execute("INSERT OR IGNORE INTO a_tensor_censuses VALUES(?,?,?,?,?,?)", (census_id, install["id"], origin, digest, _dump(census), clock.isoformat()))
                candidates = [json.loads(r[0]) for r in con.execute("SELECT data FROM a_tensor_candidates WHERE installation_id=? AND origin_ms=?", (install["id"], origin))]
                # Every enrollment read has finished before any ranking/allocation.
                candidates.sort(key=lambda d: (-d["score"], d["symbol"]))
                current_install = con.execute("SELECT enabled,config_sha256 FROM a_tensor_installations WHERE id=?", (install["id"],)).fetchone()
                for data in candidates:
                    if con.execute("SELECT 1 FROM a_tensor_decisions WHERE installation_id=? AND symbol=? AND origin_ms=? AND role='entry'", (install["id"], data["symbol"], origin)).fetchone():
                        continue
                    con.execute("INSERT OR REPLACE INTO a_tensor_cooldowns VALUES(?,?,?,?)", (install["id"], data["symbol"], data["next_eligible_bar_index"], origin))
                    if _ms(clock) >= data["expires_ms"]:
                        self._record(con, install, data["symbol"], origin, "entry", "expired", "incomplete_enrollment_cycle" if not allowed else "next_opening_opportunity_expired", data)
                    elif not allowed:
                        self._record(con, install, data["symbol"], origin, "coverage", "deferred", "incomplete_enrollment_cycle", data)
                    elif data["symbol"] not in pool:
                        self._record(con, install, data["symbol"], origin, "coverage", "deferred", "candidate_current_source_quality_blocked", data)
                    elif not current_install["enabled"]:
                        self._record(con, install, data["symbol"], origin, "entry", "denied", "entries_disabled", data)
                    elif _ms(clock) >= data["next_open_ms"]:
                        data["entry_census_sha256"] = digest
                        result["entries"] += self._entry(con, install, data, clock, guard)
                    # Pre-opening candidates remain durable and are admitted
                    # only after a fresh observed opening quote is available.

    def _entry(self, con, install, data, clock, guard):
        sym = data["symbol"]
        try:
            current = con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (install["id"],)).fetchone()
            if not current["enabled"] or current["config_sha256"] != install["config_sha256"]:
                raise DeskError("Entry installation was disabled or its frozen identity changed")
            split_basis = self._source_basis_action(con, install, sym, clock)
            if split_basis:
                self._record(con, install, sym, data["origin_ms"], "source_basis", "deferred", "Observed post-seed split requires explicit native source-basis review", split_basis)
                return 0
            held = {r["symbol"] for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (install["book_id"],)) if Decimal(r["quantity"]) > 0}
            pending = {r[0] for r in con.execute("SELECT symbol FROM p_intents WHERE book_id=? AND side='buy' AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (install["book_id"],))}
            pending_exits = con.execute("SELECT 1 FROM p_intents WHERE book_id=? AND side='sell' AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested') LIMIT 1", (install["book_id"],)).fetchone()
            if pending_exits:
                self._record(con, install, sym, data["origin_ms"], "entry_exit_coverage", "deferred", "Awaiting queued risk-reducing exits before ranked entry allocation", data)
                return 0  # Recompute actual slots, NAV and settled cash after fills.
            if sym in held | pending:
                raise DeskError("already_held_or_pending")
            if len(held | pending) >= 10:
                raise DeskError("maximum_ten_slots_including_pending")
            try:
                quote = self.trading._raw_quote(con, sym, clock)
            except DeskError as exc:
                self._record(con, install, sym, data["origin_ms"], "quote_coverage", "deferred", exc.detail, data)
                return 0  # Quote acquisition may retry inside this bounded opening.
            if _ms(quote["as_of"]) < data["next_open_ms"]:
                self._record(con, install, sym, data["origin_ms"], "quote_coverage", "deferred", "quote_precedes_eligible_native_opening", data)
                return 0
            price = Decimal(quote["price"])
            book = self.trading._book(con, install["book_id"])
            account, positions = self.trading._account(con, book, clock)
            if account["missing_marks"] or account["stale_marks"]:
                self._record(con, install, sym, data["origin_ms"], "mark_coverage", "deferred", "Strategy equity requires fresh complete position marks", data)
                return 0
            equity = Decimal(account["exact_equity_cents"]) / 100 if "exact_equity_cents" in account else Decimal(str(account["equity"]))
            cash = Decimal(self.trading.strategy_cash(con, install["book_id"], clock)["available_cents"]) / 100
            # Frozen research budget includes 10bps buy cost. Actual local policy
            # slippage/fees also enter the conservative integer quantity bound.
            policy = json.loads(book["policy"])
            effective = price * (Decimal(1) + max(Decimal(".001"), Decimal(str(policy["slippage_bps"])) / 10000))
            fee = Decimal(str(policy["fees_per_order"]))
            debit_cap = min(equity * Decimal(".10"), Decimal(str(data["dollar_volume20"])) * Decimal(".01"), cash)
            budget = debit_cap - fee
            shares = int((budget / effective).to_integral_value(rounding=ROUND_FLOOR)) if budget > 0 else 0
            if shares < 1:
                raise DeskError("whole_share_cash_or_native_liquidity_cap")
            client = "tensor-" + hashlib.sha256(f"{install['id']}|{sym}|{data['origin_ms']}|buy".encode()).hexdigest()[:48]
            payload = {"book_id": install["book_id"], "symbol": sym, "side": "buy", "quantity": shares,
                       "client_id": client, "order_type": "market", "time_in_force": "day",
                       "not_before": _dt(data["next_open_ms"]).isoformat(), "expires_at": _dt(data["expires_ms"]).isoformat(),
                       "sleeve": install["sleeve"], "reason": "Frozen deterministic Tensor research rule; local observed quote simulation"}
            payload["max_debit_cents"] = int((debit_cap * 100).to_integral_value(rounding=ROUND_FLOOR))
            intent = self.trading.submit_strategy_intent(payload, install["id"], transaction_guard=lambda writer: self._guard(writer, guard), con=con, clock=clock)
            self._record(con, install, sym, data["origin_ms"], "entry", "queued", "ranked_funded_opportunity", {**data, "sizing": {"shares": shares, "price": str(price), "equity": str(equity), "available_cash": str(cash), "capped_budget": str(budget)}}, intent["id"])
            return 1
        except DeskError as exc:
            if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                raise
            if "Corporate action" in exc.detail:
                self._record(con, install, sym, data["origin_ms"], "action_coverage", "deferred", exc.detail, data)
                return 0
            self._record(con, install, sym, data["origin_ms"], "entry", "denied", exc.detail, data)
            return 0

    def _fill_open(self, frame, fill_at):
        stamp = _ms(fill_at)
        local = _dt(stamp).astimezone(NY)
        bounds = _session(local.date().isoformat())
        if not bounds or not bounds[0] <= stamp < bounds[1]:
            raise DeskError("Actual entry fill was not inside a regular XNYS session")
        if frame == "1h":
            return bounds[0] + (stamp - bounds[0]) // 3_600_000 * 3_600_000
        if frame == "1d":
            return bounds[0]
        monday = local.date() - timedelta(days=local.weekday())
        days = _sessions(monday.isoformat(), (monday + timedelta(days=6)).isoformat())
        return _session(days[0])[0]

    def _bind_fill_anchors(self, con, install):
        frame = install["settings"]["frame"]
        fills = list(con.execute("SELECT f.* FROM p_fills f JOIN p_intents i ON i.id=f.intent_id WHERE f.book_id=? AND f.side='buy' AND i.sleeve=? ORDER BY f.timestamp,f.rowid", (install["book_id"], install["sleeve"])))
        latest_by_symbol = {f["symbol"]: f for f in fills}
        for newest in latest_by_symbol.values():
            fill = next(f for f in fills if f["intent_id"] == newest["intent_id"])
            prior = con.execute("SELECT * FROM a_tensor_position_state WHERE installation_id=? AND symbol=?", (install["id"], fill["symbol"])).fetchone()
            if prior and prior["entry_fill_id"] == fill["id"]:
                continue
            con.execute("INSERT OR REPLACE INTO a_tensor_position_state VALUES(?,?,?,?,?,?)", (install["id"], fill["symbol"], fill["id"], fill["timestamp"], self._fill_open(frame, fill["timestamp"]), "held"))

    def _held_periods(self, con, install, state, clock):
        frame = install["settings"]["frame"]
        coverage = con.execute("SELECT * FROM a_tensor_coverage WHERE frame=? AND symbol=?", (frame, state["symbol"])).fetchone()
        bars = self._unpack(coverage["bars"]) if coverage else ()
        periods = {b.executable_at_ms: b.completed_at_ms for b in bars if b.executable_at_ms >= state["entry_open_ms"] and b.completed_at_ms <= _ms(clock) and b.usable_at_ms <= _ms(clock)}
        for row in con.execute("SELECT * FROM a_tensor_observed_periods WHERE frame=? AND symbol=? AND opening_ms>=? AND completed_ms<=? AND observed_at<=?", (frame, state["symbol"], state["entry_open_ms"], _ms(clock), clock.isoformat())):
            periods[row["opening_ms"]] = row["completed_ms"]
        return periods

    def _exit_opening(self, install, clock):
        bounds = _session(clock.astimezone(NY).date().isoformat())
        stamp = _ms(clock)
        if not bounds or not bounds[0] <= stamp < bounds[1]:
            return None
        opening = bounds[0]
        if install["settings"]["frame"] == "1h":
            opening += (stamp - opening) // 3_600_000 * 3_600_000
        return opening if stamp < opening + install["settings"]["opening_window_seconds"] * 1000 else None

    def _exits(self, install, clock, guard, providers):
        frame = install["settings"]["frame"]
        count = 0
        with self.store.transaction() as con:
            self._guard(con, guard)
            self._bind_fill_anchors(con, install)
            states = list(con.execute("SELECT * FROM a_tensor_position_state WHERE installation_id=? AND status='held'", (install["id"],)))
            for state in states:
                pos = self.trading._position(con, install["book_id"], state["symbol"])
                if not pos or Decimal(pos["quantity"]) <= 0:
                    con.execute("UPDATE a_tensor_position_state SET status='closed' WHERE installation_id=? AND symbol=?", (install["id"], state["symbol"]))
                    continue
                periods = self._held_periods(con, install, state, clock)
                observed = sorted(periods)
                if not observed or observed[0] != state["entry_open_ms"] or len(observed) < 20:
                    continue
                target = _next_open(frame, periods[observed[19]])
                if _ms(clock) < target:
                    continue
                # Prevent an old partially-filled entry tail from reopening
                # exposure after its actual first fill has reached the exit.
                for pending_buy in list(con.execute("SELECT * FROM p_intents WHERE book_id=? AND symbol=? AND side='buy' AND sleeve=? AND status IN ('queued','open','partially_filled','blocked')", (install["book_id"], state["symbol"], install["sleeve"]))):
                    con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=?,error='Filled strategy entry reached its observed time exit' WHERE id=?", (clock.isoformat(), clock.isoformat(), pending_buy["id"]))
                    self.store.event(con, "tensor_entry_remainder_cancelled", "strategy", "Cancelled the old local entry remainder before its measured time exit", {"installation_id": install["id"], "intent_id": pending_buy["id"]})
                if con.execute("SELECT 1 FROM p_intents WHERE book_id=? AND symbol=? AND side='sell' AND status IN ('queued','open','partially_filled','blocked','submitting','cancel_requested')", (install["book_id"], state["symbol"])).fetchone():
                    continue
                # A missed time exit remains owed; it uses the first subsequent
                # actual session/native opening, never a fabricated historical fill.
                opening = self._exit_opening(install, clock)
                if opening is None:
                    continue
                origin = opening
                if con.execute("SELECT 1 FROM a_tensor_decisions WHERE installation_id=? AND symbol=? AND origin_ms=? AND role='exit' AND status='queued'", (install["id"], state["symbol"], origin)).fetchone():
                    continue
                try:
                    try:
                        quote = self.trading._raw_quote(con, state["symbol"], clock)
                    except DeskError:
                        continue  # Retry quote acquisition during this opening.
                    if _ms(quote["as_of"]) < opening:
                        raise DeskError("Exit quote precedes the admissible opening")
                    client = "tensor-" + hashlib.sha256(f"{install['id']}|{state['entry_fill_id']}|{opening}|sell".encode()).hexdigest()[:48]
                    expires = opening + install["settings"]["opening_window_seconds"] * 1000
                    payload = {"book_id": install["book_id"], "symbol": state["symbol"], "side": "sell", "quantity": str(Decimal(pos["quantity"])), "client_id": client,
                               "order_type": "market", "time_in_force": "day", "not_before": _dt(opening).isoformat(), "expires_at": _dt(expires).isoformat(),
                               "sleeve": install["sleeve"], "reason": "20 observed native bars from actual filled entry; risk-reducing local paper exit"}
                    intent = self.trading.submit_strategy_intent(payload, install["id"], transaction_guard=lambda writer: self._guard(writer, guard), con=con, clock=clock)
                    self._record(con, install, state["symbol"], origin, "exit", "queued", "observed_twenty_bar_exit", {"entry_fill_id": state["entry_fill_id"], "entry_open_ms": state["entry_open_ms"], "target_open_ms": target, "actual_open_ms": opening, "observed_hold_bars": len(observed), "overdue": opening > target}, intent["id"])
                    count += 1
                except DeskError as exc:
                    if getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                        raise
                    # A recovered quote/action probe can submit this same
                    # opening's owed exit. Keep transient blockage separate
                    # from the unique successful outbox receipt.
                    self._record(con, install, state["symbol"], origin, "exit_coverage", "deferred", exc.detail, {"target_open_ms": target})
        return count


# Public integration name retained for callers that spell out the manager role.
TensorRuntimeManager = TensorRuntime
