#!/usr/bin/env python3
"""RSI x OBV divergence scanner — RESEARCH MODULE ONLY.

Reconstruction of the method demonstrated in the @PredictionAlgos video
(2026-10-01, "SECRET: HOW TO PREDICT PUMPS AND DUMPS LIKE A PRO") and the
quantcharts.pro/apps2/rsiobv/ tool page the video points to.

What the method is, as observed frame-by-frame:
  1. Detect divergences between price and two indicators — RSI (momentum)
     and OBV (volume flow) — on CLOSED candles only. The forming candle is
     never measured.
  2. A divergence = two pivots 5-60 candles apart where price and the
     indicator disagree (regular: price lower-low + indicator higher-low and
     vice versa; hidden: price higher-low + indicator lower-low and vice
     versa).
  3. Per the scanner's own spec, "confirmation" is RSI+OBV AGREEMENT: both
     indicators diverging the same direction over the same two swings
     (indicator == "RSI+OBV" in this module). The opposite ("conf!") means
     the indicators disagree with each other and is not a take.

The video presenter's hand-drawn trendline break ("price breaks the local
trendline after the divergence") is a SEPARATE discretionary overlay kept
as trendline_confirmation() for reference only — it is NOT the scanner's
rule, and our 2026-10-01 backtest showed it REDUCED returns everywhere
(5m bull +0.158% -> +0.031% at 2h; 10m went negative). Do not use it.

INTERPRETATION CHOICES (the tool page was partially legible; these are
documented so the reconstruction can be audited):
  * Pivot: bar i is a pivot high(low) for lookback N when high[i] (low[i])
    is the strict extreme of the N-candle window ending at i. Ties do not
    count as pivots — this avoids flat-data pivot spam.
  * RSI scanner: RSI at periods 8, 13, AND 21 (the scanner's stated
    periods; default rsi_periods=(8,13,21), still overridable — legacy
    (14,) supported). Each period is scanned across all six lookbacks
    {8,13,21,55,89,144}; the RSI value is read at the price-pivot bars
    (standard divergence definition). Same pivot pair found by several
    periods = ONE divergence; the kept strength is the strongest across
    finding periods and rsi_periods_found records which periods found it.
  * OBV scanner: the tool's own rule uses pivot widths 2-13, so price pivots
    for OBV divergences use lookbacks 2..13. OBV disagreement must be
    "strong": |dOBV| / OBV-range-over-scanner-window >= 0.45, where the
    scanner window spans (i1 - lookback)..i2.
  * Strength labels follow the tool: STRONG = RSI at the second pivot under
    32 (bullish) or over 68 (bearish); SUPERSTRONG = under 27 / over 73.
    OBV-only divergences carry their numeric obv_strength and are labeled
    STRONG when it is >= 0.60, else NORMAL.
  * RSI+OBV agreement: an RSI divergence and an OBV divergence of the same
    direction whose pivot pairs overlap within 3 bars merge into one
    "RSI+OBV" divergence. Opposite-direction overlap sets conflict=True
    (the tool's "conf!" flag).
  * "Listed for 5 candles": a divergence is knowable once the second
    pivot's candle closes (knowable_index = i2); listed = True while the
    last input bar is within 4 bars after knowable_index.
  * Exhaustion (scan_exhaustion, separate signal type): BLOWOFF = RSI and
    OBV both in the top decile of their trailing 144-bar range on the same
    bar (down lean); CAPITULATION = both in the bottom decile (up lean).
    This is the scanner page's own frozen-backtest edge (daily bars,
    ~25y x 20 assets, in-sample: blowoff 2.1x down lean n=893,
    capitulation 3.0x up lean n=875) — distinct from swing divergence.
  * The scanner's confirmation is RSI+OBV agreement (indicator ==
    "RSI+OBV"). The video presenter's trendline-break version is kept as
    trendline_confirmation() for reference only — it is NOT the scanner's
    rule and tested negative in our 2026-10-01 backtest.

NOT wired into any trading path. Research and backtesting only.
Stdlib + math only.
"""

import math

RSI_LOOKBACKS = (8, 13, 21, 55, 89, 144)
OBV_LOOKBACKS = tuple(range(2, 14))
MIN_WIDTH = 5
MAX_WIDTH = 60
LISTING_WINDOW = 5
CONFIRM_WAIT = 5
AGREE_TOL = 3

DIV_TYPES = ("BuR", "BeR", "BuH", "BeH")  # bullish/bearish regular/hidden


# ---------------------------------------------------------------- indicators

