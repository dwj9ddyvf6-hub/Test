"""SATY PORT — the five indicators, clean-room (SPEC §5, §7, §9).

Built from ~/workspace/opt/rea-teardowns/saty-stack/SPEC.md as
corrected by VERIFICATION.md (2026-10-21), against the five
verbatim originals in that folder's source/. This module
re-implements the originals' computation in our own structure;
it is NOT a transliteration, and no claim here rests on this
file alone — tests/test_saty_port_20261021.py and
tests/test_saty_traps_20261021.py validate it against
expectations derived independently from the Pine sources.

Pure computation on bar frames (bar contract: core/saty_bars).
No I/O, no fetching, no strategy, no signals-to-orders, nothing
on any trade path. Alpaca SIP is the only lawful data source
for consumers of this module (SPEC §2); the module itself is
source-agnostic because it never fetches.

BAR-CLOSE SEMANTICS (SPEC §1): inputs are closed bars; every
state advances on closed bars only.

THE ONE DELIBERATE DIVERGENCE (SPEC §6): Time Warp. The
oscillator original fetches every series with lookahead_on and
no offset, so its warped plot carries the forming HTF bar live
and completed-HTF values early on historical bars — a genuine
future leak. The port implements warp in the completed-bar
form for ALL components: at any signal bar, warped values are
those of the last completed warped bar (the ribbons already
behave this way live via their [isrealtime ? 1 : 0] offset).
A bar-by-bar diff against the original's warped display
therefore agrees at HTF closes and differs inside HTF bars,
by design. Validation compares warped values only at HTF
closes (SPEC §8.3).

SESSION BASIS (SPEC §3): explicit per component, stamped on
every row, never silently inherited: ATR Levels and the free
Ribbon default to "extended" (their originals force it), the
Pro and the Oscillator default to "regular" (their originals
respect the chart session since the Jan 2026 fix). A component
consumes bars of ONE basis: pass `consuming_bars` for the
component's consuming timeframe on its basis (the warp target
when warping); when omitted, the signal bars themselves are
consumed. Candle-bias always reads the SIGNAL bars' own OHLC
(the originals judge the chart candle), against warped EMAs.

WARMUP (SPEC §2.3): ribbon/oscillator components trust output
after 250 consumed-timeframe bars; ATR Levels after 100 daily
bars. Rows carry warmed_up; events are suppressed until the
owning component is warmed.
"""
from core import saty_bars as sb
from core import saty_primitives as sp

WARMUP_BARS = 250          # ribbon / oscillator / pro (SPEC §2.3)
WARMUP_DAILY_BARS = 100    # ATR Levels (SPEC §2.3)

_LADDER_FIXED = (0.382, 0.5, 0.618, 0.786, 1.0, 1.236, 1.382,
                 1.5, 1.618, 1.786, 2.0, 2.236, 2.382, 2.5,
                 2.618, 2.786, 3.0)


def _closes(bars):
    return [b["close"] for b in bars]


def _consumed_counts(consuming, signal):
    """Per signal bar, how many consuming bars have completed
    (the completed-bar warp map as counts)."""
    idx = sb.completed_map(consuming, signal)
    return [(j + 1) if j is not None else 0 for j in idx]


def _align(consuming, values, signal):
    if consuming is signal:
        return list(values)
    return sb.align_values(consuming, values, signal)


def _event(etype, component, bars, i, detail):
    return {"type": etype, "component": component,
            "bar_index": i,
            "bar_close_time_et": sb.close_time(bars[i]).isoformat(),
            "detail": detail}


def _diff_events(states, bars, component, on_type, off_type,
                 warmed, detail=None):
    """Events derived by diffing consecutive states (SPEC §7.1:
    the events are the port's bookkeeping, not indicator state).
    The first computable state emits nothing (initialization is
    not a transition — trap T8); transitions during warmup are
    tracked but suppressed (SPEC §2.3)."""
    events = []
    prev = None
    for i, s in enumerate(states):
        if s is None:
            continue
        if prev is not None and s != prev and warmed[i]:
            events.append(_event(on_type if s else off_type,
                                 component, bars, i,
                                 detail or {}))
        prev = s
    return events


