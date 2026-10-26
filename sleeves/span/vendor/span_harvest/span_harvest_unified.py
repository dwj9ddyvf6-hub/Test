"""Unified causal prediction-market profit-zone replay engine.

This module synthesizes the useful parts of the earlier exit prototype and the
attached Span Harvest specification into one deterministic research engine:

* PZOE selects a complete profile only from older matches and can abstain.
* APZI runs a staged, print-proxy entry ladder and A/B/C inventory sleeves.
* The TimePortal shared nested entry bands are treated as baseline semantics.
* Sport-relative clocks and an optional normalized shock gate are causal.
* Unknown ends, malformed inputs, and unverified fills fail closed.

It has no credentials, broker, wallet, order-submission, Site mutation, or live
capital authority. A print is an observed tape event, not proof of executable
depth or queue position.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from collections import deque
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable, Mapping, MutableMapping, Sequence
from urllib.request import Request, urlopen


DEFAULT_TAPE_SOURCE = "https://timeportal.pro/polymarket/odds_data/clean_tapes.json"
DEFAULT_CLOCK_SOURCE = "https://timeportal.pro/polymarket/odds_data/game_time_by_sport.json"
TICK = 0.005
EPS = 1e-12


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ceil_to_tick(value: float) -> float:
    return math.ceil((value - EPS) / TICK) * TICK


def normalized_result(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"won", "win", "yes", "true", "1"}:
        return "won"
    if text in {"lost", "loss", "no", "false", "0"}:
        return "lost"
    return None


@dataclass(frozen=True)
class Tape:
    match_id: str
    sport: str
    cohort: str
    opening: float
    prices: tuple[float, ...]
    times: tuple[float, ...]
    result: str | None
    start_ts: float
    settlement_i: int | None
    end_recorded: bool
    execution_observations: tuple["ExecutionObservation", ...] = ()

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "Tape | None":
        raw_prices = record.get("p") or []
        raw_times = record.get("t") or []
        if not isinstance(raw_prices, Sequence) or not raw_prices:
            return None
        if not finite(record.get("open")):
            return None
        if len(raw_times) != len(raw_prices):
            return None
        prices = tuple(float(value) for value in raw_prices if finite(value))
        if len(prices) != len(raw_prices) or any(value < 0.0 or value > 1.0 for value in prices):
            return None
        times = tuple(float(value) for value in raw_times)
        if not all(finite(value) for value in times):
            return None
        if any(times[i] < times[i - 1] for i in range(1, len(times))):
            return None
        settlement_i = None
        if record.get("settlement_i") is not None:
            try:
                settlement_i = int(record["settlement_i"])
            except (TypeError, ValueError):
                return None
            if settlement_i < 0 or settlement_i > len(prices):
                return None
        start = record.get("start_ts")
        if not finite(start):
            start = times[0]
        end_recorded = bool(record.get("end_recorded", settlement_i is not None))
        raw_execution = (
            record.get("execution_observations")
            or record.get("book_snapshots")
            or record.get("orderbook")
            or record.get("book")
        )
        return cls(
            match_id=str(record.get("id", "")),
            sport=str(record.get("sport", "unknown")).lower(),
            cohort=str(
                record.get("favcohort_tracked")
                or record.get("cohort")
                or record.get("cohort_name")
                or "unknown"
            ),
            opening=float(record["open"]),
            prices=prices,
            times=times,
            result=normalized_result(record.get("result")),
            start_ts=float(start),
            settlement_i=settlement_i,
            end_recorded=end_recorded,
            execution_observations=parse_execution_observations(raw_execution),
        )

    @property
    def last_tradable_i(self) -> int:
        if self.settlement_i is not None:
            return max(-1, min(len(self.prices) - 1, self.settlement_i - 1))
        return len(self.prices) - 1

    @property
    def terminal_price(self) -> float | None:
        if not self.end_recorded:
            return None
        if self.result == "won":
            return 1.0
        if self.result == "lost":
            return 0.0
        return None


@dataclass(frozen=True)
class ClockReference:
    by_sport: Mapping[str, float]
    pooled_median: float

    def length_for(self, sport: str) -> float:
        length = self.by_sport.get(sport.lower())
        return float(length) if finite(length) and float(length) > 0 else self.pooled_median

    def relative(self, tape: Tape, index: int) -> float:
        return max(0.0, (tape.times[index] - tape.start_ts) / (60.0 * self.length_for(tape.sport)))


@dataclass(frozen=True)
class TapeFeatures:
    """Causal, profile-independent features cached once per tape/window."""

    relative_clock: tuple[float, ...]
    slope_2m: tuple[float, ...]
    slope_6m: tuple[float, ...]
    slope_acceleration: tuple[float, ...]
    prior_minimum_8m: tuple[float, ...]
    drawdown_from_causal_peak: tuple[float, ...]
    shock_window_minutes: float
    shock_values: tuple[tuple[float, float] | None, ...]


@dataclass(frozen=True)
class ExecutionObservation:
    """Minimum book state required before a print-proxy candidate is tradable."""

    best_bid: float | None
    best_ask: float | None
    bid_depth: float | None
    ask_depth: float | None
    queue_ahead: float | None
    event_ts: float
    received_ts: float
    tick_size: float = TICK
    market_open: bool = True


@dataclass(frozen=True)
class ShadowFillRecord:
    """Paper-trading record used to reconcile a decision with observed fills."""

    decision_id: str
    decision_state: str
    expected_price: float
    expected_shares: float
    decision_ts: float
    observed_price: float | None = None
    observed_shares: float | None = None
    observed_ts: float | None = None


def reconcile_shadow_fill(record: ShadowFillRecord, *, price_tolerance: float = TICK) -> dict[str, Any]:
    """Reconcile paper expectations with an independently observed fill."""
    if record.decision_state != "EDGE_OK":
        return {"status": "NOT_ACTIONABLE", "decision_id": record.decision_id}
    if record.observed_price is None or record.observed_shares is None or record.observed_ts is None:
        return {"status": "PENDING_OBSERVATION", "decision_id": record.decision_id}
    values = (record.expected_price, record.expected_shares, record.decision_ts, record.observed_price, record.observed_shares, record.observed_ts)
    if not all(finite(value) for value in values):
        return {"status": "INVALID_OBSERVATION", "decision_id": record.decision_id}
    if record.observed_shares < -EPS or record.observed_ts < record.decision_ts - EPS:
        return {"status": "INVALID_OBSERVATION", "decision_id": record.decision_id}
    slippage = record.observed_price - record.expected_price
    size_ratio = record.observed_shares / record.expected_shares if record.expected_shares > EPS else 0.0
    status = "RECONCILED" if abs(slippage) <= max(0.0, price_tolerance) + EPS and abs(size_ratio - 1.0) <= 0.05 + EPS else "MISMATCH"
    return {
        "status": status,
        "decision_id": record.decision_id,
        "price_slippage": slippage,
        "expected_shares": record.expected_shares,
        "observed_shares": record.observed_shares,
        "fill_ratio": size_ratio,
        "latency_seconds": record.observed_ts - record.decision_ts,
    }


def parse_execution_observations(raw: Any) -> tuple[ExecutionObservation, ...]:
    """Parse optional point-in-time L2 observations without inventing data.

    The TimePortal clean tape does not contain these fields. This adapter accepts
    common REST/export spellings so a future order-book collector can be replayed
    through the same engine. Missing or malformed rows are discarded and remain
    visible to callers through the resulting observation count.
    """
    if isinstance(raw, Mapping):
        raw = raw.get("snapshots") or raw.get("books") or [raw]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()
    parsed: list[ExecutionObservation] = []
    for row in raw:
        if not isinstance(row, Mapping):
            continue
        def pick(*keys: str) -> Any:
            for key in keys:
                if key in row:
                    return row[key]
            return None

        event_ts = pick("event_ts", "timestamp", "ts", "t")
        received_ts = pick("received_ts", "received_at", "ingest_ts", "rt")
        best_bid = pick("best_bid", "bid", "bid_price")
        best_ask = pick("best_ask", "ask", "ask_price")
        bid_depth = pick("bid_depth", "depth_bid", "bid_size")
        ask_depth = pick("ask_depth", "depth_ask", "ask_size")
        queue_ahead = pick("queue_ahead", "queue", "queue_position")
        if received_ts is None:
            received_ts = event_ts
        if queue_ahead is None:
            queue_ahead = 0.0
        tick_size = pick("tick_size", "minimum_tick_size")
        if tick_size is None:
            tick_size = TICK
        market_open = bool(pick("market_open", "open")) if pick("market_open", "open") is not None else True
        values = (event_ts, received_ts, best_bid, best_ask, bid_depth, ask_depth, queue_ahead, tick_size)
        if not all(finite(value) for value in values):
            continue
        parsed.append(ExecutionObservation(
            float(best_bid), float(best_ask), float(bid_depth), float(ask_depth),
            float(queue_ahead), float(event_ts), float(received_ts), float(tick_size), market_open,
        ))
    return tuple(sorted(parsed, key=lambda item: (item.event_ts, item.received_ts)))


def execution_observation_at(tape: Tape, event_ts: float) -> ExecutionObservation | None:
    """Return the latest book state available no later than an event."""
    chosen: ExecutionObservation | None = None
    for observation in tape.execution_observations:
        if observation.event_ts > event_ts + EPS:
            break
        chosen = observation
    return chosen


def evaluate_execution_gate(
    observation: ExecutionObservation,
    *,
    target_bid: float,
    fill_probability: float,
    target_hit_probability: float,
    fallback_return: float,
    stake: float = 1.0,
    fee_per_share: float = 0.0,
    slippage_per_share: float = 0.0,
    queue_penalty: float = 0.0,
    latency_penalty: float = 0.0,
    ev_uncertainty: float = 0.0,
    minimum_ev_lower_bound: float = 0.0,
    minimum_fill_probability: float = 0.20,
    maximum_latency_seconds: float = 3.0,
    participation_cap: float = 0.01,
) -> dict[str, Any]:
    """Return a pure, fail-closed execution decision for one candidate.

    Probabilities and penalties are inputs from a point-in-time calibrated
    model. The function intentionally does not place, cancel, or modify an
    order. It converts a tape candidate into an auditable execution decision.
    """
    values = (
        observation.best_bid,
        observation.best_ask,
        observation.bid_depth,
        observation.ask_depth,
        observation.queue_ahead,
        observation.event_ts,
        observation.received_ts,
        observation.tick_size,
        target_bid,
        fill_probability,
        target_hit_probability,
        fallback_return,
        stake,
        fee_per_share,
        slippage_per_share,
        queue_penalty,
        latency_penalty,
        ev_uncertainty,
    )
    if not all(finite(value) for value in values):
        return {"state": "NO_TRADE", "reason": "MISSING_EXECUTION_DATA"}
    if not observation.market_open:
        return {"state": "NO_TRADE", "reason": "MARKET_NOT_OPEN"}
    if observation.best_bid < 0.0 or observation.best_ask > 1.0 or observation.best_bid > observation.best_ask:
        return {"state": "NO_TRADE", "reason": "INVALID_BOOK"}
    if observation.bid_depth <= EPS or observation.ask_depth <= EPS or observation.tick_size <= EPS:
        return {"state": "NO_TRADE", "reason": "INSUFFICIENT_DEPTH"}
    if observation.received_ts < observation.event_ts or observation.received_ts - observation.event_ts > maximum_latency_seconds:
        return {"state": "NO_TRADE", "reason": "STALE_EXECUTION_DATA"}
    if not 0.0 <= fill_probability <= 1.0 or not 0.0 <= target_hit_probability <= 1.0:
        return {"state": "NO_TRADE", "reason": "INVALID_CALIBRATION"}
    if fill_probability < minimum_fill_probability:
        return {"state": "NO_TRADE", "reason": "LOW_QUEUE_FILL_PROBABILITY", "fill_probability": fill_probability}
    requested_shares = stake / max(observation.best_ask, observation.tick_size)
    if requested_shares > observation.ask_depth * participation_cap + EPS:
        return {
            "state": "NO_TRADE",
            "reason": "CAPACITY_LIMIT",
            "requested_shares": requested_shares,
            "capacity_shares": observation.ask_depth * participation_cap,
        }
    gross = fill_probability * (target_hit_probability * (target_bid / observation.best_ask - 1.0) + (1.0 - target_hit_probability) * fallback_return)
    fee_cost = fill_probability * (1.0 + target_hit_probability) * fee_per_share / max(observation.best_ask, observation.tick_size)
    slippage_cost = fill_probability * (1.0 + target_hit_probability) * slippage_per_share / max(observation.best_ask, observation.tick_size)
    ev = gross - fee_cost - slippage_cost - max(0.0, queue_penalty) - max(0.0, latency_penalty)
    ev_lower_bound = ev - max(0.0, ev_uncertainty)
    return {
        "state": "EDGE_OK" if ev_lower_bound > minimum_ev_lower_bound else "NO_TRADE",
        "reason": "POSITIVE_EV_LOWER_BOUND" if ev_lower_bound > minimum_ev_lower_bound else "NEGATIVE_EV_LOWER_BOUND",
        "requested_shares": requested_shares,
        "capacity_shares": observation.ask_depth * participation_cap,
        "gross_ev": gross,
        "fee_cost": fee_cost,
        "slippage_cost": slippage_cost,
        "ev": ev,
        "ev_lower_bound": ev_lower_bound,
        "fill_probability": fill_probability,
        "target_hit_probability": target_hit_probability,
    }


def prepare_features(tape: Tape, clock: ClockReference, shock_window_minutes: float = 4.0) -> TapeFeatures:
    """Precompute only information available at each print, in chronological order."""
    n = tape.last_tradable_i + 1
    rel = tuple(clock.relative(tape, index) for index in range(n))

    def prior_indices(window_minutes: float) -> list[int | None]:
        result: list[int | None] = []
        candidate = -1
        for index in range(n):
            target = tape.times[index] - window_minutes * 60.0
            while candidate + 1 < index and tape.times[candidate + 1] <= target + EPS:
                candidate += 1
            result.append(candidate if candidate >= 0 else None)
        return result

    def slope_series(window_minutes: float) -> list[float]:
        slope_prior = prior_indices(window_minutes)
        values: list[float] = []
        for index, prior in enumerate(slope_prior):
            if prior is None or tape.times[index] <= tape.times[prior]:
                values.append(0.0)
            else:
                values.append((tape.prices[index] - tape.prices[prior]) / ((tape.times[index] - tape.times[prior]) / 60.0))
        return values

    slopes_2m = slope_series(2.0)
    slopes = slope_series(6.0)
    accelerations: list[float] = []
    for index in range(n):
        accelerations.append(slopes_2m[index] - slopes[index])

    prior_mins: list[float] = []
    window: deque[int] = deque()
    left = 0
    causal_peaks: list[float] = []
    peak = tape.opening
    for index in range(n):
        peak = max(peak, tape.prices[index])
        causal_peaks.append(peak)

    # A monotone deque gives the exact `recent_minimum(index - 1, 8m)` value
    # used by staged adds without rescanning the entire prefix per print.
    for index in range(n):
        end = index - 1
        if end >= 0:
            lower = tape.times[end] - 8.0 * 60.0
            while left <= end and tape.times[left] < lower - EPS:
                if window and window[0] == left:
                    window.popleft()
                left += 1
            while window and tape.prices[window[-1]] >= tape.prices[end]:
                window.pop()
            window.append(end)
            while window and window[0] < left:
                window.popleft()
            prior_mins.append(tape.prices[window[0]] if window else tape.prices[end])
        else:
            prior_mins.append(tape.prices[0])

    shock_prior = prior_indices(shock_window_minutes)
    normal = NormalDist()
    y_values = [
        math.sqrt(max(1e-9, 1.0 - rel[index]))
        * normal.inv_cdf(clamp(tape.prices[index], TICK, 1.0 - TICK))
        for index in range(n)
    ]
    shocks: list[tuple[float, float] | None] = []
    for index, prior in enumerate(shock_prior):
        if prior is None:
            shocks.append(None)
            continue
        delta_clock = rel[index] - rel[prior]
        shocks.append((y_values[index], (y_values[index] - y_values[prior]) / math.sqrt(delta_clock)) if delta_clock > EPS else None)
    return TapeFeatures(
        tuple(rel),
        tuple(slopes_2m),
        tuple(slopes),
        tuple(accelerations),
        tuple(prior_mins),
        tuple((causal_peaks[index] - tape.prices[index]) for index in range(n)),
        float(shock_window_minutes),
        tuple(shocks),
    )

@dataclass(frozen=True)
class Profile:
    profile_id: str
    early_multiplier: float = 0.55
    late_multiplier: float = 0.38
    harvest_multiple: float = 2.15
    harvest_add: float = 0.18
    b_target: float = 0.72
    b_giveback: float = 0.38
    b_slope_cap: float = 0.002
    shock_required: bool = False
    shock_window_minutes: float = 4.0
    shock_threshold: float = -2.5
    flatten_minutes: float = 240.0


def profile_library() -> tuple[Profile, ...]:
    base = Profile("apzi_base")
    profiles = [
        base,
        replace(base, profile_id="deep_zone", early_multiplier=0.50, late_multiplier=0.34),
        replace(base, profile_id="patient_zone", early_multiplier=0.45, late_multiplier=0.30),
        replace(base, profile_id="wide_zone", early_multiplier=0.60, late_multiplier=0.42),
        replace(base, profile_id="late_deep_zone", late_multiplier=0.32),
        replace(base, profile_id="harvest_tight", harvest_multiple=1.90, harvest_add=0.14, b_target=0.65),
        replace(base, profile_id="harvest_wide", harvest_multiple=2.40, harvest_add=0.22, b_target=0.80),
        replace(base, profile_id="trail_tight", b_giveback=0.30, b_slope_cap=0.001),
        replace(base, profile_id="trail_loose", b_giveback=0.48, b_slope_cap=0.003),
        replace(base, profile_id="shock_base", shock_required=True),
        replace(base, profile_id="shock_deep_zone", early_multiplier=0.50, late_multiplier=0.34, shock_required=True),
        replace(base, profile_id="shock_wide_zone", early_multiplier=0.60, late_multiplier=0.42, shock_required=True),
        replace(base, profile_id="shock_harvest_tight", harvest_multiple=1.90, harvest_add=0.14, b_target=0.65, shock_required=True),
        replace(base, profile_id="shock_fast_flatten", shock_required=True, flatten_minutes=180.0),
    ]
    return tuple(profiles)


def exit_surface_library(*, include_shock_variants: bool = True) -> tuple[Profile, ...]:
    """Return a bounded exit-search family for training folds only.

    The production registry stays frozen at 14 profiles. This separate surface
    makes target/giveback/flatten trade-offs measurable without silently
    promoting whichever combination wins one historical replay.
    """
    base = Profile("surface_base")
    variants: list[Profile] = []
    surfaces = (
        (1.75, 0.12, 0.60, 0.26, 150.0),
        (1.95, 0.15, 0.66, 0.32, 180.0),
        (2.15, 0.18, 0.72, 0.38, 240.0),
        (2.40, 0.22, 0.80, 0.46, 300.0),
        (2.80, 0.28, 0.86, 0.54, 360.0),
        (1.65, 0.10, 0.58, 0.22, 120.0),
    )
    for index, (multiple, add, target, giveback, flatten) in enumerate(surfaces, start=1):
        variants.append(replace(
            base,
            profile_id=f"surface_{index}",
            harvest_multiple=multiple,
            harvest_add=add,
            b_target=target,
            b_giveback=giveback,
            flatten_minutes=flatten,
        ))
        if include_shock_variants:
            variants.append(replace(variants[-1], profile_id=f"surface_{index}_shock", shock_required=True))
    return tuple(variants)


def rank_exit_surface(
    tapes: Sequence[Tape],
    clock: ClockReference,
    *,
    profiles: Sequence[Profile] | None = None,
    fee_per_share: float = 0.0,
    hypotheses: int | None = None,
) -> list[dict[str, Any]]:
    """Rank exit candidates on a supplied training fold, never on a holdout."""
    candidates = tuple(profiles or exit_surface_library())
    family_size = max(1, int(hypotheses or len(candidates)))
    ranked: list[dict[str, Any]] = []
    for profile in candidates:
        trades = [simulate_profile(tape, profile, clock, fee_per_share=fee_per_share) for tape in tapes]
        result = summarize_trades(trades, hypotheses=family_size)
        result["profile_id"] = profile.profile_id
        ranked.append(result)
    ranked.sort(key=lambda row: (
        row["familywise_lower_bound_95"],
        row["clustered_lower_bound_95"],
        row["mean_net_per_match"],
        row["profile_id"],
    ), reverse=True)
    return ranked


@dataclass(frozen=True)
class Gate:
    minimum_prior_matches: int = 30
    minimum_prior_fills: int = 5
    minimum_coverage: float = 0.85
    minimum_lcb: float = 0.0
    minimum_lcb_after_best_trade: float = 0.0
    minimum_clustered_lcb: float = 0.0
    minimum_clustered_lcb_after_best_trade: float = 0.0
    profile_family_size: int = 1
    minimum_prior_clusters: int = 1
    embargo_seconds: float = 0.0
    warmup_matches: int = 30


@dataclass(frozen=True)
class Trade:
    match_id: str
    sport: str
    profile_id: str
    status: str
    entry_i: int | None
    last_fill_i: int | None
    capital_used: float
    shares_bought: float
    shares_sold: float
    entry_fees: float
    exit_fees: float
    pnl: float | None
    exit_reason: str
    entries: tuple[dict[str, Any], ...] = ()
    exits: tuple[dict[str, Any], ...] = ()
    start_ts: float = 0.0


def load_payload(source: str | Path) -> dict[str, Any]:
    text = str(source)
    if text.startswith(("http://", "https://")):
        request = Request(text, headers={"User-Agent": "span-harvest-research/1.1"})
        with urlopen(request, timeout=45) as response:  # noqa: S310 - explicit research source
            value = json.load(response)
    else:
        value = json.loads(Path(text).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("source payload must be a JSON object")
    return value


def load_tapes(source: str | Path) -> tuple[dict[str, Any], list[Tape], int]:
    payload = load_payload(source)
    raw = payload.get("matches")
    if not isinstance(raw, list):
        raise ValueError("source payload has no matches list")
    rejected = 0
    tapes: list[Tape] = []
    for row in raw:
        if not isinstance(row, dict) or row.get("omitted"):
            rejected += 1
            continue
        tape = Tape.from_record(row)
        if tape is None or tape.last_tradable_i < 0:
            rejected += 1
            continue
        tapes.append(tape)
    tapes.sort(key=lambda tape: (tape.start_ts, tape.match_id))
    return payload, tapes, rejected


def _sport_entries(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, list):
        for row in value:
            if isinstance(row, dict) and row.get("sport") is not None:
                yield str(row["sport"]).lower(), row
    elif isinstance(value, dict):
        for key, row in value.items():
            yield str(key).lower(), row


def _length_from_row(row: Any) -> float | None:
    if isinstance(row, dict):
        for key in ("median", "median_minutes", "length_minutes", "length", "mean"):
            if finite(row.get(key)) and float(row[key]) > 0:
                return float(row[key])
    elif finite(row) and float(row) > 0:
        return float(row)
    return None


def load_clock_reference(source: str | Path | None, tapes: Sequence[Tape]) -> ClockReference:
    by_sport: dict[str, float] = {}
    pooled: list[float] = []
    if source:
        payload = load_payload(source)
        for sport, row in _sport_entries(payload.get("sports")):
            length = _length_from_row(row)
            if length is not None:
                by_sport[sport] = length
                pooled.append(length)
        if not by_sport:
            for sport, row in _sport_entries(payload.get("by_sport")):
                length = _length_from_row(row)
                if length is not None:
                    by_sport[sport] = length
                    pooled.append(length)
        pooled_row = _length_from_row(payload.get("pooled"))
        if pooled_row is not None:
            pooled_median = pooled_row
        elif pooled:
            pooled_median = statistics.median(pooled)
        else:
            pooled_median = 0.0
    else:
        pooled_median = 0.0
    if not by_sport:
        for sport in sorted({tape.sport for tape in tapes}):
            durations = [
                (tape.times[tape.last_tradable_i] - tape.start_ts) / 60.0
                for tape in tapes
                if tape.sport == sport and tape.last_tradable_i >= 0
            ]
            if durations:
                by_sport[sport] = statistics.median(durations)
    if pooled_median <= 0:
        values = list(by_sport.values())
        pooled_median = statistics.median(values) if values else 1.0
    return ClockReference(by_sport=by_sport, pooled_median=max(1e-6, pooled_median))


def prior_index(tape: Tape, index: int, minutes: float) -> int | None:
    target = tape.times[index] - minutes * 60.0
    candidate = None
    for j in range(index):
        if tape.times[j] <= target + EPS:
            candidate = j
    return candidate


def slope_per_minute(tape: Tape, index: int, window_minutes: float = 6.0) -> float:
    j = prior_index(tape, index, window_minutes)
    if j is None or tape.times[index] <= tape.times[j]:
        return 0.0
    return (tape.prices[index] - tape.prices[j]) / ((tape.times[index] - tape.times[j]) / 60.0)


def recent_minimum(tape: Tape, index: int, window_minutes: float = 8.0) -> float:
    start_time = tape.times[index] - window_minutes * 60.0
    values = [tape.prices[j] for j in range(index + 1) if tape.times[j] >= start_time - EPS]
    return min(values) if values else tape.prices[index]


def shock_coordinates(tape: Tape, index: int, clock: ClockReference, window_minutes: float) -> tuple[float, float] | None:
    j = prior_index(tape, index, window_minutes)
    if j is None:
        return None
    delta_clock = clock.relative(tape, index) - clock.relative(tape, j)
    if delta_clock <= EPS:
        return None
    normal = NormalDist()
    y_now = math.sqrt(max(1e-9, 1.0 - clock.relative(tape, index))) * normal.inv_cdf(clamp(tape.prices[index], TICK, 1.0 - TICK))
    y_then = math.sqrt(max(1e-9, 1.0 - clock.relative(tape, j))) * normal.inv_cdf(clamp(tape.prices[j], TICK, 1.0 - TICK))
    shock = (y_now - y_then) / math.sqrt(delta_clock)
    return y_now, shock


def winner_state_score(tape: Tape, index: int, entry_i: int, peak: float, trough: float) -> float:
    """Bounded causal ranking diagnostic, explicitly not a probability."""
    price_component = clamp((tape.prices[index] - 0.15) / 0.70, 0.0, 1.0)
    slope_component = clamp((slope_per_minute(tape, index) + 0.002) / 0.004, 0.0, 1.0)
    span = max(TICK, peak - trough)
    recovery_component = clamp((tape.prices[index] - trough) / span, 0.0, 1.0)
    return clamp(0.45 * price_component + 0.30 * slope_component + 0.25 * recovery_component, 0.0, 1.0)


def _empty_trade(tape: Tape, profile_id: str, status: str, reason: str) -> Trade:
    return Trade(tape.match_id, tape.sport, profile_id, status, None, None, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, reason, start_ts=tape.start_ts)


def simulate_profile(
    tape: Tape,
    profile: Profile,
    clock: ClockReference,
    *,
    stake: float = 1.0,
    fee_per_share: float = 0.0,
    features: TapeFeatures | None = None,
    require_execution_book: bool = False,
) -> Trade:
    """Replay one complete policy using only information available at each print."""
    if tape.opening <= 0.0 or tape.opening >= 1.0:
        return _empty_trade(tape, profile.profile_id, "NO_TRADE", "INVALID_OPEN")
    if features is None or features.shock_window_minutes != float(profile.shock_window_minutes):
        features = prepare_features(tape, clock, profile.shock_window_minutes)

    rung_weights = (0.45, 0.35, 0.20)
    sleeve_weights = {"A": 0.34, "B": 0.33, "C": 0.33}
    next_rung = 0
    shares = 0.0
    capital_used = 0.0
    entry_fees = 0.0
    exit_fees = 0.0
    proceeds = 0.0
    sleeves = {key: 0.0 for key in sleeve_weights}
    entries: list[dict[str, Any]] = []
    exits: list[dict[str, Any]] = []
    entry_i: int | None = None
    last_fill_i: int | None = None
    peak = tape.opening
    trough = tape.opening
    seen_above_r1 = False
    entry_active = True
    shock_active = False
    shock_rearmed = not profile.shock_required
    shock_floor: float | None = None
    pending_until_clock = 0.80

    def allocate_new_shares(new_shares: float) -> None:
        """Assign only newly purchased shares; never recreate sold inventory."""
        for key, weight in sleeve_weights.items():
            sleeves[key] += max(0.0, new_shares) * weight

    def average_fill() -> float:
        return capital_used / shares if shares > EPS else 0.0

    def slope(index: int) -> float:
        return features.slope_6m[index]

    def executable_ask(index: int, limit_price: float) -> float | None:
        """Use the contemporaneous ask only when strict L2 mode is enabled."""
        if not require_execution_book:
            return None
        observation = execution_observation_at(tape, tape.times[index])
        if observation is None or not observation.market_open:
            return None
        if not all(finite(value) for value in (observation.best_ask, observation.ask_depth, observation.tick_size)):
            return None
        if observation.best_ask <= 0.0 or observation.ask_depth <= EPS or observation.best_ask > limit_price + EPS:
            return None
        return max(observation.tick_size, observation.best_ask)

    def sell(index: int, price: float, quantity: float, sleeve: str, reason: str) -> None:
        nonlocal shares, proceeds, exit_fees
        quantity = min(max(0.0, quantity), sleeves[sleeve], shares)
        if quantity <= EPS:
            return
        sleeves[sleeve] -= quantity
        shares -= quantity
        proceeds += quantity * price
        exit_fees += quantity * fee_per_share
        exits.append({"i": index, "price": price, "shares": quantity, "sleeve": sleeve, "reason": reason})

    for index in range(tape.last_tradable_i + 1):
        price = tape.prices[index]
        rel = features.relative_clock[index]
        phase_limit = tape.opening * (profile.early_multiplier if rel <= 0.25 else profile.late_multiplier)
        shock = features.shock_values[index]
        if profile.shock_required and shock is not None and rel >= (1.0 / max(1.0, clock.length_for(tape.sport))):
            y_now, shock_value = shock
            if shock_value <= profile.shock_threshold and not shock_active:
                shock_active = True
                shock_rearmed = False
                shock_floor = y_now
                seen_above_r1 = False
            elif shock_active:
                if shock_floor is None or y_now < shock_floor:
                    shock_floor = y_now
                elif y_now > shock_floor + 1e-6:
                    shock_active = False
                    shock_rearmed = True

        if rel <= pending_until_clock and entry_active and (not profile.shock_required or shock_rearmed):
            in_band = 0.15 <= price <= 0.85
            if next_rung == 0:
                if price > phase_limit:
                    seen_above_r1 = True
                elif in_band:
                    fill_price = phase_limit if seen_above_r1 else price
                    book_price = executable_ask(index, phase_limit)
                    if require_execution_book and book_price is None:
                        continue
                    if book_price is not None:
                        fill_price = book_price
                    budget = stake * rung_weights[next_rung]
                    new_shares = budget / max(TICK, fill_price)
                    shares += new_shares
                    capital_used += budget
                    entry_fees += new_shares * fee_per_share
                    entries.append({"i": index, "rung": 1, "limit": phase_limit, "price": fill_price, "capital": budget})
                    next_rung = 1
                    entry_i = index if entry_i is None else entry_i
                    last_fill_i = index
                    peak = trough = price
                    allocate_new_shares(new_shares)
            elif next_rung < 3 and in_band and price <= phase_limit:
                # The bounce test must compare with a minimum known before
                # this print; including the current print would make a bounce
                # mathematically impossible.
                prior_min = features.prior_minimum_8m[index]
                bounce_ok = price >= prior_min + 0.015 - EPS
                slope_now = slope(index)
                falling_knife = prior_min - price >= 0.08 - EPS and slope_now < 0.0
                toxic = price <= 0.06 + EPS and slope_now < 0.0
                if bounce_ok and slope_now >= -EPS and not falling_knife and not toxic:
                    fill_price = min(price, phase_limit)
                    book_price = executable_ask(index, phase_limit)
                    if require_execution_book and book_price is None:
                        continue
                    if book_price is not None:
                        fill_price = book_price
                    budget = stake * rung_weights[next_rung]
                    new_shares = budget / max(TICK, fill_price)
                    shares += new_shares
                    capital_used += budget
                    entry_fees += new_shares * fee_per_share
                    entries.append({"i": index, "rung": next_rung + 1, "limit": phase_limit, "price": fill_price, "capital": budget})
                    next_rung += 1
                    entry_i = index if entry_i is None else entry_i
                    last_fill_i = index
                    peak = max(peak, price)
                    trough = min(trough, price)
                    allocate_new_shares(new_shares)

        if entry_i is None:
            if rel > pending_until_clock:
                entry_active = False
            continue

        # A newly filled rung cannot also exit on its own print.
        if index <= (last_fill_i if last_fill_i is not None else entry_i):
            peak = max(peak, price)
            trough = min(trough, price)
            continue

        avg = average_fill()
        peak = max(peak, price)
        trough = min(trough, price)
        slope_now = slope(index)
        score = winner_state_score(tape, index, entry_i, peak, trough)

        harvest_target = ceil_to_tick(max(profile.harvest_multiple * avg, avg + profile.harvest_add))
        if sleeves["A"] > EPS and price >= harvest_target:
            sell(index, price, sleeves["A"], "A", "HARVEST")
            entry_active = False

        runup = max(0.0, peak - trough)
        giveback = (peak - price) / runup if runup > EPS else 0.0
        b_target = max(profile.b_target, avg + TICK)
        b_exit = price >= b_target or (peak > avg and runup > TICK and giveback >= profile.b_giveback and slope_now <= profile.b_slope_cap)
        if sleeves["B"] > EPS and b_exit:
            sell(index, price, sleeves["B"], "B", "TRAIL_OR_TARGET")
            entry_active = False

        if sleeves["C"] > EPS and score <= 0.28:
            sleeves["B"] += sleeves["C"]
            sleeves["C"] = 0.0
            exits.append({"i": index, "price": price, "shares": 0.0, "sleeve": "C", "reason": "TRANSFER_TO_B"})

        if shares > EPS and price <= 0.08 and slope_now < 0.0:
            for sleeve in ("A", "B", "C"):
                sell(index, price, sleeves[sleeve], sleeve, "SALVAGE")
            entry_active = False

        if shares > EPS and (tape.times[index] - tape.start_ts) / 60.0 >= profile.flatten_minutes:
            for sleeve in ("A", "B", "C"):
                sell(index, price, sleeves[sleeve], sleeve, "FLATTEN")
            entry_active = False

        if shares <= EPS:
            break

    terminal = tape.terminal_price
    pending_order = entry_active and next_rung < 3 and (tape.last_tradable_i < 0 or clock.relative(tape, tape.last_tradable_i) < pending_until_clock)
    if shares > EPS and terminal is not None:
        for sleeve in ("A", "B", "C"):
            sell(tape.last_tradable_i, terminal, sleeves[sleeve], sleeve, "SETTLEMENT")
        exit_reason = "SETTLEMENT" if not exits or all(row["reason"] == "SETTLEMENT" for row in exits) else "SETTLEMENT_AFTER_PARTIAL"
        status = "RESOLVED"
    elif shares > EPS or (terminal is None and pending_order):
        return Trade(
            tape.match_id,
            tape.sport,
            profile.profile_id,
            "UNRESOLVED",
            entry_i,
            last_fill_i,
            capital_used,
            sum(row["capital"] / max(TICK, row["price"]) for row in entries),
            sum(row["shares"] for row in exits),
            entry_fees,
            exit_fees,
            None,
            "UNRESOLVED_END",
            tuple(entries),
            tuple(exits),
            tape.start_ts,
        )
    else:
        status = "RESOLVED"
        exit_reason = exits[-1]["reason"] if exits else "NO_FILL"

    pnl = proceeds - capital_used - entry_fees - exit_fees
    return Trade(
        tape.match_id,
        tape.sport,
        profile.profile_id,
        status,
        entry_i,
        last_fill_i,
        capital_used,
        sum(row["capital"] / max(TICK, row["price"]) for row in entries),
        sum(row["shares"] for row in exits),
        entry_fees,
        exit_fees,
        pnl,
        exit_reason,
        tuple(entries),
        tuple(exits),
        tape.start_ts,
    )


def max_drawdown(values: Iterable[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def normal_lower_bound(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = statistics.mean(values)
    dispersion = statistics.pstdev(values) if len(values) > 1 else 0.0
    return mean - 1.645 * dispersion / math.sqrt(len(values))


def familywise_lower_bound_95(values: Sequence[float], hypotheses: int = 1) -> float:
    """Bonferroni-adjusted lower bound for a searched family of profiles."""
    if not values:
        return 0.0
    hypotheses = max(1, int(hypotheses))
    alpha = 0.05 / hypotheses
    z = NormalDist().inv_cdf(1.0 - alpha)
    mean = statistics.mean(values)
    dispersion = statistics.pstdev(values) if len(values) > 1 else 0.0
    return mean - z * dispersion / math.sqrt(len(values))


def wilson_lower_bound(successes: int, trials: int, confidence: float = 0.95) -> float:
    """Distribution-free lower bound for a Bernoulli rate."""
    if trials <= 0:
        return 0.0
    successes = max(0, min(int(successes), int(trials)))
    p = successes / trials
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    denominator = 1.0 + z * z / trials
    center = p + z * z / (2.0 * trials)
    radius = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * trials)) / trials)
    return max(0.0, (center - radius) / denominator)


def calibrated_rate(scores: Sequence[float], outcomes: Sequence[bool], bins: int = 10) -> list[dict[str, float | int]]:
    """Return point-in-time reliability bins for a score/probability stream.

    This is deliberately a reporting primitive rather than an automatic model
    fit. Callers must build scores from training data only, then apply the table
    to later observations. Empty bins are omitted and every row exposes its
    Wilson lower bound for conservative gating.
    """
    if len(scores) != len(outcomes):
        raise ValueError("scores and outcomes must have equal length")
    bins = max(1, int(bins))
    buckets: list[list[bool]] = [[] for _ in range(bins)]
    for score, outcome in zip(scores, outcomes):
        if not finite(score):
            continue
        index = min(bins - 1, max(0, int(clamp(float(score), 0.0, 1.0) * bins)))
        buckets[index].append(bool(outcome))
    result: list[dict[str, float | int]] = []
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        successes = sum(bucket)
        result.append({
            "bin": index,
            "lower": index / bins,
            "upper": (index + 1) / bins,
            "count": len(bucket),
            "successes": successes,
            "observed_rate": successes / len(bucket),
            "wilson_lower_95": wilson_lower_bound(successes, len(bucket)),
        })
    return result


def cluster_bootstrap_lower_bound_95(
    trades: Sequence[Trade], *, iterations: int = 2000, seed: int = 17
) -> float:
    """Estimate a cluster-aware 95% lower bound by deterministic block bootstrap."""
    groups: dict[tuple[str, int], list[float]] = {}
    for trade in trades:
        if trade.pnl is None:
            continue
        day = math.floor(float(trade.start_ts) / 86400.0) if finite(trade.start_ts) else 0
        groups.setdefault((trade.sport.lower(), int(day)), []).append(float(trade.pnl))
    if not groups:
        return 0.0
    if len(groups) == 1:
        return statistics.mean(next(iter(groups.values())))
    iterations = max(100, int(iterations))
    rng = random.Random(seed)
    keys = tuple(groups)
    samples: list[float] = []
    for _ in range(iterations):
        sampled = [rng.choice(keys) for _ in keys]
        values = [value for key in sampled for value in groups[key]]
        samples.append(statistics.mean(values))
    samples.sort()
    return samples[max(0, min(len(samples) - 1, int(0.05 * len(samples))))]


def clustered_lower_bound_95(trades: Sequence[Trade]) -> float:
    """Conservative lower bound that treats sport/date clusters as dependent.

    The ordinary match-level interval assumes independent observations. That is
    unsafe when many matches share a tournament day, sport, or information
    regime. This screen preserves the per-match mean but estimates uncertainty
    from independent cluster contributions. With one cluster there is no
    defensible dispersion estimate, so the function returns the observed mean;
    promotion still requires prospective block-bootstrap evidence.
    """
    groups: dict[tuple[str, int], list[float]] = {}
    for trade in trades:
        if trade.pnl is None:
            continue
        day = math.floor(float(trade.start_ts) / 86400.0) if finite(trade.start_ts) else 0
        groups.setdefault((trade.sport.lower(), int(day)), []).append(float(trade.pnl))
    if not groups:
        return 0.0
    total_n = sum(len(values) for values in groups.values())
    mean = sum(sum(values) for values in groups.values()) / total_n
    if len(groups) < 2:
        return mean
    contributions = [sum(values) / total_n for values in groups.values()]
    dispersion = statistics.stdev(contributions)
    standard_error = math.sqrt(len(contributions)) * dispersion
    return mean - 1.645 * standard_error


def summarize_trades(
    trades: Sequence[Trade], *, hypotheses: int = 1, bootstrap: bool = False
) -> dict[str, Any]:
    nets = [float(trade.pnl) for trade in trades if trade.pnl is not None]
    mean = statistics.mean(nets) if nets else 0.0
    lcb = normal_lower_bound(nets)
    filled = [trade for trade in trades if trade.entry_i is not None]
    resolved_filled = [trade for trade in filled if trade.pnl is not None]
    without_best_trades = list(resolved_filled)
    best_trade = max((float(trade.pnl) for trade in without_best_trades), default=0.0)
    if without_best_trades:
        best_index = max(range(len(without_best_trades)), key=lambda index: (float(without_best_trades[index].pnl), without_best_trades[index].match_id))
        without_best_trades.pop(best_index)
    without_best = [float(trade.pnl) for trade in without_best_trades]
    positive = sum(value for value in nets if value > 0.0)
    negative = sum(value for value in nets if value < 0.0)
    bootstrap_lcb = cluster_bootstrap_lower_bound_95(resolved_filled) if bootstrap else None
    bootstrap_lcb_without_best = cluster_bootstrap_lower_bound_95(without_best_trades) if bootstrap else None
    return {
        "matches": len(trades),
        "evaluable": len(nets),
        "coverage": len(nets) / len(trades) if trades else 0.0,
        "filled": len(filled),
        "resolved_filled": len(resolved_filled),
        "unresolved": sum(1 for trade in trades if trade.status == "UNRESOLVED"),
        "profitable": sum(1 for value in nets if value > 0),
        "total_net": sum(nets),
        "mean_net_per_match": mean,
        "lower_bound_95": lcb,
        "familywise_lower_bound_95": familywise_lower_bound_95(nets, hypotheses),
        "cluster_count": len({(trade.sport.lower(), math.floor(float(trade.start_ts) / 86400.0)) for trade in resolved_filled if finite(trade.start_ts)}),
        "clustered_lower_bound_95": clustered_lower_bound_95(resolved_filled),
        "cluster_bootstrap_lower_bound_95": bootstrap_lcb,
        "best_trade_net": best_trade,
        "total_net_without_best_trade": sum(without_best),
        "lower_bound_95_without_best_trade": normal_lower_bound(without_best),
        "familywise_lower_bound_95_without_best_trade": familywise_lower_bound_95(without_best, hypotheses),
        "clustered_lower_bound_95_without_best_trade": clustered_lower_bound_95(without_best_trades),
        "cluster_bootstrap_lower_bound_95_without_best_trade": bootstrap_lcb_without_best,
        "mean_net_per_filled": sum(nets) / len(resolved_filled) if resolved_filled else 0.0,
        "profit_factor": positive / abs(negative) if negative < -EPS else (float("inf") if positive > 0 else 0.0),
        "max_drawdown": max_drawdown(nets),
        "exit_reasons": {reason: sum(1 for trade in trades if trade.exit_reason == reason) for reason in sorted({trade.exit_reason for trade in trades})},
    }


def opening_bucket(opening: float) -> str:
    if opening < 0.20:
        return "lt_20c"
    if opening < 0.40:
        return "20c_to_40c"
    if opening < 0.60:
        return "40c_to_60c"
    return "gte_60c"


def hierarchy_specs(tape: Tape) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return semantic group names and the current tape's concrete keys."""
    return (
        ("sport_cohort_open", (tape.sport, tape.cohort, opening_bucket(tape.opening))),
        ("sport_cohort", (tape.sport, tape.cohort)),
        ("cohort_open", (tape.cohort, opening_bucket(tape.opening))),
        ("sport", (tape.sport,)),
        ("cohort", (tape.cohort,)),
        ("all", ("all",)),
    )