def wilder_rsi(closes, period=14):
    """Wilder RSI. Returns list aligned with closes; None for the first
    `period` bars (warmup). Flat data -> 50.0 (no momentum either way)."""
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        ch = closes[i] - closes[i - 1]
        gains[i] = ch if ch > 0 else 0.0
        losses[i] = -ch if ch < 0 else 0.0
    avg_g = sum(gains[1:period + 1]) / period
    avg_l = sum(losses[1:period + 1]) / period
    for i in range(period, n):
        if i > period:
            avg_g = (avg_g * (period - 1) + gains[i]) / period
            avg_l = (avg_l * (period - 1) + losses[i]) / period
        if avg_l == 0.0:
            out[i] = 100.0 if avg_g > 0.0 else 50.0
        else:
            rs = avg_g / avg_l
            out[i] = 100.0 - 100.0 / (1.0 + rs)
    return out


def obv_series(bars):
    """On-Balance Volume from OHLCV bars. obv[0] = 0."""
    out = [0.0] * len(bars)
    run = 0.0
    for i in range(1, len(bars)):
        c, pc = bars[i]["c"], bars[i - 1]["c"]
        v = bars[i].get("v") or 0.0
        if c > pc:
            run += v
        elif c < pc:
            run -= v
        out[i] = run
    return out


# ---------------------------------------------------------------- pivots

def pivot_indices(values, lookback):
    """Return (highs, lows): bar indices where values[i] is the STRICT
    extreme of the `lookback`-candle window ending at i. Strict (ties do
    not count) so flat stretches produce no pivots."""
    highs, lows = [], []
    n = len(values)
    for i in range(lookback - 1, n):
        w = values[i - lookback + 1:i + 1]
        v = values[i]
        if v is None:
            continue
        prev = w[:-1]  # the lookback-1 bars before i
        if all(x is None or v > x for x in prev):
            highs.append(i)
        if all(x is None or v < x for x in prev):
            lows.append(i)
    return highs, lows


# ---------------------------------------------------------------- detection

def _classify_pair(p1, p2, v1, v2, is_high):
    """Classify a pivot pair. p1/p2 = price extremes, v1/v2 = indicator
    values at the same bars. Returns div type or None. Strict inequalities
    only — equality is not disagreement."""
    if is_high:
        if p2 > p1 and v2 < v1:
            return "BeR"   # price higher high, indicator lower high
        if p2 < p1 and v2 > v1:
            return "BeH"   # price lower high, indicator higher high
    else:
        if p2 < p1 and v2 > v1:
            return "BuR"   # price lower low, indicator higher low
        if p2 > p1 and v2 < v1:
            return "BuH"   # price higher low, indicator lower low
    return None


def find_divergences(price_high, price_low, ind, lookbacks,
                     min_width=MIN_WIDTH, max_width=MAX_WIDTH,
                     ind_kind="RSI", obv_min_strength=0.45):
    """Core detector. price_high/price_low/ind are aligned lists.
    Returns raw divergence dicts (no agreement merging, no strength yet)."""
    raw = []
    n = len(price_high)
    for lb in lookbacks:
        ph, pl = pivot_indices(price_high, lb), pivot_indices(price_low, lb)
        for is_high, pivs, pvals in ((True, ph[0], price_high),
                                     (False, pl[1], price_low)):
            for j in range(1, len(pivs)):
                i2 = pivs[j]
                # earlier pivots within the width window
                for k in range(j - 1, -1, -1):
                    i1 = pivs[k]
                    w = i2 - i1
                    if w > max_width:
                        break
                    if w < min_width:
                        continue
                    v1, v2 = ind[i1], ind[i2]
                    if v1 is None or v2 is None:
                        continue
                    dtype = _classify_pair(pvals[i1], pvals[i2], v1, v2,
                                           is_high)
                    if dtype is None:
                        continue
                    d = {
                        "type": dtype,
                        "direction": 1 if dtype.startswith("Bu") else -1,
                        "indicator": ind_kind,
                        "i1": i1, "i2": i2, "width": w,
                        "knowable_index": i2,
                        "price_p1": pvals[i1], "price_p2": pvals[i2],
                        "ind_p1": v1, "ind_p2": v2,
                        "lookback": lb,
                    }
                    if ind_kind == "OBV":
                        lo = max(0, i1 - lb)
                        win = [x for x in ind[lo:i2 + 1] if x is not None]
                        rng = (max(win) - min(win)) if win else 0.0
                        strength = abs(v2 - v1) / rng if rng > 0 else 0.0
                        d["obv_strength"] = strength
                        if strength < obv_min_strength:
                            continue  # tool's own rule: weak OBV ignored
                    raw.append(d)
    return raw


