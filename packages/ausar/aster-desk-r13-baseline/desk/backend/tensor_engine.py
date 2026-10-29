"""Past-only transport to the source-pinned Tensor v690 research engine.

The caller owns exchange-calendar aggregation, canonical history origins and
actual first-seen timestamps. This module never fetches data or submits orders.
"""
from __future__ import annotations

import hashlib
import atexit
import json
import math
import os
import re
import selectors
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


ENGINE_ROOT = Path(__file__).resolve().parents[1] / "strategies" / "tensor_state_repair" / "engine"
SOURCE_MANIFEST_SHA256 = "5f38a63a611bdfbe62ceb6a0619f64559e7b9d136f51ac57597988d8da2ee28c"
VOTE_NAMES = ("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave")
SUPPORTED_FRAMES = ("1h", "1d", "1wk")
MAX_HISTORY_BARS = 50_000
_JS_SAFE_INTEGER = 2**53 - 1
_FEATURE_KEYS = {
    "symbol", "frame", "bar_index", "bar_id", "timestamp_ms", "completed_at_ms", "usable_at_ms",
    "executable_at_ms", "source_origin_timestamp_ms", "native_status", "open", "high", "low", "close",
    "volume", "votes", "bullish_votes", "bearish_votes", "total_votes", "atr14", "obv_slope5", "dollar_volume20",
}
STATE_ROW_KEYS = (
    "symbol", "interval", "bar_index", "timestamp", "completed_at", "usable_at",
    "source_origin_timestamp", "native_status", "open", "high", "low", "close", "volume",
    "vote_stoch", "vote_aroon", "vote_di", "vote_obv", "vote_squeeze", "vote_pivot", "vote_wave",
    "bullish_votes", "bearish_votes", "total_votes", "atr14", "obv_slope5", "dollar_volume20",
    "bar_id", "timestamp_ms", "completed_at_ms", "usable_at_ms", "executable_at_ms",
    "source_origin_timestamp_ms", "balance",
)
_STATE_WORKER_LIMIT = 8
_STATE_RESULT_LIMIT = 64 * 1024 * 1024
_STATE_WORKER_LOCK = threading.Lock()
_STATE_WORKER_SLOTS = threading.BoundedSemaphore(_STATE_WORKER_LIMIT)
_STATE_IDLE_WORKERS: list["_StateWorker"] = []
_STATE_ALL_WORKERS: list["_StateWorker"] = []


class TensorEngineError(RuntimeError):
    """Missing, invalid or unauthenticated native output; callers must abstain."""


