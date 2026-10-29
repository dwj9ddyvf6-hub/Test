"""Explicit public-rule sleeves in independent local quote-paper books.

This manager has no broker submission path. Completed, actually observed daily
bars produce immutable ranked decisions; entries expire at the next opening.
Persisted exit obligations survive entry disablement, restarts and missed opens.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import threading
import zlib

from .providers import NY, utc_clock
from .store import DeskError, identifier, symbol
from .tensor_engine import NativeBar
from .tensor_actions import split_mark_price
from .tensor_runtime import canonical_native_bars, latest_native_clock, _dt, _ms, _next_open, _session

UTC = timezone.utc
ACTIVE_SQL = "'queued','open','partially_filled','blocked','submitting','cancel_requested'"


def _dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class TraderRuntimeManager:
    """Bounded daily acquisition and the existing guarded paper intent boundary."""

    def __init__(self, store, trading, providers, *, evaluator=None, definitions=None):
        self.store, self.trading, self.providers = store, trading, providers
        self.actions = None
        self._evaluator, self._definitions = evaluator, definitions
        self._mutex = threading.Lock()
        self._invalid_installations = []
        with store.connect() as con:
            con.executescript("""
              CREATE TABLE IF NOT EXISTS a_trader_installations(id TEXT PRIMARY KEY,sleeve TEXT NOT NULL,book_id TEXT NOT NULL UNIQUE,
                enabled INTEGER NOT NULL,config TEXT NOT NULL,config_sha256 TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS a_trader_coverage(symbol TEXT PRIMARY KEY,revision_id TEXT NOT NULL,bars BLOB NOT NULL,
                origin_ms INTEGER NOT NULL,status TEXT NOT NULL,error TEXT,observed_at TEXT NOT NULL,updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS a_trader_source_receipts(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,revision_id TEXT,
                origin_ms INTEGER NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL,created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS a_trader_assessments(installation_id TEXT NOT NULL,origin_ms INTEGER NOT NULL,
                config_sha256 TEXT NOT NULL,data TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(installation_id,origin_ms));
              CREATE TABLE IF NOT EXISTS a_trader_decisions(id TEXT PRIMARY KEY,installation_id TEXT NOT NULL,symbol TEXT NOT NULL,
                origin_ms INTEGER NOT NULL,role TEXT NOT NULL,status TEXT NOT NULL,reason TEXT NOT NULL,data TEXT NOT NULL,
                intent_id TEXT,created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS a_trader_position_state(installation_id TEXT NOT NULL,symbol TEXT NOT NULL,
                entry_fill_id TEXT NOT NULL,entry_open_ms INTEGER NOT NULL,fill_at TEXT NOT NULL,status TEXT NOT NULL,
                initial_stop_price TEXT,stop_distance TEXT,
                PRIMARY KEY(installation_id,symbol));
              CREATE TABLE IF NOT EXISTS a_trader_exit_obligations(id TEXT PRIMARY KEY,installation_id TEXT NOT NULL,
                symbol TEXT NOT NULL,entry_fill_id TEXT NOT NULL,target_open_ms INTEGER NOT NULL,reason TEXT NOT NULL,
                data TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(installation_id,symbol,entry_fill_id,target_open_ms,reason));
              CREATE TABLE IF NOT EXISTS a_trader_observed_periods(symbol TEXT NOT NULL,opening_ms INTEGER NOT NULL,
                completed_ms INTEGER NOT NULL,observed_at TEXT NOT NULL,revision_id TEXT NOT NULL,PRIMARY KEY(symbol,opening_ms));
              CREATE INDEX IF NOT EXISTS a_trader_decisions_lookup ON a_trader_decisions(installation_id,origin_ms,symbol,role,status);
            """)

    def _rule_module(self):
        return importlib.import_module(".trader_signals", __package__)

    def definitions(self):
        return self._definitions if self._definitions is not None else self._rule_module().DEFINITIONS

    def _source_hash(self):
        if self._definitions is not None:
            return hashlib.sha256(_dump(self._definitions).encode()).hexdigest()
        return hashlib.sha256(Path(self._rule_module().__file__).read_bytes()).hexdigest()

    def verify_rule_assets(self):
        definitions = self.definitions()
        if self._definitions is None:
            module = self._rule_module()
            document = Path(__file__).resolve().parents[1] / "strategies/trader_catalogue/rules-v1.json"
            if not document.is_file() or hashlib.sha256(document.read_bytes()).hexdigest() != module.RULES_DOCUMENT_SHA256:
                raise DeskError("Frozen public rule document is missing or differs from its source identity")
        return {"rule_source_sha256": self._source_hash(), "definition_count": len(definitions)}

    def _verify_config(self, row, *, verify_assets=True):
        try:
            config = json.loads(row["config"])
            if not isinstance(config, dict) or hashlib.sha256(_dump(config).encode()).hexdigest() != row["config_sha256"]:
                raise ValueError()
            definition = self.definitions()[config["rule_id"]]
            if config["id"] != row["id"] or config["sleeve"] != row["sleeve"] or config["book_id"] != row["book_id"]:
                raise ValueError()
            if config["symbols"] != sorted(definition["symbols"]) or config["rule_config"] != definition.get("rule_config", {}) or config["minimum_bars"] != definition["minimum_bars"] or config["max_hold_bars"] != definition.get("max_hold_bars"):
                raise ValueError()
            if config["rule_definition_sha256"] != hashlib.sha256(_dump(definition).encode()).hexdigest():
                raise ValueError()
            fixed = {"frame": "1d", "opening_window_seconds": 300, "maximum_slots": 10,
                     "entry_cap_equity": .10, "entry_cap_native_dv": .01, "history_range": "2y",
                     "missing_data_policy": "require_complete_enrollment",
                     "expected_bar_provider": "fixture" if self._definitions is not None else "yahoo"}
            if any(config.get(key) != value for key, value in fixed.items()) or type(config.get("max_fetch_per_run")) is not int or not 1 <= config["max_fetch_per_run"] <= 16 or row["enabled"] not in (0, 1):
                raise ValueError()
            if verify_assets:
                if config["rule_source_sha256"] != self.verify_rule_assets()["rule_source_sha256"]:
                    raise ValueError()
            return config
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            raise DeskError("Installed public rule configuration or source identity failed verification") from None

    @staticmethod
    def _guard(con, guard):
        if guard is not None:
            try:
                guard(con)
            except Exception as exc:
                setattr(exc, "trader_fence_failure", True)
                raise

    def bind_actions(self, actions):
        self.actions = actions

    def install(self, config):
        if not isinstance(config, dict):
            raise DeskError("Strategy installation must be an object", 422)
        supplied = dict(config)
        supplied.pop("family", None)
        self.verify_rule_assets()
        definitions = self.definitions()
        rule_id = supplied.get("rule_id", supplied.get("strategy_id", supplied.get("sleeve")))
        if rule_id not in definitions:
            raise DeskError("Select a shipped public strategy rule", 422)
        definition = definitions[rule_id]
        rid = supplied.get("id", "trader-" + rule_id)
        if not isinstance(rid, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", rid):
            raise DeskError("Invalid installation identity", 422)
        symbols = definition["symbols"]
        if not isinstance(symbols, list) or not 1 <= len(symbols) <= 40 or len(set(symbols)) != len(symbols):
            raise DeskError("Shipped strategy requires a fixed bounded universe", 422)
        symbols = sorted(symbol(value) for value in symbols)
        if supplied.get("symbols", supplied.get("universe", symbols)) != symbols:
            raise DeskError("Public strategy enrollment is frozen; use its shipped universe", 422)
        rule_config = definition.get("rule_config", {})
        if supplied.get("rule_config", rule_config) != rule_config:
            raise DeskError("Public strategy parameters are frozen", 422)
        enabled = supplied.get("enabled", False)
        budget = supplied.get("max_fetch_per_run", 8)
        if type(enabled) is not bool or type(budget) is not int or not 1 <= budget <= 16:
            raise DeskError("Enabled and bounded acquisition budget are invalid", 422)
        fixed = {"frame": "1d", "opening_window_seconds": 300, "maximum_slots": 10,
                 "entry_cap_equity": .10, "entry_cap_native_dv": .01,
                 "history_range": "2y", "missing_data_policy": "require_complete_enrollment",
                 "expected_bar_provider": "fixture" if self._definitions is not None else "yahoo"}
        for key, value in fixed.items():
            if key in supplied and supplied[key] != value:
                raise DeskError("Public strategy execution contract is frozen: " + key, 422)
        normalized = {**supplied, **fixed, "id": rid, "sleeve": definition["sleeve"],
                      "rule_id": rule_id, "symbols": symbols, "rule_config": rule_config,
                      "enabled": enabled, "max_fetch_per_run": budget,
                      "minimum_bars": definition["minimum_bars"],
                      "max_hold_bars": definition.get("max_hold_bars"),
                      "rule_source_sha256": self._source_hash(),
                      "rule_definition_sha256": hashlib.sha256(_dump(definition).encode()).hexdigest()}
        digest = hashlib.sha256(_dump(normalized).encode()).hexdigest()
        with self.store.transaction() as con:
            existing = con.execute("SELECT * FROM a_trader_installations WHERE id=?", (rid,)).fetchone()
            if existing:
                if existing["config_sha256"] != digest:
                    raise DeskError("Installation identity already binds another frozen configuration")
                return self._installation(con, existing)
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='a_tensor_installations'").fetchone() and con.execute("SELECT 1 FROM a_tensor_installations WHERE id=? OR book_id=?", (rid, normalized.get("book_id"))).fetchone():
                raise DeskError("Installation identity or book belongs to an existing Tensor sleeve")
            book = self.trading._book(con, normalized.get("book_id"))
            policy = json.loads(book["policy"])
            if policy["allow_short"] or Decimal(str(policy["slippage_bps"])) < Decimal(10) or policy["max_fill_quantity"] is not None:
                raise DeskError("Public sleeves require long-only 10bps local policy and no partial-fill setting")
            self.trading.claim_strategy_book(book["id"], rid, con=con)
            stamp = utc_clock().isoformat()
            con.execute("INSERT INTO a_trader_installations VALUES(?,?,?,?,?,?,?,?)",
                        (rid, definition["sleeve"], book["id"], int(enabled), _dump(normalized), digest, stamp, stamp))
            self.store.event(con, "trader_strategy_installed", "operator", "Installed frozen public-rule local paper sleeve",
                             {"installation_id": rid, "rule_id": rule_id, "book_id": book["id"], "config_sha256": digest})
            return self._installation(con, con.execute("SELECT * FROM a_trader_installations WHERE id=?", (rid,)).fetchone())

    def set_enabled(self, installation_id, enabled):
        if type(enabled) is not bool:
            raise DeskError("enabled must be a boolean", 422)
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM a_trader_installations WHERE id=?", (installation_id,)).fetchone()
            if not row:
                raise DeskError("Public-rule installation not found", 404)
            con.execute("UPDATE a_trader_installations SET enabled=?,updated_at=? WHERE id=?",
                        (int(enabled), utc_clock().isoformat(), installation_id))
            self.store.event(con, "trader_strategy_enabled", "operator", "Changed entry enablement; owed exits continue",
                             {"installation_id": installation_id, "enabled": enabled})
            return self._installation(con, con.execute("SELECT * FROM a_trader_installations WHERE id=?", (installation_id,)).fetchone())

    def _installation(self, con, row):
        config = self._verify_config(row)
        definitions = self.definitions()
        definition = definitions.get(config["rule_id"], {})
        coverage = [dict(r) for r in con.execute("SELECT symbol,status,error,origin_ms,updated_at FROM a_trader_coverage WHERE symbol IN (%s) ORDER BY symbol" % ",".join("?" for _ in config["symbols"]), config["symbols"])]
        assessment = con.execute("SELECT data FROM a_trader_assessments WHERE installation_id=? ORDER BY origin_ms DESC LIMIT 1", (row["id"],)).fetchone()
        return {**dict(row), "enabled": bool(row["enabled"]), "config": config, "family": "trader",
                "rule_metadata": definition, "selection": definition.get("selection"), "ranking": definition.get("ranking"),
                "exit": definition.get("exit"), "sizing": "Whole shares; 10% equity, 1% daily dollar-volume and settled-cash caps; maximum ten slots",
                "readiness": {"enrollment_count": len(config["symbols"]), "native_coverage": sum(r["status"] == "ready" for r in coverage),
                              "status": "ready" if coverage and len(coverage) == len(config["symbols"]) and all(r["status"] == "ready" for r in coverage) else "awaiting_complete_native_cycle",
                              "coverage": coverage, "entry_eligibility": json.loads(assessment[0]) if assessment else None},
                "owned_positions": [dict(r) for r in con.execute("SELECT * FROM a_trader_position_state WHERE installation_id=? AND status='held'", (row["id"],))],
                "pending_intents": con.execute(f"SELECT COUNT(*) FROM p_intents WHERE book_id=? AND status IN ({ACTIVE_SQL})", (row["book_id"],)).fetchone()[0],
                "execution": "dedicated local observed quote paper fills; no broker orders"}

    def snapshot(self):
        with self.store.connect() as con:
            con.execute("BEGIN")
            installations = []
            for row in con.execute("SELECT * FROM a_trader_installations ORDER BY id"):
                try:
                    installations.append(self._installation(con, row))
                except DeskError as exc:
                    installations.append({"id": row["id"], "sleeve": row["sleeve"], "book_id": row["book_id"], "enabled": False,
                                          "family": "trader", "config": {}, "config_sha256": row["config_sha256"],
                                          "readiness": {"status": "configuration_integrity_blocked", "error": exc.detail},
                                          "execution": "Local paper execution withheld for this invalid installation"})
            decisions = [{**dict(r), "data": json.loads(r["data"])} for r in con.execute("SELECT * FROM a_trader_decisions ORDER BY rowid DESC LIMIT 200")]
            return {"enabled": any(r["enabled"] for r in installations), "strategy_count": len(installations),
                    "installations": installations, "registry": installations, "decisions": decisions,
                    "definitions": [{"id": key, "rule_id": key, **value, "requires_explicit_installation": True} for key, value in self.definitions().items()],
                    "status": "installed" if installations else "empty", "scope": "Independent public-rule local paper books"}

    @staticmethod
    def _pack(bars):
        return zlib.compress(_dump([asdict(bar) for bar in bars]).encode(), 1)

    @staticmethod
    def _unpack(blob):
        return tuple(NativeBar(**row) for row in json.loads(zlib.decompress(blob)))

    def _record(self, con, install, sym, origin, role, status, reason, data, clock, intent_id=None):
        # Append-only evidence; identical retries do not inflate receipts.
        payload = _dump(data)
        prior = con.execute("SELECT status,reason,data,intent_id FROM a_trader_decisions WHERE installation_id=? AND symbol=? AND origin_ms=? AND role=? ORDER BY rowid DESC LIMIT 1",
                            (install["id"], sym, origin, role)).fetchone()
        if prior and tuple(prior) == (status, reason, payload, intent_id):
            return
        con.execute("INSERT INTO a_trader_decisions VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (identifier(), install["id"], sym, origin, role, status, reason, payload, intent_id, clock.isoformat()))

    def _install_rows(self):
        with self.store.connect() as con:
            rows = list(con.execute("SELECT * FROM a_trader_installations ORDER BY id"))
        valid, errors = [], []
        for row in rows:
            try:
                valid.append({**dict(row), "settings": self._verify_config(row, verify_assets=False)})
            except DeskError as exc:
                errors.append({"installation_id": row["id"], "id": row["id"], "error": exc.detail,
                               "book_id": row["book_id"], "sleeve": row["sleeve"],
                               "stored_config_sha256": row["config_sha256"], "observed_config_sha256": hashlib.sha256(row["config"].encode()).hexdigest()})
        self._invalid_installations = errors
        return valid

    def _integrity_errors(self, clock, guard):
        errors = list(self._invalid_installations)
        if errors:
            with self.store.transaction() as con:
                self._guard(con, guard)
                for error in errors:
                    self._record(con, error, "*", 0, "configuration_integrity", "blocked", error["error"], error, clock)
        return errors

    def _merge(self, con, sym, bars):
        old = con.execute("SELECT bars FROM a_trader_coverage WHERE symbol=?", (sym,)).fetchone()
        prior = self._unpack(old[0]) if old else ()
        if not prior:
            return bars
        known = {bar.timestamp_ms: bar for bar in prior}
        fields = ("open", "high", "low", "close", "volume", "completed_at_ms", "executable_at_ms")
        for bar in bars:
            if bar.timestamp_ms <= prior[-1].timestamp_ms and bar.timestamp_ms not in known:
                raise DeskError("Historical backfill would alter the immutable observed prefix")
            if bar.timestamp_ms in known and any(getattr(known[bar.timestamp_ms], field) != getattr(bar, field) for field in fields):
                raise DeskError("Historical native revision requires explicit source-basis review")
        return prior + tuple(bar for bar in bars if bar.timestamp_ms > prior[-1].timestamp_ms)

    def _acquire(self, symbols, native, clock, guard, providers, budget, *, dynamic_clock=False):
        origin = native["timestamp_ms"]
        with self.store.connect() as con:
            saved = {r["symbol"]: dict(r) for r in con.execute("SELECT * FROM a_trader_coverage")}
        needed = [sym for sym in symbols if sym not in saved or saved[sym]["origin_ms"] != origin or
                  (saved[sym]["status"] != "ready" and (clock - utc_clock(saved[sym]["updated_at"])).total_seconds() >= 30)]
        selected = needed[:budget]
        def fetch(sym):
            try:
                response = providers.bars(sym, "2y", "1d")
                expected = "fixture" if self._definitions is not None else "yahoo"
                if response.get("provider") != expected:
                    raise DeskError("Source provider differs from the frozen public rule data contract")
                identity = {"symbol": sym, "currency": "USD", "instrument_type": "fixture", "source": "Explicit injected fixture"}
                if expected == "yahoo":
                    if not hasattr(providers, "_yahoo"):
                        raise DeskError("Yahoo identity metadata adapter is unavailable")
                    chart = providers._yahoo(sym, "5d", "1d")
                    meta = chart.get("meta") or {}
                    if meta.get("symbol") != sym or meta.get("currency") != "USD" or meta.get("instrumentType") != "ETF" or meta.get("exchangeTimezoneName") != "America/New_York":
                        raise DeskError("Source symbol, USD denomination, ETF identity or exchange timezone is unverified")
                    identity = {"symbol": meta["symbol"], "currency": meta["currency"], "instrument_type": meta["instrumentType"],
                                "exchange_timezone": meta["exchangeTimezoneName"], "exchange_name": meta.get("exchangeName"),
                                "observed_at": utc_clock().isoformat(), "source": "Yahoo public chart metadata GET", "meta": meta}
                _dump(identity)
                return sym, {**response, "trader_identity": identity}, None
            except Exception as exc:
                return sym, None, str(exc)
        with ThreadPoolExecutor(max_workers=min(4, len(selected) or 1)) as pool:
            responses = list(pool.map(fetch, selected))
        result = {"acquired": 0, "errors": []}
        for sym, response, fetch_error in responses:
            decision = utc_clock() if dynamic_clock else clock
            error, bars, diagnostics = fetch_error, (), []
            if not error:
                try:
                    bars = canonical_native_bars(response, "1d", decision, expected_symbol=sym, diagnostics=diagnostics)
                    if bars[-1].completed_at_ms != native["completed_at_ms"] or bars[-1].executable_at_ms != native["executable_at_ms"]:
                        raise DeskError("Source has not observed the latest completed native daily period")
                except Exception as exc:
                    error = str(exc)
            with self.store.transaction() as con:
                self._guard(con, guard)
                if not error:
                    try:
                        bars = self._merge(con, sym, bars)
                    except Exception as exc:
                        error = exc.detail if isinstance(exc, DeskError) else "Stored native history failed strict decoding or prefix validation: " + str(exc)
                revision = response.get("revision_id") if response else None
                con.execute("INSERT INTO a_trader_source_receipts VALUES(?,?,?,?,?,?,?)",
                            (identifier(), sym, revision, origin, "failed" if error else "ready",
                             _dump({"error": error, "diagnostics": diagnostics, "observed_at": response.get("observed_at") if response else None,
                                    "fetched_at": response.get("fetched_at") if response else None,
                                    "provider": response.get("provider") if response else None,
                                    "identity": response.get("trader_identity") if response else None,
                                    "completed_native_bars": len(bars)}), decision.isoformat()))
                if error:
                    old = con.execute("SELECT bars,revision_id,observed_at FROM a_trader_coverage WHERE symbol=?", (sym,)).fetchone()
                    con.execute("INSERT OR REPLACE INTO a_trader_coverage VALUES(?,?,?,?,?,?,?,?)",
                                (sym, old["revision_id"] if old else revision or "unavailable", old["bars"] if old else self._pack(()),
                                 origin, "failed", error, old["observed_at"] if old else decision.isoformat(), decision.isoformat()))
                    result["errors"].append({"symbol": sym, "error": error})
                else:
                    con.execute("INSERT OR REPLACE INTO a_trader_coverage VALUES(?,?,?,?,?,?,?,?)",
                                (sym, revision, self._pack(bars), origin, "ready", None, response["observed_at"], decision.isoformat()))
                    for bar in bars:
                        con.execute("INSERT OR IGNORE INTO a_trader_observed_periods VALUES(?,?,?,?,?)",
                                    (sym, bar.executable_at_ms, bar.completed_at_ms, decision.isoformat(), revision))
                    result["acquired"] += 1
        return result

    def _evaluate(self, install, bars, held, clock):
        config = install["settings"]
        if config["rule_source_sha256"] != self.verify_rule_assets()["rule_source_sha256"]:
            raise DeskError("Installed rule source hash changed; new entries are blocked")
        evaluate = self._evaluator or self._rule_module().evaluate
        kwargs = {"held_symbols": tuple(sorted(held))}
        if self._evaluator is None:
            kwargs["as_of_ms"] = _ms(clock)
        outcome = evaluate(config["rule_id"], bars, config["rule_config"], **kwargs)
        if not isinstance(outcome, dict) or not isinstance(outcome.get("candidates", []), list) or not isinstance(outcome.get("exits", []), list):
            raise DeskError("Strategy evaluator returned an invalid decision contract")
        if self._evaluator is None and any(outcome.get("diagnostics", {}).get(sym, {}).get("status") != "ready" for sym in bars):
            raise DeskError("Frozen native indicator diagnostics are not ready for every supplied source")
        for candidate in outcome.get("candidates", []):
            if candidate.get("symbol") not in config["symbols"] or any(not math.isfinite(float(candidate[key])) for key in ("score", "dollar_volume20")) or candidate["dollar_volume20"] <= 0:
                raise DeskError("Strategy candidate has invalid symbol, rank or native liquidity")
        if len({v["symbol"] for v in outcome.get("candidates", [])}) != len(outcome.get("candidates", [])):
            raise DeskError("Strategy evaluator returned duplicate candidates")
        if any(v.get("symbol") not in held or not isinstance(v.get("reason"), str) or not v["reason"] for v in outcome.get("exits", [])):
            raise DeskError("Strategy evaluator returned an invalid owned exit")
        _dump(outcome)
        return outcome

    def _assess(self, install, native, clock, guard):
        origin = native["timestamp_ms"]
        with self.store.transaction() as con:
            self._guard(con, guard)
            self._bind_fills(con, install)
            current = con.execute("SELECT * FROM a_trader_installations WHERE id=?", (install["id"],)).fetchone()
            self._verify_config(current)
            coverage = {r["symbol"]: r for r in con.execute("SELECT * FROM a_trader_coverage")}
            bars = {}
            bindings = {}
            for sym in install["settings"]["symbols"]:
                value = coverage.get(sym)
                if not value or value["status"] != "ready" or value["origin_ms"] != origin:
                    return None
                bars[sym] = self._unpack(value["bars"])
                if len(bars[sym]) < install["settings"]["minimum_bars"] or max(bar.usable_at_ms for bar in bars[sym]) > _ms(clock) or max(bar.completed_at_ms for bar in bars[sym]) > _ms(clock):
                    return None
                if bars[sym][-1].completed_at_ms != native["completed_at_ms"] or bars[sym][-1].executable_at_ms != native["executable_at_ms"]:
                    return None
                bindings[sym] = {"revision_id": value["revision_id"], "bars_sha256": hashlib.sha256(value["bars"]).hexdigest(), "bar_count": len(bars[sym]), "origin_ms": origin}
            existing = con.execute("SELECT * FROM a_trader_assessments WHERE installation_id=? AND origin_ms=?", (install["id"], origin)).fetchone()
            if existing:
                outcome = json.loads(existing["data"])
                if outcome.get("coverage_bindings") != bindings or existing["config_sha256"] != install["config_sha256"]:
                    raise DeskError("Immutable assessment differs from its current strict census binding")
                return outcome
            held = {r["symbol"] for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (install["book_id"],)) if Decimal(r["quantity"]) > 0}
            outcome = self._evaluate(install, bars, held, clock)
            outcome.update(origin_ms=origin, next_open_ms=native["next_open_ms"], expires_ms=native["next_open_ms"] + 300000,
                           census={"attempted": len(bars), "ready": len(bars), "required": len(bars), "complete": True},
                           config_sha256=install["config_sha256"], assessed_at=clock.isoformat(), coverage_bindings=bindings)
            outcome["candidates"] = sorted(outcome.get("candidates", []), key=lambda v: tuple(v["rank_key"]) if "rank_key" in v else (-v["score"], v["symbol"]))
            con.execute("INSERT INTO a_trader_assessments VALUES(?,?,?,?,?)",
                        (install["id"], origin, install["config_sha256"], _dump(outcome), clock.isoformat()))
            self._record(con, install, "*", origin, "assessment", "ready", "complete_native_census", outcome, clock)
            for request in outcome.get("exits", []):
                state = con.execute("SELECT * FROM a_trader_position_state WHERE installation_id=? AND symbol=? AND status='held'", (install["id"], request["symbol"])).fetchone()
                if state:
                    self._owe_exit(con, install, state, native["next_open_ms"], request["reason"], {"signal_origin_ms": origin, "rule_exit": request}, clock)
            return outcome

    def _entry(self, con, install, candidate, assessment, clock, guard):
        sym, origin = candidate["symbol"], assessment["origin_ms"]
        prior = con.execute("SELECT 1 FROM a_trader_decisions WHERE installation_id=? AND symbol=? AND origin_ms=? AND role='entry' AND status IN ('queued','denied','expired')", (install["id"], sym, origin)).fetchone()
        if prior:
            return 0
        try:
            current = con.execute("SELECT * FROM a_trader_installations WHERE id=?", (install["id"],)).fetchone()
            if not current["enabled"] or current["config_sha256"] != install["config_sha256"]:
                return 0
            self._verify_config(current)
            if assessment.get("config_sha256") != install["config_sha256"]:
                raise DeskError("Assessment configuration binding differs from its installation")
            for name in install["settings"]["symbols"]:
                covered = con.execute("SELECT * FROM a_trader_coverage WHERE symbol=?", (name,)).fetchone()
                expected = assessment.get("coverage_bindings", {}).get(name)
                if not covered or covered["status"] != "ready" or covered["origin_ms"] != origin or not expected or covered["revision_id"] != expected["revision_id"] or hashlib.sha256(covered["bars"]).hexdigest() != expected["bars_sha256"]:
                    raise DeskError("Current complete native census no longer binds the immutable assessment")
                native_bars = self._unpack(covered["bars"])
                if len(native_bars) < install["settings"]["minimum_bars"] or max(bar.usable_at_ms for bar in native_bars) > _ms(clock) or max(bar.completed_at_ms for bar in native_bars) > _ms(clock):
                    raise DeskError("Current native census contains unavailable causal rows")
            held = {r["symbol"] for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (install["book_id"],)) if Decimal(r["quantity"]) > 0}
            pending = {r[0] for r in con.execute(f"SELECT symbol FROM p_intents WHERE book_id=? AND side='buy' AND status IN ({ACTIVE_SQL})", (install["book_id"],))}
            if sym in held | pending:
                raise DeskError("already_held_or_pending")
            if len(held | pending) >= 10:
                raise DeskError("maximum_ten_slots_including_pending")
            if con.execute(f"SELECT 1 FROM p_intents WHERE book_id=? AND side='sell' AND status IN ({ACTIVE_SQL})", (install["book_id"],)).fetchone():
                self._record(con, install, sym, origin, "entry_coverage", "deferred", "awaiting_owned_exit_fills", candidate, clock)
                return 0
            quote = self.trading._raw_quote(con, sym, clock)
            if _ms(quote["as_of"]) < assessment["next_open_ms"]:
                raise DeskError("Quote precedes the next eligible opening")
            book = self.trading._book(con, install["book_id"])
            account, positions = self.trading._account(con, book, clock)
            if account["missing_marks"] or account["stale_marks"]:
                raise DeskError("Fresh complete owned position marks are required")
            policy = json.loads(book["policy"])
            if policy["allow_short"] or Decimal(str(policy["slippage_bps"])) < 10 or policy["max_fill_quantity"] is not None:
                raise DeskError("Paper book long-only 10bps/no-partial policy changed")
            equity = Decimal(account["exact_equity_cents"]) / 100
            cash = Decimal(self.trading.strategy_cash(con, book["id"], clock)["available_cents"]) / 100
            cap = min(equity * Decimal(".10"), Decimal(str(candidate["dollar_volume20"])) * Decimal(".01"), cash)
            fee = Decimal(str(policy["fees_per_order"]))
            effective = Decimal(quote["price"]) * (1 + Decimal(str(policy["slippage_bps"])) / 10000)
            shares = int(((cap - fee) / effective).to_integral_value(rounding=ROUND_FLOOR)) if cap > fee else 0
            stop_distance = candidate.get("stop_distance")
            risk_fraction = candidate.get("risk_budget_fraction")
            if stop_distance is not None or risk_fraction is not None:
                if not math.isfinite(float(stop_distance)) or float(stop_distance) <= 0 or risk_fraction != .005:
                    raise DeskError("Frozen initial ATR risk budget is invalid")
                risk_shares = int((equity * Decimal(".005") / Decimal(str(stop_distance))).to_integral_value(rounding=ROUND_FLOOR))
                shares = min(shares, risk_shares)
            if shares < 1:
                raise DeskError("whole_share_cash_or_native_liquidity_cap")
            client = "trader-" + hashlib.sha256(f"{install['id']}|{origin}|{sym}|buy".encode()).hexdigest()[:48]
            payload = {"book_id": book["id"], "symbol": sym, "side": "buy", "quantity": shares, "client_id": client,
                       "order_type": "market", "time_in_force": "day", "not_before": _dt(assessment["next_open_ms"]).isoformat(),
                       "expires_at": _dt(assessment["expires_ms"]).isoformat(), "sleeve": install["sleeve"],
                       "max_debit_cents": int((cap * 100).to_integral_value(rounding=ROUND_FLOOR)),
                       "reason": candidate.get("reason", "Frozen deterministic public trading rule")}
            intent = self.trading.submit_strategy_intent(payload, install["id"], con=con, clock=clock,
                         transaction_guard=lambda writer: self._guard(writer, guard))
            self._record(con, install, sym, origin, "entry", "queued", "ranked_funded_opportunity",
                         {**candidate, "rank": next(i for i,v in enumerate(assessment["candidates"], 1) if v["symbol"] == sym),
                          "sizing": {"shares": shares, "debit_cap": str(cap), "quote_price": quote["price"], "available_cash": str(cash)}}, clock, intent["id"])
            return 1
        except DeskError as exc:
            if getattr(exc, "trader_fence_failure", False) or getattr(exc, "paused", False):
                raise
            transient = any(text in exc.detail.lower() for text in ("quote", "timestamped", "corporate action", "marks", "halt", "drawdown", "cash", "policy changed", "native census", "causal rows"))
            self._record(con, install, sym, origin, "entry_coverage" if transient else "entry", "deferred" if transient else "denied", exc.detail, candidate, clock)
            return 0

    def _bind_fills(self, con, install):
        fills = list(con.execute("SELECT f.* FROM p_fills f JOIN p_intents i ON i.id=f.intent_id WHERE f.book_id=? AND f.side='buy' AND i.sleeve=? ORDER BY f.rowid", (install["book_id"], install["sleeve"])))
        first_per_intent = {}
        latest_by_symbol = {}
        for fill in fills:
            first_per_intent.setdefault(fill["intent_id"], fill)
            latest_by_symbol[fill["symbol"]] = first_per_intent[fill["intent_id"]]
        for fill in latest_by_symbol.values():
            existing = con.execute("SELECT entry_fill_id FROM a_trader_position_state WHERE installation_id=? AND symbol=?", (install["id"], fill["symbol"])).fetchone()
            if existing and existing[0] == fill["id"]:
                continue
            stamp = utc_clock(fill["timestamp"] or fill["observed_at"])
            bounds = _session(stamp.astimezone(NY).date().isoformat())
            if not bounds or not bounds[0] <= _ms(stamp) < bounds[1]:
                raise DeskError("Strategy entry fill is outside an actual exchange session")
            decision = con.execute("SELECT data FROM a_trader_decisions WHERE installation_id=? AND intent_id=? AND role='entry' AND status='queued' ORDER BY rowid LIMIT 1", (install["id"], fill["intent_id"])).fetchone()
            distance = json.loads(decision[0]).get("stop_distance") if decision else None
            stop = Decimal(fill["price"]) - Decimal(str(distance)) if distance is not None else None
            con.execute("INSERT OR REPLACE INTO a_trader_position_state VALUES(?,?,?,?,?,?,?,?)",
                        (install["id"], fill["symbol"], fill["id"], bounds[0], stamp.isoformat(), "held",
                         str(max(Decimal(0), stop)) if stop is not None else None, str(distance) if distance is not None else None))

    def prepare_fills(self, clock=None, transaction_guard=None):
        """No-network preflight before supervisor fill boundaries.

        A first measured partial is retained, with its actual-fill stop anchor;
        its unfilled remainder is cancelled before another supervisor fill can
        move average cost away from that immutable initial stop.
        """
        decision, count, safe = utc_clock(clock), 0, True
        installs = self._install_rows()
        for install in installs:
            with self.store.transaction() as con:
                self._guard(con, transaction_guard)
                self._bind_fills(con, install)
                book = self.trading._book(con, install["book_id"])
                partial_policy = json.loads(book["policy"])["max_fill_quantity"] is not None
                for intent in list(con.execute(f"SELECT * FROM p_intents WHERE book_id=? AND side='buy' AND status IN ({ACTIVE_SQL})", (book["id"],))):
                    measured = Decimal(intent["filled_quantity"]) > 0
                    if measured or partial_policy:
                        reason = "Measured first partial: cancelled remainder to preserve frozen initial-stop risk" if measured else "Partial-fill policy changed after admission: entry cancelled before local fill"
                        con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=?,error=? WHERE id=?",
                                    (decision.isoformat(), decision.isoformat(), reason, intent["id"]))
                        self._record(con, install, intent["symbol"], _ms(intent["created_at"]), "entry_remainder", "cancelled", reason,
                                     {"intent_id": intent["id"], "filled_quantity": intent["filled_quantity"], "authorized_quantity": intent["quantity"], "partial_policy": partial_policy}, decision, intent["id"])
                        self.store.event(con, "trader_entry_remainder_cancelled", "strategy", reason, {"installation_id": install["id"], "intent_id": intent["id"], "filled_quantity": intent["filled_quantity"]})
                        count += 1
        # An invalid scientific configuration cannot leave an active entry for
        # the shared execution clerk. Ownership supplies the original book
        # identity; uncertain configuration fields never select another book.
        for invalid in self._invalid_installations:
            with self.store.transaction() as con:
                self._guard(con, transaction_guard)
                owner = con.execute("SELECT * FROM a_strategy_ownership WHERE installation_id=?", (invalid["id"],)).fetchone()
                if not owner:
                    safe = False
                    continue
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='a_tensor_installations'").fetchone() and con.execute("SELECT 1 FROM a_tensor_installations WHERE book_id=?", (owner["book_id"],)).fetchone():
                    safe = False
                    continue
                book = self.trading._book(con, owner["book_id"])
                if book["broker"] != "local":
                    safe = False
                    continue
                for intent in list(con.execute(f"SELECT * FROM p_intents WHERE book_id=? AND side='buy' AND status IN ({ACTIVE_SQL})", (book["id"],))):
                    reason = "Invalid public rule configuration: cancelled uncertain new exposure"
                    con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=?,error=? WHERE id=?",
                                (decision.isoformat(), decision.isoformat(), reason, intent["id"]))
                    self._record(con, invalid, intent["symbol"], 0, "invalid_configuration_entry_quarantine", "cancelled", reason,
                                 {"intent_id": intent["id"], "owned_book_id": book["id"], "filled_quantity": intent["filled_quantity"]}, decision, intent["id"])
                    self.store.event(con, "trader_invalid_entry_quarantined", "strategy", reason, {"installation_id": invalid["id"], "book_id": book["id"], "intent_id": intent["id"]})
                    count += 1
                safe = safe and not con.execute(f"SELECT 1 FROM p_intents WHERE book_id=? AND side='buy' AND status IN ({ACTIVE_SQL})", (book["id"],)).fetchone()
        return {"status": "data_blocked" if self._invalid_installations else "ok", "cancelled": count,
                "fills_safe": bool(safe), "errors": self._integrity_errors(decision, transaction_guard)}

    def _owe_exit(self, con, install, state, target, reason, data, clock):
        if con.execute("SELECT 1 FROM a_trader_exit_obligations WHERE installation_id=? AND symbol=? AND entry_fill_id=? AND reason=? LIMIT 1", (install["id"], state["symbol"], state["entry_fill_id"], reason)).fetchone():
            return
        con.execute("INSERT OR IGNORE INTO a_trader_exit_obligations VALUES(?,?,?,?,?,?,?,?)",
                    (identifier(), install["id"], state["symbol"], state["entry_fill_id"], target, reason, _dump(data), clock.isoformat()))

    def _time_exits(self, con, install, clock):
        maximum = install["settings"].get("max_hold_bars")
        if maximum is None:
            return
        for state in con.execute("SELECT * FROM a_trader_position_state WHERE installation_id=? AND status='held'", (install["id"],)):
            observed = list(con.execute("SELECT * FROM a_trader_observed_periods WHERE symbol=? AND opening_ms>=? AND completed_ms<=? AND observed_at<=? ORDER BY opening_ms", (state["symbol"], state["entry_open_ms"], _ms(clock), clock.isoformat())))
            if len(observed) >= maximum and observed[0]["opening_ms"] == state["entry_open_ms"]:
                self._owe_exit(con, install, state, _next_open("1d", observed[maximum - 1]["completed_ms"]), "maximum_observed_hold_bars",
                               {"observed_hold_bars": len(observed), "maximum": maximum}, clock)

    def _rule_exits(self, con, install, clock):
        """Held-name exit science is independent of the broad entry census."""
        native = latest_native_clock("1d", clock)
        for state in list(con.execute("SELECT * FROM a_trader_position_state WHERE installation_id=? AND status='held'", (install["id"],))):
            sym, origin = state["symbol"], native["timestamp_ms"]
            position = self.trading._position(con, install["book_id"], sym)
            if not position or Decimal(position["quantity"]) <= 0:
                continue
            coverage = con.execute("SELECT * FROM a_trader_coverage WHERE symbol=?", (sym,)).fetchone()
            try:
                if not coverage or coverage["status"] != "ready" or coverage["origin_ms"] != origin:
                    raise DeskError("Own held symbol has no current healthy causal native source")
                bars = self._unpack(coverage["bars"])
                if len(bars) < install["settings"]["minimum_bars"] or max(bar.usable_at_ms for bar in bars) > _ms(clock) or max(bar.completed_at_ms for bar in bars) > _ms(clock) or bars[-1].completed_at_ms != native["completed_at_ms"] or bars[-1].executable_at_ms != native["executable_at_ms"]:
                    raise DeskError("Own held symbol source is incomplete or not yet causal")
                binding = {"entry_fill_id": state["entry_fill_id"], "revision_id": coverage["revision_id"], "bars_sha256": hashlib.sha256(coverage["bars"]).hexdigest(), "origin_ms": origin}
                prior = con.execute("SELECT data FROM a_trader_decisions WHERE installation_id=? AND symbol=? AND origin_ms=? AND role='held_exit_assessment' AND status='ready' ORDER BY rowid DESC LIMIT 1", (install["id"], sym, origin)).fetchone()
                if prior and json.loads(prior[0]).get("binding") == binding:
                    continue
                outcome = self._evaluate(install, {sym: bars}, {sym}, clock)
                data = {"binding": binding, "exits": outcome.get("exits", []), "diagnostics": outcome.get("diagnostics", {}), "held_only": True, "full_entry_census_required": False}
                self._record(con, install, sym, origin, "held_exit_assessment", "ready", "own_healthy_native_source", data, clock)
                for request in outcome.get("exits", []):
                    self._owe_exit(con, install, state, native["next_open_ms"], request["reason"],
                                   {"signal_origin_ms": origin, "rule_exit": request, "own_source_binding": binding, "held_only": True}, clock)
            except Exception as exc:
                if getattr(exc, "trader_fence_failure", False) or getattr(exc, "paused", False):
                    raise
                self._record(con, install, sym, origin, "held_exit_assessment", "deferred",
                             exc.detail if isinstance(exc, DeskError) else "Held source or rule evaluation failed: " + str(exc),
                             {"held_only": True, "entry_fill_id": state["entry_fill_id"]}, clock)

    def _opening(self, clock):
        bounds = _session(clock.astimezone(NY).date().isoformat())
        return bounds[0] if bounds and bounds[0] <= _ms(clock) < bounds[0] + 300000 else None

    def _exits(self, install, clock, guard):
        count = 0
        with self.store.transaction() as con:
            self._guard(con, guard)
            self._bind_fills(con, install)
            self._time_exits(con, install, clock)
            self._rule_exits(con, install, clock)
            states = list(con.execute("SELECT * FROM a_trader_position_state WHERE installation_id=? AND status='held'", (install["id"],)))
            for state in states:
                pos = self.trading._position(con, install["book_id"], state["symbol"])
                if not pos or Decimal(pos["quantity"]) <= 0:
                    con.execute("UPDATE a_trader_position_state SET status='closed' WHERE installation_id=? AND symbol=?", (install["id"], state["symbol"]))
                    continue
                # Initial stop is measured from the actual first fill. A fresh
                # observed quote can trigger risk reduction throughout the
                # regular session; candle highs/lows never imply a stop fill.
                if state["initial_stop_price"] is not None:
                    bounds = _session(clock.astimezone(NY).date().isoformat())
                    if bounds and bounds[0] <= _ms(clock) < bounds[1]:
                        try:
                            observed = self.trading._raw_quote(con, state["symbol"], clock)
                            current_stop = split_mark_price(con, install["book_id"], state["symbol"], state["initial_stop_price"], state["fill_at"])
                            current_quote = split_mark_price(con, install["book_id"], state["symbol"], observed["price"], observed["as_of"])
                            if _ms(observed["as_of"]) >= bounds[0] and current_quote <= current_stop:
                                self._owe_exit(con, install, state, _ms(clock), "observed_initial_atr_stop",
                                               {"original_stop_price": state["initial_stop_price"], "current_unit_stop_price": str(current_stop),
                                                "current_unit_observed_price": str(current_quote), "entry_fill_at": state["fill_at"],
                                                "observed_price": observed["price"], "quote_as_of": observed["as_of"]}, clock)
                        except DeskError:
                            pass
                owed = con.execute("SELECT * FROM a_trader_exit_obligations WHERE installation_id=? AND symbol=? AND entry_fill_id=? AND target_open_ms<=? ORDER BY (reason='observed_initial_atr_stop') DESC,target_open_ms,rowid LIMIT 1", (install["id"], state["symbol"], state["entry_fill_id"], _ms(clock))).fetchone()
                if not owed:
                    continue
                # Cancel every old unfilled entry remainder before risk reduction.
                for pending in list(con.execute(f"SELECT * FROM p_intents WHERE book_id=? AND symbol=? AND side='buy' AND status IN ({ACTIVE_SQL})", (install["book_id"], state["symbol"]))):
                    con.execute("UPDATE p_intents SET status='cancelled',reserved_cents=0,reserved_quantity='0',completed_at=?,updated_at=?,error='Owned strategy exit became owed' WHERE id=?", (clock.isoformat(), clock.isoformat(), pending["id"]))
                    self.store.event(con, "trader_entry_remainder_cancelled", "strategy", "Cancelled entry remainder before owned exit", {"intent_id": pending["id"], "installation_id": install["id"]})
                stopped = owed["reason"] == "observed_initial_atr_stop"
                bounds = _session(clock.astimezone(NY).date().isoformat())
                opening = max(bounds[0], owed["target_open_ms"]) if stopped and bounds and bounds[0] <= _ms(clock) < bounds[1] else self._opening(clock)
                if opening is None or con.execute(f"SELECT 1 FROM p_intents WHERE book_id=? AND symbol=? AND side='sell' AND status IN ({ACTIVE_SQL})", (install["book_id"], state["symbol"])).fetchone():
                    continue
                try:
                    quote = self.trading._raw_quote(con, state["symbol"], clock)
                    if _ms(quote["as_of"]) < opening:
                        raise DeskError("Exit quote precedes the actual opening")
                    client = "trader-" + hashlib.sha256(f"{install['id']}|{state['entry_fill_id']}|{opening}|sell".encode()).hexdigest()[:48]
                    payload = {"book_id": install["book_id"], "symbol": state["symbol"], "side": "sell", "quantity": str(Decimal(pos["quantity"])),
                               "client_id": client, "order_type": "market", "time_in_force": "day", "not_before": _dt(opening).isoformat(),
                               "expires_at": _dt(bounds[1] if stopped else opening + 300000).isoformat(), "sleeve": install["sleeve"], "reason": owed["reason"]}
                    intent = self.trading.submit_strategy_intent(payload, install["id"], con=con, clock=clock,
                                  transaction_guard=lambda writer: self._guard(writer, guard))
                    self._record(con, install, state["symbol"], opening, "exit", "queued", owed["reason"],
                                 {"entry_fill_id": state["entry_fill_id"], "target_open_ms": owed["target_open_ms"], "actual_open_ms": opening,
                                  "overdue": opening > owed["target_open_ms"]}, clock, intent["id"])
                    count += 1
                except DeskError as exc:
                    if getattr(exc, "trader_fence_failure", False) or getattr(exc, "paused", False):
                        raise
                    self._record(con, install, state["symbol"], opening, "exit_coverage", "deferred", exc.detail, {"target_open_ms": owed["target_open_ms"]}, clock)
        return count

    def _refresh(self, symbols, providers):
        errors = []
        if hasattr(providers, "refresh") and symbols:
            def refresh(sym):
                try:
                    result = providers.refresh([sym])
                    return result.get("errors", []) if isinstance(result, dict) else []
                except Exception as exc:
                    if getattr(exc, "trader_fence_failure", False) or getattr(exc, "tensor_fence_failure", False) or getattr(exc, "paused", False):
                        raise
                    return [{"symbol": sym, "error": "Observed quote acquisition failed: " + str(exc)}]
            with ThreadPoolExecutor(max_workers=min(4, len(symbols))) as pool:
                for result in pool.map(refresh, sorted(set(symbols))[:40]):
                    errors.extend(result)
        return errors

    def service_exits(self, clock=None, transaction_guard=None, providers=None, *, acquire_native_clocks=True):
        if not self._mutex.acquire(blocking=False):
            return {"status": "busy", "exits": 0, "observed_periods": 0, "errors": []}
        try:
            dynamic, decision = clock is None, utc_clock(clock)
            self.prepare_fills(decision, transaction_guard)
            source = providers or self.providers
            installs = self._install_rows()
            result = {"status": "empty" if not installs else "ok", "exits": 0, "observed_periods": 0, "errors": self._integrity_errors(decision, transaction_guard)}
            with self.store.connect() as con:
                owned = sorted({r["symbol"] for install in installs for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (install["book_id"],)) if Decimal(r["quantity"]) > 0})
            if acquire_native_clocks and owned:
                acquired = self._acquire(owned, latest_native_clock("1d", decision), decision, transaction_guard, source, 16, dynamic_clock=dynamic)
                result["observed_periods"] = acquired["acquired"]
                result["errors"].extend(acquired["errors"])
            if self._opening(decision) is not None:
                result["errors"].extend(self._refresh(owned, source))
                if self.actions is not None and owned:
                    self.actions.probe_symbols(owned, clock=None if dynamic else decision, fence=transaction_guard, max_symbols=min(40, len(owned)))
            if dynamic:
                decision = utc_clock()
            for install in installs:
                result["exits"] += self._exits(install, decision, transaction_guard)
            if result["errors"]:
                result["status"] = "data_blocked"
            self.prepare_fills(None if dynamic else decision, transaction_guard)
            return result
        finally:
            self._mutex.release()

    def run_once(self, clock=None, transaction_guard=None, providers=None, *, allow_acquisition=True):
        if type(allow_acquisition) is not bool:
            raise DeskError("allow_acquisition must be a boolean", 422)
        if not self._mutex.acquire(blocking=False):
            return {"status": "busy", "acquired": 0, "entries": 0, "exits": 0, "errors": []}
        try:
            dynamic, decision = clock is None, utc_clock(clock)
            self.prepare_fills(decision, transaction_guard)
            source, installs = providers or self.providers, self._install_rows()
            result = {"status": "empty" if not installs else "ok", "acquired": 0, "entries": 0, "exits": 0, "errors": self._integrity_errors(decision, transaction_guard)}
            if not installs:
                if result["errors"]:
                    result["status"] = "data_blocked"
                return result
            native = latest_native_clock("1d", decision)
            universe = sorted({sym for install in installs for sym in install["settings"]["symbols"]})
            if allow_acquisition:
                acquired = self._acquire(universe, native, decision, transaction_guard, source, max(i["settings"]["max_fetch_per_run"] for i in installs), dynamic_clock=dynamic)
                result.update(acquired=acquired["acquired"])
                result["errors"].extend(acquired["errors"])
            if dynamic:
                decision = utc_clock()
                native = latest_native_clock("1d", decision)
            assessments = []
            for install in installs:
                try:
                    outcome = self._assess(install, native, decision, transaction_guard)
                except DeskError as exc:
                    if getattr(exc, "trader_fence_failure", False) or getattr(exc, "paused", False):
                        raise
                    result["errors"].append({"installation_id": install["id"], "error": exc.detail})
                    continue
                if outcome is not None:
                    assessments.append((install, outcome))
                else:
                    result["status"] = "collecting"
            active = [(install, outcome) for install, outcome in assessments if outcome["next_open_ms"] <= _ms(decision) < outcome["expires_ms"]]
            with self.store.connect() as con:
                owned = {r["symbol"] for install in installs for r in con.execute("SELECT * FROM p_positions WHERE book_id=?", (install["book_id"],)) if Decimal(r["quantity"]) > 0}
            targets = sorted(owned | {candidate["symbol"] for install, outcome in active if install["enabled"] for candidate in outcome["candidates"]})
            if active:
                result["errors"].extend(self._refresh(targets, source))
                if self.actions is not None and targets:
                    self.actions.probe_symbols(targets, clock=None if dynamic else decision, fence=transaction_guard, max_symbols=min(40, len(targets)))
                if dynamic:
                    decision = utc_clock()
            for install in installs:
                result["exits"] += self._exits(install, decision, transaction_guard)
            for install, outcome in assessments:
                with self.store.transaction() as con:
                    self._guard(con, transaction_guard)
                    for candidate in outcome["candidates"]:
                        if _ms(decision) >= outcome["expires_ms"]:
                            self._record(con, install, candidate["symbol"], outcome["origin_ms"], "entry", "expired", "next_opening_window_missed_no_replay", candidate, decision)
                        elif _ms(decision) >= outcome["next_open_ms"]:
                            result["entries"] += self._entry(con, install, candidate, outcome, decision, transaction_guard)
            if result["errors"]:
                result["status"] = "data_blocked"
            self.prepare_fills(None if dynamic else decision, transaction_guard)
            return result
        finally:
            self._mutex.release()


TraderRuntime = TraderRuntimeManager
