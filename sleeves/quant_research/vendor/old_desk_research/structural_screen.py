#!/usr/bin/env python3
"""desk/structural_screen.py -- the structural chart screen (2026-10-12).

WHY THIS EXISTS (The owner, 2026-10-12, the SNDK incident): a desk scoring
surface crowned SNDK the best buy of the watchlist on the very day it
lost its rising trendline support, closed under its 50-day average and
broke its September pivot low. The scoring inputs (signal votes,
confidence, "how reset is it") contain NO structural information --
worse, they score a breakdown *higher* as it deepens. The owner's ruling:
"Gate every ranking behind chart reads." This module is Layer 1 of
that gate: the deterministic geometry half of the chart-read protocol
(chart-read skill, Pass A), encoded as explicit structural questions:

  1. Is price above or below EMA20 / EMA50 / EMA200, and by how much
     (in ATR14 units)?
  2. Is the rising support line drawn from the two most recent higher
     confirmed pivot lows still holding, or did today's close break it?
  3. Did the close lose the most recent confirmed pivot low?
  4. How close is price to that support line (proximity warning)?

Verdicts:
  BROKEN  -- active breakdown: (support-line break OR last pivot low
             lost) AND the close is below EMA50. A BROKEN name may not
             be presented as a top-ranked buy; the ranking gate demotes
             it below every non-BROKEN candidate (see
             apply_structure_rank).
  WATCH   -- one structural condition is degraded (below EMA50 alone,
             a single break condition without EMA50 confirmation, or
             price within 0.5 ATR above the support line).
  INTACT  -- no structural condition triggered.
  UNKNOWN -- insufficient bars or a computation failure. UNKNOWN never
             earns a rank penalty (the trading path must not break on a
             data hiccup), but it IS recorded, so an assessment surface
             can see the name was not structurally cleared.

Conventions: daily bars, desk data policy via desk.bars.fetch_bars
(feed=sip, adjustment=split). Pivots are 2-left/2-right confirmed
fractals (a pivot is only known once the 2 bars after it exist --
no lookahead). Break tolerance is 0.1 x ATR14, stated as a tolerance,
not a fabricated line. All functions are pure on bar lists; the only
I/O is screen_symbol(), which never raises (fail-open to UNKNOWN).
"""

from __future__ import annotations

MIN_BARS = 60
BREAK_TOL_ATR = 0.1        # tolerance around a level, in ATR units
PROXIMITY_ATR = 0.5        # WATCH when support is this close below
BROKEN_RANK_PENALTY = 1000  # demotes below every plausible rank_score


def _f(bar, *keys):
    for k in keys:
        v = bar.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


def _closes(bars):
    return [_f(b, "c", "close") for b in bars]


def _ema(values, period):
    # Full audit 2026-10-12: the old code DELETED missing closes before
    # computing, time-warping the EMA (bar spacing no longer matched
    # calendar spacing; one None close shifted the EMA permanently
    # while screen_from_bars compares it to closes[-1] as if aligned).
    # Forward-fill instead: a missing close carries the last known
    # close (no index shift). No value at all -> None.
    vals = []
    _last = None
    for v in values:
        if v is not None:
            _last = v
        if _last is not None:
            vals.append(_last)
    if len(vals) < period:
        return None
    k = 2.0 / (period + 1.0)
    e = sum(vals[:period]) / period
    for v in vals[period:]:
        e = v * k + e * (1.0 - k)
    return e