def group_key(tape: Tape, name: str) -> tuple[str, ...]:
    return dict(hierarchy_specs(tape))[name]


def select_profile(
    current: Tape,
    prior_tapes: Sequence[Tape],
    clock: ClockReference,
    profiles: Sequence[Profile],
    gate: Gate,
    *,
    fee_per_share: float = 0.0,
    stake: float = 1.0,
    trade_cache: MutableMapping[tuple[str, str, float, float, bool], Trade] | None = None,
    feature_cache: MutableMapping[tuple[str, float], TapeFeatures] | None = None,
    require_execution_book: bool = False,
) -> tuple[Profile | None, dict[str, Any]]:
    embargo_cutoff = current.start_ts - max(0.0, gate.embargo_seconds)
    eligible_prior = [tape for tape in prior_tapes if tape.start_ts <= embargo_cutoff + EPS]
    selected_group: list[Tape] = []
    selected_key: tuple[str, ...] | None = None
    for name, key in hierarchy_specs(current):
        group = [tape for tape in eligible_prior if group_key(tape, name) == key]
        if len(group) >= gate.minimum_prior_matches:
            selected_group = group
            selected_key = key
            break
    if not selected_group:
        return None, {"reason": "INSUFFICIENT_HISTORY", "group": None, "candidates": []}

    candidates: list[dict[str, Any]] = []
    viable: list[tuple[float, float, float, int, str, Profile, dict[str, Any]]] = []
    for profile in profiles:
        trades = []
        for tape in selected_group:
            cache_key = (profile.profile_id, tape.match_id, float(stake), float(fee_per_share), bool(require_execution_book))
            if trade_cache is not None and cache_key in trade_cache:
                trade = trade_cache[cache_key]
            else:
                feature_key = (tape.match_id, float(profile.shock_window_minutes))
                features = feature_cache.get(feature_key) if feature_cache is not None else None
                if features is None:
                    features = prepare_features(tape, clock, profile.shock_window_minutes)
                    if feature_cache is not None:
                        feature_cache[feature_key] = features
                trade = simulate_profile(tape, profile, clock, stake=stake, fee_per_share=fee_per_share, features=features, require_execution_book=require_execution_book)
                if trade_cache is not None:
                    trade_cache[cache_key] = trade
            trades.append(trade)
        result = summarize_trades(trades, hypotheses=max(gate.profile_family_size, len(profiles)))
        result["profile_id"] = profile.profile_id
        candidates.append(result)
        if (
            result["resolved_filled"] >= gate.minimum_prior_fills
            and result["coverage"] >= gate.minimum_coverage
            and result["familywise_lower_bound_95"] > gate.minimum_lcb
            and result["familywise_lower_bound_95_without_best_trade"] > gate.minimum_lcb_after_best_trade
            and result["cluster_count"] >= gate.minimum_prior_clusters
            and result["clustered_lower_bound_95"] > gate.minimum_clustered_lcb
            and result["clustered_lower_bound_95_without_best_trade"] > gate.minimum_clustered_lcb_after_best_trade
        ):
            viable.append((result["familywise_lower_bound_95"], result["mean_net_per_match"], result["coverage"], result["filled"], profile.profile_id, profile, result))
    if not viable:
        return None, {"reason": "NO_PROFILE_CLEARS_GATE", "group": selected_key, "group_matches": len(selected_group), "candidates": candidates}
    viable.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4]), reverse=True)
    chosen = viable[0]
    return chosen[5], {
        "reason": "PROFILE_SELECTED",
        "group": selected_key,
        "group_matches": len(selected_group),
        "profile_id": chosen[4],
        "selection_result": chosen[6],
        "candidates": candidates,
    }