# ----------------------------------------------------------------
# 5.5 Saty Volume Stack — stateless per bar (SPEC §7.7)
# ----------------------------------------------------------------

def volume_stack(bars, average_length=10, show_average=True):
    """Close-location volume split. This is a PROXY (the
    author's own caveat): buy_volume_proxy is not tape delta.
    Zero-range bar (high == low): buy/sell/pct are NaN, exactly
    as the original's unguarded division yields na — and the
    winner stays "BUY", because in the original the buyers
    default survives (na < na is not true). Ties on a real bar
    go to buyers: the original flips only when buy < sell."""
    nan = float("nan")
    volumes = [b.get("volume") or 0.0 for b in bars]
    sma = sp.sma_series(volumes, average_length)
    rows = []
    for i, b in enumerate(bars):
        h, l, c = b["high"], b["low"], b["close"]
        v = volumes[i]
        rng = h - l
        if rng == 0:
            buy = sell = buy_pct = sell_pct = nan
            winner = "BUY"
        else:
            buy = v * (c - l) / rng
            sell = v * (h - c) / rng
            buy_pct = (buy / v * 100.0) if v else nan
            sell_pct = (sell / v * 100.0) if v else nan
            winner = "SELL" if buy < sell else "BUY"
        rows.append({
            "buy_volume_proxy": buy,
            "sell_volume_proxy": sell,
            "buy_pct": buy_pct,
            "sell_pct": sell_pct,
            "winner": winner,
            "volume_sma": sma[i],
            "warmed_up": (i + 1 >= average_length)
                         if show_average else True,
        })
    return {"rows": rows, "events": []}


# ----------------------------------------------------------------
# 5.1 Saty ATR Levels (SPEC §5.1, §7.6)
# ----------------------------------------------------------------

def atr_levels(daily_bars, signal_bars, mode="Day", atr_length=14,
               trigger_fraction=0.236, session_basis="extended"):
    """Frozen per-period ladder: anchor = previous completed
    period's close, unit = that period's ATR(atr_length), both
    frozen at period open (LEVELS_SET). The range gauge and the
    8/21/34 trend header are live by design in the original and
    here: the gauge accumulates the current period's high/low
    from the signal bars supplied (supply bars of this
    component's basis if you want the original's extended-basis
    gauge), the trend reads signal-bar closes. The current-close
    repaint mode of the original is NOT implemented (SPEC §10).
    """
    if mode not in sb.MODE_TO_PERIOD:
        raise ValueError(f"unknown ATR Levels mode: {mode!r}")
    period_tf = sb.MODE_TO_PERIOD[mode]
    periods = sb.aggregate_periods(daily_bars, period_tf)
    period_atr = sp.atr_series(periods, atr_length)
    p_index = {p["period"]: k for k, p in enumerate(periods)}
    fractions = sorted({trigger_fraction} | set(_LADDER_FIXED))

    daily_dates = [b["t"].date() for b in daily_bars]
    s_closes = _closes(signal_bars)
    e8 = sp.ema_series(s_closes, 8)
    e21 = sp.ema_series(s_closes, 21)
    e34 = sp.ema_series(s_closes, 34)

    rows, events = [], []
    run_hi = run_lo = None
    cur_period = None
    seen_periods_with_set = set()
    for i, bar in enumerate(signal_bars):
        key = sb.period_key(bar["t"].date(), period_tf)
        if key != cur_period:
            cur_period = key
            run_hi, run_lo = bar["high"], bar["low"]
        else:
            run_hi = max(run_hi, bar["high"])
            run_lo = min(run_lo, bar["low"])
        k = p_index.get(key)
        anchor = unit = None
        if k is not None and k >= 1:
            anchor = periods[k - 1]["close"]
            unit = period_atr[k - 1]
            if unit is None:
                anchor = None
        levels = range_pct = range_band = None
        if anchor is not None:
            levels = {}
            for f in fractions:
                levels[f"+{f:.3f}"] = anchor + f * unit
                levels[f"-{f:.3f}"] = anchor - f * unit
            range_pct = (run_hi - run_lo) / unit * 100.0
            range_band = ("LOW" if range_pct <= 70 else
                          "HIGH" if range_pct >= 90 else "MID")
        daily_seen = sum(1 for d in daily_dates
                         if d <= bar["t"].date())
        warmed = daily_seen >= WARMUP_DAILY_BARS
        if (anchor is not None and warmed
                and key not in seen_periods_with_set):
            seen_periods_with_set.add(key)
            events.append(_event(
                "LEVELS_SET", "atr_levels", signal_bars, i,
                {"period": key, "anchor": anchor, "unit": unit}))
        c = bar["close"]
        if c >= e8[i] >= e21[i] >= e34[i]:
            trend = "BULLISH"
        elif c <= e8[i] <= e21[i] <= e34[i]:
            trend = "BEARISH"
        else:
            trend = "MIXED"
        rows.append({
            "anchor": anchor, "unit": unit, "levels": levels,
            "range_pct": range_pct, "range_band": range_band,
            "trend": trend, "period": key,
            "session_basis": session_basis, "warmed_up": warmed,
        })
    return {"rows": rows, "events": events}