def _atr14(bars):
    """Wilder ATR14; None when fewer than 15 usable bars."""
    trs = []
    prev_c = None
    for b in bars:
        h, l, c = _f(b, "h", "high"), _f(b, "l", "low"), _f(b, "c", "close")
        if h is None or l is None or c is None:
            prev_c = c
            continue
        tr = h - l if prev_c is None else max(
            h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
        prev_c = c
    if len(trs) < 14:
        return None
    atr = sum(trs[:14]) / 14.0
    for tr in trs[14:]:
        atr = (atr * 13.0 + tr) / 14.0
    return atr


def _pivot_lows(bars, left=2, right=2):
    """Confirmed pivot lows: [(index, low)] with `right` bars after --
    a pivot only exists once confirmed (no lookahead)."""
    lows = [_f(b, "l", "low") for b in bars]
    out = []
    for i in range(left, len(bars) - right):
        if lows[i] is None:
            continue
        window = lows[i - left:i + right + 1]
        if any(v is None for v in window):
            continue
        if all(lows[i] <= v for v in window) and (
                lows[i] < max(window[:left] + window[left + 1:]) or
                window.count(lows[i]) == 1):
            out.append((i, lows[i]))
    return out


MIN_LINE_SEPARATION = 10   # bars between anchor pivots (a trendline
                           # needs temporal span; two wiggles 8 bars
                           # apart make a slope price cannot sustain)


def _rising_support(pivots, closes, tol):
    """Rising support line anchored on two HIGHER confirmed pivot lows.

    Picks the widest-separation valid pair among the recent pivots (a
    human anchors a trendline across the base, not between adjacent
    wiggles). A candidate line is DEAD -- skipped -- if any close after
    its second anchor already closed below it (minus tolerance): that
    break is stale news, not today's event. Returns
    (slope_per_bar, i2, low2) or None. value(i) = low2 + slope*(i - i2).
    """
    if len(pivots) < 2:
        return None
    recent = pivots[-8:]
    candidates = []
    for a in range(len(recent)):
        for b in range(a + 1, len(recent)):
            (i1, l1), (i2, l2) = recent[a], recent[b]
            if l2 > l1 and (i2 - i1) >= MIN_LINE_SEPARATION:
                candidates.append((i2 - i1, i2, (l2 - l1) / (i2 - i1),
                                   l2, i1))
    # widest separation first, then most recent anchor
    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
    n = len(closes)
    for _sep, i2, slope, l2, i1 in candidates:
        # Dead if any close since the FIRST anchor traded below the
        # line (minus tolerance) -- between the anchors the segment
        # itself was crossed, after them the break already happened;
        # either way it is stale news, not today's event.
        dead = False
        for i in range(i1 + 1, n - 1):
            if closes[i] is not None and \
                    closes[i] < l2 + slope * (i - i2) - tol:
                dead = True
                break
        if not dead:
            return (slope, i2, l2)
    return None


def screen_from_bars(symbol, bars):
    """Structural verdict from a daily bar list (oldest first)."""
    sym = str(symbol).upper()
    base = {"symbol": sym, "verdict": "UNKNOWN", "reasons": [],
            "metrics": {}}
    if not bars or len(bars) < MIN_BARS:
        base["reasons"].append("insufficient bars (%d < %d)"
                               % (len(bars or []), MIN_BARS))
        return base
    closes = _closes(bars)
    close = closes[-1]
    if close is None:
        base["reasons"].append("last close unusable")
        return base
    ema20, ema50, ema200 = (_ema(closes, 20), _ema(closes, 50),
                            _ema(closes, 200))
    atr = _atr14(bars)
    if atr is None or atr <= 0:
        base["reasons"].append("ATR14 unavailable")
        return base
    n = len(bars)
    pivots = _pivot_lows(bars)
    last_pivot_low = pivots[-1][1] if pivots else None
    tol = BREAK_TOL_ATR * atr
    support = _rising_support(pivots, closes, tol)
    support_value = None
    if support is not None:
        slope, i2, l2 = support
        support_value = l2 + slope * (n - 1 - i2)
    below_50 = ema50 is not None and close < ema50
    support_break = (support_value is not None
                     and close < support_value - tol)
    pivot_lost = (last_pivot_low is not None
                  and close < last_pivot_low - tol)

    m = base["metrics"]
    m.update({
        "close": round(close, 2),
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "ema200": round(ema200, 2) if ema200 else None,
        "atr14": round(atr, 2),
        "dist_ema50_atr": (round((close - ema50) / atr, 2)
                           if ema50 else None),
        "last_pivot_low": (round(last_pivot_low, 2)
                           if last_pivot_low else None),
        "support_line_value": (round(support_value, 2)
                               if support_value is not None else None),
        "support_break": bool(support_break),
        "pivot_lost": bool(pivot_lost),
        "below_ema50": bool(below_50),
    })

    reasons = base["reasons"]
    if support_break:
        reasons.append("close broke rising support line ($%.2f)"
                       % support_value)
    if pivot_lost:
        reasons.append("close lost last confirmed pivot low ($%.2f)"
                       % last_pivot_low)
    if below_50:
        reasons.append("close below EMA50 ($%.2f, %+.2f ATR)"
                       % (ema50, (close - ema50) / atr))

    if (support_break or pivot_lost) and below_50:
        base["verdict"] = "BROKEN"
    elif below_50 or pivot_lost or support_break:
        base["verdict"] = "WATCH"
    elif (support_value is not None
          and 0 <= (close - support_value) <= PROXIMITY_ATR * atr):
        base["verdict"] = "WATCH"
        reasons.append("within %.1f ATR above rising support ($%.2f)"
                       % (PROXIMITY_ATR, support_value))
    else:
        base["verdict"] = "INTACT"
        if not reasons:
            reasons.append("structure intact: above EMA50, support "
                           "holding, last pivot low intact")
    return base


def apply_structure_rank(rank_score, verdict):
    """The ranking gate: a BROKEN structure demotes a candidate below
    every non-BROKEN one. Other verdicts leave the score untouched --
    the screen annotates; only an active breakdown vetoes rank."""
    if verdict == "BROKEN":
        return rank_score - BROKEN_RANK_PENALTY
    return rank_score


def screen_symbol(symbol, limit=300):
    """Fetch daily bars under desk policy and screen. Never raises."""
    try:
        from desk import bars as desk_bars
        bars = desk_bars.fetch_bars(symbol, limit=limit, timeframe="1d")
    except Exception as e:  # noqa: BLE001 -- fail-open to UNKNOWN
        return {"symbol": str(symbol).upper(), "verdict": "UNKNOWN",
                "reasons": ["fetch failed: %s" % str(e)[:120]],
                "metrics": {}}
    return screen_from_bars(symbol, bars or [])


if __name__ == "__main__":
    import json
    import sys
    for sym in sys.argv[1:]:
        print(json.dumps(screen_symbol(sym), indent=1))
