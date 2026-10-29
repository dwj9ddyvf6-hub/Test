"""Studies: pure scorers (S1 gap-fill, S2 ORB/IB, S3 earnings, S6 state vectors / P_NN), ported from Silicon.
No network, no ledger writes here; studies_feed.py feeds them real inputs and studies_card.py owns the ledger-first
writes and the explicit no-data states. The engine measures; it does not trade.

Conventions: intraday days are dicts
  {"date": "2026-10-23", "prev_close": float,
   "bars": [{"minute": int minutes after 09:30 ET, "o","h","l","c","v"}]}
Only completed sessions are ever passed in by the caller.
"""
from __future__ import annotations

import math
import statistics
from datetime import date

# ---------------- S1 gap-fill ----------------

def _band(gap_pct_abs: float) -> str:
    if gap_pct_abs < 0.01:
        return "<1%"
    if gap_pct_abs < 0.02:
        return "1-2%"
    return ">=2%"


def _cell(n: int, fills: int) -> dict:
    return {"n": n, "fills": fills,
            "frequency": (fills / n) if n else None}


def gap_fill_study(days: list[dict], fill_pct: float = 1.0) -> dict:
    """Gap = first bar open vs prior close. A session with no gap is
    excluded from the denominator (vendor contract). Fill at
    `fill_pct` of the gap retraced intraday."""
    n = fills = 0
    by_band: dict[str, list[int]] = {}
    by_weekday: dict[str, list[int]] = {}
    for d in days:
        bars = d.get("bars") or []
        if not bars or not d.get("prev_close"):
            continue
        pc = d["prev_close"]
        open_ = bars[0]["o"]
        gap = open_ - pc
        if gap == 0:
            continue  # no-gap session: excluded, never counted
        target = pc + gap * (1.0 - fill_pct)
        if gap > 0:
            filled = any(b["l"] <= target for b in bars)
        else:
            filled = any(b["h"] >= target for b in bars)
        n += 1
        fills += int(filled)
        b = _band(abs(gap) / pc)
        wd = date.fromisoformat(d["date"]).strftime("%a")
        for part, key in ((by_band, b), (by_weekday, wd)):
            cell = part.setdefault(key, [0, 0])
            cell[0] += 1
            cell[1] += int(filled)
    if n == 0:
        return {"state": "no_data", "n": 0, "fills": 0, "frequency": None,
                "fill_pct": fill_pct, "partitions": {"by_band": {},
                                                     "by_weekday": {}},
                "reason": "no gapped completed sessions in the sample"}
    return {"state": "graded", "n": n, "fills": fills,
            "frequency": fills / n, "fill_pct": fill_pct,
            "partitions": {
                "by_band": {k: _cell(*v) for k, v in sorted(by_band.items())},
                "by_weekday": {k: _cell(*v) for k, v in
                               sorted(by_weekday.items())}}}


# ---------------- S2 opening range / initial balance ----------------

WINDOWS = (5, 15, 30, 60)
EXTENSIONS = (0.5, 1.0, 1.5)


def _orb_one(days: list[dict], window: int) -> dict:
    n = one = both = none = 0
    ext_hits = {str(x): 0 for x in EXTENSIONS}
    ext_base = 0
    for d in days:
        bars = d.get("bars") or []
        opening = [b for b in bars if b.get("minute", 0) < window]
        rest = [b for b in bars if b.get("minute", 0) >= window]
        if not opening or not rest:
            continue
        hi = max(b["h"] for b in opening)
        lo = min(b["l"] for b in opening)
        width = hi - lo
        if width <= 0:
            continue
        n += 1
        broke_up = any(b["h"] > hi for b in rest)
        broke_dn = any(b["l"] < lo for b in rest)
        if broke_up and broke_dn:
            both += 1
        elif broke_up or broke_dn:
            one += 1
        else:
            none += 1
        if broke_up or broke_dn:
            ext_base += 1
            exc = 0.0
            if broke_up:
                exc = max(exc, (max(b["h"] for b in rest) - hi) / width)
            if broke_dn:
                exc = max(exc, (lo - min(b["l"] for b in rest)) / width)
            for x in EXTENSIONS:
                if exc >= x - 1e-12:
                    ext_hits[str(x)] += 1
    if n == 0:
        return {"state": "no_data", "n": 0, "window_min": window,
                "reason": "no completed sessions with an opening range"}
    return {"state": "graded", "n": n, "window_min": window,
            "break_one_side": one, "break_both": both, "no_break": none,
            "break_one_side_rate": one / n, "break_both_rate": both / n,
            "no_break_rate": none / n,
            "extension_rates": {k: (v / ext_base if ext_base else None)
                                for k, v in ext_hits.items()},
            "extension_n": ext_base}


def orb_ib_study(days: list[dict], windows=WINDOWS) -> dict:
    return {str(w): _orb_one(days, w) for w in windows}


# ---------------- S3 earnings distributions ----------------