# ----------------------------------------------------------------
# Shared ribbon machinery (SPEC §5.2, §5.3, §7.2)
# ----------------------------------------------------------------

def _conviction(cons_closes, signal, consuming, fast_len, slow_len,
                warmed):
    cf = sp.ema_series(cons_closes, fast_len)
    cs = sp.ema_series(cons_closes, slow_len)
    a_cf = _align(consuming, cf, signal)
    a_cs = _align(consuming, cs, signal)
    states = [(f >= s) if (f is not None and s is not None)
              else None for f, s in zip(a_cf, a_cs)]
    return a_cf, a_cs, states


def _bias_state(bar, bias_value, strong, pullback, bounce, weak):
    """The §7.3/§7.4 five-way candle map vs a bias EMA value."""
    if bias_value is None:
        return None
    above = bar["close"] >= bias_value
    up = bar["close"] > bar["open"]
    down = bar["close"] < bar["open"]
    if above and up:
        return strong
    if not above and up:
        return bounce
    if above and down:
        return pullback
    if not above and down:
        return weak
    return "NEUTRAL"  # doji


# ----------------------------------------------------------------
# 5.2 Saty Pivot Ribbon (free) (SPEC §5.2, §7.2, §7.3)
# ----------------------------------------------------------------

def pivot_ribbon(bars, consuming_bars=None, fast_length=8,
                 pivot_length=21, slow_length=34,
                 conv_fast_length=13, conv_slow_length=48,
                 bias_length=21, session_basis="extended"):
    """3-EMA ribbon (8/21/34) + 13/48 conviction + candle bias
    vs the (warped) bias EMA. Session basis default "extended":
    the original forces extended-session closes (SPEC §3)."""
    consuming = consuming_bars if consuming_bars is not None else bars
    c_closes = _closes(consuming)
    counts = _consumed_counts(consuming, bars)
    warmed = [n >= WARMUP_BARS for n in counts]
    a_e8 = _align(consuming, sp.ema_series(c_closes, fast_length), bars)
    a_e21 = _align(consuming, sp.ema_series(c_closes, pivot_length), bars)
    a_e34 = _align(consuming, sp.ema_series(c_closes, slow_length), bars)
    a_bias = _align(consuming, sp.ema_series(c_closes, bias_length), bars)
    a_cf, a_cs, conv_states = _conviction(
        c_closes, bars, consuming, conv_fast_length,
        conv_slow_length, warmed)
    events = _diff_events(conv_states, bars, "ribbon",
                          "CONVICTION_BULL", "CONVICTION_BEAR",
                          warmed)
    rows = []
    for i, bar in enumerate(bars):
        rows.append({
            "ema8": a_e8[i], "ema21": a_e21[i], "ema34": a_e34[i],
            "conv13": a_cf[i], "conv48": a_cs[i],
            "ema_bias": a_bias[i],
            "fast_cloud": (a_e8[i] >= a_e21[i]) if (
                a_e8[i] is not None and a_e21[i] is not None)
                else None,
            "slow_cloud": (a_e21[i] >= a_e34[i]) if (
                a_e21[i] is not None and a_e34[i] is not None)
                else None,
            "conviction_state": conv_states[i],
            "bias_state": _bias_state(
                bar, a_bias[i], "BULL_STRONG", "BULL_PULLBACK",
                "BEAR_BOUNCE", "BEAR_STRONG"),
            "session_basis": session_basis,
            "warmed_up": warmed[i],
        })
    return {"rows": rows, "events": events}