class _StateWorker:
    """Exclusive line-framed Node process; no source or input history cache."""

    def __init__(self, node: str, root: Path):
        self.root = root
        self.process = subprocess.Popen(
            [node, str(root / "state_features.mjs"), "--worker"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=root,
        )
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        try:
            self.process.wait(timeout=1)
        finally:
            self.process.stdin.close()
            self.process.stdout.close()

    def request(self, encoded: bytes, deadline: float) -> bytes:
        payload, written, result = encoded + b"\n", 0, bytearray()
        with selectors.DefaultSelector() as selected:
            selected.register(self.process.stdin, selectors.EVENT_WRITE, "write")
            selected.register(self.process.stdout, selectors.EVENT_READ, "read")
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TensorEngineError("Native Tensor calculation timed out; no signal is available")
                events = selected.select(remaining)
                if not events:
                    raise TensorEngineError("Native Tensor calculation timed out; no signal is available")
                for key, _ in events:
                    if key.data == "write":
                        try:
                            sent = os.write(self.process.stdin.fileno(), payload[written:written + 65536])
                        except BlockingIOError:
                            continue
                        written += sent
                        if written == len(payload):
                            selected.unregister(self.process.stdin)
                    else:
                        try:
                            block = os.read(self.process.stdout.fileno(), 65536)
                        except BlockingIOError:
                            continue
                        if not block:
                            raise TensorEngineError("Native Tensor calculation failed; no signal is available")
                        result.extend(block)
                        if len(result) > _STATE_RESULT_LIMIT:
                            raise TensorEngineError("Native Tensor returned an oversized result")
                        if b"\n" in block:
                            if not result.endswith(b"\n") or result.count(b"\n") != 1 or written != len(payload):
                                raise TensorEngineError("Native Tensor state worker returned invalid framing")
                            return bytes(result)


def _close_state_workers():
    with _STATE_WORKER_LOCK:
        workers = list(_STATE_ALL_WORKERS)
        _STATE_ALL_WORKERS.clear()
        _STATE_IDLE_WORKERS.clear()
    for worker in workers:
        worker.close()


atexit.register(_close_state_workers)


def _run_state_process(node: str, encoded: bytes, timeout_seconds: float) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    if not _STATE_WORKER_SLOTS.acquire(timeout=timeout_seconds):
        raise TensorEngineError("Native Tensor worker capacity timed out; no signal is available")
    worker = None
    healthy = False
    try:
        root = ENGINE_ROOT.resolve()
        with _STATE_WORKER_LOCK:
            while _STATE_IDLE_WORKERS:
                candidate = _STATE_IDLE_WORKERS.pop()
                if candidate.root == root and candidate.process.poll() is None:
                    worker = candidate
                    break
                candidate.close()
                _STATE_ALL_WORKERS.remove(candidate)
            if worker is None:
                worker = _StateWorker(node, root)
                _STATE_ALL_WORKERS.append(worker)
        output = worker.request(encoded, deadline)
        healthy = True
        return output
    except (OSError, subprocess.SubprocessError) as exc:
        raise TensorEngineError("Native Tensor calculation could not be completed") from exc
    finally:
        if worker is not None:
            with _STATE_WORKER_LOCK:
                if healthy:
                    _STATE_IDLE_WORKERS.append(worker)
                else:
                    worker.close()
                    if worker in _STATE_ALL_WORKERS:
                        _STATE_ALL_WORKERS.remove(worker)
        _STATE_WORKER_SLOTS.release()


@dataclass(frozen=True)
class NativeBar:
    timestamp_ms: int
    completed_at_ms: int
    usable_at_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    executable_at_ms: int | None = None


def _bar_payload(bar: NativeBar) -> dict[str, Any]:
    # The same field order and values as dataclasses.asdict, without recursive
    # copying of these immutable scalar-only rows on every worker request.
    return {
        "timestamp_ms": bar.timestamp_ms, "completed_at_ms": bar.completed_at_ms,
        "usable_at_ms": bar.usable_at_ms, "open": bar.open, "high": bar.high,
        "low": bar.low, "close": bar.close, "volume": bar.volume,
        "executable_at_ms": bar.executable_at_ms,
    }


@dataclass(frozen=True)
class TensorFeature:
    symbol: str
    frame: str
    bar_index: int
    bar_id: str
    timestamp_ms: int
    completed_at_ms: int
    usable_at_ms: int
    executable_at_ms: int | None
    source_origin_timestamp_ms: int
    native_status: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    votes: tuple[int | None, ...]
    bullish_votes: int
    bearish_votes: int
    total_votes: int
    atr14: float | None
    obv_slope5: float | None
    dollar_volume20: float | None

    @property
    def balance(self) -> int:
        return self.bullish_votes - self.bearish_votes

    @property
    def b(self) -> int:
        return self.balance

    @property
    def strategy_ready(self) -> bool:
        return self.bar_index >= 233 and self.native_status == "ready"

    @property
    def vote_values(self) -> dict[str, int | None]:
        return dict(zip(VOTE_NAMES, self.votes, strict=True))


@dataclass(frozen=True)
class TensorSnapshot:
    symbol: str
    frame: str
    as_of_ms: int
    source_origin_timestamp_ms: int
    source_bar_count: int
    input_sha256: str
    source_manifest_sha256: str
    features: tuple[TensorFeature, ...]

    @property
    def latest(self) -> TensorFeature:
        return self.features[-1]

    @property
    def state_repair_change(self) -> int | None:
        return self.latest.balance - self.features[0].balance if len(self.features) == 4 else None

    @property
    def increasing_vote_count(self) -> int:
        if len(self.features) != 4:
            return 0
        return sum(any(
            previous.votes[k] is not None and current.votes[k] is not None
            and current.votes[k] > previous.votes[k]
            for previous, current in zip(self.features, self.features[1:])
        ) for k in range(7))


@dataclass(frozen=True)
class TensorFeatureHistory:
    snapshot: TensorSnapshot
    rows: tuple[dict[str, Any], ...]


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_engine_source() -> dict[str, Any]:
    """Verify the pinned manifest and every dependency before any execution."""
    try:
        manifest_path = ENGINE_ROOT / "SOURCE_MANIFEST.json"
        if manifest_path.is_symlink() or _hash_file(manifest_path) != SOURCE_MANIFEST_SHA256:
            raise TensorEngineError("Tensor source manifest does not match the executable strategy pin")
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("schema") != "aster-tensor-native-source/1" or len(manifest.get("files", [])) != 26:
            raise TensorEngineError("Tensor source manifest has invalid scope")
        for entry in manifest["files"]:
            relative = Path(entry["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise TensorEngineError("Tensor source manifest contains an invalid path")
            path = ENGINE_ROOT / relative
            if path.is_symlink() or path.stat().st_size != entry["size"] or _hash_file(path) != entry["sha256"]:
                raise TensorEngineError("Tensor dependency differs from the frozen executable source")
        return manifest
    except TensorEngineError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise TensorEngineError("Tensor source closure is unavailable or invalid") from exc


def source_manifest_sha256() -> str:
    verify_engine_source()
    return SOURCE_MANIFEST_SHA256


def _clock(value: Any) -> bool:
    return type(value) is int and 0 < value <= _JS_SAFE_INTEGER


def _number(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _normalize_bars(bars: Sequence[NativeBar | Mapping[str, Any]], as_of_ms: int) -> tuple[NativeBar, ...]:
    if not _clock(as_of_ms):
        raise TensorEngineError("as_of_ms must be positive integer UTC milliseconds")
    if not isinstance(bars, (list, tuple)) or not 0 < len(bars) <= MAX_HISTORY_BARS:
        raise TensorEngineError("A nonempty bounded full canonical bar history is required")
    normalized = []
    prior_start = prior_completed = 0
    for value in bars:
        try:
            bar = value if isinstance(value, NativeBar) else NativeBar(**value)
        except (TypeError, ValueError) as exc:
            raise TensorEngineError("Invalid native OHLCV bar shape") from exc
        if not all(_clock(getattr(bar, k)) for k in ("timestamp_ms", "completed_at_ms", "usable_at_ms")):
            raise TensorEngineError("Native bar clocks must be positive integer UTC milliseconds")
        if bar.timestamp_ms % 1000 or bar.timestamp_ms <= prior_start:
            raise TensorEngineError("Native bar starts must be whole-second aligned and strictly increasing")
        if (bar.completed_at_ms <= bar.timestamp_ms or bar.completed_at_ms <= prior_completed
                or bar.usable_at_ms < bar.completed_at_ms or bar.usable_at_ms > as_of_ms):
            raise TensorEngineError("Native bars must be completed, monotone and available at as-of")
        if bar.executable_at_ms is not None and (
            not _clock(bar.executable_at_ms) or not bar.timestamp_ms <= bar.executable_at_ms < bar.completed_at_ms
        ):
            raise TensorEngineError("Executable clock must identify the observed native period open")
        if not all(_number(getattr(bar, k)) for k in ("open", "high", "low", "close", "volume")):
            raise TensorEngineError("Native OHLCV must contain finite numeric values")
        if (min(bar.open, bar.high, bar.low, bar.close) <= 0 or bar.volume < 0
                or bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close) or bar.high < bar.low):
            raise TensorEngineError("Native OHLCV has invalid prices, volume or candle envelope")
        normalized.append(bar)
        prior_start, prior_completed = bar.timestamp_ms, bar.completed_at_ms
    return tuple(normalized)


def _feature(raw: Mapping[str, Any], bar: NativeBar, index: int, symbol: str, frame: str, origin: int) -> TensorFeature:
    if set(raw) != _FEATURE_KEYS:
        raise TensorEngineError("Native feature output has an unexpected schema")
    expected = {
        "symbol": symbol, "frame": frame, "bar_index": index,
        "bar_id": f"{symbol}:{frame}:{bar.timestamp_ms}", "source_origin_timestamp_ms": origin,
        **_bar_payload(bar),
    }
    for key, value in expected.items():
        if raw[key] != value:
            raise TensorEngineError("Native output does not match its input bar identity")
    votes = raw["votes"]
    if not isinstance(votes, list) or len(votes) != 7 or any(
        v is not None and (type(v) is not int or v not in (-1, 1)) for v in votes
    ):
        raise TensorEngineError("Native vote output must contain seven signed or unavailable channels")
    counts = {"bullish_votes": sum(v == 1 for v in votes), "bearish_votes": sum(v == -1 for v in votes),
              "total_votes": sum(v is not None for v in votes)}
    if any(type(raw[k]) is not int or raw[k] != v for k, v in counts.items()):
        raise TensorEngineError("Native published vote counts do not reconcile")
    for key in ("atr14", "obv_slope5", "dollar_volume20"):
        if raw[key] is not None and not _number(raw[key]):
            raise TensorEngineError("Native numeric feature is nonfinite")
    minimum = 4 if frame == "1wk" else 35
    if raw["native_status"] != ("ready" if index + 1 >= minimum else "warming"):
        raise TensorEngineError("Native readiness output differs from the source minimum")
    return TensorFeature(**{**raw, "votes": tuple(votes)})


def _validate_state_row(row: dict[str, Any], bar: NativeBar, index: int,
                        symbol: str, frame: str, origin: int):
    """Authenticate every state row without allocating discarded dataclasses."""
    if (
        row["symbol"], row["interval"], row["bar_index"], row["bar_id"],
        row["timestamp_ms"], row["completed_at_ms"], row["usable_at_ms"], row["executable_at_ms"],
        row["source_origin_timestamp_ms"], row["open"], row["high"], row["low"], row["close"], row["volume"],
        row["timestamp"], row["completed_at"], row["usable_at"], row["source_origin_timestamp"],
    ) != (
        symbol, frame, index, f"{symbol}:{frame}:{bar.timestamp_ms}",
        bar.timestamp_ms, bar.completed_at_ms, bar.usable_at_ms, bar.executable_at_ms,
        origin, bar.open, bar.high, bar.low, bar.close, bar.volume,
        bar.timestamp_ms // 1000, math.ceil(bar.completed_at_ms / 1000), math.ceil(bar.usable_at_ms / 1000), origin // 1000,
    ):
        raise TensorEngineError("Native state-history identity, clocks or OHLCV differ from input")
    bullish = bearish = 0
    for channel in VOTE_NAMES:
        value = row["vote_" + channel]
        if value is None:
            continue
        if type(value) is not int or value not in (-1, 1):
            raise TensorEngineError("Native state-history contains an invalid signed vote")
        if value == 1:
            bullish += 1
        else:
            bearish += 1
    for key, value in (("bullish_votes", bullish), ("bearish_votes", bearish),
                       ("total_votes", bullish + bearish), ("balance", bullish - bearish)):
        if type(row[key]) is not int or row[key] != value:
            raise TensorEngineError("Native state-history vote counts or balance do not reconcile")
    minimum = 4 if frame == "1wk" else 35
    if row["native_status"] != ("ready" if index + 1 >= minimum else "warming"):
        raise TensorEngineError("Native state-history readiness differs from the source minimum")
    for key in ("atr14", "obv_slope5", "dollar_volume20"):
        if row[key] is not None and not _number(row[key]):
            raise TensorEngineError("Native state-history contains nonfinite numeric output")


def _run(symbol: str, frame: str, bars: Sequence[NativeBar | Mapping[str, Any]], as_of_ms: int,
         timeout_seconds: float, include_full_rows: bool, state_only: bool = False) -> TensorFeatureHistory:
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,15}", symbol):
        raise TensorEngineError("Explicit normalized equity symbol required")
    if frame not in SUPPORTED_FRAMES:
        raise TensorEngineError("Native frame must be 1h, 1d or 1wk")
    if not _number(timeout_seconds) or not 0 < timeout_seconds <= 300:
        raise TensorEngineError("Native process timeout must be positive and bounded")
    source = _normalize_bars(bars, as_of_ms)
    verify_engine_source()
    node = shutil.which("node")
    if node is None:
        raise TensorEngineError("Node.js is unavailable; the Tensor strategy must abstain")
    request = {"schema": "aster-tensor-native-request/1", "symbol": symbol, "frame": frame,
               "as_of_ms": as_of_ms, "bars": [_bar_payload(b) for b in source]}
    base = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
    input_sha256 = hashlib.sha256(base).hexdigest()
    encoded = base[:-1] + (b',"include_full_rows":true}' if include_full_rows else b',"include_full_rows":false}')
    try:
        if state_only:
            output = _run_state_process(node, encoded, timeout_seconds)
        else:
            process = subprocess.run([node, str(ENGINE_ROOT / "native_features.mjs")], input=encoded,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds,
                                     check=False, cwd=ENGINE_ROOT)
            if process.returncode != 0:
                # Do not expose arbitrary native output in user-facing errors.
                raise TensorEngineError("Native Tensor calculation failed; no signal is available")
            output = process.stdout
    except subprocess.TimeoutExpired as exc:
        raise TensorEngineError("Native Tensor calculation timed out; no signal is available") from exc
    except OSError as exc:
        raise TensorEngineError("Native Tensor calculation could not be started") from exc
    try:
        result = json.loads(output)
        if not isinstance(result, dict) or result.get("schema") != "aster-tensor-native-result/1":
            raise TensorEngineError("Native Tensor returned an invalid result schema")
        expected_count = min(4, len(source))
        if not isinstance(result.get("features"), list) or len(result["features"]) != expected_count:
            raise TensorEngineError("Native Tensor returned an incomplete component history")
        offset = len(source) - expected_count
        features = tuple(_feature(raw, source[index], index, symbol, frame, source[0].timestamp_ms)
                         for index, raw in enumerate(result["features"], offset))
        snapshot = TensorSnapshot(symbol, frame, as_of_ms, source[0].timestamp_ms, len(source),
                                  input_sha256, SOURCE_MANIFEST_SHA256, features)
        rows: tuple[dict[str, Any], ...] = ()
        if include_full_rows:
            header = result.get("full_header")
            raw_rows = result.get("full_rows")
            if state_only:
                if header != list(STATE_ROW_KEYS):
                    raise TensorEngineError("Native state-history header differs from the pinned state transport")
            elif not isinstance(header, list) or len(header) != 93 or len(set(header)) != 93:
                raise TensorEngineError("Native full-history header differs from the sealed 93-field exporter")
            if not isinstance(raw_rows, list) or len(raw_rows) != len(source):
                raise TensorEngineError("Native full-history row denominator does not match source bars")
            header_keys = set(header)
            for i, row in enumerate(raw_rows):
                if not isinstance(row, dict) or set(row) != header_keys:
                    raise TensorEngineError("Native full-history row schema is invalid")
                if state_only:
                    _validate_state_row(row, source[i], i, symbol, frame, source[0].timestamp_ms)
                    if i >= offset:
                        state = {key: row[key] for key in _FEATURE_KEYS if key not in ("frame", "votes")}
                        state["frame"] = row["interval"]
                        state["votes"] = [row["vote_" + channel] for channel in VOTE_NAMES]
                        if _feature(state, source[i], i, symbol, frame, source[0].timestamp_ms) != features[i - offset]:
                            raise TensorEngineError("Native state-history and component snapshot differ")
                    continue
                if (row["symbol"] != symbol or row["interval"] != frame or row["bar_index"] != i
                        or row["timestamp"] != source[i].timestamp_ms // 1000
                        or row["completed_at"] != math.ceil(source[i].completed_at_ms / 1000)
                        or row["usable_at"] != math.ceil(source[i].usable_at_ms / 1000)
                        or row["source_origin_timestamp"] != source[0].timestamp_ms // 1000):
                    raise TensorEngineError("Native full-history identity or clocks differ from input")
                if any(isinstance(v, float) and not math.isfinite(v) for v in row.values()):
                    raise TensorEngineError("Native full-history contains nonfinite numeric output")
            rows = tuple(raw_rows)
        elif result.get("full_rows") is not None or result.get("full_header") is not None:
            raise TensorEngineError("Native component-only result contains unexpected payloads")
        return TensorFeatureHistory(snapshot, rows)
    except TensorEngineError:
        raise
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        raise TensorEngineError("Native Tensor result could not be authenticated") from exc


def extract_tensor_features(symbol: str, frame: str, bars: Sequence[NativeBar | Mapping[str, Any]],
                            as_of_ms: int, timeout_seconds: float = 30) -> TensorSnapshot:
    """Return the final four exact native component states from a full prefix."""
    return _run(symbol, frame, bars, as_of_ms, timeout_seconds, False).snapshot


def extract_native_feature_rows(symbol: str, frame: str, bars: Sequence[NativeBar | Mapping[str, Any]],
                                as_of_ms: int, timeout_seconds: float = 30) -> TensorFeatureHistory:
    """Return all exact 93-field native rows plus the component snapshot.

    All bar ordinals are relative to the supplied, explicitly bound origin.
    The caller must preserve that origin across restarts and model inference.
    """
    return _run(symbol, frame, bars, as_of_ms, timeout_seconds, True)


def extract_state_feature_rows(symbol: str, frame: str, bars: Sequence[NativeBar | Mapping[str, Any]],
                               as_of_ms: int, timeout_seconds: float = 30) -> TensorFeatureHistory:
    """Return exact native STATE_REPAIR history without unrelated exporters.

    The entire canonical prefix reaches the unchanged engine once. All seven
    state votes, counts, ATR14, OBV slope5 and the original DV20 summation are
    preserved. Full 93-field extraction remains the separate daily-model API.
    """
    return _run(symbol, frame, bars, as_of_ms, timeout_seconds, True, state_only=True)