def replay_unified(
    tapes: Sequence[Tape],
    clock: ClockReference,
    *,
    profiles: Sequence[Profile] | None = None,
    gate: Gate = Gate(),
    stake: float = 1.0,
    fee_per_share: float = 0.0,
    require_execution_book: bool = False,
) -> dict[str, Any]:
    ordered = sorted(tapes, key=lambda tape: (tape.start_ts, tape.match_id))
    profiles = tuple(profiles or profile_library())
    decisions: list[dict[str, Any]] = []
    trades: list[Trade] = []
    trade_cache: dict[tuple[str, str, float, float, bool], Trade] = {}
    feature_cache: dict[tuple[str, float], TapeFeatures] = {}
    for index, tape in enumerate(ordered):
        if index < gate.warmup_matches:
            decisions.append({"match_id": tape.match_id, "action": "NO_TRADE", "reason": "WALK_FORWARD_WARMUP"})
            trades.append(_empty_trade(tape, "NONE", "NO_TRADE", "WALK_FORWARD_WARMUP"))
            continue
        profile, selection = select_profile(tape, ordered[:index], clock, profiles, gate, stake=stake, fee_per_share=fee_per_share, trade_cache=trade_cache, feature_cache=feature_cache, require_execution_book=require_execution_book)
        if profile is None:
            decisions.append({"match_id": tape.match_id, "action": "NO_TRADE", "reason": selection["reason"], "selection": selection})
            trades.append(_empty_trade(tape, "NONE", "NO_TRADE", selection["reason"]))
            continue
        feature_key = (tape.match_id, float(profile.shock_window_minutes))
        features = feature_cache.get(feature_key)
        if features is None:
            features = prepare_features(tape, clock, profile.shock_window_minutes)
            feature_cache[feature_key] = features
        trade = simulate_profile(tape, profile, clock, stake=stake, fee_per_share=fee_per_share, features=features, require_execution_book=require_execution_book)
        decisions.append({"match_id": tape.match_id, "action": "REPLAY_PROFILE", "profile_id": profile.profile_id, "selection": selection, "status": trade.status, "pnl": trade.pnl})
        trades.append(trade)
    summary = summarize_trades(trades, bootstrap=True)
    return {
        "algorithm": "SPAN_HARVEST_UNIFIED_1.2.0",
        "replay": "causal_profile_selection_plus_apzi_state_machine",
        "status": "RESEARCH_ONLY_NO_PROMOTION",
        "gate": asdict(gate),
        "fee_per_share": fee_per_share,
        "require_execution_book": require_execution_book,
        "profile_count": len(profiles),
        "profile_library_sha256": profile_hash(profiles),
        "summary": summary,
        "trades": [asdict(trade) for trade in trades],
        "decisions": decisions,
    }