# ----------------------------------------------------------------
# 5.3 Saty Pivot Ribbon Pro (SPEC §5.3, §7.2, §7.4)
# ----------------------------------------------------------------

def pivot_ribbon_pro(bars, consuming_bars=None, fast_length=8,
                     overlap_length=13, pivot_length=21,
                     pivot_bias_length=8, slow_length=48,
                     lt_length=200, lt_bias_length=21,
                     bias_length=48, conv_fast_length=13,
                     conv_slow_length=48, pullback_overlap=True,
                     show_candle_bias=True,
                     show_compression_candles=True,
                     session_basis="regular"):
    """Five-EMA Pro ribbon. THERE IS NO 34 EMA (the manual's 34
    is a phantom from the free ribbon — VERIFICATION claim 4).
    Compression instance B is computed LOCALLY on the signal
    timeframe with the original's hardcoded 21/21/14 (Pro lines
    160-179) — never warped, never borrowed from the oscillator.
    Candle bias reads the warped EMA(bias_length) (SPEC §7.4);
    the compression override takes precedence; the two toggles
    are independent, as in the current original build."""
    consuming = consuming_bars if consuming_bars is not None else bars
    c_closes = _closes(consuming)
    counts = _consumed_counts(consuming, bars)
    sig_seen = [i + 1 for i in range(len(bars))]
    if consuming_bars is not None:
        warmed = [n >= WARMUP_BARS and s >= WARMUP_BARS
                  for n, s in zip(counts, sig_seen)]
    else:
        warmed = [n >= WARMUP_BARS for n in counts]
    a_e8 = _align(consuming, sp.ema_series(c_closes, fast_length), bars)
    a_e13 = _align(consuming, sp.ema_series(c_closes, overlap_length), bars)
    a_e21 = _align(consuming, sp.ema_series(c_closes, pivot_length), bars)
    a_e48 = _align(consuming, sp.ema_series(c_closes, slow_length), bars)
    a_e200 = _align(consuming, sp.ema_series(c_closes, lt_length), bars)
    a_pbias = _align(consuming,
                     sp.ema_series(c_closes, pivot_bias_length), bars)
    a_ltbias = _align(consuming,
                      sp.ema_series(c_closes, lt_bias_length), bars)
    a_bias = _align(consuming, sp.ema_series(c_closes, bias_length), bars)
    a_cf, a_cs, conv_states = _conviction(
        c_closes, bars, consuming, conv_fast_length,
        conv_slow_length, warmed)
    events = _diff_events(conv_states, bars, "ribbon_pro",
                          "CONVICTION_BULL", "CONVICTION_BEAR",
                          warmed)
    # Compression instance B — signal timeframe, hardcoded
    # 21/21/14 as the original computes it locally (SPEC §7.1B).
    s_closes = _closes(bars)
    comp_pivot = sp.ema_series(s_closes, 21)
    comp_sd = sp.stdev_series(s_closes, 21)
    comp_atr = sp.atr_series(bars, 14)
    comp_states = []
    comp_prev = None
    for i, bar in enumerate(bars):
        state, comp = sp.compression_rule(
            bar["close"], comp_pivot[i], comp_sd[i], comp_atr[i],
            comp_prev)
        comp_states.append(state)
        comp_prev = comp
    events += _diff_events(comp_states, bars, "ribbon_pro",
                           "COMPRESSION_ON", "COMPRESSION_OFF",
                           warmed, {"instance": "B"})
    rows = []
    for i, bar in enumerate(bars):
        if pullback_overlap:
            slow_cloud = (a_e13[i] >= a_e48[i]) if (
                a_e13[i] is not None and a_e48[i] is not None) else None
        else:
            slow_cloud = (a_e21[i] >= a_e48[i]) if (
                a_e21[i] is not None and a_e48[i] is not None) else None
        # Candle state (SPEC §7.4): compression override first.
        candle = None
        up = bar["close"] > bar["open"]
        down = bar["close"] < bar["open"]
        if show_compression_candles and comp_states[i]:
            if up:
                candle = "COMPRESSED_UP"
            elif down:
                candle = "COMPRESSED_DOWN"
        if candle is None:
            if show_candle_bias:
                candle = _bias_state(
                    bar, a_bias[i], "BULL_STRONG", "BULL_PULLBACK",
                    "BEAR_BOUNCE", "BEAR_STRONG")
            else:
                candle = ("UP" if up else "DOWN" if down
                          else "NEUTRAL")
        rows.append({
            "ema8": a_e8[i], "ema13": a_e13[i], "ema21": a_e21[i],
            "ema48": a_e48[i], "ema200": a_e200[i],
            "ema_bias": a_bias[i],
            "conv13": a_cf[i], "conv48": a_cs[i],
            "fast_cloud": (a_e8[i] >= a_e21[i]) if (
                a_e8[i] is not None and a_e21[i] is not None)
                else None,
            "slow_cloud": slow_cloud,
            "pivot_line_bias": (a_pbias[i] >= a_e21[i]) if (
                a_pbias[i] is not None and a_e21[i] is not None)
                else None,
            "lt_line_bias": (a_ltbias[i] >= a_e200[i]) if (
                a_ltbias[i] is not None and a_e200[i] is not None)
                else None,
            "conviction_state": conv_states[i],
            "compression_b": comp_states[i],
            "candle_state": candle,
            "session_basis": session_basis,
            "warmed_up": warmed[i],
        })
    return {"rows": rows, "events": events}


