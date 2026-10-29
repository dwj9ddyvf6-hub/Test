"""Forecast-first evaluation metrics; these functions do not evaluate P&L."""

from __future__ import annotations

from math import expm1, fsum, isfinite, log, log1p
from typing import Iterable, Sequence


def _finite_number(value: object, label: str) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite numeric value, not a boolean or coercible value")
    try:
        return isfinite(value)
    except OverflowError as exc:
        raise ValueError(f"{label} must be a finite numeric value") from exc


def _stable_mean(values: Sequence[float]) -> float:
    """Average finite values without overflowing on a representable mean."""
    if not values:
        raise ValueError("cannot average an empty sequence")
    scale = max(abs(value) for value in values)
    if scale == 0:
        return 0.0
    normalized_mean = fsum(value / scale for value in values) / len(values)
    return scale * max(-1.0, min(1.0, normalized_mean))


def probability_metrics(actual: Sequence[int], probability: Sequence[float], *, calibrated: bool) -> dict[str, float]:
    """Score binary outcomes; caller must explicitly attest probabilities are calibrated OOS."""
    if calibrated is not True:
        raise ValueError("probability metrics require a calibrated, out-of-sample probability series")
    if len(actual) != len(probability) or not actual:
        raise ValueError("actual and probability arrays must have equal, non-zero length")
    if any(isinstance(y, bool) or not isinstance(y, int) or y not in (0, 1) for y in actual):
        raise ValueError("actual labels must be 0 or 1")
    if any(not _finite_number(p, "probability") or not 0.0 <= p <= 1.0 for p in probability):
        raise ValueError("probabilities must be in [0, 1]")
    eps = 1e-15
    brier = sum((p - y) ** 2 for y, p in zip(actual, probability)) / len(actual)
    log_loss = -sum(y * log(max(eps, p)) + (1 - y) * log(max(eps, 1 - p)) for y, p in zip(actual, probability)) / len(actual)
    base_rate = sum(actual) / len(actual)
    baseline_brier = sum((base_rate - y) ** 2 for y in actual) / len(actual)
    return {
        "n": float(len(actual)),
        "event_rate": base_rate,
        "brier": brier,
        "brier_skill_vs_base_rate": 1.0 - brier / baseline_brier if baseline_brier else 0.0,
        "log_loss": log_loss,
    }


def calibration_bins(actual: Sequence[int], probability: Sequence[float], *, bins: int = 10,
                     calibrated: bool) -> list[dict[str, float]]:
    """Return reliability-bin statistics; empty bins are omitted."""
    if calibrated is not True:
        raise ValueError("reliability bins require a calibrated, out-of-sample probability series")
    if (isinstance(bins, bool) or not isinstance(bins, int) or bins < 2 or bins > 2**53
            or len(actual) != len(probability) or not actual):
        raise ValueError("provide equal non-empty arrays and between 2 and 2^53 bins")
    # Only populated bins need storage. A dense list lets a caller-provided
    # bin count allocate unbounded memory even for a two-row sample.
    groups: dict[int, list[tuple[int, float]]] = {}
    for y, p in zip(actual, probability):
        if (isinstance(y, bool) or not isinstance(y, int) or y not in (0, 1)
                or not _finite_number(p, "probability") or not 0.0 <= p <= 1.0):
            raise ValueError("invalid binary outcome or probability")
        index = min(bins - 1, int(p * bins))
        groups.setdefault(index, []).append((y, p))
    return [
        {"bin_low": i / bins, "bin_high": (i + 1) / bins,
         "n": float(len(group)), "mean_probability": fsum(p / len(group) for _, p in group),
         "event_rate": fsum(y / len(group) for y, _ in group)}
        for i, group in sorted(groups.items())
    ]


def qlike(actual_variance: Sequence[float], forecast_variance: Sequence[float]) -> float:
    """QLIKE loss for strictly positive realized and forecast variance observations."""
    if len(actual_variance) != len(forecast_variance) or not actual_variance:
        raise ValueError("variance arrays must have equal, non-zero length")
    losses = []
    for actual, forecast in zip(actual_variance, forecast_variance):
        if (not _finite_number(actual, "actual variance")
                or not _finite_number(forecast, "forecast variance")
                or actual <= 0.0 or forecast <= 0.0):
            raise ValueError("variance observations must be positive")
        # Use relative change around one so the loss does not disappear to
        # cancellation when the forecast is very close to the realized value.
        # Away from one, subtracting logs avoids overflowing actual/forecast.
        try:
            relative_change = (actual - forecast) / forecast
        except OverflowError:
            relative_change = float("inf")
        if isfinite(relative_change) and -0.5 <= relative_change <= 0.5:
            log_ratio = log1p(relative_change)
        else:
            log_ratio = log(actual) - log(forecast)
        try:
            loss = expm1(log_ratio) - log_ratio
        except OverflowError as exc:
            raise ValueError("QLIKE loss exceeds the finite numeric range") from exc
        if not isfinite(loss):
            raise ValueError("QLIKE loss exceeds the finite numeric range")
        losses.append(loss)
    return fsum(loss / len(losses) for loss in losses)