def _dedupe(divs):
    """Same (type, indicator, i1, i2) from several lookbacks/periods = ONE.
    Accumulates rsi_periods_found across the merged copies and keeps the
    strongest strength label (NORMAL < STRONG < SUPERSTRONG)."""
    order = {"NORMAL": 0, "STRONG": 1, "SUPERSTRONG": 2}
    seen, out = {}, []
    for d in divs:
        key = (d["type"], d["indicator"], d["i1"], d["i2"])
        if key in seen:
            prev = out[seen[key]]
            for p in d.get("rsi_periods_found", []):
                if p not in prev.setdefault("rsi_periods_found", []):
                    prev["rsi_periods_found"].append(p)
            ds = d.get("strength", "NORMAL")
            ps = prev.get("strength", "NORMAL")
            if order[ds] > order[ps]:
                prev["strength"] = ds
            continue
        seen[key] = len(out)
        d = dict(d)
        d["rsi_periods_found"] = list(d.get("rsi_periods_found", []))
        out.append(d)
    return out


def _rsi_strength(dtype, rsi_at_p2):
    bull = dtype.startswith("Bu")
    if rsi_at_p2 is None:
        return "NORMAL"
    if bull:
        if rsi_at_p2 < 27:
            return "SUPERSTRONG"
        if rsi_at_p2 < 32:
            return "STRONG"
    else:
        if rsi_at_p2 > 73:
            return "SUPERSTRONG"
        if rsi_at_p2 > 68:
            return "STRONG"
    return "NORMAL"


def scan_divergences(bars, rsi_periods=(8, 13, 21), rsi_lookbacks=RSI_LOOKBACKS,
                     obv_lookbacks=OBV_LOOKBACKS, min_width=MIN_WIDTH,
                     max_width=MAX_WIDTH, obv_min_strength=0.45,
                     listing_window=LISTING_WINDOW):
    """Scan CLOSED bars for RSI/OBV divergences.

    bars: list of dicts with o,h,l,c,v (t optional). ALL bars must be
    closed candles — the caller strips the forming bar; this function
    never peeks past the bars it is given.
    rsi_periods: RSI periods to scan (default (8,13,21) = the scanner's
    stated config; (14,) reproduces the legacy single-period run).
    Returns divergences sorted by knowable_index, each a dict with:
      type, direction (+1/-1), indicator (RSI/OBV/RSI+OBV),
      strength (NORMAL/STRONG/SUPERSTRONG — strongest across the finding
      RSI periods), rsi_period (first finding period), rsi_periods_found
      (all finding periods), i1, i2, width, knowable_index,
      listed (within the 5-candle listing window),
      obv_strength, conflict ("conf!" flag bool),
      price_p1/price_p2, ind_p1/ind_p2.

    The scanner's "confirmation" = indicator == "RSI+OBV" (both
    indicators diverging the same direction over the same swings).
    """
    n = len(bars)
    if n == 0:
        return []
    highs = [b["h"] for b in bars]
    lows = [b["l"] for b in bars]
    closes = [b["c"] for b in bars]
    obv = obv_series(bars)

    all_divs = []
    for per in rsi_periods:
        rsi = wilder_rsi(closes, per)
        for d in find_divergences(highs, lows, rsi, rsi_lookbacks,
                                 min_width, max_width, ind_kind="RSI"):
            d["rsi_period"] = per
            d["rsi_periods_found"] = [per]
            d["strength"] = _rsi_strength(d["type"], rsi[d["i2"]])
            d["obv_strength"] = None
            all_divs.append(d)
    for d in find_divergences(highs, lows, obv, obv_lookbacks,
                             min_width, max_width, ind_kind="OBV",
                             obv_min_strength=obv_min_strength):
        d["rsi_period"] = None
        d["rsi_periods_found"] = []
        d["strength"] = ("STRONG" if d["obv_strength"] >= 0.60 else "NORMAL")
        all_divs.append(d)

    divs = _dedupe(all_divs)
    rsi_divs = [d for d in divs if d["indicator"] == "RSI"]
    obv_divs = [d for d in divs if d["indicator"] == "OBV"]
    merged = _merge_agreement(rsi_divs, obv_divs)

    last = n - 1
    for d in merged:
        d.setdefault("conflict", False)
        d["listed"] = (last - d["knowable_index"]) < listing_window
    merged.sort(key=lambda d: (d["knowable_index"], d["i1"]))
    return merged


def _merge_agreement(rsi_divs, obv_divs, tol=AGREE_TOL):
    """Merge RSI and OBV divergences over the same swings.

    Same direction + pivot pairs overlapping within `tol` bars ->
    one "RSI+OBV" divergence (keeps the stronger strength label).
    Opposite direction overlap -> both flagged conflict=True
    (the tool's "conf!" flag). Unmatched divergences pass through.
    """
    merged, used_obv = [], set()
    for rd in rsi_divs:
        match = None
        for j, od in enumerate(obv_divs):
            if j in used_obv:
                continue
            if (abs(rd["i1"] - od["i1"]) <= tol and
                    abs(rd["i2"] - od["i2"]) <= tol):
                match = (j, od)
                break
        if match is None:
            merged.append(rd)
            continue
        j, od = match
        used_obv.add(j)
        if rd["direction"] == od["direction"]:
            m = dict(rd)
            m["indicator"] = "RSI+OBV"
            m["obv_strength"] = od["obv_strength"]
            order = {"NORMAL": 0, "STRONG": 1, "SUPERSTRONG": 2}
            if order[od["strength"]] > order[rd["strength"]]:
                m["strength"] = od["strength"]
            m["conflict"] = False
            merged.append(m)
        else:
            rd["conflict"] = True
            od["conflict"] = True
            merged.append(rd)
            merged.append(od)
    for j, od in enumerate(obv_divs):
        if j not in used_obv:
            merged.append(od)
    return merged


