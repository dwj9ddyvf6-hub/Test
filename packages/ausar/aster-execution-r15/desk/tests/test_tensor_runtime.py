import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import gzip
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
import zlib
from unittest.mock import patch

from backend.providers import exchange_calendar
from backend.store import DeskError, Store
from backend.tensor_engine import NativeBar
from backend.tensor_runtime import TensorRuntime, canonical_native_bars, historical_state_cooldown, latest_native_clock, _native_period, _next_open, _sessions, _session, _ms, _dt
from backend.trading import TradingDesk

UTC = timezone.utc
CLOCK = datetime(2026, 10, 9, 14, 30, 2, tzinfo=UTC)
PIN = "f" * 64


def native_history(frame="1h", clock=CLOCK, count=234):
    latest = latest_native_clock(frame, clock)
    local = clock.date()
    days = _sessions((local - timedelta(days=2500 if frame == "1wk" else 900)).isoformat(), local.isoformat())
    result = []
    if frame == "1wk":
        mondays = sorted({datetime.fromisoformat(day).date() - timedelta(days=datetime.fromisoformat(day).weekday()) for day in days})
        stamps = [_ms(datetime.combine(day, datetime.min.time(), UTC)) for day in mondays]
    elif frame == "1d":
        stamps = [_ms(datetime.combine(datetime.fromisoformat(day).date(), datetime.min.time(), UTC)) for day in days]
    else:
        stamps = []
        for day in days:
            opened, closed = _session(day)
            stamps.extend(range(opened, closed, 3_600_000))
    for stamp in stamps:
        opened, complete = _native_period(stamp, frame)
        if complete <= latest["completed_at_ms"]:
            result.append({"timestamp": _dt(stamp).isoformat(), "open": 10., "high": 11., "low": 9., "close": 10., "volume": 2_000_000.})
    return result[-count:]


def revision(sym="AAA", frame="1h", clock=CLOCK, count=234):
    bars = native_history(frame, clock, count)
    return {"symbol": sym, "interval": {"1h": "60m", "1d": "1d", "1wk": "1wk"}[frame],
            "provider": "fixture", "source": "Immutable observed OHLCV fixture", "adjustment": "raw OHLC",
            "vendor_interval": {"1h": "60m", "1d": "1d", "1wk": "1wk"}[frame], "bars": bars,
            "revision_id": "a" * 64, "content_sha256": "a" * 64,
            "observed_at": clock.isoformat(), "fetched_at": clock.isoformat(), "provider_asof": bars[-1]["timestamp"],
            "truncated": False, "omitted_rows": 0, "stale_cache": False,
            "completeness": {"status": "complete_vendor_response"}}


class FixtureProviders:
    kind = "fixture"
    broker = None
    brokers = {}

    def __init__(self, symbols=("AAA",), frame="1h", clock=CLOCK, count=234):
        self.data = {(frame, sym): revision(sym, frame, clock, count) for sym in symbols}
        self.calls = []
        self.fail = set()

    def bars(self, sym, period, interval):
        frame = {"60m": "1h", "1d": "1d", "1wk": "1wk"}[interval]
        self.calls.append((sym, period, interval))
        if sym in self.fail:
            raise RuntimeError("Provider unavailable")
        return copy.deepcopy(self.data[(frame, sym)])

    def calendar(self, clock=None):
        return exchange_calendar(clock)


def extract(sym, frame, bars, clock_ms):
    return SimpleNamespace(snapshot=SimpleNamespace(source_manifest_sha256=PIN, bars=bars), rows=())


class FixturePolicy:
    def __init__(self, frame, pin):
        self.frame = frame

    def evaluate(self, sym, snapshot, *, as_of_ms, next_eligible_bar_index=None):
        i = len(snapshot.bars) - 1
        if next_eligible_bar_index is not None and i < next_eligible_bar_index:
            return SimpleNamespace(signal=None, reason="cooldown")
        return SimpleNamespace(signal={"symbol": sym, "origin_bar_index": i, "score": float(ord(sym[0])),
                    "next_eligible_bar_index": i + 20, "dollar_volume20": 20_000_000,
                    "close": 10, "decision_at_ms": snapshot.bars[-1].usable_at_ms}, reason="selected")


class TensorRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "desk.sqlite")
        self.trading = TradingDesk(self.store)
        self.providers = FixtureProviders()
        self.runtime = TensorRuntime(self.store, self.trading, self.providers, feature_extractor=extract, policy_factory=FixturePolicy)

    def tearDown(self):
        self.temp.cleanup()

    def install(self, sleeve="H1STATE", symbols=None, enabled=True, budget=16, key=None, **config):
        book = self.trading.create_book({"name": key or sleeve, "broker": "local", "kind": "forward"})
        self.trading.fund_book(book["id"], 100_000, "fixture-funding")
        self.trading.set_book(book["id"], {"policy": {"slippage_bps": 10}})
        row = self.runtime.install({"id": key or sleeve, "sleeve": sleeve, "book_id": book["id"],
                    "symbols": symbols or ["AAA"], "enabled": enabled, "max_fetch_per_run": budget, **config})
        return row

    def quote(self, sym="AAA", price=10, clock=CLOCK):
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)", (sym, str(price), clock.isoformat(), "Observed intraday fixture trade"))

    def test_constructor_preserves_empty_registry_and_no_funding(self):
        self.assertEqual(self.runtime.snapshot()["strategy_count"], 0)
        self.assertEqual(self.runtime.run_once(CLOCK)["status"], "empty")
        self.assertEqual(self.trading.snapshot()["books"][0]["account"]["cash"], 0)

    def test_fast_coverage_codec_preserves_every_value_and_native_input_identity(self):
        from backend.tensor_engine import _bar_payload, _normalize_bars
        original = canonical_native_bars(self.providers.data[("1h", "AAA")], "1h", CLOCK)
        # Exercise actual binary float representations, integer zero volume,
        # and conservative nonintegral-second knowledge-time receipts.
        records = [dict(vars(bar)) for bar in original]
        for i, row in enumerate(records):
            row.update(open=10.000000000000002 + i / 10000, high=11.125, low=9.0625,
                       close=10.000000000000004 + i / 10000, volume=0 if i == 0 else 1234567.125,
                       usable_at_ms=row["usable_at_ms"] - 1)
        bars = tuple(NativeBar(**row) for row in records)
        legacy = zlib.compress(json.dumps(records, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), 6)
        current = self.runtime._pack(bars)
        self.assertNotEqual(legacy, current)
        def typed_fingerprint(values):
            return tuple(tuple((key, type(value).__name__, value.hex() if isinstance(value, float) else value) for key, value in vars(bar).items()) for bar in values)
        def native_input_sha(values):
            normalized = _normalize_bars(values, _ms(CLOCK))
            request = {"bars": [_bar_payload(bar) for bar in normalized]}
            return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        for blob in (legacy, current):
            restored = self.runtime._unpack(blob)
            self.assertEqual(restored, bars)
            self.assertEqual(typed_fingerprint(restored), typed_fingerprint(bars))
            self.assertEqual(native_input_sha(restored), native_input_sha(bars))

    def _bound_cooldown_fixture(self, frame="1h"):
        from backend.tensor_engine import source_manifest_sha256
        self.providers.data[(frame, "AAA")] = revision(frame=frame)
        bars = canonical_native_bars(self.providers.data[(frame, "AAA")], frame, CLOCK)
        directory = Path(self.temp.name) / "cooldown-seed"
        member = directory / f"bars/{frame}/AAA.json.gz"
        member.parent.mkdir(parents=True, exist_ok=True)
        native = {"symbol": "AAA", "interval": frame, "bars": [{"timestamp": b.timestamp_ms // 1000, "completedAt": b.completed_at_ms // 1000,
                  "usableAt": b.completed_at_ms // 1000, **{k: getattr(b, k) for k in ("open", "high", "low", "close", "volume")}} for b in bars]}
        encoded = gzip.compress(json.dumps(native).encode())
        member.write_bytes(encoded)
        group = {"symbol": "AAA", "interval": frame, "path": f"bars/{frame}/AAA.json.gz", "accepted_bars": len(bars),
                 "last_completed_at": bars[-1].completed_at_ms // 1000, "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}
        manifest = Path(self.temp.name) / f"cooldown-{frame}.json"
        raw = json.dumps({"sources": [{"groups": [group]}]}).encode()
        manifest.write_bytes(raw)
        pin = source_manifest_sha256()
        sleeve = "H1STATE" if frame == "1h" else "WSTATE"
        row = self.install(sleeve=sleeve, enabled=False, engine_source_manifest_sha256=pin, seed_directory=str(directory),
                           seed_manifest_file=str(manifest), seed_manifest_sha256=hashlib.sha256(raw).hexdigest())
        self.runtime = TensorRuntime(self.store, self.trading, self.providers)
        self.trading.set_book(row["book_id"], {"policy": {"halted": True}})
        with self.store.transaction() as con:
            installed = dict(con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (row["id"],)).fetchone())
            installed["settings"] = json.loads(installed["config"])
            bars = self.runtime._merge(con, frame, "AAA", bars, [installed["settings"]])
            self.runtime._write_coverage(con, frame, "AAA", self.providers.data[(frame, "AAA")], bars, CLOCK)
            con.execute("INSERT INTO a_tensor_cooldowns VALUES(?,?,?,?)", (row["id"], "AAA", len(bars) + 19, bars[-1].timestamp_ms))
        return installed, bars, pin

    def test_bound_h_and_w_cooldowns_skip_only_new_features_and_preserve_candidates(self):
        for frame in ("1h", "1wk"):
            with self.subTest(frame=frame):
                installed, bars, pin = self._bound_cooldown_fixture(frame)
                native = latest_native_clock(frame, CLOCK)
                candidate = {"symbol": "AAA", "score": 1, "origin_ms": native["timestamp_ms"], "expires_ms": _ms(CLOCK) - 1,
                             "next_eligible_bar_index": len(bars) + 19, "next_open_ms": native["next_open_ms"]}
                with self.store.transaction() as con:
                    con.execute("INSERT INTO a_tensor_candidates VALUES(?,?,?,?)", (installed["id"], native["timestamp_ms"], "AAA", json.dumps(candidate)))
                result = {"entries": 0, "exits": 0, "acquired": 0}
                with patch.object(self.runtime, "_extract", side_effect=AssertionError("Blocked native ordinal was recomputed")):
                    self.runtime._frame_cycle(frame, [installed], CLOCK, None, self.providers, result)
                self.assertEqual(result["acquired"], 1)
                with self.store.connect() as con:
                    self.assertEqual(con.execute("SELECT status FROM a_tensor_cycle_reads WHERE frame=?", (frame,)).fetchone()[0], "ready")
                    self.assertEqual(con.execute("SELECT next_index FROM a_tensor_cooldowns WHERE installation_id=?", (installed["id"],)).fetchone()[0], len(bars) + 19)
                    self.assertEqual(con.execute("SELECT data FROM a_tensor_candidates WHERE installation_id=?", (installed["id"],)).fetchone()[0], json.dumps(candidate))
                    proof = json.loads(con.execute("SELECT data FROM a_tensor_decisions WHERE installation_id=? AND role='signal'", (installed["id"],)).fetchone()[0])
                    self.assertFalse(proof["native_features_recomputed"])
                    self.assertTrue(proof["full_native_input_validated"])
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_cooldown_proof_falls_back_at_crossing_repair_custom_daily_and_pin_failure(self):
        installed, bars, pin = self._bound_cooldown_fixture()
        origin = bars[-1].timestamp_ms
        def prove(con, **overrides):
            return self.runtime._state_cooldown_proof(con, overrides.get("frame", "1h"), "AAA", overrides.get("bars", bars),
                     overrides.get("installs", [installed]), origin, CLOCK, overrides.get("pin", pin), overrides.get("bound", True), overrides.get("diagnostics", []))
        with self.store.transaction() as con:
            self.assertIsNotNone(prove(con))
            self.assertIsNone(prove(con, frame="1d"))
            self.assertIsNone(prove(con, bound=False))
            self.assertIsNone(prove(con, pin="f" * 64))
            self.assertIsNone(prove(con, diagnostics=[{"reason": "restored_exact_pinned_native_prefix"}]))
            bad_pin = {**installed, "settings": {**installed["settings"], "engine_source_manifest_sha256": None}}
            self.assertIsNone(prove(con, installs=[bad_pin]))
            self.runtime.feature_extractor = extract
            self.assertIsNone(prove(con))
            self.runtime.feature_extractor = None
            self.runtime.policy_factory = FixturePolicy
            self.assertIsNone(prove(con))
            self.runtime.policy_factory = None
            for next_index, recorded_origin in ((len(bars) - 1, origin), (len(bars) + 20, origin), (len(bars) + 19, origin + 1000), (len(bars) + 19, 0), (len(bars) + 19, -1)):
                con.execute("UPDATE a_tensor_cooldowns SET next_index=?,origin_ms=?", (next_index, recorded_origin))
                self.assertIsNone(prove(con))
            con.execute("UPDATE a_tensor_cooldowns SET next_index=?,origin_ms=?", (len(bars) + 19, origin))
            malformed = list(bars)
            malformed[0] = NativeBar(**{**vars(bars[0]), "usable_at_ms": _ms(CLOCK) + 1})
            with self.assertRaisesRegex(Exception, "available at as-of"):
                prove(con, bars=tuple(malformed))
        with self.store.transaction() as con:
            con.execute("UPDATE a_tensor_cooldowns SET next_index=?", (len(bars) - 1,))
        result = {"entries": 0, "exits": 0, "acquired": 0}
        with patch.object(self.runtime, "_extract", wraps=self.runtime._extract) as engine:
            self.runtime._frame_cycle("1h", [installed], CLOCK, None, self.providers, result)
            self.assertEqual(engine.call_count, 1)
        self.assertEqual(result["acquired"], 1)

    def test_legacy_coverage_tail_is_primed_once_without_decisions_or_orders(self):
        bars = canonical_native_bars(self.providers.data[("1h", "AAA")], "1h", CLOCK)
        blob = self.runtime._pack(bars)
        with self.store.transaction() as con:
            con.execute("INSERT INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", ("1h", "AAA", "a" * 64, CLOCK.isoformat(), blob, "ready", None, CLOCK.isoformat()))
        with patch.object(TensorRuntime, "_unpack", wraps=TensorRuntime._unpack) as unpack:
            restarted = TensorRuntime(self.store, self.trading, self.providers, feature_extractor=extract, policy_factory=FixturePolicy)
            self.assertEqual(unpack.call_count, 1)
        with patch.object(restarted, "_unpack", side_effect=AssertionError("Warm query hint decoded full history")):
            self.assertEqual(restarted._coverage_tail("1h", "AAA", None), bars[-1].completed_at_ms)
            self.assertEqual(restarted.prime_coverage_tails()["initialized"], 0)
        with self.store.connect() as con:
            tail = dict(con.execute("SELECT * FROM a_tensor_coverage_tails").fetchone())
            self.assertEqual(tail["blob_sha256"], hashlib.sha256(blob).hexdigest())
            self.assertEqual(tail["bar_count"], len(bars))
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_coverage_and_tail_commit_or_rollback_together(self):
        response = self.providers.data[("1h", "AAA")]
        bars = canonical_native_bars(response, "1h", CLOCK)
        with self.store.transaction() as con:
            self.runtime._write_coverage(con, "1h", "AAA", response, bars, CLOCK)
        with self.store.connect() as con:
            before = tuple(con.execute("SELECT * FROM a_tensor_coverage").fetchone())
            old_tail = tuple(con.execute("SELECT * FROM a_tensor_coverage_tails").fetchone())
        changed = {**response, "revision_id": "b" * 64}
        with self.assertRaisesRegex(RuntimeError, "interrupted"), patch.object(self.runtime, "_write_tail", side_effect=RuntimeError("interrupted metadata commit")):
            with self.store.transaction() as con:
                self.runtime._write_coverage(con, "1h", "AAA", changed, bars[:-1], CLOCK)
        with self.store.connect() as con:
            self.assertEqual(tuple(con.execute("SELECT * FROM a_tensor_coverage").fetchone()), before)
            self.assertEqual(tuple(con.execute("SELECT * FROM a_tensor_coverage_tails").fetchone()), old_tail)
        with self.store.transaction() as con:
            self.runtime._write_coverage(con, "1h", "AAA", changed, bars[:-1], CLOCK)
        with self.store.connect() as con:
            coverage = con.execute("SELECT * FROM a_tensor_coverage").fetchone()
            tail = con.execute("SELECT * FROM a_tensor_coverage_tails").fetchone()
            self.assertTrue(self.runtime._valid_tail("1h", "AAA", coverage["revision_id"], coverage["bars"], tail))
            self.assertEqual(tail["last_completed_ms"], bars[-2].completed_at_ms)
            self.assertEqual(tail["bar_count"], len(bars) - 1)

    def test_malformed_legacy_coverage_is_isolated_without_blocking_healthy_restart(self):
        response = self.providers.data[("1h", "AAA")]
        bars = canonical_native_bars(response, "1h", CLOCK)
        damaged = b"preserved damaged compressed research evidence"
        with self.store.transaction() as con:
            con.execute("INSERT INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", ("1h", "AAA", "a" * 64, CLOCK.isoformat(), self.runtime._pack(bars), "ready", None, CLOCK.isoformat()))
            con.execute("INSERT INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", ("1h", "BBB", "b" * 64, CLOCK.isoformat(), damaged, "ready", None, CLOCK.isoformat()))
        restarted = TensorRuntime(self.store, self.trading, self.providers, feature_extractor=extract, policy_factory=FixturePolicy)
        self.assertEqual(restarted._coverage_tail("1h", "AAA", None), bars[-1].completed_at_ms)
        with self.assertRaises(Exception):
            restarted._coverage_tail("1h", "BBB", None)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT bars FROM a_tensor_coverage WHERE symbol='BBB'").fetchone()[0], damaged)
            self.assertEqual([r[0] for r in con.execute("SELECT symbol FROM a_tensor_coverage_tails")], ["AAA"])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_tail_metadata_mismatches_are_rederived_from_exact_current_blob(self):
        response = self.providers.data[("1h", "AAA")]
        bars = canonical_native_bars(response, "1h", CLOCK)
        with self.store.transaction() as con:
            self.runtime._write_coverage(con, "1h", "AAA", response, bars, CLOCK)
        for mutation, parameters, expected in (
                ("UPDATE a_tensor_coverage_tails SET last_completed_ms=?", (_ms(CLOCK + timedelta(days=100)),), bars[-1].completed_at_ms),
                ("UPDATE a_tensor_coverage_tails SET last_completed_ms=?", (float("inf"),), bars[-1].completed_at_ms),
                ("UPDATE a_tensor_coverage SET revision_id=?", ("c" * 64,), bars[-1].completed_at_ms),
                ("UPDATE a_tensor_coverage SET bars=?", (self.runtime._pack(bars[:-1]),), bars[-2].completed_at_ms)):
            with self.subTest(mutation=mutation):
                with self.store.transaction() as con:
                    con.execute(mutation, parameters)
                with patch.object(self.runtime, "_unpack", wraps=self.runtime._unpack) as unpack:
                    self.assertEqual(self.runtime._coverage_tail("1h", "AAA", None), expected)
                    self.assertEqual(unpack.call_count, 1)
                with self.store.connect() as con:
                    coverage = con.execute("SELECT * FROM a_tensor_coverage").fetchone()
                    tail = con.execute("SELECT * FROM a_tensor_coverage_tails").fetchone()
                    self.assertTrue(self.runtime._valid_tail("1h", "AAA", coverage["revision_id"], coverage["bars"], tail))

    def test_sqlite_text_legacy_coverage_is_isolated_with_existing_metadata(self):
        self._assert_text_legacy_coverage_isolated(retain_metadata=True)

    def test_sqlite_text_legacy_coverage_is_isolated_without_metadata(self):
        self._assert_text_legacy_coverage_isolated(retain_metadata=False)

    def test_sqlite_real_legacy_coverage_failure_receipt_remains_finite(self):
        self._assert_text_legacy_coverage_isolated(retain_metadata=True, malformed=float("inf"))

    def _assert_text_legacy_coverage_isolated(self, *, retain_metadata, malformed="explicit SQLite TEXT in BLOB-affinity column"):
        response = self.providers.data[("1h", "AAA")]
        bars = canonical_native_bars(response, "1h", CLOCK)
        with self.store.transaction() as con:
            for sym in ("AAA", "BBB"):
                self.runtime._write_coverage(con, "1h", sym, response, bars, CLOCK)
            con.execute("UPDATE a_tensor_coverage SET bars=? WHERE symbol='BBB'", (malformed,))
            if not retain_metadata:
                con.execute("DELETE FROM a_tensor_coverage_tails WHERE symbol='BBB'")
        restarted = TensorRuntime(self.store, self.trading, self.providers, feature_extractor=extract, policy_factory=FixturePolicy)
        self.assertEqual(restarted._coverage_tail("1h", "AAA", None), bars[-1].completed_at_ms)
        with self.assertRaisesRegex(DeskError, "SQLite storage type"):
            restarted._coverage_tail("1h", "BBB", None)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT bars FROM a_tensor_coverage WHERE symbol='BBB'").fetchone()[0], malformed)
            self.assertEqual([r[0] for r in con.execute("SELECT symbol FROM a_tensor_coverage_tails")], ["AAA"])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_invalid_tail_repair_obeys_writer_fence_and_never_grants_bar_completion(self):
        response = self.providers.data[("1h", "AAA")]
        bars = canonical_native_bars(response, "1h", CLOCK)
        with self.store.transaction() as con:
            self.runtime._write_coverage(con, "1h", "AAA", response, bars, CLOCK)
            con.execute("DELETE FROM a_tensor_coverage_tails")
        def fence(con):
            raise RuntimeError("lease lost")
        with self.assertRaisesRegex(RuntimeError, "lease lost"):
            self.runtime._coverage_tail("1h", "AAA", fence)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_coverage_tails").fetchone()[0], 0)
        self.assertEqual(self.runtime._coverage_tail("1h", "AAA", None), bars[-1].completed_at_ms)
        cached = copy.deepcopy(response)
        cached["fetched_at"] = _dt(bars[-1].completed_at_ms - 1).isoformat()
        cached["observed_at"] = cached["fetched_at"]
        self.assertEqual(canonical_native_bars(cached, "1h", CLOCK)[-1].completed_at_ms, bars[-2].completed_at_ms)

    def test_thirty_two_readers_preserve_deterministic_full_census_ranking(self):
        symbols = [f"A{i:02d}" for i in range(65)]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        self.install(symbols=symbols, budget=65)
        for sym in symbols:
            self.quote(sym)
        original = self.providers.bars
        gate, started = threading.Event(), threading.Event()
        lock = threading.Lock()
        active, maximum, calls = [0], [0], []
        def bounded_read(sym, period, interval):
            with lock:
                active[0] += 1
                maximum[0] = max(maximum[0], active[0])
                calls.append(sym)
                if active[0] == 32:
                    started.set()
            try:
                self.assertTrue(gate.wait(5))
                return original(sym, period, interval)
            finally:
                with lock:
                    active[0] -= 1
        result, errors = [], []
        def run():
            try:
                result.append(self.runtime.run_once(CLOCK))
            except Exception as exc:
                errors.append(exc)
        self.providers.bars = bounded_read
        worker = threading.Thread(target=run)
        worker.start()
        try:
            self.assertTrue(started.wait(5))
            self.assertEqual(maximum[0], 32)
            with self.store.connect() as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)
        finally:
            gate.set()
            worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result[0]["acquired"], len(symbols))
        self.assertEqual(result[0]["entries"], 10)
        self.assertLessEqual(maximum[0], 32)
        self.assertEqual(set(calls), set(symbols))
        with self.store.connect() as con:
            self.assertEqual([r[0] for r in con.execute("SELECT symbol FROM p_intents ORDER BY rowid")], symbols[:10])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_coverage_tails").fetchone()[0], len(symbols))

    def test_daily_repaired_prefix_waits_for_maximum_history_knowledge_clock(self):
        capture = CLOCK.replace(microsecond=37_000)
        available = CLOCK + timedelta(seconds=1)
        self.providers = FixtureProviders(frame="1d", clock=capture)
        self.runtime.providers = self.providers
        current = [capture]
        waits, evaluated = [], []
        def actual_clock(value=None):
            return current[0] if value is None else value if isinstance(value, datetime) else datetime.fromisoformat(value)
        def wait(seconds):
            waits.append(seconds)
            current[0] += timedelta(seconds=seconds)
        def exported_history(sym, frame, bars, clock_ms):
            # Prefix repair is newly known at a fractional-second receipt;
            # the retained later endpoint was genuinely known much earlier.
            rows = ({"usable_at": _ms(available) // 1000}, {"usable_at": _ms(CLOCK - timedelta(minutes=10)) // 1000})
            return SimpleNamespace(snapshot=SimpleNamespace(source_manifest_sha256=PIN, bars=bars), rows=rows)
        def daily(sym, rows, clock_ms):
            evaluated.append(clock_ms)
            self.assertGreaterEqual(clock_ms, max(r["usable_at"] for r in rows) * 1000)
            return tuple({"sleeve_id": sleeve, "selected": False, "reason": "below_frozen_threshold"} for sleeve in ("D20_PV", "D20_TENSOR"))
        self.runtime.feature_extractor = exported_history
        self.runtime.daily_evaluator = daily
        self.install(sleeve="D20PV")
        with patch("backend.tensor_runtime.utc_clock", actual_clock), patch("backend.tensor_runtime.time.sleep", wait):
            result = self.runtime.run_once()
        self.assertEqual(result["acquired"], 1)
        self.assertEqual(evaluated, [_ms(available)])
        self.assertEqual(len(waits), 1)
        self.assertAlmostEqual(waits[0], .963)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT status FROM a_tensor_cycle_reads").fetchone()[0], "ready")

    def test_duplicate_alias_enrollment_is_rejected_without_silent_roster_change(self):
        book = self.trading.create_book({"name": "duplicate", "broker": "local", "kind": "forward"})
        with self.assertRaisesRegex(DeskError, "duplicate"):
            self.runtime.install({"sleeve": "H1STATE", "book_id": book["id"], "universe": ["AAA", "aaa"]})
        self.assertEqual(self.runtime.snapshot()["strategy_count"], 0)

    def test_full_pool_ranking_pending_slots_and_atomic_restart(self):
        symbols = [f"{chr(65 + i)}AA" for i in range(12)]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        row = self.install(symbols=symbols, budget=6)
        for sym in symbols:
            self.quote(sym)
        first = self.runtime.run_once(CLOCK)
        self.assertEqual(first["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cooldowns").fetchone()[0], 6)
        restarted = TensorRuntime(self.store, self.trading, self.providers, feature_extractor=extract, policy_factory=FixturePolicy)
        second = restarted.run_once(CLOCK)
        self.assertEqual(second["entries"], 10)
        with self.store.connect() as con:
            intents = [dict(r) for r in con.execute("SELECT * FROM p_intents ORDER BY rowid")]
            self.assertEqual([r["symbol"] for r in intents], list(reversed(symbols))[0:10])
            self.assertTrue(all(Decimal(r["quantity"]) == int(r["quantity"]) for r in intents))
            self.assertLessEqual(sum(r["reserved_cents"] for r in intents), 10_000_000)
        self.assertEqual(restarted.run_once(CLOCK)["entries"], 0)
        self.assertEqual(row["config"]["symbols"], symbols)

    def test_native_work_overlaps_outstanding_reads_without_partial_pool_allocation(self):
        self.providers = FixtureProviders(["AAA", "BBB"])
        self.runtime.providers = self.providers
        started = threading.Event()
        bars = self.providers.bars
        def staged(sym, period, interval):
            if sym == "BBB" and not started.wait(2):
                raise RuntimeError("No native work began while the remaining source read was outstanding")
            return bars(sym, period, interval)
        self.providers.bars = staged
        def staged_extract(sym, *args):
            if sym == "AAA":
                with self.store.connect() as con:
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)
                started.set()
            return extract(sym, *args)
        self.runtime.feature_extractor = staged_extract
        self.install(symbols=["AAA", "BBB"])
        self.quote("AAA")
        self.quote("BBB")
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 2)
        self.assertTrue(started.is_set())
        with self.store.connect() as con:
            self.assertEqual([r[0] for r in con.execute("SELECT symbol FROM p_intents ORDER BY rowid")], ["BBB", "AAA"])

    def test_unknown_data_failure_blocks_partial_pool_but_warmup_does_not(self):
        self.providers = FixtureProviders(["AAA", "BBB"])
        self.runtime.providers = self.providers
        self.providers.fail.add("BBB")
        self.install(symbols=["AAA", "BBB"])
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        with self.store.connect() as con:
            denial = con.execute("SELECT reason FROM a_tensor_decisions WHERE role='coverage'").fetchone()[0]
            self.assertEqual(denial, "incomplete_enrollment_cycle")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions WHERE role='entry'").fetchone()[0], 0)
        self.providers.fail.clear()
        self.quote("BBB")
        recovered = self.runtime.run_once(CLOCK)
        self.assertEqual(recovered["entries"], 2)
        self.assertEqual(self.runtime.snapshot()["installations"][0]["readiness"]["failed_reads"], 0)

    def test_completed_census_recovery_uses_configured_width_without_partial_ranking(self):
        symbols = ["T" + str(i).zfill(3) for i in range(24)]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        self.providers.fail.update(symbols)
        self.install(symbols=symbols, budget=12)
        for _ in range(3):
            self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads").fetchone()[0], 24)
            self.assertGreaterEqual(con.execute("SELECT cursor FROM a_tensor_cycles").fetchone()[0], 24)
        self.providers.fail.clear()
        self.providers.calls.clear()
        for sym in symbols:
            self.quote(sym)
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        self.assertEqual(len(self.providers.calls), 12)
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 10)
        self.assertEqual(len(self.providers.calls), 24)
        self.assertEqual({c[0] for c in self.providers.calls}, set(symbols))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE status='failed'").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 10)

    def test_restart_recovers_bound_staged_coverage_missing_assessment_behind_end_cursor(self):
        symbols = ["AAA", "BBB", "CCC", "DDD"]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        self.install(symbols=symbols, budget=1, enabled=False)
        for sym in symbols:
            self.quote(sym)
        for _ in symbols:
            self.runtime.run_once(CLOCK)
        latest = latest_native_clock("1h", CLOCK)
        with self.store.transaction() as con:
            # The coverage and binding committed during repair, but the worker
            # was interrupted before the replacement feature assessment.
            for sym in ("AAA", "BBB"):
                cached = self.runtime._unpack(con.execute("SELECT bars FROM a_tensor_coverage WHERE symbol=?", (sym,)).fetchone()[0])
                con.execute("INSERT INTO a_tensor_prefix_bindings VALUES(?,?,?,?,?,?,?,?)", ("1h", sym, "b" * 64, len(cached), cached[0].timestamp_ms, cached[-1].timestamp_ms, cached[-1].executable_at_ms, CLOCK.isoformat()))
                con.execute("DELETE FROM a_tensor_cycle_reads WHERE symbol=?", (sym,))
            con.execute("UPDATE a_tensor_cycle_reads SET status='failed',error='retained_quality_receipt' WHERE symbol='CCC'")
            con.execute("UPDATE a_tensor_cycle_reads SET status='ineligible',error='retained_verified_ineligibility' WHERE symbol='DDD'")
            con.execute("UPDATE a_tensor_cycles SET cursor=4,status='incomplete'")
        restarted = TensorRuntime(self.store, self.trading, self.providers, feature_extractor=extract, policy_factory=FixturePolicy)
        self.providers.calls.clear()
        self.assertEqual(restarted.run_once(CLOCK)["entries"], 0)
        self.assertEqual([c[0] for c in self.providers.calls], ["AAA"])
        self.assertEqual(restarted.run_once(CLOCK)["entries"], 0)
        self.assertEqual([c[0] for c in self.providers.calls], ["AAA", "BBB"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE frame='1h' AND origin_ms=?", (latest["timestamp_ms"],)).fetchone()[0], 4)
            self.assertEqual(tuple(con.execute("SELECT status,error FROM a_tensor_cycle_reads WHERE symbol='CCC'").fetchone()), ("failed", "retained_quality_receipt"))
            self.assertEqual(tuple(con.execute("SELECT status,error FROM a_tensor_cycle_reads WHERE symbol='DDD'").fetchone()), ("ineligible", "retained_verified_ineligibility"))
            self.assertEqual(con.execute("SELECT cursor FROM a_tensor_cycles").fetchone()[0], 4)

    def test_recovery_width_reserves_and_rotates_actual_held_source_reads(self):
        symbols = ["T" + str(i).zfill(3) for i in range(24)]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        self.install(symbols=symbols, budget=12)
        for sym in symbols:
            self.quote(sym)
        self.runtime.run_once(CLOCK)
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 10)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 10)
        self.runtime.run_once(CLOCK)
        with self.store.connect() as con:
            held = {r[0] for r in con.execute("SELECT symbol FROM p_positions WHERE book_id!='main' AND CAST(quantity AS REAL)>0")}
        later = CLOCK + timedelta(hours=1)
        self.providers.data = {("1h", sym): revision(sym, clock=later) for sym in symbols}
        self.providers.fail.update(symbols)
        for _ in range(16):
            self.assertEqual(self.runtime.run_once(later)["entries"], 0)
            with self.store.connect() as con:
                if con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE origin_ms=(SELECT origin_ms FROM a_tensor_cycles)").fetchone()[0] == 24:
                    break
        else:
            self.fail("Held priorities starved first attempts")
        self.providers.fail.clear()
        for sym in symbols:
            self.quote(sym, clock=later)
        held_reads = set()
        for _ in range(6):
            self.providers.calls.clear()
            self.assertEqual(self.runtime.run_once(later)["entries"], 0)
            self.assertLessEqual(len(self.providers.calls), 12)
            seen = {c[0] for c in self.providers.calls}
            self.assertGreaterEqual(len(seen & held), 6)
            held_reads.update(seen & held)
            with self.store.connect() as con:
                if con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE origin_ms=(SELECT origin_ms FROM a_tensor_cycles) AND status='failed'").fetchone()[0] == 0:
                    break
        else:
            self.fail("Configured recovery width did not drain the assessed failures")
        self.assertEqual(held_reads, held)

    def test_width_one_with_actual_holdings_never_overruns_or_starves_first_attempts(self):
        symbols = ["AAA", "BBB"]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        self.install(symbols=symbols, budget=1)
        for sym in symbols:
            self.quote(sym)
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 2)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 2)
        later = CLOCK + timedelta(hours=1)
        self.providers.data = {("1h", sym): revision(sym, clock=later) for sym in symbols}
        self.providers.fail.update(symbols)
        for _ in range(2):
            self.providers.calls.clear()
            self.assertEqual(self.runtime.run_once(later)["entries"], 0)
            self.assertEqual(len(self.providers.calls), 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE origin_ms=(SELECT origin_ms FROM a_tensor_cycles)").fetchone()[0], 2)
        self.providers.fail.clear()
        recovered = []
        for _ in range(2):
            self.providers.calls.clear()
            self.assertEqual(self.runtime.run_once(later)["entries"], 0)
            self.assertEqual(len(self.providers.calls), 1)
            recovered.append(self.providers.calls[0][0])
        self.assertEqual(set(recovered), set(symbols))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads WHERE origin_ms=(SELECT origin_ms FROM a_tensor_cycles) AND status='failed'").fetchone()[0], 0)

    def test_known_warmup_is_not_a_missing_eligible_source(self):
        self.providers = FixtureProviders(["AAA", "BBB"])
        self.providers.data[("1h", "BBB")] = revision("BBB", count=50)
        self.runtime.providers = self.providers
        self.install(symbols=["AAA", "BBB"])
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT status FROM a_tensor_cycle_reads WHERE symbol='BBB'").fetchone()[0], "ineligible")

    def test_expired_entry_never_replays_and_consumes_cooldown(self):
        self.install()
        late = CLOCK + timedelta(minutes=8)
        self.quote(clock=late)
        self.assertEqual(self.runtime.run_once(late)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT status FROM a_tensor_decisions WHERE role='entry'").fetchone()[0], "expired")
            self.assertEqual(con.execute("SELECT next_index FROM a_tensor_cooldowns").fetchone()[0], 253)

    def test_future_revision_and_wrong_grid_are_rejected(self):
        value = revision()
        value["observed_at"] = (CLOCK + timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(DeskError, "observed after"):
            canonical_native_bars(value, "1h", CLOCK)
        value = revision()
        value["bars"][-1]["timestamp"] = _dt(_ms(value["bars"][-1]["timestamp"]) + 60_000).isoformat()
        with self.assertRaisesRegex(DeskError, "09:30"):
            canonical_native_bars(value, "1h", CLOCK)

    def test_cached_preclose_rows_require_an_actual_postclose_fetch_in_every_frame(self):
        for frame in ("1h", "1d", "1wk"):
            with self.subTest(frame=frame):
                response = revision(frame=frame)
                completion = latest_native_clock(frame, CLOCK)["completed_at_ms"]
                preclose = _dt(completion - 10_000).isoformat()
                response["observed_at"] = preclose
                response["fetched_at"] = preclose
                self.assertEqual(len(canonical_native_bars(response, frame, CLOCK)), 233)
                # Identical prices/content may reuse the old revision identity;
                # its new actual read, rather than old firstseen, knows closure.
                response["fetched_at"] = _dt(completion + 2_000).isoformat()
                final = canonical_native_bars(response, frame, CLOCK)
                self.assertEqual(len(final), 234)
                self.assertEqual(final[-1].usable_at_ms, completion + 2_000)
                with self.assertRaisesRegex(DeskError, "after the decision"):
                    canonical_native_bars(response, frame, _dt(completion + 1_000))

    def test_first_revision_observation_cannot_follow_its_actual_fetch(self):
        response = revision()
        response["fetched_at"] = (CLOCK - timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(DeskError, "first observation"):
            canonical_native_bars(response, "1h", CLOCK)

    def test_unfinished_bar_excluded_and_early_close_keeps_short_bucket(self):
        value = revision()
        value["bars"].append({**value["bars"][-1], "timestamp": datetime(2026, 10, 9, 14, 30, tzinfo=UTC).isoformat()})
        value["provider_asof"] = value["bars"][-1]["timestamp"]
        self.assertEqual(len(canonical_native_bars(value, "1h", CLOCK)), 234)
        opened, complete = _native_period(_ms(datetime(2025, 11, 28, 17, 30, tzinfo=UTC)), "1h")
        self.assertEqual(complete - opened, 30 * 60 * 1000)

    def test_daily_utc_label_and_weekly_utc_monday_are_not_previous_day(self):
        opened, completed = _native_period(_ms(datetime(2026, 10, 9, tzinfo=UTC)), "1d")
        self.assertEqual(_dt(opened), datetime(2026, 10, 9, 13, 30, tzinfo=UTC))
        opened, completed = _native_period(_ms(datetime(2025, 5, 26, tzinfo=UTC)), "1wk")
        self.assertEqual(_dt(opened), datetime(2025, 5, 27, 13, 30, tzinfo=UTC))
        self.assertEqual(_dt(completed), datetime(2025, 5, 30, 20, tzinfo=UTC))

    def test_source_revision_does_not_silently_recalculate_history(self):
        self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        response = self.providers.data[("1h", "AAA")]
        response["bars"][-2]["volume"] += 1
        with self.store.transaction() as con:
            bars = canonical_native_bars(response, "1h", CLOCK)
            with self.assertRaisesRegex(DeskError, "revised"):
                self.runtime._merge(con, "1h", "AAA", bars, [{}])

    def test_entry_transaction_fence_rolls_back_signal_and_intent(self):
        self.install()
        self.quote()
        calls = 0
        def fence(con):
            nonlocal calls
            calls += 1
            if calls > 5:
                raise DeskError("Worker lease was lost")
        with self.assertRaises(DeskError):
            self.runtime.run_once(CLOCK, transaction_guard=fence)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_disabled_and_halted_entries_still_exit_after_twenty_observed_bars(self):
        row = self.install()
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 1)
        self.runtime.set_enabled(row["id"], False)
        self.trading.set_book(row["book_id"], {"policy": {"halted": True}})
        # Native count crosses a weekend without inventing weekend bars.
        later = datetime(2026, 10, 14, 13, 30, 2, tzinfo=UTC)
        old = self.providers.data[("1h", "AAA")]
        old_bars = old["bars"]
        forward = native_history("1h", later, 300)
        latest = {b["timestamp"]: b for b in old_bars}
        for bar in forward:
            if _ms(bar["timestamp"]) > _ms(old_bars[-1]["timestamp"]):
                latest[bar["timestamp"]] = bar
        value = revision(clock=later)
        value["bars"] = [latest[k] for k in sorted(latest)]
        value["provider_asof"] = value["bars"][-1]["timestamp"]
        self.providers.data[("1h", "AAA")] = value
        self.quote(clock=later)
        result = self.runtime.run_once(later)
        self.assertEqual(result["entries"], 0)
        self.assertEqual(result["exits"], 1)
        self.assertEqual(self.trading.process(self.providers, later)["fills"], 1)
        with self.store.connect() as con:
            self.assertEqual(Decimal(con.execute("SELECT quantity FROM p_positions WHERE book_id=?", (row["book_id"],)).fetchone()[0]), 0)
            settlement = self.trading.strategy_cash(con, row["book_id"], later, release=False)
            self.assertGreater(settlement["unsettled_cents"], 0)
        self.assertEqual(self.runtime.run_once(later)["exits"], 0)

    def test_four_dedicated_books_and_shared_daily_evaluation(self):
        self.providers = FixtureProviders()
        self.providers.data[("1wk", "AAA")] = revision(frame="1wk")
        self.providers.data[("1d", "AAA")] = revision(frame="1d")
        evaluations = []
        def daily(sym, rows, asof):
            evaluations.append(sym)
            return tuple({"sleeve_id": sleeve, "symbol": sym, "bar_index": 233, "selected": True,
                          "eligible": True, "reason": "selected", "predicted_net_qqq_excess": score,
                          "dollar_volume20": 20_000_000} for sleeve, score in (("D20_PV", .02), ("D20_TENSOR", .03)))
        self.runtime.providers = self.providers
        self.runtime.daily_evaluator = daily
        for sleeve in ("H1STATE", "WSTATE", "D20PV", "D20TENSOR"):
            self.install(sleeve=sleeve)
        self.quote()
        self.runtime.run_once(CLOCK + timedelta(minutes=20))
        self.assertEqual(evaluations, ["AAA"])
        snapshot = self.runtime.snapshot()
        self.assertEqual(snapshot["strategy_count"], 4)
        self.assertEqual(len({r["book_id"] for r in snapshot["installations"]}), 4)

    def test_enablement_is_rechecked_after_asynchronous_computation(self):
        row = self.install()
        self.quote()
        def pause_during_compute(sym, frame, bars, clock_ms):
            self.runtime.set_enabled(row["id"], False)
            return extract(sym, frame, bars, clock_ms)
        self.runtime.feature_extractor = pause_during_compute
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT reason FROM a_tensor_decisions WHERE role='entry'").fetchone()[0], "entries_disabled")

    def test_original_greedy_cooldown_recovers_skipped_origins_without_orders(self):
        rows = []
        for i in range(237):
            votes = [-1] * 7
            if i >= 233:
                votes[:2] = [1, 1]
            if i >= 236:
                votes[2:4] = [1, 1]
            row = {"bar_index": i, "close": 10, "dollar_volume20": 20_000_000, "atr14": 1,
                   "total_votes": 7, "bullish_votes": votes.count(1), "bearish_votes": votes.count(-1)}
            row.update({"vote_" + name: v for name, v in zip(("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave"), votes)})
            rows.append(row)
        recovered = historical_state_cooldown(rows, 236)
        self.assertEqual(recovered["last_consumed_origin_index"], 233)
        self.assertEqual(recovered["next_eligible_bar_index"], 253)
        self.assertEqual(recovered["orders_created"], 0)

    def test_flat_fee_is_inside_equity_and_liquidity_total_debit_caps(self):
        row = self.install()
        self.trading.set_book(row["book_id"], {"policy": {"fees_per_order": 20}})
        self.quote(price="9.99")
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        with self.store.connect() as con:
            intent = con.execute("SELECT * FROM p_intents").fetchone()
            quantity = Decimal(intent["quantity"])
            self.assertLessEqual(quantity * Decimal("9.99") * Decimal("1.001") + 20, Decimal(10_000))
            self.assertEqual(quantity, 998)

    def test_hash_verified_seed_keeps_prefix_and_period_label_when_vendor_aliases(self):
        bars = canonical_native_bars(revision(), "1h", CLOCK)
        source = {"symbol": "AAA", "interval": "1h", "bars": [
            {"timestamp": b.timestamp_ms // 1000, "completedAt": b.completed_at_ms // 1000,
             "usableAt": b.completed_at_ms // 1000, **{k: getattr(b, k) for k in ("open", "high", "low", "close", "volume")}} for b in bars]}
        directory = Path(self.temp.name) / "native-inputs"
        member = directory / "bars/1h/AAA.json.gz"
        member.parent.mkdir(parents=True)
        encoded = gzip.compress(json.dumps(source).encode())
        member.write_bytes(encoded)
        group = {"symbol": "AAA", "interval": "1h", "path": "bars/1h/AAA.json.gz", "accepted_bars": 234,
                 "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}
        manifest = Path(self.temp.name) / "source.json"
        raw = json.dumps({"sources": [{"groups": [group]}]}).encode()
        manifest.write_bytes(raw)
        config = {"seed_directory": str(directory), "seed_manifest_file": str(manifest), "seed_manifest_sha256": hashlib.sha256(raw).hexdigest()}
        with self.store.transaction() as con:
            merged = self.runtime._merge(con, "1h", "AAA", bars[-20:], [config])
            self.assertEqual(len(merged), 234)
            self.assertEqual(merged[0].timestamp_ms, bars[0].timestamp_ms)
        member.write_bytes(encoded + b"corrupt")
        with self.assertRaisesRegex(DeskError, "differs"):
            self.runtime._seed("1h", "AAA", [config], _ms(CLOCK))

    def test_explicit_forward_minor_revisions_are_audited_without_rewriting_prefix(self):
        self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        response = self.providers.data[("1h", "AAA")]
        response["bars"][-2]["volume"] += 2000
        response["bars"][-2]["open"] += .001
        bars = canonical_native_bars(response, "1h", CLOCK)
        diagnostics = []
        with self.store.transaction() as con:
            merged = self.runtime._merge(con, "1h", "AAA", bars, [{"forward_revision_policy": "retain_frozen_prefix_audit_minor"}], diagnostics=diagnostics)
        self.assertEqual(merged[-2].open, 10)
        self.assertEqual(merged[-2].volume, 2_000_000)
        self.assertEqual(diagnostics[0]["changed_native_periods"], 1)
        self.assertFalse(diagnostics[0]["historical_values_rewritten"])
        response["bars"][-2]["open"] = 20
        response["bars"][-2]["high"] = 22
        with self.store.transaction() as con:
            with self.assertRaisesRegex(DeskError, "price-basis"):
                self.runtime._merge(con, "1h", "AAA", canonical_native_bars(response, "1h", CLOCK), [{"forward_revision_policy": "retain_frozen_prefix_audit_minor"}])

    def test_actual_yahoo_shape_close_quote_stubs_are_quarantined(self):
        previous = datetime(2026, 10, 9, 12, tzinfo=UTC)
        for frame in ("1h", "1wk"):
            response = revision(frame=frame, clock=previous)
            response["bars"].append({"timestamp": datetime(2026, 10, 8, 20, 0, 1 if frame == "1wk" else 0, tzinfo=UTC).isoformat(),
                       "open": 10, "high": 10, "low": 10, "close": 10, "volume": 0})
            response["provider_asof"] = response["bars"][-1]["timestamp"]
            diagnostics = []
            result = canonical_native_bars(response, frame, previous, diagnostics=diagnostics)
            self.assertEqual(len(result), 234)
            self.assertEqual(diagnostics[0]["reason"], "quarantined_vendor_session_close_quote_stub")
            self.assertFalse(diagnostics[0]["native_bar_admitted"])

    def test_actual_yahoo_weekly_daily_aggregate_requires_exact_final_metadata_identity(self):
        clock = datetime(2026, 10, 9, 12, tzinfo=UTC)
        response = revision(frame="1wk", clock=clock)
        marker = "2026-10-08T20:00:38+00:00"
        response.update(provider="yahoo", vendor_regular_market_timestamp=marker, provider_asof=marker)
        response["bars"].append({"timestamp": marker, "open": 167.48, "high": 168.66,
                                "low": 163.32, "close": 168.17, "volume": 2_713_389})
        diagnostics = []
        result = canonical_native_bars(response, "1wk", clock, diagnostics=diagnostics)
        self.assertEqual(len(result), 234)
        self.assertEqual(diagnostics[0]["reason"], "quarantined_yahoo_weekly_regular_market_supplement")
        self.assertTrue(diagnostics[0]["raw_row_preserved_in_provider_revision"])
        del response["vendor_regular_market_timestamp"]
        with self.assertRaisesRegex(DeskError, "weekly"):
            canonical_native_bars(response, "1wk", clock)
        response["vendor_regular_market_timestamp"] = "2026-10-08T20:00:37+00:00"
        with self.assertRaisesRegex(DeskError, "weekly"):
            canonical_native_bars(response, "1wk", clock)
        response["vendor_regular_market_timestamp"] = marker
        response["provider"] = "fixture"
        with self.assertRaisesRegex(DeskError, "weekly"):
            canonical_native_bars(response, "1wk", clock)

    def test_actual_intraday_hourly_point_quote_tail_is_not_a_completed_bar(self):
        clock = datetime(2026, 10, 9, 13, 32, 10, tzinfo=UTC)
        marker = "2026-10-09T13:31:48+00:00"
        response = revision(clock=clock)
        response.update(provider="yahoo", vendor_regular_market_timestamp=marker, provider_asof=marker)
        response["bars"].extend([
            {"timestamp": "2026-10-09T13:30:00+00:00", "open": 169, "high": 170, "low": 168, "close": 169.8, "volume": 1000},
            {"timestamp": marker, "open": 169.835, "high": 169.835, "low": 169.835, "close": 169.835, "volume": 0}])
        diagnostics = []
        result = canonical_native_bars(response, "1h", clock, diagnostics=diagnostics)
        self.assertEqual(len(result), 234)
        self.assertEqual(result[-1].completed_at_ms, _ms("2026-10-08T20:00:00+00:00"))
        self.assertEqual(diagnostics[-1]["reason"], "quarantined_yahoo_hourly_regular_market_point_quote")
        self.assertFalse(diagnostics[-1]["native_bar_admitted"])
        for change in ({"volume": 1}, {"high": 170}):
            altered = copy.deepcopy(response)
            altered["bars"][-1].update(change)
            with self.assertRaisesRegex(DeskError, "hourly"):
                canonical_native_bars(altered, "1h", clock)
        for missing_or_wrong in (None, "2026-10-09T13:31:47+00:00"):
            altered = copy.deepcopy(response)
            altered["vendor_regular_market_timestamp"] = missing_or_wrong
            with self.assertRaisesRegex(DeskError, "hourly"):
                canonical_native_bars(altered, "1h", clock)
        altered = copy.deepcopy(response)
        altered["bars"].append({"timestamp": "2026-10-09T13:32:00+00:00", "open": 169.9, "high": 169.9, "low": 169.9, "close": 169.9, "volume": 0})
        with self.assertRaisesRegex(DeskError, "hourly"):
            canonical_native_bars(altered, "1h", clock)

    def test_exact_market_point_tail_is_frame_specific_and_closing_seconds_are_not_guessed(self):
        clock = datetime(2026, 10, 9, 12, tzinfo=UTC)
        marker = "2026-10-08T20:00:02+00:00"
        for frame in ("1h", "1d", "1wk"):
            response = revision(frame=frame, clock=clock)
            response.update(provider="yahoo", vendor_regular_market_timestamp=marker, provider_asof=marker)
            response["bars"].append({"timestamp": marker, "open": 10, "high": 10, "low": 10, "close": 10, "volume": 0})
            if frame == "1d":
                with self.assertRaisesRegex(DeskError, "daily"):
                    canonical_native_bars(response, frame, clock)
            else:
                diagnostics = []
                self.assertEqual(len(canonical_native_bars(response, frame, clock, diagnostics=diagnostics)), 234)
                self.assertFalse(diagnostics[-1]["native_bar_admitted"])
                del response["vendor_regular_market_timestamp"]
                with self.assertRaises(DeskError):
                    canonical_native_bars(response, frame, clock)
                # Even an exact-close live quote needs the vendor marker;
                # the old one-second fixture allowance is not live admission.
                response["bars"][-1]["timestamp"] = "2026-10-08T20:00:00+00:00"
                with self.assertRaises(DeskError):
                    canonical_native_bars(response, frame, clock)

    def test_proved_unfinished_native_omissions_do_not_hide_completed_or_unknown_rows(self):
        clock = datetime(2026, 10, 9, 13, 32, tzinfo=UTC)
        for frame, stamp in (("1h", "2026-10-09T13:30:00+00:00"), ("1d", "2026-10-09T13:30:00+00:00"), ("1wk", "2026-10-05T04:00:00+00:00")):
            response = revision(frame=frame, clock=clock)
            response.update(provider="yahoo", omitted_rows=1, source_row_count=235,
                            completeness={"status": "bounded_partial"},
                            omitted_bar_rows=[{"row_index": 234, "timestamp": stamp, "open": None, "high": None,
                                               "low": None, "close": None, "volume": None}])
            diagnostics = []
            self.assertEqual(len(canonical_native_bars(response, frame, clock, diagnostics=diagnostics)), 234)
            self.assertEqual(diagnostics[0]["reason"], "quarantined_proved_unfinished_vendor_omission")
            self.assertFalse(diagnostics[0]["native_bar_admitted"])
            for mutation in ("missing_evidence", "wrong_count", "completed", "valid_ohlc", "unsupported", "bad_index"):
                altered = copy.deepcopy(response)
                if mutation == "missing_evidence":
                    del altered["omitted_bar_rows"]
                elif mutation == "wrong_count":
                    altered["source_row_count"] = 236
                elif mutation == "completed":
                    altered["omitted_bar_rows"][0]["timestamp"] = altered["bars"][-1]["timestamp"]
                elif mutation == "valid_ohlc":
                    altered["omitted_bar_rows"][0].update(open=10, high=11, low=9, close=10, volume=1)
                elif mutation == "unsupported":
                    altered["omitted_bar_rows"][0]["timestamp"] = "2026-10-09T13:31:17+00:00"
                else:
                    altered["omitted_bar_rows"][0]["row_index"] = 235
                with self.assertRaises(DeskError, msg=f"{frame}/{mutation}"):
                    canonical_native_bars(altered, frame, clock)
            completion = _native_period(_ms(stamp), frame)[1]
            with self.assertRaisesRegex(DeskError, "completed"):
                canonical_native_bars(response, frame, _dt(completion + 1_000))

    def test_unfinished_native_null_volume_is_excluded_before_ohlcv_validation(self):
        clock = datetime(2026, 10, 9, 13, 32, tzinfo=UTC)
        response = revision(clock=clock)
        partial = {"timestamp": "2026-10-09T13:30:00+00:00", "open": 10, "high": 11, "low": 9, "close": 10, "volume": None}
        response["bars"].append(partial)
        response["provider_asof"] = partial["timestamp"]
        diagnostics = []
        self.assertEqual(len(canonical_native_bars(response, "1h", clock, diagnostics=diagnostics)), 234)
        self.assertEqual(diagnostics[0]["reason"], "quarantined_unfinished_native_period")
        completed = _dt(_native_period(_ms(partial["timestamp"]), "1h")[1] + 1_000)
        response.update(observed_at=completed.isoformat(), fetched_at=completed.isoformat())
        with self.assertRaisesRegex(DeskError, "OHLCV"):
            canonical_native_bars(response, "1h", completed)

    def test_omitted_inconsistent_daily_candle_is_only_safe_while_its_period_is_unfinished(self):
        clock = datetime(2026, 10, 9, 14, 0, tzinfo=UTC)
        response = revision(frame="1d", clock=clock)
        response.update(provider="yahoo", omitted_rows=1, source_row_count=235, completeness={"status": "bounded_partial"},
            omitted_bar_rows=[{"row_index": 234, "timestamp": "2026-10-09T13:30:00+00:00", "open": 200, "high": 110,
                               "low": 100, "close": 105, "volume": 1000}])
        diagnostics = []
        self.assertEqual(len(canonical_native_bars(response, "1d", clock, diagnostics=diagnostics)), 234)
        self.assertEqual(diagnostics[0]["reason"], "quarantined_proved_unfinished_vendor_omission")
        completed = datetime(2026, 10, 9, 20, 0, 1, tzinfo=UTC)
        response.update(observed_at=completed.isoformat(), fetched_at=completed.isoformat())
        with self.assertRaisesRegex(DeskError, "completed"):
            canonical_native_bars(response, "1d", completed)

    def test_weekly_omitted_malformed_supplement_requires_exact_final_raw_marker(self):
        clock = datetime(2026, 10, 9, 14, 0, tzinfo=UTC)
        marker = "2026-10-09T13:59:58+00:00"
        response = revision(frame="1wk", clock=clock)
        response.update(provider="yahoo", omitted_rows=1, source_row_count=235, completeness={"status": "bounded_partial"},
            vendor_regular_market_timestamp=marker,
            omitted_bar_rows=[{"row_index": 234, "timestamp": marker, "open": 200, "high": 110,
                               "low": 100, "close": 105, "volume": 1000}])
        diagnostics = []
        self.assertEqual(len(canonical_native_bars(response, "1wk", clock, diagnostics=diagnostics)), 234)
        self.assertEqual(diagnostics[0]["reason"], "quarantined_yahoo_weekly_regular_market_supplement_omission")
        for mutation in ("missing_marker", "wrong_marker", "not_final", "future"):
            altered = copy.deepcopy(response)
            if mutation == "missing_marker":
                del altered["vendor_regular_market_timestamp"]
            elif mutation == "wrong_marker":
                altered["vendor_regular_market_timestamp"] = "2026-10-09T13:59:57+00:00"
            elif mutation == "not_final":
                altered["omitted_bar_rows"][0]["row_index"] = 233
            else:
                altered["omitted_bar_rows"][0]["timestamp"] = "2026-10-09T14:00:01+00:00"
                altered["vendor_regular_market_timestamp"] = "2026-10-09T14:00:01+00:00"
            with self.assertRaises(DeskError):
                canonical_native_bars(altered, "1wk", clock)
        hourly = revision(clock=clock)
        hourly.update({k: response[k] for k in ("provider", "omitted_rows", "source_row_count", "completeness", "vendor_regular_market_timestamp", "omitted_bar_rows")})
        with self.assertRaisesRegex(DeskError, "hourly"):
            canonical_native_bars(hourly, "1h", clock)
    def test_actual_pinned_daily_prefix_quarantines_backfill_and_repairs_pre_fix_cache(self):
        root = Path(__file__).resolve().parents[1]
        manifest = root / "strategies/research-input-manifest.json"
        member = root / "data/research-seed-r11/native-inputs/bars/1d/A.json.gz"
        if not manifest.is_file() or not member.is_file():
            self.skipTest("The exact pinned R11 A daily source is not restored in this environment")
        config = {"seed_directory": str(member.parents[2]), "seed_manifest_file": str(manifest),
                  "seed_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                  "forward_revision_policy": "retain_frozen_prefix_audit_minor"}
        row = self.install(sleeve="D20PV", symbols=["A"], **config)
        seed = self.runtime._seed("1d", "A", [config], _ms(CLOCK))
        self.assertEqual(len(seed), 2512)
        absent_stamp = _ms("2026-09-22T00:00:00+00:00")
        self.assertNotIn(absent_stamp, {b.timestamp_ms for b in seed})
        opened, completed = _native_period(absent_stamp, "1d")
        backfill = NativeBar(timestamp_ms=absent_stamp, completed_at_ms=completed, usable_at_ms=_ms(CLOCK),
                            executable_at_ms=opened, open=167.48, high=168.66, low=163.32, close=168.17, volume=2_713_389)
        future_stamp = _ms("2026-09-25T00:00:00+00:00")
        opened, completed = _native_period(future_stamp, "1d")
        future = NativeBar(timestamp_ms=future_stamp, completed_at_ms=completed, usable_at_ms=_ms(CLOCK),
                          executable_at_ms=opened, open=167, high=169, low=163, close=168, volume=2_000_000)
        observed = tuple(sorted((*seed[-20:], backfill, future), key=lambda b: b.timestamp_ms))
        diagnostics = []
        with self.store.transaction() as con:
            merged = self.runtime._merge(con, "1d", "A", observed, [config], diagnostics=diagnostics)
            self.assertEqual([b.timestamp_ms for b in merged[:2512]], [b.timestamp_ms for b in seed])
            self.assertEqual(len(merged), 2513)
            self.assertEqual(merged[-1].timestamp_ms, future_stamp)
            self.assertEqual(diagnostics[-1]["reason"], "quarantined_vendor_backfill_inside_immutable_native_prefix")
            # Simulate the already persisted pre-fix cache, including its
            # shifted candidate and cooldown. No financial execution occurred.
            corrupt = tuple(sorted((*seed, backfill, future), key=lambda b: b.timestamp_ms))
            con.execute("INSERT OR REPLACE INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", ("1d", "A", "a" * 64, CLOCK.isoformat(), self.runtime._pack(corrupt), "ready", None, CLOCK.isoformat()))
            con.execute("DELETE FROM a_tensor_prefix_bindings WHERE frame='1d' AND symbol='A'")
            con.execute("INSERT INTO a_tensor_cooldowns VALUES(?,?,?,?)", (row["id"], "A", 2534, future_stamp))
            con.execute("INSERT INTO a_tensor_candidates VALUES(?,?,?,?)", (row["id"], future_stamp, "A", "{}"))
            con.execute("INSERT INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", ("1d", future_stamp, "A", "ready", None))
            repaired = self.runtime._merge(con, "1d", "A", observed, [config], diagnostics=diagnostics)
            self.assertEqual([b.timestamp_ms for b in repaired], [b.timestamp_ms for b in merged])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_candidates").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cooldowns").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads").fetchone()[0], 0)
            self.assertTrue(any(d["reason"] == "restored_exact_pinned_native_prefix" for d in diagnostics))
            self.assertEqual(con.execute("SELECT original_rows FROM a_tensor_prefix_bindings").fetchone()[0], 2512)
            # Restarted acquisition must revisit old ready rows behind its
            # durable cursor; their missing binding cannot admit old signals.
            latest = latest_native_clock("1d", CLOCK)
            con.execute("DELETE FROM a_tensor_prefix_bindings")
            con.execute("INSERT OR REPLACE INTO a_tensor_cycles VALUES(?,?,?,?,?,?,?,?)", ("1d", latest["timestamp_ms"], latest["next_open_ms"], latest["next_open_ms"] + 300_000, 1, '["A"]', "complete", CLOCK.isoformat()))
            con.execute("INSERT INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", ("1d", latest["timestamp_ms"], "A", "ready", None))
            install = dict(con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (row["id"],)).fetchone())
            install["settings"] = json.loads(install["config"])
            self.assertEqual(self.runtime._unverified_prefix_barrier(con, "1d", [install], latest["timestamp_ms"], ["A"]), 0)
            self.assertEqual(con.execute("SELECT cursor FROM a_tensor_cycles").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cycle_reads").fetchone()[0], 0)

    def test_forward_census_excludes_one_unknown_at_99_percent_without_winner_filter(self):
        symbols = ["T" + str(i).zfill(3) for i in range(100)]
        self.providers = FixtureProviders(symbols)
        self.providers.fail.add("T099")
        self.runtime.providers = self.providers
        self.install(symbols=symbols, budget=256, missing_data_policy="exclude_unavailable_with_census_receipts")
        for sym in symbols:
            self.quote(sym)
        result = self.runtime.run_once(CLOCK)
        self.assertEqual(result["entries"], 10)
        self.assertEqual(result["status"], "degraded")
        census = self.runtime.snapshot()["installations"][0]["readiness"]["entry_eligibility"]
        self.assertEqual(census["assessed_count"], 100)
        self.assertEqual(census["known_fraction"], .99)
        self.assertEqual(census["unknown_entry_blocked_symbols"], ["T099"])
        self.assertTrue(census["entries_admissible"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents WHERE symbol='T099'").fetchone()[0], 0)
            self.assertTrue(all(json.loads(r[0]).get("entry_census_sha256") for r in con.execute("SELECT data FROM a_tensor_decisions WHERE role='entry' AND status='queued'")))

    def test_forward_census_mass_outage_still_blocks_every_entry(self):
        symbols = ["T" + str(i).zfill(3) for i in range(100)]
        self.providers = FixtureProviders(symbols)
        self.providers.fail.update({"T098", "T099"})
        self.runtime.providers = self.providers
        self.install(symbols=symbols, budget=256, missing_data_policy="exclude_unavailable_with_census_receipts")
        for sym in symbols:
            self.quote(sym)
        result = self.runtime.run_once(CLOCK)
        self.assertEqual(result["entries"], 0)
        self.assertEqual(result["status"], "data_blocked")
        self.assertFalse(self.runtime.snapshot()["installations"][0]["readiness"]["entry_eligibility"]["entries_admissible"])

    def test_source_provider_and_installed_engine_pins_are_enforced(self):
        self.install(expected_bar_provider="yahoo", engine_source_manifest_sha256=PIN)
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        self.assertEqual(self.runtime.snapshot()["installations"][0]["readiness"]["failed_reads"], 1)

    def test_engine_pin_mismatch_blocks_candidate_and_cooldown_commit(self):
        self.install(engine_source_manifest_sha256="e" * 64)
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_candidates").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_cooldowns").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT status FROM a_tensor_cycle_reads").fetchone()[0], "failed")

    def test_all_four_enter_and_fill_the_same_monday_open_then_exit_native_horizons(self):
        # Keep the whole20-week financial horizon inside the independently
        # evidenced2022–26 settlement calendar; uncovered years fail closed.
        opening = datetime(2026, 5, 4, 13, 30, 2, tzinfo=UTC)
        preclock = opening - timedelta(minutes=2)
        self.providers = FixtureProviders(frame="1h", clock=preclock)
        for frame in ("1d", "1wk"):
            self.providers.data[(frame, "AAA")] = revision(frame=frame, clock=preclock)
        self.runtime.providers = self.providers
        self.runtime.daily_evaluator = lambda sym, rows, asof: tuple({"sleeve_id": sleeve, "symbol": sym, "bar_index": 233, "selected": True,
                          "eligible": True, "reason": "selected", "predicted_net_qqq_excess": score,
                          "dollar_volume20": 20_000_000} for sleeve, score in (("D20_PV", .02), ("D20_TENSOR", .03)))
        installed = {sleeve: self.install(sleeve=sleeve) for sleeve in ("H1STATE", "WSTATE", "D20PV", "D20TENSOR")}
        self.assertEqual(self.runtime.run_once(preclock)["entries"], 0)
        for frame in ("1h", "1d", "1wk"):
            self.providers.data[(frame, "AAA")] = revision(frame=frame, clock=opening)
        self.quote(clock=opening)
        self.assertEqual(self.runtime.run_once(opening)["entries"], 4)
        self.assertEqual(self.trading.process(self.providers, opening)["fills"], 4)
        self.runtime.run_once(opening)  # Bind actual four fill anchors.
        for row in installed.values():
            self.runtime.set_enabled(row["id"], False)
        for frame, deadline in (("1h", datetime(2026, 5, 6, 19, 30, 2, tzinfo=UTC)),
                                ("1d", datetime(2026, 6, 2, 13, 30, 2, tzinfo=UTC)),
                                ("1wk", datetime(2026, 9, 21, 13, 30, 2, tzinfo=UTC))):
            old_bars = self.providers.data[(frame, "AAA")]["bars"]
            combined = {b["timestamp"]: b for b in old_bars}
            for b in native_history(frame, deadline, 500):
                if _ms(b["timestamp"]) > _ms(old_bars[-1]["timestamp"]):
                    combined[b["timestamp"]] = b
            response = revision(frame=frame, clock=deadline)
            response["bars"] = [combined[k] for k in sorted(combined)]
            response["provider_asof"] = response["bars"][-1]["timestamp"]
            self.providers.data[(frame, "AAA")] = response
            self.quote(clock=deadline)
            risk = self.runtime.service_exits(deadline)
            out = self.runtime.run_once(deadline)
            expected_exits = 2 if frame == "1d" else 1
            self.assertEqual(risk["exits"] + out["exits"], expected_exits)
            self.assertEqual(self.trading.process(self.providers, deadline)["fills"], expected_exits)
        with self.store.connect() as con:
            self.assertTrue(all(Decimal(r[0]) == 0 for r in con.execute("SELECT quantity FROM p_positions WHERE book_id!='main'")))
            exits = [json.loads(r[0]) for r in con.execute("SELECT data FROM a_tensor_decisions WHERE role='exit' AND status='queued'")]
            self.assertEqual(len(exits), 4)
            self.assertTrue(all(v["observed_hold_bars"] == 20 for v in exits))

    def test_hourly_opening_excludes_slow_daily_weekly_reads_but_admits_ready_census(self):
        opening = datetime(2026, 10, 12, 13, 30, 2, tzinfo=UTC)
        preclock = opening - timedelta(minutes=2)
        self.providers = FixtureProviders(frame="1d", clock=preclock)
        self.providers.data[("1wk", "AAA")] = revision(frame="1wk", clock=preclock)
        self.runtime.providers = self.providers
        self.runtime.daily_evaluator = lambda sym, rows, asof: tuple({"sleeve_id": sleeve, "symbol": sym, "bar_index": 233,
            "selected": True, "eligible": True, "reason": "selected", "predicted_net_qqq_excess": score,
            "dollar_volume20": 20_000_000} for sleeve, score in (("D20_PV", .02), ("D20_TENSOR", .03)))
        for sleeve in ("WSTATE", "D20PV", "D20TENSOR"):
            self.install(sleeve=sleeve)
        self.assertEqual(self.runtime.run_once(preclock)["entries"], 0)
        self.install(symbols=["AAA", "BBB"], budget=1)
        for sym in ("AAA", "BBB"):
            self.providers.data[("1h", sym)] = revision(sym=sym, clock=opening)
            self.quote(sym, clock=opening)
        self.providers.calls.clear()
        original_read = self.providers.bars
        def opening_read(sym, period, interval):
            self.assertEqual(interval, "60m", "Unrelated source acquisition consumed the hourly opening")
            return original_read(sym, period, interval)
        self.providers.bars = opening_read
        first = self.runtime.run_once(opening)
        self.assertEqual(first["entries"], 3)
        self.assertEqual(first["acquisition_deferred_frames"], ["1d", "1wk"])
        self.assertEqual([c[2] for c in self.providers.calls], ["60m"])
        self.assertEqual(self.trading.process(self.providers, opening)["fills"], 3)
        second = self.runtime.run_once(opening)
        self.assertEqual(second["entries"], 2)
        self.assertEqual(self.trading.process(self.providers, opening)["fills"], 2)
        # Once queued, the same window remains reserved until normal fills:
        # completing the hourly census does not permit unrelated source reads.
        self.assertEqual(self.runtime.run_once(opening)["acquisition_deferred_frames"], ["1d", "1wk"])

    def test_missing_action_probe_is_retryable_until_verified_within_same_opening(self):
        row = self.install()
        self.quote()
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO a_strategy_action_control VALUES(1,1,0)")
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions WHERE role='entry'").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT status FROM a_tensor_decisions WHERE role='action_coverage'").fetchone()[0], "deferred")
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO a_strategy_action_probes VALUES(?,?,'ok',NULL,?)", ("AAA", CLOCK.isoformat(), "fixture-current-action-receipt"))
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 1)

    def test_clock_only_observations_exit_even_when_split_price_basis_blocks_features(self):
        row = self.install()
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 1)
        self.runtime.run_once(CLOCK)
        later = datetime(2026, 10, 14, 13, 30, 2, tzinfo=UTC)
        old = self.providers.data[("1h", "AAA")]["bars"]
        combined = {b["timestamp"]: b for b in old}
        for b in native_history("1h", later, 300):
            if _ms(b["timestamp"]) > _ms(old[-1]["timestamp"]):
                combined[b["timestamp"]] = b
        response = revision(clock=later)
        response["bars"] = [combined[k] for k in sorted(combined)]
        # The vendor restates old prices after a2:1 split. Frozen prefix stays
        # unchanged, and the canonical native feature admission is blocked.
        for bar in response["bars"]:
            for field in ("open", "high", "low", "close"):
                bar[field] /= 2
        response["provider_asof"] = response["bars"][-1]["timestamp"]
        self.providers.data[("1h", "AAA")] = response
        self.quote(price=5, clock=later)
        with self.store.transaction() as con:
            con.execute("UPDATE p_positions SET quantity=CAST(CAST(quantity AS INTEGER)*2 AS TEXT) WHERE book_id=? AND symbol='AAA'", (row["book_id"],))
        output = self.runtime.run_once(later)
        self.assertEqual(output["entries"], 0)
        self.assertEqual(output["exits"], 1)
        self.assertEqual(output["status"], "data_blocked")
        self.assertEqual(self.trading.process(self.providers, later)["fills"], 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_observed_periods WHERE frame='1h' AND opening_ms>=?", (_ms(CLOCK.replace(second=0)),)).fetchone()[0], 20)
            self.assertEqual(Decimal(con.execute("SELECT quantity FROM p_positions WHERE book_id=?", (row["book_id"],)).fetchone()[0]), 0)

    def test_retryable_exit_blockage_recovers_with_linked_same_opening_receipt(self):
        row = self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 1)
        self.runtime.set_enabled(row["id"], False)
        later = datetime(2026, 10, 14, 13, 30, 2, tzinfo=UTC)
        original = self.providers.data[("1h", "AAA")]["bars"]
        combined = {b["timestamp"]: b for b in original}
        combined.update({b["timestamp"]: b for b in native_history("1h", later, 300)
                         if _ms(b["timestamp"]) > _ms(original[-1]["timestamp"])})
        response = revision(clock=later)
        response["bars"] = [combined[k] for k in sorted(combined)]
        response["provider_asof"] = response["bars"][-1]["timestamp"]
        self.providers.data[("1h", "AAA")] = response
        self.quote(clock=later)
        submit = self.trading.submit_strategy_intent
        self.trading.submit_strategy_intent = lambda *args, **kwargs: (_ for _ in ()).throw(DeskError("Corporate action probe unavailable"))
        self.assertEqual(self.runtime.run_once(later)["exits"], 0)
        self.trading.submit_strategy_intent = submit
        self.assertEqual(self.runtime.run_once(later)["exits"], 1)
        with self.store.connect() as con:
            blocked = con.execute("SELECT * FROM a_tensor_decisions WHERE role='exit_coverage'").fetchone()
            queued = con.execute("SELECT * FROM a_tensor_decisions WHERE role='exit'").fetchone()
            self.assertEqual(blocked["status"], "deferred")
            self.assertEqual(queued["status"], "queued")
            self.assertIsNotNone(con.execute("SELECT id FROM p_intents WHERE id=? AND side='sell'", (queued["intent_id"],)).fetchone())
        self.assertEqual(self.trading.process(self.providers, later)["fills"], 1)

    def test_pending_owed_exits_defer_other_symbol_entry_until_actual_slots_reopen(self):
        symbols = [f"{chr(65+i)}AA" for i in range(10)] + ["ZAA"]
        self.providers = FixtureProviders(symbols)
        self.runtime.providers = self.providers
        only_new = [False]
        class RotatingPolicy(FixturePolicy):
            def evaluate(inner, sym, snapshot, **kwargs):
                if (sym == "ZAA") != only_new[0]:
                    return SimpleNamespace(signal=None, reason="no_state_repair")
                return super(RotatingPolicy, inner).evaluate(sym, snapshot, **kwargs)
        self.runtime.policy_factory = RotatingPolicy
        row = self.install(symbols=symbols, budget=32)
        for sym in symbols:
            self.quote(sym, price=10 if sym == "ZAA" else 99)
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 10)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 10)
        only_new[0] = True
        later = datetime(2026, 10, 14, 13, 30, 2, tzinfo=UTC)
        for sym in symbols:
            original = self.providers.data[("1h", sym)]["bars"]
            combined = {b["timestamp"]: b for b in original}
            combined.update({b["timestamp"]: b for b in native_history("1h", later, 300)
                             if _ms(b["timestamp"]) > _ms(original[-1]["timestamp"])})
            response = revision(sym=sym, clock=later)
            response["bars"] = [combined[k] for k in sorted(combined)]
            response["provider_asof"] = response["bars"][-1]["timestamp"]
            self.providers.data[("1h", sym)] = response
            self.quote(sym, price=10 if sym == "ZAA" else 99, clock=later)
        result = self.runtime.run_once(later)
        self.assertEqual(result["exits"], 10)
        self.assertEqual(result["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions WHERE symbol='ZAA' AND role='entry'").fetchone()[0], 0)
        self.assertEqual(self.trading.process(self.providers, later)["fills"], 10)
        # T+1 sale proceeds remain unavailable, but the unused whole-share
        # sizing cushion funds an honestly smaller entry into the new name.
        recovered = self.runtime.run_once(later)
        with self.store.connect() as con:
            details = [dict(r) for r in con.execute("SELECT role,status,reason FROM a_tensor_decisions WHERE symbol='ZAA'")]
        self.assertEqual(recovered["entries"], 1, details)
        self.assertEqual(self.trading.process(self.providers, later)["fills"], 1)
        with self.store.connect() as con:
            self.assertGreater(Decimal(con.execute("SELECT quantity FROM p_positions WHERE book_id=? AND symbol='ZAA'", (row["book_id"],)).fetchone()[0]), 0)

    def test_post_seed_split_discovered_in_candidate_preflight_blocks_mixed_basis_entry(self):
        from backend.tensor_actions import TensorActions
        row = self.install(seed_manifest_file="injected-source-endpoint")
        # This fixture isolates the pinned seed-endpoint lookup from native
        # prices; actual member hashes/prefix checks have separate tests.
        self.runtime._seed_group = lambda *args: {"last_completed_at": _ms(CLOCK - timedelta(days=2)) // 1000}
        self.quote()
        actions = TensorActions(self.store, self.trading, self.providers)
        class Discovery:
            def probe_symbols(inner, symbols, **kwargs):
                actions.apply_event(row["book_id"], "AAA", {"kind": "split", "date": "2026-10-09", "numerator": 2, "denominator": 1}, "Fixture verified split receipt", CLOCK)
        self.runtime.bind_actions(Discovery())
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT status FROM a_tensor_decisions WHERE role='source_basis'").fetchone()[0], "deferred")
            self.assertEqual(con.execute("SELECT status FROM a_strategy_actions").fetchone()[0], "not_entitled")

    def test_caught_up_daily_and_hourly_network_reads_request_delta_without_rebasing(self):
        self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        self.trading.process(self.providers, CLOCK)
        self.runtime.run_once(CLOCK)
        self.assertEqual(self.providers.calls[-1][1], "5d")
        with self.store.connect() as con:
            coverage = self.runtime._unpack(con.execute("SELECT bars FROM a_tensor_coverage").fetchone()[0])
            self.assertEqual(len(coverage), 234)
            self.assertEqual(coverage[0].timestamp_ms, _ms(native_history()[0]["timestamp"]))

    def test_stale_owned_nav_mark_can_recover_within_the_same_opening(self):
        self.providers = FixtureProviders(["AAA", "BBB"])
        self.runtime.providers = self.providers
        selected = ["AAA"]
        class OnePolicy(FixturePolicy):
            def evaluate(inner, sym, snapshot, **kwargs):
                return super(OnePolicy, inner).evaluate(sym, snapshot, **kwargs) if sym == selected[0] else SimpleNamespace(signal=None, reason="no_state_repair")
        self.runtime.policy_factory = OnePolicy
        self.install(symbols=["AAA", "BBB"])
        self.quote("AAA")
        self.quote("BBB")
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        self.assertEqual(self.trading.process(self.providers, CLOCK)["fills"], 1)
        selected[0] = "BBB"
        later = CLOCK + timedelta(hours=1)
        for sym in ("AAA", "BBB"):
            self.providers.data[("1h", sym)] = revision(sym=sym, clock=later, count=235)
        self.quote("BBB", clock=later)
        self.assertEqual(self.runtime.run_once(later)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_tensor_decisions WHERE symbol='BBB' AND role='entry'").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT status FROM a_tensor_decisions WHERE symbol='BBB' AND role='mark_coverage'").fetchone()[0], "deferred")
        self.quote("AAA", clock=later)
        self.assertEqual(self.runtime.run_once(later)["entries"], 1)

    def test_held_only_exit_service_observes_new_twentieth_bar_before_broad_research(self):
        row = self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        self.trading.process(self.providers, CLOCK)
        later = datetime(2026, 10, 14, 13, 30, 2, tzinfo=UTC)
        original = self.providers.data[("1h", "AAA")]["bars"]
        combined = {b["timestamp"]: b for b in original}
        combined.update({b["timestamp"]: b for b in native_history("1h", later, 300)
                         if _ms(b["timestamp"]) > _ms(original[-1]["timestamp"])})
        response = revision(clock=later)
        response["bars"] = [combined[k] for k in sorted(combined)]
        response["provider_asof"] = response["bars"][-1]["timestamp"]
        self.providers.data[("1h", "AAA")] = response
        self.quote(clock=later)
        self.runtime.feature_extractor = lambda *a: (_ for _ in ()).throw(AssertionError("Risk service must never compute broad features"))
        self.providers.calls.clear()
        self.assertEqual(self.runtime.service_exits(later, acquire_native_clocks=False)["exits"], 0)
        self.assertEqual(self.providers.calls, [])
        result = self.runtime.service_exits(later)
        self.assertEqual(result["exits"], 1)
        self.assertEqual({c[0] for c in self.providers.calls}, {"AAA"})
        self.assertEqual(self.trading.process(self.providers, later)["fills"], 1)
        with self.store.connect() as con:
            self.assertEqual(Decimal(con.execute("SELECT quantity FROM p_positions WHERE book_id=?", (row["book_id"],)).fetchone()[0]), 0)
        self.assertEqual(self.runtime.service_exits(later)["exits"], 0)

    def test_failed_held_clock_reads_retry_on_bounded_cadence_without_inventing_bars(self):
        self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        self.trading.process(self.providers, CLOCK)
        later = CLOCK + timedelta(hours=1)
        self.providers.fail.add("AAA")
        self.providers.calls.clear()
        self.assertEqual(len(self.runtime.service_exits(later)["errors"]), 1)
        self.assertEqual(self.runtime.service_exits(later)["observed_periods"], 0)
        self.assertEqual(len(self.providers.calls), 1)
        self.providers.fail.clear()
        self.providers.data[("1h", "AAA")] = revision(clock=later, count=235)
        recovered = self.runtime.service_exits(later + timedelta(seconds=31))
        self.assertEqual(recovered["exits"], 0)
        self.assertEqual(recovered["observed_periods"], 1)
        self.assertEqual(len(self.providers.calls), 2)
        self.runtime.service_exits(later + timedelta(seconds=32))
        self.assertEqual(len(self.providers.calls), 2)

    def test_risk_clock_tape_preserves_postclose_fetch_knowledge_and_asof(self):
        row = self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        self.trading.process(self.providers, CLOCK)
        later = datetime(2026, 10, 14, 13, 30, 2, tzinfo=UTC)
        response = revision(clock=later, count=300)
        completion = latest_native_clock("1h", later)["completed_at_ms"]
        response["observed_at"] = _dt(completion - 10_000).isoformat()
        response["fetched_at"] = _dt(completion + 2_000).isoformat()
        self.providers.data[("1h", "AAA")] = response
        self.quote(clock=later)
        self.assertEqual(self.runtime.service_exits(later)["exits"], 1)
        with self.store.connect() as con:
            install = dict(con.execute("SELECT * FROM a_tensor_installations").fetchone())
            install["settings"] = json.loads(install["config"])
            state = dict(con.execute("SELECT * FROM a_tensor_position_state").fetchone())
            tape = con.execute("SELECT observed_at FROM a_tensor_observed_periods WHERE completed_ms=?", (completion,)).fetchone()
            self.assertEqual(tape[0], response["fetched_at"])
            self.assertEqual(len(self.runtime._held_periods(con, install, state, _dt(completion + 1_999))), 0)
            self.assertEqual(len(self.runtime._held_periods(con, install, state, _dt(completion + 2_000))), 20)

    def test_forward_gap_is_rejected_without_fabricating_a_bar_or_new_ordinal(self):
        self.install()
        self.quote()
        self.runtime.run_once(CLOCK)
        later = CLOCK + timedelta(hours=2)
        response = revision(clock=later)
        bars = canonical_native_bars(response, "1h", later)
        with self.store.transaction() as con:
            with self.assertRaisesRegex(DeskError, "omits"):
                self.runtime._merge(con, "1h", "AAA", bars[:-2] + bars[-1:], [{"forward_revision_policy": "retain_frozen_prefix_audit_minor"}])

    def test_verified_inactive_manifest_is_known_ineligible_and_keeps_enrollment(self):
        self.providers = FixtureProviders(["AAA", "BBB"])
        self.runtime.providers = self.providers
        manifest = Path(self.temp.name) / "inactive.json"
        raw = json.dumps({"retrieved_at": CLOCK.isoformat(), "records": [{"asset": {"symbol": "BBB", "status": "inactive", "tradable": False}, "response_sha256": "b" * 64}]}).encode()
        manifest.write_bytes(raw)
        row = self.install(symbols=["AAA", "BBB"], verified_ineligible_file=str(manifest), verified_ineligible_sha256=hashlib.sha256(raw).hexdigest())
        self.quote()
        self.assertEqual(self.runtime.run_once(CLOCK)["entries"], 1)
        self.assertEqual(row["config"]["symbols"], ["AAA", "BBB"])
        self.assertEqual(self.runtime.snapshot()["installations"][0]["readiness"]["known_ineligible"], 1)
        self.assertNotIn("BBB", [c[0] for c in self.providers.calls])

    def test_prefix_binding_barrier_preserves_attempted_failure_in_full_99_percent_census(self):
        symbols = ["T" + str(i).zfill(3) for i in range(100)]
        row = self.install(symbols=symbols, missing_data_policy="exclude_unavailable_with_census_receipts",
                           seed_directory="injected-unused-seed", seed_manifest_file="injected-unused-manifest")
        latest = latest_native_clock("1h", CLOCK)
        origin, opening = latest["timestamp_ms"], latest["next_open_ms"]
        with self.store.transaction() as con:
            con.execute("INSERT INTO a_tensor_cycles VALUES(?,?,?,?,?,?,?,?)", ("1h", origin, opening, opening + 300_000, 100, json.dumps(symbols), "collecting", CLOCK.isoformat()))
            con.executemany("INSERT INTO a_tensor_cycle_reads VALUES(?,?,?,?,?)", [("1h", origin, sym, "ready" if sym != "T099" else "failed", None if sym != "T099" else "price_basis_review_required") for sym in symbols])
            con.execute("INSERT INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", ("1h", "T099", "a" * 64, CLOCK.isoformat(), self.runtime._pack(canonical_native_bars(revision(), "1h", CLOCK)), "ready", None, CLOCK.isoformat()))
            install = dict(con.execute("SELECT * FROM a_tensor_installations WHERE id=?", (row["id"],)).fetchone())
            install["settings"] = json.loads(install["config"])
        result = {"entries": 0, "exits": 0}
        self.runtime._finish_cycle("1h", [install], origin, opening, 300_000, 100, [], symbols, CLOCK, None, self.providers, result, False)
        with self.store.connect() as con:
            failure = con.execute("SELECT status,error FROM a_tensor_cycle_reads WHERE symbol='T099'").fetchone()
            self.assertEqual(tuple(failure), ("failed", "price_basis_review_required"))
            cycle = con.execute("SELECT cursor,status FROM a_tensor_cycles").fetchone()
            self.assertEqual(tuple(cycle), (100, "degraded"))
            census = json.loads(con.execute("SELECT data FROM a_tensor_censuses").fetchone()[0])
            self.assertTrue(census["entries_admissible"])
            self.assertEqual(census["assessed_count"], 100)
            self.assertEqual(census["unknown_entry_blocked_symbols"], ["T099"])


if __name__ == "__main__":
    unittest.main()