def earnings_stats(moves: list[float]) -> dict:
    """moves: per-event close-to-close returns (fractions). Vendor stats:
    n, mean, median, std (sample), share positive, Sharpe = mean/std.
    Fewer than 3 events render explicit no-data — never a padded n."""
    n = len(moves)
    if n < 3:
        return {"state": "no_data", "n": n,
                "reason": f"only {n} earnings events found (<3 required)"}
    mean = statistics.fmean(moves)
    std = statistics.stdev(moves) if n > 1 else 0.0
    return {"state": "graded", "n": n, "mean": mean,
            "median": statistics.median(moves), "std": std,
            "share_positive": sum(1 for m in moves if m > 0) / n,
            "sharpe": (mean / std) if std > 0 else None,
            "label": "Sharpe = mean/std of underlying event moves "
                     "(vendor definition, OURS adaptation to daily bars)"}


def earnings_moves(event_dates: list[str], daily_bars: list[dict],
                   cap: int = 12) -> list[float]:
    """Event-session close-to-close moves for the last <=cap events.
    daily_bars: [{"t": date str, "c": close}] ascending."""
    closes = {b["t"][:10]: b["c"] for b in daily_bars}
    dates = sorted(closes)
    moves = []
    for ev in sorted(event_dates)[-cap:]:
        prior = [d for d in dates if d < ev]
        sess = [d for d in dates if d >= ev]
        if prior and sess and closes[prior[-1]]:
            moves.append(closes[sess[0]] / closes[prior[-1]] - 1.0)
    return moves


def parse_earnings_dates(submissions: dict) -> list[str]:
    """8-K Item 2.02 filing dates from an EDGAR submissions payload
    (declared OURS proxy for an earnings calendar)."""
    recent = (submissions.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    items = recent.get("items") or []
    out = []
    for i, f in enumerate(forms):
        if f == "8-K" and i < len(dates) and \
                (not items or "2.02" in (items[i] if i < len(items) else "")):
            out.append(dates[i])
    return sorted(set(out))


# ---------------- S6 state vectors + P_NN ----------------

MAD_TO_Z = 1.4826  # OURS: the constant the vendor never named


def price_coordinate(closes: list[float]) -> float | None:
    """P coordinate (declared OURS form): 21-session log return."""
    if len(closes) < 22 or closes[-22] <= 0:
        return None
    return math.log(closes[-1] / closes[-22])


def vol_coordinate(closes: list[float]) -> float | None:
    """V coordinate: stdev of the last 21 daily log returns."""
    if len(closes) < 22:
        return None
    rets = [math.log(closes[i] / closes[i - 1])
            for i in range(len(closes) - 21, len(closes))]
    return statistics.pstdev(rets)


def dix_coordinate(ratios: list) -> float | None:
    """D: per-name FNQC ratios, missing day filled 0.5, 5-session
    average, lagged 1 session (so the last value is dropped)."""
    if len(ratios) < 2:
        return None
    lagged = ratios[:-1]
    window = lagged[-5:]
    filled = [0.5 if r is None else r for r in window]
    return statistics.fmean(filled)


def normalise(value: float, history: list[float]) -> float | None:
    """Median/MAD normalisation over prior sessions, tanh-compressed.
    Requires >=126 finite history values."""
    finite = [h for h in history if h is not None and math.isfinite(h)]
    if len(finite) < 126 or value is None:
        return None
    med = statistics.median(finite)
    mad = statistics.median([abs(h - med) for h in finite])
    if mad == 0:
        return None
    z = MAD_TO_Z * (value - med) / mad
    return math.tanh(z / 3.0)  # bounded compression, declared


MIN_NEIGHBOURS = 30   # SqueezeMetrics' count-and-spread read (REA CX-sm-1): a mean of fewer than 30 is not shown


def _quantile(sorted_vals, q):
    """linear-interpolated quantile of an ascending list"""
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def p_nn(current: list, history: list[dict]) -> dict:
    """P_NN: mean matured P (+21 sessions) over the nearest one-sixth
    of historical states in normalised 5-coordinate space. History
    rows: {"vector": [5 floats|None], "matured_p": float|None}.
    <126 accrued sessions -> explicit insufficient-history state."""
    accrued = len(history)
    usable = [h for h in history
              if h.get("vector") and all(v is not None for v in h["vector"])
              and h.get("matured_p") is not None]
    if accrued < 126 or not usable or \
            any(v is None for v in (current or [])):
        return {"state": "insufficient_history", "p_nn": None,
                "history_sessions_accrued": accrued,
                "reason": "P_NN needs >=126 accrued state sessions with "
                          "matured outcomes; none are imputed"}
    def dist(h):
        return math.sqrt(sum((a - b) ** 2
                             for a, b in zip(current, h["vector"])))
    ordered = sorted(usable, key=dist)
    k = max(1, math.ceil(len(ordered) / 6))
    nearest = ordered[:k]
    ps = sorted(h["matured_p"] for h in nearest)
    base = {"history_sessions_accrued": accrued, "neighbours": k, "n_neighbours": k,
            "nearest_distance": dist(nearest[0])}
    if k < MIN_NEIGHBOURS:
        return {"state": "too_few_neighbours", "p_nn": None, **base,
                "reason": f"{k} neighbours, under the {MIN_NEIGHBOURS} a spread needs; none are imputed"}
    return {"state": "graded", "p_nn": statistics.fmean(ps), **base,
            "p10": _quantile(ps, 0.10), "p50": _quantile(ps, 0.50), "p90": _quantile(ps, 0.90)}
