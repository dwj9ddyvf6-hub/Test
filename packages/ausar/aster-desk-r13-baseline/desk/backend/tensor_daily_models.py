"""Frozen R11 daily twenty-bar forecasts for two independent paper sleeves.

The numerical tree assets are exact exports of the original C01 models. This
module does not fit, calibrate, read future returns, or unpickle anything. Daily
sampling requires the complete canonical per-symbol source history; a rolling
window cannot preserve the original modulo-20 sampling or state ages.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence


ASSET_ROOT = Path(__file__).resolve().parents[1] / "strategies/tensor_daily20/models"
MANIFEST_SHA256 = "9be2845edd541c0a48ef33063cab165689e25bdbbd7e7a6df94e30e66506d757"
SOURCE_SHA256 = {
    "price_volume": "36216e1b8f0000066cf51356b70a7a54a885e154ee417a42d360ab921d634965",
    "price_volume_plus_tensor": "e7776b115b908380dc3df85210302736d306d38538568e91e26cf3f6e0c4b300",
}
PRICE_VOLUME_COLUMNS = (
    "return20", "return60", "atr_pct", "rvol", "log_dollar_volume20", "close_ema21_distance_atr",
)
VOTE_COLUMNS = tuple("vote_" + x for x in ("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave"))
TENSOR_COLUMNS = VOTE_COLUMNS + (
    "balance_delta3", "ribbon_inversion_count", "ribbon_repair3", "ribbon_width", "ribbon_slope",
    "normalized_obv_slope5", "squeeze_on", "normalized_squeeze_momentum", "squeeze_length",
    "first_squeeze_release", "squeeze_release_age", "ut_state", "ut_state_age", "mcdx_position",
    "mcdx_position_delta3", "normalized_macd_histogram", "normalized_sign_entropy20", "entropy_delta3",
    "efficiency10", "efficiency_delta3", "prior_sell_avwap_distance_atr", "overhead60_atr",
)
ALL_COLUMNS = PRICE_VOLUME_COLUMNS + TENSOR_COLUMNS
REQUIRED_NATIVE_COLUMNS = frozenset((
    "symbol", "bar_index", "timestamp", "completed_at", "usable_at", "source_origin_timestamp",
    "native_status", "open", "close", "volume", "atr14", "return20", "return60", "rvol",
    "dollar_volume20", "ema21", "bullish_votes", "bearish_votes", "ribbon_inversion_count",
    "ribbon_width", "ribbon_slope", "obv_slope5", "squeeze_on", "squeeze_momentum", "squeeze_length",
    "ut_regime", "mcdx_position", "mcdx_position_delta3", "macd_histogram", "efficiency10",
    "normalized_sign_entropy20", "prior_sell_avwap", "prior_sell_completed_at", "overhead60_atr",
)) | frozenset(VOTE_COLUMNS)
EXCLUDED_SYMBOLS = frozenset(("QQQ", "SPY", "B", "GOLD"))
MODEL_SLEEVES = (("price_volume", "D20_PV"), ("price_volume_plus_tensor", "D20_TENSOR"))


class DailyModelInputError(ValueError):
    """Native source history or clock does not satisfy the frozen contract."""


class DailyModelIntegrityError(ValueError):
    """An immutable numerical model or its provenance identity differs."""


@dataclass(frozen=True)
class DailySourceAnchor:
    symbol: str
    first_timestamp: int
    last_timestamp: int
    original_rows: int
    input_sha256: str
    native_feature_sha256: str
    phase: int

    @property
    def first_timestamp_ms(self) -> int:
        return self.first_timestamp * 1000


@dataclass(frozen=True)
class FrozenDaily20Model:
    name: str
    columns: tuple[str, ...]
    medians: tuple[float, ...]
    threshold: float
    baseline: float
    # Each node: (value, feature, threshold, left, right, leaf, missing_left).
    trees: tuple[tuple[tuple, ...], ...]
    source_sha256: str

    def impute(self, features: Mapping[str, object]) -> tuple[float, ...]:
        if any(column not in features for column in self.columns):
            raise DailyModelInputError("A frozen model feature is absent")
        return tuple(value if (value := _number(features[column])) is not None else median
                     for column, median in zip(self.columns, self.medians))

    def predict(self, features: Mapping[str, object]) -> float:
        vector = self.impute(features)
        prediction = self.baseline
        for tree in self.trees:
            j = 0
            while not tree[j][5]:
                node = tree[j]
                j = node[3] if vector[node[1]] <= node[2] else node[4]
            prediction += tree[j][0]
        return prediction

    def selects(self, prediction: float) -> bool:
        if not math.isfinite(prediction):
            raise DailyModelInputError("Forecast must be finite")
        return prediction >= self.threshold


@dataclass(frozen=True)
class Daily20Decision:
    sleeve_id: str
    symbol: str
    frame: str
    bar_index: int
    decision_at_ms: int
    hold_bars: int
    entry_bar_index: int
    target_exit_bar_index: int
    predicted_net_qqq_excess: float | None
    threshold: float
    close: float | None
    dollar_volume20: float | None
    phase: int
    anchor_timestamp_ms: int
    eligible: bool
    selected: bool
    reason: str
    feature_vector: tuple[float, ...]
    source_model_sha256: str

    @property
    def score(self) -> float | None:
        return self.predicted_net_qqq_excess

    @property
    def decision_at(self) -> int:
        """Epoch seconds, matching the original research ledger."""
        return self.decision_at_ms // 1000

    @property
    def cooldown_until_index(self) -> int:
        return self.bar_index + 20


_ASSETS: tuple[dict[str, FrozenDaily20Model], dict[str, DailySourceAnchor]] | None = None


def _number(value: object) -> float | None:
    # Mirrors pandas.to_numeric(errors='coerce') followed by finite-value handling.
    if value is None or isinstance(value, bool):
        return float(value) if isinstance(value, bool) else None
    try:
        v = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return v if math.isfinite(v) else None


def _integer(value: object, name: str) -> int:
    v = _number(value)
    if isinstance(value, bool) or v is None or v != int(v):
        raise DailyModelInputError(name + " must be a finite integer")
    return int(v)


def _ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return _number(a / b)


def _difference(a: float | None, b: float | None) -> float | None:
    return _number(a - b) if a is not None and b is not None else None


def _read_assets(directory: Path) -> tuple[dict[str, FrozenDaily20Model], dict[str, DailySourceAnchor]]:
    manifest_bytes = (directory / "MANIFEST.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise DailyModelIntegrityError("Frozen model manifest identity differs")
    manifest = json.loads(manifest_bytes)
    if manifest.get("new_fits") != 0 or manifest.get("new_calibrations") != 0:
        raise DailyModelIntegrityError("Model asset provenance authorizes unexpected fits")
    bodies = {}
    for item in manifest["files"]:
        name = item["path"]
        if Path(name).name != name or name in bodies:
            raise DailyModelIntegrityError("Invalid numerical model asset path")
        body = (directory / name).read_bytes()
        if len(body) != item["bytes"] or hashlib.sha256(body).hexdigest() != item["sha256"]:
            raise DailyModelIntegrityError("Frozen numerical asset identity differs: " + name)
        bodies[name] = body
    models = {}
    for name, _ in MODEL_SLEEVES:
        p = json.loads(bodies[name + ".json"])
        expected_columns = PRICE_VOLUME_COLUMNS if name == "price_volume" else ALL_COLUMNS
        if (p.get("schema") != "tensor-daily20-frozen-numerical-model/1" or p.get("new_fits") != 0
                or p["source_sha256"] != SOURCE_SHA256[name]
                or tuple(p["columns"]) != expected_columns or p["frame"] != "1d" or p["hold_bars"] != 20
                or len(p["trees"]) != 100 or len(p["medians"]) != len(expected_columns)):
            raise DailyModelIntegrityError("Frozen numerical model contract differs")
        source = bodies[p["source_filename"]]
        if hashlib.sha256(source).hexdigest() != SOURCE_SHA256[name]:
            raise DailyModelIntegrityError("Original frozen model body differs")
        trees = tuple(tuple((float(n["value"]), int(n["feature"]), float(n["threshold"]),
                             int(n["left"]), int(n["right"]), bool(n["leaf"]), bool(n["missing_left"]))
                            for n in tree) for tree in p["trees"])
        # The identity check is primary; validate structure before numerical use too.
        for tree in trees:
            visited = set()
            pending = [0]
            while pending:
                j = pending.pop()
                if j in visited or not 0 <= j < len(tree):
                    raise DailyModelIntegrityError("Invalid frozen tree topology")
                visited.add(j)
                node = tree[j]
                if not math.isfinite(node[0]) or not math.isfinite(node[2]):
                    raise DailyModelIntegrityError("Nonfinite frozen tree value")
                if not node[5]:
                    if not 0 <= node[1] < len(expected_columns):
                        raise DailyModelIntegrityError("Invalid frozen tree feature")
                    pending.extend((node[3], node[4]))
            if len(visited) != len(tree):
                raise DailyModelIntegrityError("Unreachable frozen tree node")
        model = FrozenDaily20Model(name, expected_columns, tuple(float(x) for x in p["medians"]),
                                   float(p["threshold"]), float(p["baseline"]), trees, p["source_sha256"])
        if not all(math.isfinite(x) for x in (*model.medians, model.threshold, model.baseline)):
            raise DailyModelIntegrityError("Nonfinite frozen metadata")
        models[name] = model
    a = json.loads(bodies["DAILY_SOURCE_ANCHORS.json"])
    anchors = {symbol: DailySourceAnchor(symbol, int(p["first_timestamp"]), int(p["last_timestamp"]),
                                        int(p["original_rows"]), p["input_sha256"],
                                        p["native_feature_sha256"], int(p["phase"]))
               for symbol, p in a["symbols"].items()}
    if len(anchors) != 1817 or any(anchor.phase != phase(symbol) for symbol, anchor in anchors.items()):
        raise DailyModelIntegrityError("Canonical daily source anchors differ")
    return models, anchors


def load_frozen_models(asset_directory: Path | str | None = None) -> dict[str, FrozenDaily20Model]:
    """Verify all immutable assets; custom directories never bypass hash checks."""
    global _ASSETS
    if asset_directory is not None:
        return _read_assets(Path(asset_directory))[0]
    if _ASSETS is None:
        _ASSETS = _read_assets(ASSET_ROOT)
    return dict(_ASSETS[0])


def verify_model_assets() -> dict:
    models, anchors = _read_assets(ASSET_ROOT)
    return {"status": "PASS", "manifest_sha256": MANIFEST_SHA256, "new_fits": 0,
            "new_calibrations": 0, "canonical_symbols": len(anchors),
            "model_source_sha256": {name: model.source_sha256 for name, model in models.items()}}


def anchor_for(symbol: str) -> DailySourceAnchor:
    load_frozen_models()
    try:
        return _ASSETS[1][symbol]  # type: ignore[index]
    except KeyError as exc:
        raise DailyModelInputError("No original daily source anchor for " + symbol + "; enrollment must be explicit") from exc


def phase(symbol: str) -> int:
    return int(hashlib.sha256(symbol.encode("utf-8")).hexdigest(), 16) % 20


def feature_frame(rows: Sequence[Mapping[str, object]]) -> tuple[dict[str, float | None], ...]:
    """The C01 35-column past-only transform in its original column order.

    Missing scalar observations remain unavailable until the frozen model's own
    training medians are applied. Published neutral votes become zero only on
    ready native rows. No column with a forward label is ever consulted.
    """
    converted = [{key: _number(row.get(key)) for key in REQUIRED_NATIVE_COLUMNS
                  if key not in {"symbol", "native_status", "ut_regime"}} for row in rows]
    result = []
    seen_on = False
    off_age = None
    last_ut = None
    ut_age = 0
    for i, (row, v) in enumerate(zip(rows, converted)):
        if not REQUIRED_NATIVE_COLUMNS.issubset(row):
            raise DailyModelInputError("Required native feature columns are absent")
        close, atr = v["close"], v["atr14"]
        if atr == 0:
            atr = None
        lag = converted[i - 3] if i >= 3 else {}
        balance = _difference(v["bullish_votes"], v["bearish_votes"])
        old_balance = _difference(lag.get("bullish_votes"), lag.get("bearish_votes"))
        volume = [p["volume"] for p in converted[max(0, i - 19):i + 1]]
        mean_volume = math.fsum(volume) / 20 if len(volume) == 20 and all(x is not None for x in volume) else None
        dollar = v["dollar_volume20"]
        log_dollar = math.log1p(dollar) if dollar is not None and dollar > -1 else None
        on = v["squeeze_on"]
        if on == 1:
            release_age = 0.0
            seen_on, off_age = True, 0
        elif on == 0 and seen_on and off_age is not None:
            off_age += 1
            release_age = float(off_age)
        else:
            off_age = None
            release_age = None
        regime = str(row["ut_regime"] or "").lower()
        direction = 1 if regime == "bullish" else -1 if regime == "bearish" else None
        if direction is None:
            last_ut, ut_age = None, 0
            encoded_ut, encoded_age = None, None
        else:
            ut_age = ut_age + 1 if last_ut == direction else 0
            last_ut = direction
            encoded_ut, encoded_age = float(direction), float(ut_age)
        first_release = float(on == 0 and i >= 3 and all(p["squeeze_on"] == 1 for p in converted[i-3:i]))
        f = {
            "return20": v["return20"], "return60": v["return60"], "atr_pct": _ratio(atr, close),
            "rvol": v["rvol"], "log_dollar_volume20": log_dollar,
            "close_ema21_distance_atr": _ratio(_difference(close, v["ema21"]), atr),
            "balance_delta3": _difference(balance, old_balance),
            "ribbon_inversion_count": v["ribbon_inversion_count"],
            "ribbon_repair3": _difference(lag.get("ribbon_inversion_count"), v["ribbon_inversion_count"]),
            "ribbon_width": v["ribbon_width"], "ribbon_slope": v["ribbon_slope"],
            "normalized_obv_slope5": _ratio(v["obv_slope5"], mean_volume),
            "squeeze_on": on, "normalized_squeeze_momentum": _ratio(v["squeeze_momentum"], atr),
            "squeeze_length": v["squeeze_length"], "first_squeeze_release": first_release,
            "squeeze_release_age": release_age, "ut_state": encoded_ut, "ut_state_age": encoded_age,
            "mcdx_position": v["mcdx_position"], "mcdx_position_delta3": v["mcdx_position_delta3"],
            "normalized_macd_histogram": _ratio(v["macd_histogram"], atr),
            "normalized_sign_entropy20": v["normalized_sign_entropy20"],
            "entropy_delta3": _difference(v["normalized_sign_entropy20"], lag.get("normalized_sign_entropy20")),
            "efficiency10": v["efficiency10"],
            "efficiency_delta3": _difference(v["efficiency10"], lag.get("efficiency10")),
            "prior_sell_avwap_distance_atr": _ratio(_difference(close, v["prior_sell_avwap"]), atr),
            "overhead60_atr": v["overhead60_atr"],
        }
        for column in VOTE_COLUMNS:
            f[column] = (v[column] if v[column] is not None else 0.0) if row["native_status"] == "ready" else None
        anchor, complete = v["prior_sell_completed_at"], v["completed_at"]
        if anchor is not None and (complete is None or anchor >= complete):
            raise DailyModelInputError("Sell anchor must belong to an earlier completed bar")
        result.append({column: f[column] for column in ALL_COLUMNS})
    return tuple(result)


def _validate_history(symbol: str, rows: Sequence[Mapping[str, object]], as_of_ms: int,
                      anchor: DailySourceAnchor) -> None:
    if not rows:
        raise DailyModelInputError("Daily native history is empty")
    as_of_ms = _integer(as_of_ms, "as_of_ms")
    last_timestamp = last_completed = None
    for i, row in enumerate(rows):
        if not REQUIRED_NATIVE_COLUMNS.issubset(row):
            raise DailyModelInputError("Required native feature columns are absent")
        if row["symbol"] != symbol or ("interval" in row and row["interval"] != "1d"):
            raise DailyModelInputError("Daily history symbol or frame differs")
        if _integer(row["bar_index"], "bar_index") != i:
            raise DailyModelInputError("Canonical source bars were omitted or ordinal rebased")
        timestamp = _integer(row["timestamp"], "timestamp")
        completed = _integer(row["completed_at"], "completed_at")
        usable = _integer(row["usable_at"], "usable_at")
        origin = _integer(row["source_origin_timestamp"], "source_origin_timestamp")
        if origin != anchor.first_timestamp or (i == 0 and timestamp != anchor.first_timestamp):
            raise DailyModelInputError("Canonical daily source origin differs; no silent phase rebase")
        if timestamp >= completed or completed > usable or usable * 1000 > as_of_ms:
            raise DailyModelInputError("Daily decision contains an incomplete or unavailable bar")
        if i and (timestamp <= last_timestamp or completed <= last_completed):
            raise DailyModelInputError("Daily source and completion clocks must increase strictly")
        last_timestamp, last_completed = timestamp, completed
    # A forward append must conserve the original complete tape's terminal ordinal.
    # Equal first timestamps alone cannot detect a deleted/reindexed middle bar.
    if last_timestamp >= anchor.last_timestamp:
        if (len(rows) < anchor.original_rows or
                _integer(rows[anchor.original_rows - 1]["timestamp"], "timestamp") != anchor.last_timestamp):
            raise DailyModelInputError("Canonical historical endpoint ordinal differs; source bars were omitted or rebased")


def evaluate_daily20(symbol: str, rows: Sequence[Mapping[str, object]], *, as_of_ms: int) -> tuple[Daily20Decision, ...]:
    """Assess both sleeves at the last closed source bar, without future prices.

    Return both eligible/selected decisions and explicit non-selection reasons.
    A selected decision schedules entry at the next observed regular opening;
    the caller records the actual fill and exits at source ordinal entry+20.
    Neither a future opening price nor a mature future horizon is required here.
    """
    models = load_frozen_models()
    anchor = anchor_for(symbol)
    _validate_history(symbol, rows, as_of_ms, anchor)
    row = rows[-1]
    i = len(rows) - 1
    close = _number(row["close"])
    dollar = _number(row["dollar_volume20"])
    atr = _number(row["atr14"])
    if symbol in EXCLUDED_SYMBOLS:
        reason = "excluded_symbol"
    elif i < 233:
        reason = "warmup"
    elif row["native_status"] != "ready":
        reason = "native_not_ready"
    elif close is None or close < 5:
        reason = "price_below_5"
    elif dollar is None or dollar < 1e6:
        reason = "liquidity_below_1m"
    elif atr is None or atr <= 0:
        reason = "invalid_atr"
    elif i % 20 != anchor.phase:
        reason = "phase_not_selected"
    else:
        reason = "eligible"
    features = feature_frame(rows)[-1] if reason == "eligible" else None
    decisions = []
    for name, sleeve in MODEL_SLEEVES:
        model = models[name]
        eligible = reason == "eligible"
        score = model.predict(features) if features is not None else None
        selected = eligible and model.selects(score)
        decision_reason = ("selected" if selected else "below_frozen_threshold") if eligible else reason
        decisions.append(Daily20Decision(
            sleeve, symbol, "1d", i, _integer(row["usable_at"], "usable_at") * 1000,
            20, i + 1, i + 21, score, model.threshold, close, dollar,
            anchor.phase, anchor.first_timestamp_ms, eligible, selected, decision_reason,
            model.impute(features) if features is not None else (), model.source_sha256,
        ))
    return tuple(decisions)


def rank_daily20(decisions: Sequence[Daily20Decision]) -> tuple[Daily20Decision, ...]:
    """One sleeve's candidates: original prediction descending, then symbol."""
    sleeves = {d.sleeve_id for d in decisions}
    if len(sleeves) > 1:
        raise DailyModelInputError("Rank independent sleeves separately")
    selected = [d for d in decisions if d.selected]
    if any(d.score is None or not math.isfinite(d.score) for d in selected):
        raise DailyModelInputError("Selected candidate lacks a finite score")
    return tuple(sorted(selected, key=lambda d: (-d.score, d.symbol)))