# ----------------------------------------------------------------
# 5.4 Saty Phase Oscillator (SPEC §5.4, §7.1A, §7.5)
# ----------------------------------------------------------------

_ZONE_GRID = (100.0, 61.8, 23.6, 0.0, -23.6, -61.8, -100.0)


def _zone_of(v):
    """Zone band of an oscillator value on the original's grid
    (constants, not parameters). Our classification labels; the
    original plots the grid lines only."""
    if v is None:
        return None
    if v >= 100.0:
        return "EXTENDED_UP"
    if v >= 61.8:
        return "DISTRIBUTION"
    if v >= 23.6:
        return "NEUTRAL_UP"
    if v > -23.6:
        return "NEUTRAL"
    if v > -61.8:
        return "NEUTRAL_DOWN"
    if v > -100.0:
        return "ACCUMULATION"
    return "EXTENDED_DOWN"


def phase_oscillator(bars, consuming_bars=None,
                     session_basis="regular",
                     compression_colors="Clean"):
    """Phase Oscillator on the consuming (warped) timeframe:
    pivot EMA21, ATR14, stdev21 (population); raw =
    (close - pivot) / (3 * atr) * 100; osc = EMA(raw, 3) —
    output field named phase_oscillator per SPEC §5.4.
    Compression instance A lives on the consuming timeframe
    (SPEC §7.1A). Warp uses the completed-bar rule (SPEC §6) —
    the deliberate divergence from the original's leaking
    lookahead_on warp, documented in the module header."""
    consuming = consuming_bars if consuming_bars is not None else bars
    c_closes = _closes(consuming)
    counts = _consumed_counts(consuming, bars)
    warmed = [n >= WARMUP_BARS for n in counts]
    pivot = sp.ema_series(c_closes, 21)
    atrs = sp.atr_series(consuming, 14)
    sds = sp.stdev_series(c_closes, 21)
    raw = []
    for i, c in enumerate(c_closes):
        if atrs[i] is None or atrs[i] == 0 or pivot[i] is None:
            raw.append(None)
        else:
            raw.append((c - pivot[i]) / (3.0 * atrs[i]) * 100.0)
    osc = sp.ema_series(raw, 3)
    comp_states = []
    comp_prev = None
    for i, c in enumerate(c_closes):
        state, comp = sp.compression_rule(
            c, pivot[i], sds[i], atrs[i], comp_prev)
        comp_states.append(state)
        comp_prev = comp
    # Leaving-zone events on the consuming series (SPEC §7.5),
    # attributed to the first signal bar that shows the new
    # completed value.
    cmap = sb.completed_map(consuming, bars)
    first_signal_for = {}
    for i, j in enumerate(cmap):
        if j is not None and j not in first_signal_for:
            first_signal_for[j] = i
    events = []
    crosses = (
        ("LEAVE_ACCUMULATION", -61.8, "up"),
        ("LEAVE_EXTREME_DOWN", -100.0, "up"),
        ("LEAVE_DISTRIBUTION", 61.8, "down"),
        ("LEAVE_EXTREME_UP", 100.0, "down"),
    )
    for j in range(1, len(osc)):
        prev_v, cur_v = osc[j - 1], osc[j]
        if prev_v is None or cur_v is None:
            continue
        for etype, level, direction in crosses:
            hit = ((direction == "up" and prev_v <= level < cur_v)
                   or (direction == "down"
                       and prev_v >= level > cur_v))
            if not hit:
                continue
            i = first_signal_for.get(j)
            if i is None or not warmed[i]:
                continue
            events.append(_event(etype, "oscillator", bars, i,
                                 {"level": level, "value": cur_v}))
    events += _diff_events(
        _align(consuming, comp_states, bars), bars, "oscillator",
        "COMPRESSION_ON", "COMPRESSION_OFF", warmed,
        {"instance": "A"})
    a_osc = _align(consuming, osc, bars)
    a_comp = _align(consuming, comp_states, bars)
    a_pivot = _align(consuming, pivot, bars)
    a_atr = _align(consuming, atrs, bars)
    a_sd = _align(consuming, sds, bars)
    rows = []
    for i in range(len(bars)):
        v = a_osc[i]
        if a_comp[i]:
            color = ("COMPRESSION_CLEAN"
                     if compression_colors == "Clean"
                     else "COMPRESSION_CLASSIC")
        elif v is None:
            color = None
        else:
            color = "POSITIVE" if v >= 0 else "NEGATIVE"
        rows.append({
            "phase_oscillator": v,
            "zone": _zone_of(v),
            "compression_a": a_comp[i],
            "color_state": color,
            "zero_line_compression": a_comp[i],
            "pivot": a_pivot[i], "atr": a_atr[i], "stdev": a_sd[i],
            "session_basis": session_basis,
            "warmed_up": warmed[i],
        })
    return {"rows": rows, "events": events}


