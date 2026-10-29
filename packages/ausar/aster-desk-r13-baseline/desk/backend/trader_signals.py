"""Frozen public adaptations of three catalogue strategy families.

These rules are reproducible public implementations, not byte-for-byte copies of
Trader.dev's paid Pine scripts, and historical results advertised by a catalogue
do not validate these adaptations.  Evaluation performs no I/O, uses no wall
clock, changes no portfolio and consumes only the completed causal bars supplied
by the execution manager.  Entries and close-based exits execute at a later
opening; an observed-quote protective stop is an execution-manager obligation.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real


UNIVERSE = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLU", "XLB", "XLY", "SMH", "SOXX")
DONCHIAN = "trader_donchian55_public_v1"
RSI2 = "trader_rsi2_public_v1"
SQUEEZE = "trader_squeeze20_public_v1"

_COMMON = {
    "frame": "1d", "minimum_bars": 252,
    "universe": list(UNIVERSE), "atr_risk_period": 14,
    "dollar_volume_period": 20, "max_positions": 10,
    "max_notional_fraction": 0.10, "max_dollar_volume_fraction": 0.01,
    "entry_execution": "next_actual_exchange_opening_within_300_seconds",
    "signal_exit_execution": "next_actual_exchange_opening",
    "data_contract": "strict_ordered_completed_daily_ohlcv_consistent_price_volume_units",
    "cash_contract": "whole_shares_fee_and_slippage_inclusive_settled_cash_only",
    "tie_break": "symbol_ascending",
    "parameter_selection": "frozen_before_historical_performance_evaluation_no_return_optimization",
}

_RULES = {
    DONCHIAN: {
        **_COMMON, "sleeve": "TRADER_DONCHIAN55", "name": "Public Donchian 55 Trend",
        "channel_entry_period": 55, "channel_exit_period": 20,
        "trend_sma_period": 200, "max_hold_bars": 126,
        "initial_stop_atr_multiple": 2.0, "risk_budget_fraction": 0.005,
        "entry": "close > max(previous_55_high) and close > sma200",
        "selection": "prior-only_55_high_breakout_above_sma200_no_volume_expansion_gate",
        "ranking": "descending_(close-prior55_high)/atr14_then_symbol_ascending",
        "exit": "close < min(previous_20_low) or close < sma200 or observed_quote_initial_2atr_stop or 126_completed_holding_bars",
        "family_source": "https://mcp-api.trader.dev/backtest/01M1SDTK0DDN79QJNFSADNNTHN",
        "adaptations": ["15_liquid_us_etfs", "55_20_prior_only_channels", "sma200_trend_gate", "no_unverified_volume_expansion_filter", "126_bar_timeout", "fixed_whole_share_risk_caps"],
    },
    RSI2: {
        **_COMMON, "sleeve": "TRADER_RSI2", "name": "Public RSI(2) Pullback",
        "rsi_period": 2, "rsi_entry_threshold": 5.0,
        "trend_sma_period": 200, "exit_sma_period": 5, "max_hold_bars": 10,
        "initial_stop_atr_multiple": None, "risk_budget_fraction": None,
        "entry": "wilder_rsi2 <= 5 and close > sma200 and close < sma5",
        "selection": "long_term_uptrend_extreme_short_term_pullback",
        "ranking": "ascending_rsi2_then_descending_(sma5-close)/atr14_then_symbol_ascending",
        "exit": "close > sma5 or 10_completed_holding_bars_no_initial_atr_stop",
        "family_source": "https://mcp-api.trader.dev/backtest/01M2546HA55Q3CQYSXAVYPJ5P5",
        "adaptations": ["15_liquid_us_etfs", "inclusive_rsi2_5_gate", "10_bar_timeout", "fixed_whole_share_notional_liquidity_caps"],
    },
    SQUEEZE: {
        **_COMMON, "sleeve": "TRADER_SQUEEZE20", "name": "Public Modern BB/KC Squeeze",
        "bb_period": 20, "bb_std_multiple": 2.0, "bb_std_ddof": 0,
        "kc_period": 20, "kc_atr_multiple": 1.5,
        "kc_center": "ema20_close_sma_seed", "kc_range": "wilder_rma20_true_range_sma_seed",
        "momentum_period": 20, "breakout_period": 20, "max_hold_bars": 20,
        "initial_stop_atr_multiple": 2.0, "risk_budget_fraction": 0.005,
        "momentum": "endpoint_linreg20(close - (((highest20_high+lowest20_low)/2+sma20_close)/2))",
        "entry": "previous_bb_inside_kc and not_current_bb_inside_kc and momentum > 0 and momentum > previous_momentum and close > max(previous_20_high)",
        "selection": "modern_bb_kc_release_positive_rising_public_lazybear_style_momentum_prior20_breakout",
        "ranking": "descending_momentum/atr14_then_symbol_ascending",
        "exit": "close < ema20_close or momentum <= 0 or observed_quote_initial_2atr_stop or 20_completed_holding_bars",
        "family_source": "https://mcp-api.trader.dev/backtest/01M0T5GJ06NE3TY1P7GSRK59SP",
        "adaptations": ["modern_ema_atr_keltner_not_original_carter_ttm_replica", "public_lazybear_style_momentum", "positive_and_rising_momentum", "prior_only_20_high_confirmation", "20_bar_timeout", "fixed_whole_share_risk_caps"],
    },
}

RULES_DOCUMENT = {
    "schema_version": 1, "frozen_on": "2026-10-09", "status": "public_reimplementations_not_paid_trader_pine_replicas",
    "validation_boundary": "catalogue_claims_are_not_independent_validation_of_these_rules",
    "wilder_seed": "first_period_finite_samples_arithmetic_mean_then_(prior*(period-1)+current)/period",
    "ema_seed": "first_period_samples_arithmetic_mean_then_alpha=2/(period+1)",
    "rsi_flat_convention": "both_zero_50_loss_zero_gain_positive_100_gain_zero_loss_positive_0",
    "ohlcv_contract": "positive_finite_prices_nonnegative_finite_volume_high_gte_open_close_low_lte_open_close_strict_integer_increasing_timestamps",
    "public_method_references": [
        "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/price-channels",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/keltner-channels",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ttm-squeeze",
        "https://www.tradingview.com/script/nqQ1DT5a-Squeeze-Momentum-Indicator-LazyBear/",
    ],
    "rules": _RULES,
}

def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


# Pin canonical snapshots independently from the public mutable metadata copies.
# The checked-in JSON is this exact UTF-8 representation plus a final newline.
_DOCUMENT_BYTES = (_canonical(RULES_DOCUMENT) + "\n").encode("utf-8")
RULES_DOCUMENT_SHA256 = hashlib.sha256(_DOCUMENT_BYTES).hexdigest()
_CONFIG_JSON = {key: _canonical(value) for key, value in _RULES.items()}
CONFIG_SHA256 = {key: hashlib.sha256(value.encode("utf-8")).hexdigest() for key, value in _CONFIG_JSON.items()}
DEFINITIONS = {key: {
    "id": key, "sleeve": value["sleeve"], "name": value["name"],
    "symbols": list(UNIVERSE), "minimum_bars": value["minimum_bars"],
    "max_hold_bars": value["max_hold_bars"], "rule_config": copy.deepcopy(value),
    "selection": value["selection"], "ranking": value["ranking"], "exit": value["exit"],
    "source": value["family_source"], "frame": "1d",
    "config_sha256": CONFIG_SHA256[key], "rules_document_sha256": RULES_DOCUMENT_SHA256,
    "implementation_kind": "public_adaptation_not_paid_pine_replica",
} for key, value in _RULES.items()}


@dataclass(frozen=True)
class _Bar:
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def _get(row, name, fallback=None):
    if isinstance(row, Mapping):
        return row.get(name, fallback)
    return getattr(row, name, fallback)


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field}: expected a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field}: nonfinite number")
    return result


def _normalize(bars, as_of_ms=None):
    """Validate all rows, never sort, fill, silently omit or mutate input data."""
    if not isinstance(bars, Sequence) or isinstance(bars, (str, bytes, bytearray)):
        raise ValueError("bars: expected ordered sequence")
    if as_of_ms is not None and (type(as_of_ms) is not int or as_of_ms <= 0):
        raise ValueError("as_of_ms: expected positive integer milliseconds")
    result = []
    previous = None
    for index, row in enumerate(bars):
        stamp = _get(row, "timestamp_ms", _get(row, "timestamp"))
        if type(stamp) is not int or stamp <= 0:
            raise ValueError(f"bar {index}: timestamp must be a positive integer")
        if previous is not None and stamp <= previous:
            raise ValueError(f"bar {index}: timestamps must strictly increase")
        previous = stamp
        completed = _get(row, "completed_at_ms")
        usable = _get(row, "usable_at_ms")
        for field, clock in (("completed_at_ms", completed), ("usable_at_ms", usable)):
            if clock is not None and (type(clock) is not int or clock <= 0):
                raise ValueError(f"bar {index}: {field} must be a positive integer")
        if completed is not None and completed < stamp:
            raise ValueError(f"bar {index}: completion precedes source label")
        if usable is not None and completed is not None and usable < completed:
            raise ValueError(f"bar {index}: usable clock precedes completion")
        if as_of_ms is not None:
            if completed is None or usable is None:
                raise ValueError(f"bar {index}: explicit as_of requires causal completion and usable clocks")
            if max(completed, usable) > as_of_ms:
                raise ValueError(f"bar {index}: future or unusable observation")
        values = {name: _finite_number(_get(row, name), f"bar {index} {name}") for name in ("open", "high", "low", "close", "volume")}
        if any(values[field] <= 0 for field in ("open", "high", "low", "close")) or values["volume"] < 0:
            raise ValueError(f"bar {index}: prices must be positive and volume nonnegative")
        if values["high"] < max(values["open"], values["close"], values["low"]) or values["low"] > min(values["open"], values["close"], values["high"]):
            raise ValueError(f"bar {index}: inconsistent OHLC")
        result.append(_Bar(stamp, **values))
    return tuple(result)


def _sma(values, period):
    result = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = math.fsum(values[i + 1 - period:i + 1]) / period
    return result


def _smooth(values, period, alpha):
    result = [None] * len(values)
    if len(values) < period:
        return result
    result[period - 1] = math.fsum(values[:period]) / period
    for i in range(period, len(values)):
        result[i] = result[i - 1] + alpha * (values[i] - result[i - 1])
    return result


def _ema(values, period):
    return _smooth(values, period, 2.0 / (period + 1))


def _rma(values, period):
    return _smooth(values, period, 1.0 / period)


def _true_range(bars):
    return [max(b.high - b.low, abs(b.high - bars[i - 1].close), abs(b.low - bars[i - 1].close)) if i else b.high - b.low for i, b in enumerate(bars)]


def _rsi(values, period):
    """Wilder RSI seeded by the first period actual price changes, not a zero."""
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gain = _rma([max(v, 0.0) for v in changes], period)
    loss = _rma([max(-v, 0.0) for v in changes], period)
    result = [None] * len(values)
    for i in range(period, len(values)):
        g, l = gain[i - 1], loss[i - 1]
        result[i] = 50.0 if g == l == 0 else 100.0 if l == 0 else 0.0 if g == 0 else 100.0 - 100.0 / (1.0 + g / l)
    return result


def _prior_high(bars, index, period):
    return max(bar.high for bar in bars[index - period:index])


def _prior_low(bars, index, period):
    return min(bar.low for bar in bars[index - period:index])


def _linreg_endpoint(values):
    """Ordinary least squares fitted value at last x, equivalent linreg(...,0)."""
    period = len(values)
    center_x = (period - 1) / 2.0
    center_y = math.fsum(values) / period
    denominator = math.fsum((i - center_x) ** 2 for i in range(period))
    slope = math.fsum((i - center_x) * (value - center_y) for i, value in enumerate(values)) / denominator
    return center_y + slope * center_x


def _squeeze_series(bars, config):
    closes = [b.close for b in bars]
    n, k, m = config["bb_period"], config["kc_period"], config["momentum_period"]
    sma = _sma(closes, n)
    center = _ema(closes, k)
    atr = _rma(_true_range(bars), k)
    squeeze, delta, momentum = [None] * len(bars), [None] * len(bars), [None] * len(bars)
    for i in range(max(n, k) - 1, len(bars)):
        mean = sma[i]
        stdev = math.sqrt(math.fsum((v - mean) ** 2 for v in closes[i + 1 - n:i + 1]) / n)
        upper, lower = mean + config["bb_std_multiple"] * stdev, mean - config["bb_std_multiple"] * stdev
        kcupper, kclower = center[i] + config["kc_atr_multiple"] * atr[i], center[i] - config["kc_atr_multiple"] * atr[i]
        squeeze[i] = lower > kclower and upper < kcupper
        window = bars[i + 1 - m:i + 1]
        midrange = (max(b.high for b in window) + min(b.low for b in window)) / 2.0
        delta[i] = closes[i] - (midrange + sma[i]) / 2.0
        if i >= max(n, k) - 1 + m - 1:
            momentum[i] = _linreg_endpoint(delta[i + 1 - m:i + 1])
    return {"squeeze": squeeze, "momentum": momentum, "kc_center": center, "kc_atr": atr}


def _features(rule_id, bars, config):
    closes = [b.close for b in bars]
    i, close = len(bars) - 1, bars[-1].close
    atr = _rma(_true_range(bars), config["atr_risk_period"])[i]
    dollar_volume = math.fsum(b.close * b.volume for b in bars[-config["dollar_volume_period"]:]) / config["dollar_volume_period"]
    if not math.isfinite(dollar_volume) or not math.isfinite(atr) or atr <= 0 or dollar_volume <= 0:
        raise ValueError("nonpositive_or_nonfinite_atr_or_dollar_volume")
    features = {"timestamp_ms": bars[-1].timestamp_ms, "bar_count": len(bars), "close": close, "atr14": atr, "dollar_volume20": dollar_volume}
    if rule_id == DONCHIAN:
        sma200 = _sma(closes, config["trend_sma_period"])[i]
        high = _prior_high(bars, i, config["channel_entry_period"])
        low = _prior_low(bars, i, config["channel_exit_period"])
        entry = close > high and close > sma200
        reasons = [name for condition, name in ((close < low, "close_below_prior20_low"), (close < sma200, "close_below_sma200")) if condition]
        features.update({"sma200": sma200, "prior55_high": high, "prior20_low": low, "breakout_atr": (close - high) / atr})
        rank = (-(close - high) / atr,)
        score = (close - high) / atr
    elif rule_id == RSI2:
        rsi = _rsi(closes, config["rsi_period"])[i]
        sma200 = _sma(closes, config["trend_sma_period"])[i]
        sma5 = _sma(closes, config["exit_sma_period"])[i]
        pullback = (sma5 - close) / atr
        entry = rsi <= config["rsi_entry_threshold"] and close > sma200 and close < sma5
        reasons = ["close_above_sma5"] if close > sma5 else []
        features.update({"rsi2": rsi, "sma200": sma200, "sma5": sma5, "pullback_atr": pullback})
        rank, score = (rsi, -pullback), -rsi
    else:
        values = _squeeze_series(bars, config)
        momentum, previous = values["momentum"][i], values["momentum"][i - 1]
        high = _prior_high(bars, i, config["breakout_period"])
        center = values["kc_center"][i]
        release = values["squeeze"][i - 1] is True and values["squeeze"][i] is False
        entry = release and momentum > 0 and momentum > previous and close > high
        reasons = [name for condition, name in ((close < center, "close_below_kc_center"), (momentum <= 0, "momentum_nonpositive")) if condition]
        features.update({"squeeze_on": values["squeeze"][i], "previous_squeeze_on": values["squeeze"][i - 1], "squeeze_release": release, "momentum": momentum, "previous_momentum": previous, "kc_center": center, "kc_atr20": values["kc_atr"][i], "prior20_high": high, "momentum_atr": momentum / atr})
        rank, score = (-momentum / atr,), momentum / atr
    features["entry_signal"] = entry
    features["exit_signal"] = bool(reasons)
    return features, entry, reasons, rank, score


def evaluate(rule_id, bars_by_symbol, rule_config=None, held_symbols=(), *, as_of_ms=None):
    """Return deterministic ranked candidates and close-based exit obligations.

    ``bars_by_symbol`` must be a mapping of frozen-universe symbols to strictly
    ordered completed daily bars.  Every supplied row is validated; invalid input
    is a per-name failure with no signal.  ``as_of_ms`` optionally enforces each
    bar's explicit completion/usable clock.  Without it, causal completion is the
    caller's responsibility and no clock is fabricated.  Holdings are membership
    only: fill prices, elapsed holds, stops, cash and liquidity enforcement belong
    to the durable execution manager.  A supplied config must match the freeze.
    """
    if rule_id not in _CONFIG_JSON:
        raise ValueError("Unknown frozen Trader rule")
    if not isinstance(bars_by_symbol, Mapping):
        raise ValueError("bars_by_symbol must be a mapping")
    if rule_config is not None and _canonical(rule_config) != _CONFIG_JSON[rule_id]:
        raise ValueError("Rule configuration differs from frozen public adaptation")
    config = json.loads(_CONFIG_JSON[rule_id])
    held = set(held_symbols)
    output = {"rule_id": rule_id, "config_sha256": CONFIG_SHA256[rule_id], "rules_document_sha256": RULES_DOCUMENT_SHA256, "implementation_kind": "public_adaptation_not_paid_pine_replica", "candidates": [], "exits": [], "features": {}, "diagnostics": {}}
    ranked = []
    for name in sorted(bars_by_symbol):
        if name not in config["universe"]:
            output["diagnostics"][name] = {"status": "ineligible", "reason": "outside_frozen_etf_universe"}
            continue
        try:
            bars = _normalize(bars_by_symbol[name], as_of_ms)
            if len(bars) < config["minimum_bars"]:
                output["diagnostics"][name] = {"status": "ineligible", "reason": "insufficient_completed_daily_warmup", "bar_count": len(bars), "minimum_bars": config["minimum_bars"]}
                continue
            features, entry, exit_reasons, rank, score = _features(rule_id, bars, config)
        except (ValueError, TypeError, OverflowError) as exc:
            output["diagnostics"][name] = {"status": "failed", "reason": str(exc)}
            continue
        output["features"][name] = features
        output["diagnostics"][name] = {"status": "ready", "reason": "completed_causal_daily_indicators"}
        if name in held and exit_reasons:
            output["exits"].append({"symbol": name, "reason": ";".join(exit_reasons), "features": features})
        if entry and name not in held:
            distance = None if config["initial_stop_atr_multiple"] is None else config["initial_stop_atr_multiple"] * features["atr14"]
            candidate = {"symbol": name, "score": score, "dollar_volume20": features["dollar_volume20"], "reason": config["entry"], "features": features, "atr": features["atr14"], "stop_distance": distance, "risk_budget_fraction": config["risk_budget_fraction"], "max_hold_bars": config["max_hold_bars"], "max_notional_fraction": config["max_notional_fraction"], "max_dollar_volume_fraction": config["max_dollar_volume_fraction"], "rank_key": list(rank) + [name]}
            ranked.append((rank + (name,), candidate))
    output["candidates"] = [candidate for _, candidate in sorted(ranked, key=lambda item: item[0])]
    return output