# ---------------------------------------------------------------- exhaustion

EXHAUST_RANGE = 144


def scan_exhaustion(bars, rsi_period=14, range_lookback=EXHAUST_RANGE):
    """BLOWOFF / CAPITULATION exhaustion detector — a SEPARATE signal type
    from swing divergence, from the scanner page's own frozen backtest
    (the only rules it marked as edges: daily bars, ~25y x 20 assets,
    in-sample).

    On each closed bar i with `range_lookback` bars of RSI history:
      BLOWOFF      = RSI and OBV both in the TOP decile of their trailing
                     range_lookback-bar range  -> direction -1 (down lean)
      CAPITULATION = both in the BOTTOM decile  -> direction +1 (up lean)
    "Top decile" = value >= min + 0.9 * (max - min) over the window;
    flat windows (zero range) never signal. Emits the first bar of each
    contiguous run (rising edge) with run_length. Returns list of dicts:
    type, direction, index, rsi, obv, run_length.
    """
    n = len(bars)
    closes = [b["c"] for b in bars]
    rsi = wilder_rsi(closes, rsi_period)
    obv = obv_series(bars)
    hits = []
    for i in range(n):
        lo = i - range_lookback + 1
        if lo < 0:
            continue
        rw = rsi[lo:i + 1]
        ow = obv[lo:i + 1]
        if any(x is None for x in rw):
            continue
        rmn, rmx = min(rw), max(rw)
        omn, omx = min(ow), max(ow)
        if rmx == rmn or omx == omn:
            continue  # flat window: no exhaustion read
        r_hi = rsi[i] >= rmn + 0.9 * (rmx - rmn)
        r_lo = rsi[i] <= rmn + 0.1 * (rmx - rmn)
        o_hi = obv[i] >= omn + 0.9 * (omx - omn)
        o_lo = obv[i] <= omn + 0.1 * (omx - omn)
        if r_hi and o_hi:
            hits.append({"type": "BLOWOFF", "direction": -1, "index": i,
                         "rsi": rsi[i], "obv": obv[i]})
        elif r_lo and o_lo:
            hits.append({"type": "CAPITULATION", "direction": 1, "index": i,
                         "rsi": rsi[i], "obv": obv[i]})
    # rising edge: first bar of each contiguous same-type run
    edge = []
    for s in hits:
        if edge and s["index"] == edge[-1]["_last"] + 1 \
                and s["type"] == edge[-1]["type"]:
            edge[-1]["_last"] = s["index"]
        else:
            edge.append(dict(s, _last=s["index"]))
    for e in edge:
        e["run_length"] = e.pop("_last") - e["index"] + 1
    return edge


# ---------------------------------------------------------------- confirmation
# NOTE: the scanner's real confirmation is RSI+OBV agreement
# (indicator == "RSI+OBV"). What follows is the video presenter's
# discretionary overlay — NOT the scanner's rule. Our 2026-10-01 backtest
# showed it REDUCED returns everywhere; kept for reference only.

def trendline_confirmation(bars, div, max_wait=CONFIRM_WAIT, pivot_lb=8):
    """DISCRETIONARY OVERLAY ONLY — NOT the scanner's confirmation rule.

    Bullish: trendline through the two most recent pivot highs (lookback
    `pivot_lb`) at/before i2; confirmation = a close above the line within
    `max_wait` bars after knowable_index. Bearish mirrors with pivot lows.
    Returns the confirming bar index, or None.
    """
    n = len(bars)
    i2 = div["i2"]
    ki = div["knowable_index"]
    bull = div["direction"] == 1
    vals = ([b["h"] for b in bars] if bull else [b["l"] for b in bars])
    highs, lows = pivot_indices(vals, pivot_lb)
    pivs = [p for p in (highs if bull else lows) if p <= i2]
    if len(pivs) < 2:
        return None
    a, b = pivs[-2], pivs[-1]
    if b == a:
        return None
    va, vb = vals[a], vals[b]
    for k in range(1, max_wait + 1):
        idx = ki + k
        if idx >= n:
            break
        line = va + (vb - va) * (idx - a) / (b - a)
        c = bars[idx]["c"]
        if (bull and c > line) or (not bull and c < line):
            return idx
    return None