def run_cost_stress(
    tapes: Sequence[Tape],
    clock: ClockReference,
    *,
    fee_levels: Sequence[float] = (0.0, 0.005, 0.01, 0.02),
    gate: Gate = Gate(),
    profiles: Sequence[Profile] | None = None,
    require_execution_book: bool = False,
) -> list[dict[str, Any]]:
    """Run the identical chronological replay across a fee-sensitivity grid."""
    results: list[dict[str, Any]] = []
    for fee in fee_levels:
        if not finite(fee) or fee < 0.0:
            raise ValueError("fee levels must be finite and non-negative")
        replay = replay_unified(
            tapes,
            clock,
            profiles=profiles,
            gate=gate,
            fee_per_share=float(fee),
            require_execution_book=require_execution_book,
        )
        results.append({
            "fee_per_share": float(fee),
            "summary": replay["summary"],
            "status": replay["status"],
        })
    return results


def profile_hash(profiles: Sequence[Profile]) -> str:
    payload = json.dumps([asdict(profile) for profile in profiles], sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_report(
    tape_source: str | Path = DEFAULT_TAPE_SOURCE,
    clock_source: str | Path | None = DEFAULT_CLOCK_SOURCE,
    *,
    fee_per_share: float = 0.0,
    gate: Gate = Gate(),
    require_execution_book: bool = False,
) -> dict[str, Any]:
    payload, tapes, rejected = load_tapes(tape_source)
    clock = load_clock_reference(clock_source, tapes)
    replay = replay_unified(tapes, clock, gate=gate, fee_per_share=fee_per_share, require_execution_book=require_execution_book)
    replay["source"] = {
        "tape_source": str(tape_source),
        "clock_source": str(clock_source) if clock_source else None,
        "release_id": payload.get("release_id"),
        "generated_utc": payload.get("generated_utc"),
        "raw_population": payload.get("n_population"),
        "kept_in_source": payload.get("n_kept"),
        "loaded_tapes": len(tapes),
        "rejected_or_omitted": rejected,
        "payload_sha256": payload_hash(payload),
        "clock_by_sport": dict(sorted(clock.by_sport.items())),
        "pooled_clock_minutes": clock.pooled_median,
    }
    replay["guardrails"] = [
        "complete profiles are selected only from older chronological matches",
        "all features use prints at or before the current event",
        "rung one uses actual first-crossing print when it is below the limit",
        "conditional adds require bounce, non-negative slope, and no toxicity",
        "new fills cannot exit on the same print",
        "unknown ends with open inventory or pending entry are UNRESOLVED",
        "state score and normalized shock are diagnostics, not calibrated probabilities",
        "print proxies do not imply queue position, depth, or live fillability",
        "strict L2 mode requires a contemporaneous ask and depth observation for every entry",
        "no broker, wallet, order route, Site mutation, or public posting authority",
    ]
    return replay


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_TAPE_SOURCE, help="clean_tapes.json URL or local path")
    parser.add_argument("--clock-source", default=DEFAULT_CLOCK_SOURCE, help="game_time_by_sport.json URL or local path")
    parser.add_argument("--fee-per-share", type=float, default=0.0)
    parser.add_argument("--require-execution-book", action="store_true", help="fail closed unless a contemporaneous L2 ask/depth is available")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.source, args.clock_source, fee_per_share=args.fee_per_share, require_execution_book=args.require_execution_book)
    json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