# ----------------------------------------------------------------
# §9 run harness — one row per signal bar
# ----------------------------------------------------------------

def run_stack(symbol, timeframe, signal_bars, daily_bars=None,
              consuming_bars=None, warp="off",
              signal_basis="regular", config=None):
    """Compose all five components over one signal-bar series
    into SPEC §9 rows. `consuming_bars` (the warp target's bars,
    on each component's basis) is shared by the ribbon, Pro, and
    oscillator; ATR Levels consume `daily_bars`. No strategy,
    no orders — rows and events only."""
    cfg = config or {}
    ribbon = pivot_ribbon(signal_bars, consuming_bars,
                          **cfg.get("ribbon", {}))
    pro = pivot_ribbon_pro(signal_bars, consuming_bars,
                           **cfg.get("ribbon_pro", {}))
    osc = phase_oscillator(signal_bars, consuming_bars,
                           **cfg.get("oscillator", {}))
    vol = volume_stack(signal_bars, **cfg.get("volume_stack", {}))
    atr = (atr_levels(daily_bars, signal_bars, **cfg.get("atr_levels", {}))
           if daily_bars is not None else None)
    by_bar = {}
    for comp in (ribbon, pro, osc, vol) + ((atr,) if atr else ()):
        for ev in comp["events"]:
            by_bar.setdefault(ev["bar_index"], []).append({
                "type": ev["type"], "component": ev["component"],
                "bar_close_time_et": ev["bar_close_time_et"],
                "detail": ev["detail"]})
    rows = []
    for i, bar in enumerate(signal_bars):
        rows.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "session_basis": signal_basis,
            "warp": warp,
            "bar_close_time_et": sb.close_time(bar).isoformat(),
            "atr_levels": atr["rows"][i] if atr else None,
            "ribbon": ribbon["rows"][i],
            "ribbon_pro": pro["rows"][i],
            "oscillator": osc["rows"][i],
            "volume_stack": vol["rows"][i],
            "events": by_bar.get(i, []),
            "warmed_up": all(
                r["warmed_up"] for r in
                (ribbon["rows"][i], pro["rows"][i], osc["rows"][i],
                 vol["rows"][i])
                + ((atr["rows"][i],) if atr else ())),
        })
    return rows