def benjamini_hochberg(p_values: Sequence[float]) -> list[float]:
    """Return BH-adjusted p-values in original order for a declared test family."""
    if any(not _finite_number(p, "p-value") or not 0.0 <= p <= 1.0 for p in p_values):
        raise ValueError("p-values must be in [0, 1]")
    n = len(p_values)
    if n == 0:
        return []
    ranked = sorted(enumerate(p_values), key=lambda pair: pair[1])
    adjusted = [1.0] * n
    running = 1.0
    for rank_from_end in range(n - 1, -1, -1):
        original_index, p_value = ranked[rank_from_end]
        rank = rank_from_end + 1
        running = min(running, p_value * n / rank)
        adjusted[original_index] = min(1.0, running)
    return adjusted


def paired_loss_delta(candidate_loss: Iterable[float], baseline_loss: Iterable[float]) -> dict[str, float]:
    """Summarize paired loss differences; negative candidate-minus-baseline is better."""
    candidate = list(candidate_loss)
    baseline = list(baseline_loss)
    if len(candidate) != len(baseline) or not candidate:
        raise ValueError("paired loss arrays must have equal, non-zero length")
    if any(not _finite_number(value, "loss") for value in candidate + baseline):
        raise ValueError("loss inputs must be finite")
    delta = [c - b for c, b in zip(candidate, baseline)]
    if any(not isfinite(value) for value in delta):
        raise ValueError("paired loss differences must remain finite")
    ordered = sorted(delta)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else ordered[middle - 1] / 2.0 + ordered[middle] / 2.0
    return {"n": float(len(delta)), "mean_candidate_minus_baseline": _stable_mean(delta),
            "median_candidate_minus_baseline": median}


def risk_ranking_auc(actual_event: Sequence[int], risk_score: Sequence[float]) -> float | None:
    """Pairwise AUC for an uncalibrated risk ranking; None when only one class occurs."""
    if len(actual_event) != len(risk_score) or not actual_event:
        raise ValueError("event and score arrays must have equal, non-zero length")
    if any(isinstance(label, bool) or not isinstance(label, int) or label not in (0, 1) for label in actual_event):
        raise ValueError("event labels must be 0 or 1")
    if any(not _finite_number(score, "risk score") for score in risk_score):
        raise ValueError("risk scores must be finite")
    positives = sum(label == 1 for label in actual_event)
    negatives = len(actual_event) - positives
    if not positives or not negatives:
        return None

    # Mann–Whitney pair counting with score ties grouped after sorting. The
    # previous nested positive/negative loop was quadratic and became
    # impractical for the large validation panels this metric is meant to
    # summarize. `wins_twice` keeps half-credit ties exact using integers.
    ranked = sorted(zip(risk_score, actual_event), key=lambda pair: pair[0])
    negatives_below = 0
    wins_twice = 0
    index = 0
    while index < len(ranked):
        end = index + 1
        score_value = ranked[index][0]
        while end < len(ranked) and ranked[end][0] == score_value:
            end += 1
        group_positives = sum(label == 1 for _, label in ranked[index:end])
        group_negatives = end - index - group_positives
        wins_twice += group_positives * (2 * negatives_below + group_negatives)
        negatives_below += group_negatives
        index = end
    return wins_twice / (2 * positives * negatives)


def directional_hit_rate(actual_return: Sequence[float], signed_score: Sequence[float]) -> dict[str, float]:
    """Report sign agreement and coverage; this is not a profitability metric."""
    if len(actual_return) != len(signed_score) or not actual_return:
        raise ValueError("return and score arrays must have equal, non-zero length")
    if any(not _finite_number(value, "return or score") for value in list(actual_return) + list(signed_score)):
        raise ValueError("returns and scores must be finite")
    eligible = [(y, s) for y, s in zip(actual_return, signed_score) if y != 0.0 and s != 0.0]
    if not eligible:
        return {"n": 0.0, "coverage": 0.0, "directional_hit_rate": 0.0}
    hits = sum(1 for y, s in eligible if (y > 0.0) == (s > 0.0))
    return {"n": float(len(eligible)), "coverage": len(eligible) / len(actual_return),
            "directional_hit_rate": hits / len(eligible)}
