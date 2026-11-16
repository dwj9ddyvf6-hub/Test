#!/usr/bin/env python3
"""Pass A — deterministic chart geometry. No model, no narration.

Fetches 10m/1H/1D/1W bars via the alpaca-paper skill CLIs and computes the
measurement objects Pass B narrates:
  pivots (confirmed) -> swings -> averages -> ATR distances ->
  level tests (ATR-cut, kind-aware) -> volume stats -> gaps ->
  momentum layer (thesis A.1 contracts) -> pattern primitives.

Indicator conventions (from the thesis, App. A.1):
  RSI14   : Wilder RMA, alpha=1/14, seed = SMA of first 14 price changes
            (TradingView RMA convention). Both-zero -> neutral 50 (declared).
  MACD    : 12/26/9, EMA12(C)-EMA26(C); signal=EMA9(line); hist=line-signal.
  StochRSI: 14/3/3 on the RSI series; K=SMA3(raw)*, D=SMA3(K); raw 0-100.
            Flat RSI window -> 50 (declared), not a silent library choice.
  CCI20   : TP=(H+L+C)/3; (TP-SMA20(TP))/(0.015*MD); MD = MEAN |dev| (not stdev).
  ADX14   : Wilder contract. +DM=UpMove iff UpMove>DownMove and >0 (mirror -DM);
            +DI=100*RMA(+DM)/RMA(TR); DX=100*|+DI-(-DI)|/(+DI+(-DI)); ADX=RMA(DX).
  OBV     : cumulative signed volume on close direction; flat closes add 0.
  VWAP    : regular-session 10m bars only, typical-price weighted.
  Close location: unit=(C-L)/R in [0,1]; signed=2*unit-1 in [-1,1].

Usage: python3 pass_a.py --symbol PLTR
Output: JSON on stdout.
"""
import argparse, json, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ALPACA = Path.home() / "workspace/skills/alpaca-paper"

_KRAKEN_BARS_PATH = (Path.home() / "workspace/alpaca-swing-desk/desk"
                     / "kraken_bars.py")
_kraken_bars = None
_kraken_bars_tried = False

# THE COURTROOM (Stage 5, 2026-10-17): the battery lives in ONE
# place — femto-lean's core/ta_battery.py, ported from this file.
# This skill is a CALLER: it fetches bars and renders the read;
# the numbers come from the shared battery, so the desk and the
# skill can never compute two truths.
import sys as _sys
from pathlib import Path as _Path
_REPO = _Path.home() / "workspace" / "femto-lean"
_sys.path.insert(0, str(_REPO))
from core.ta_battery import (  # noqa: E402,F401
    sma, ema, rma, sma_skip, wilder_atr, rsi_wilder, macd,
    stoch_rsi, cci, adx_dmi, obv, session_vwap, cmf, mfi,
    frame_stance, pivots, ema_stack, pivot_sequence)

def _load_kraken_bars():
    """Load the desk's Kraken bar source (fix-all 2026-10-13, F3).

    The Alpaca stock-bars route serves NO bars for crypto pairs, so
    crypto symbols route to Kraken public OHLC via
    desk/kraken_bars.py. Loaded by file path (the module is
    standalone); None when unavailable -- the caller then falls back
    to the stock-bars route and the NO_VIEW guard below reports the
    missing bars (fail-soft, never a crash).
    """
    global _kraken_bars, _kraken_bars_tried
    if _kraken_bars_tried:
        return _kraken_bars
    _kraken_bars_tried = True
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "desk_kraken_bars", _KRAKEN_BARS_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _kraken_bars = mod
    except Exception:
        _kraken_bars = None
    return _kraken_bars

def fetch(symbol, tf, limit):
    kb = _load_kraken_bars()
    if kb is not None and kb.is_kraken_symbol(symbol):
        # Crypto route (F3): Kraken OHLC in the same bar shape; []
        # on any Kraken failure -> the NO_VIEW guard in main().
        return kb.fetch_kraken_bars(symbol, tf, limit)
    p = subprocess.run(
        [sys.executable, str(ALPACA / "bin/alpaca_get_bars_1h.py"),
         "--symbol", symbol, "--timeframe", tf, "--limit", str(limit),
         # Split-adjusted explicitly (cure 2026-11-10, lane4): the CLI
         # defaults to --adjustment raw, which mixes pre-split history
         # at the old scale with post-split bars (SOXX 3-for-1,
         # effective 2026-11-05: raw Nov 4 close 450.41 -> Nov 5
         # 131.90, a phantom -70.7% gap that contaminated every
         # averaged block). "split" restates pre-split bars at the
         # post-split scale and is the basis tonight's SOXX
         # reconstruction and the desk structural screen use
         # (EMA20 158.19 / EMA50 168.31 / ATR14 8.19 to the cent);
         # "all" was tested and rejected: its dividend adjustment
         # moves EMA50 to 168.29 and would rewrite every
         # dividend-payer's history. For names with no split in the
         # window, split == raw, so their output is unchanged.
         "--adjustment", "split"],
        capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        raise RuntimeError(f"bars fetch failed {tf}: {p.stderr[:200]}")
    return json.loads(p.stdout)

# ---------- moving averages ----------





# ---------- ATR ----------


# ---------- momentum layer (thesis A.1) ----------








# ---------- structure ----------



def double_bottom(pivots, atr, tol_atr=0.50, min_sep=10):
    """Double-bottom candidate (thesis 2.8): two separated L pivots within
    tol_atr of each other, an intervening H pivot (the rebound), neckline =
    intervening high. The morphology is observable before any breakout; a
    close above the neckline is the declared completion rule, not assumed.
    """
    if not atr: return []
    out = []
    lows = [p for p in pivots if p["kind"] == "L"][-6:]
    for a, b in zip(lows[:-1], lows[1:]):
        if b["i"]-a["i"] < min_sep: continue
        if abs(b["px"]-a["px"]) > tol_atr*atr: continue
        between = [p for p in pivots if p["kind"] == "H" and a["i"] < p["i"] < b["i"]]
        if not between: continue
        neck = max(between, key=lambda p: p["px"])
        out.append({"lows": [round(a["px"], 2), round(b["px"], 2)],
                    "low_t": [a["t"][:10], b["t"][:10]],
                    "low_mismatch_atr": round(abs(b["px"]-a["px"])/atr, 2),
                    "neckline": round(neck["px"], 2),
                    "neckline_t": neck["t"][:10]})
    return out

def reset_candidate(bars, clusters, atr_series, atr, up_streak):
    """Reset-candidate sequence (thesis 2.4): a decline reaching a structural
    area, followed by compression and improving closes. Each component is
    measured; the sequence is a research candidate, not a signal. Do not
    label it 'accumulation'.
    """
    if not atr or len(bars) < 31 or len(atr_series) < 22: return None
    last = bars[-1]
    decline_atr = (max(b["h"] for b in bars[-30:])-last["c"])/atr
    at_support = None
    for z in clusters:
        lo, hi = z["zone"]
        d = 0.0 if lo <= last["c"] <= hi else min(abs(last["c"]-lo), abs(last["c"]-hi))/atr
        at_support = d if at_support is None else min(at_support, d)
    compressed = atr_series[-1]/atr_series[-21] < 0.9 if atr_series[-21] else False
    improving = up_streak >= 2
    return {"decline_atr": round(decline_atr, 2),
            "dist_to_support_atr": round(at_support, 2) if at_support is not None else None,
            "compressed": bool(compressed),
            "improving_closes": bool(improving),
            "candidate": bool(decline_atr >= 2.0 and (at_support or 99) <= 0.5
                              and compressed and improving)}

def data_status(n_bars, has_volume, provisional, ema200_ok, last_t):
    """Formal data-quality status (thesis 4.10 output contract).
    VERIFIED / PARTIAL / STALE / CONFLICT / NO_VIEW.
    """
    if n_bars < 20:
        return "NO_VIEW"
    try:
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        stale = last_t[:10] < today and (datetime.strptime(today, "%Y-%m-%d")
               - datetime.strptime(last_t[:10], "%Y-%m-%d")).days > 3
    except Exception:
        stale = False
    if stale:
        return "STALE"
    if not has_volume or provisional or not ema200_ok:
        return "PARTIAL"
    return "VERIFIED"


def bar_payload_hash(*bar_lists):
    """Provenance: sha256 over the raw bar payloads (thesis 4.10 versions block)."""
    import hashlib
    h = hashlib.sha256()
    for bars in bar_lists:
        for b in bars:
            h.update(f"{b['t']}{b['o']}{b['h']}{b['l']}{b['c']}{b.get('v')}".encode())
    return h.hexdigest()[:16]

PASS_A_VERSION = "2.4.0"

def last_bar_provisional(last_t):
    """Thesis 2.8: label open-bar observations provisional, separate from
    completed-bar signals. True when the last bar is today's and it's
    before 16:05 ET.
    """
    try:
        from zoneinfo import ZoneInfo
        now_et = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        return None
    if last_t[:10] != now_et.strftime("%Y-%m-%d"): return False
    return now_et.strftime("%H:%M") < "16:05"

def level_clusters(pivots, bars, atr, tol_atr=0.25, min_gap=5):
    """Cluster confirmed pivot prices with ATR-scaled distance (thesis 2.5).

    Each zone is an interval with constituents, bar touches, and INDEPENDENT
    episodes (visits separated by >= min_gap bars away). Ten adjacent
    candles at one level are not ten independent validations.
    """
    if not atr or not pivots: return []
    clusters = []
    for p in sorted(pivots, key=lambda p: p["px"]):
        for c in clusters:
            if abs(p["px"]-c["mid"]) <= tol_atr*atr:
                c["members"].append(p)
                c["mid"] = sum(m["px"] for m in c["members"])/len(c["members"])
                break
        else:
            clusters.append({"mid": p["px"], "members": [p]})
    zones = []
    for c in clusters:
        pxs = [m["px"] for m in c["members"]]
        lo, hi = min(pxs), max(pxs)
        touch = [i for i, b in enumerate(bars)
                 if b["l"] <= hi+0.1*atr and b["h"] >= lo-0.1*atr]
        eps, last = 0, -10**9
        for i in touch:
            if i-last >= min_gap: eps += 1
            last = i
        zones.append({"zone": [round(lo, 2), round(hi, 2)],
                      "width_atr": round((hi-lo)/atr, 2),
                      "pivot_touches": len(c["members"]),
                      "kind_mix": "".join(sorted(set(m["kind"] for m in c["members"]))),
                      "bar_touches": len(touch), "episodes": eps,
                      "first_t": min(m["t"][:10] for m in c["members"]),
                      "last_t": max(m["t"][:10] for m in c["members"])})
    return sorted(zones, key=lambda z: (-z["pivot_touches"], -z["episodes"]))

def round_numbers(close, atr):
    """Declared round-number grid near price (thesis 2.5). Step scales
    with price magnitude. Distances in ATR, positive = above close.
    """
    if not atr or close <= 0: return []
    step = 10 if close >= 200 else (5 if close >= 50 else 1)
    base = round(close/step)*step
    return [{"level": base+k*step,
             "dist_atr": round((base+k*step-close)/atr, 2)} for k in (-2, -1, 0, 1, 2)]


def level_tests(level_px, kind, bar, atr):
    """Kind-aware ATR-cut level interaction.

    kind 'H' (prior high / resistance): only upward penetration counts.
    kind 'L' (prior low / support):    only downward penetration counts.
    A bar sitting below a prior high can never be a 'rejected-low-test'.
    """
    base = {"level": round(level_px, 2), "kind": kind}
    if not atr:
        return {**base, "relationship": None}
    up = (bar["h"]-level_px)/atr if bar["h"] > level_px else 0.0
    dn = (level_px-bar["l"])/atr if bar["l"] < level_px else 0.0
    touched_up = bar["h"] >= level_px
    touched_dn = bar["l"] <= level_px
    cx = (bar["c"]-level_px)/atr
    rel = None
    if kind == "H":
        if up >= 0.20 and cx >= 0.20: rel = "broke-above-held"
        elif up >= 0.20: rel = "rejected-high-test"
        elif touched_up: rel = "nicked-high"
        elif abs(cx) <= 0.30: rel = "approach-below"
    else:  # "L"
        if dn >= 0.20 and cx <= -0.20: rel = "broke-below-held"
        elif dn >= 0.20: rel = "rejected-low-test"
        elif touched_dn: rel = "nicked-low"
        elif abs(cx) <= 0.30: rel = "approach-above"
    return {**base, "through_up_atr": round(up, 2),
            "through_dn_atr": round(dn, 2), "close_atr": round(cx, 2),
            "relationship": rel}

def rsi_divergence(pivots, rsi_vals):
    """Pivot-paired RSI divergence (thesis A.1).

    Regular bullish: lower price low + higher RSI low at consecutive
    confirmed LOW pivots. Bearish: mirror on HIGH pivots. Minimum 5 bars
    apart; confirmed pivots only (no lookahead). Observable geometry —
    NOT a validated signal.
    """
    out = []
    def consec(kind):
        ps = [p for p in pivots if p["kind"] == kind
              and p["i"] < len(rsi_vals) and rsi_vals[p["i"]] is not None][-5:]
        return list(zip(ps[:-1], ps[1:]))
    for a, b in consec("L"):
        if b["i"]-a["i"] >= 5 and b["px"] < a["px"] and rsi_vals[b["i"]] > rsi_vals[a["i"]]:
            out.append({"type": "bullish", "t": [a["t"][:10], b["t"][:10]],
                        "price": [round(a["px"], 2), round(b["px"], 2)],
                        "rsi": [round(rsi_vals[a["i"]], 1), round(rsi_vals[b["i"]], 1)]})
    for a, b in consec("H"):
        if b["i"]-a["i"] >= 5 and b["px"] > a["px"] and rsi_vals[b["i"]] < rsi_vals[a["i"]]:
            out.append({"type": "bearish", "t": [a["t"][:10], b["t"][:10]],
                        "price": [round(a["px"], 2), round(b["px"], 2)],
                        "rsi": [round(rsi_vals[a["i"]], 1), round(rsi_vals[b["i"]], 1)]})
    return out


def candle_anatomy(bar, atr):
    """Last-bar anatomy in absolute and ATR terms (thesis 4.8 worked example).
    Zero-range bars: wicks/body reported as 0 with degenerate flag.
    """
    o, h, l, c = bar["o"], bar["h"], bar["l"], bar["c"]
    rng = h - l
    body, uw, lw = abs(c-o), h-max(o, c), min(o, c)-l
    a = lambda x: round(x/atr, 2) if atr else None
    return {"range": round(rng, 2), "range_atr": a(rng),
            "body": round(body, 2), "body_atr": a(body),
            "upper_wick": round(uw, 2), "upper_wick_atr": a(uw),
            "lower_wick": round(lw, 2), "lower_wick_atr": a(lw),
            "direction": "up" if c >= o else "down",
            "degenerate": rng == 0}

def failed_breakouts(bars, pivots, atr):
    """Failed-breakout scan (thesis 4.4 ontology).

    For each recent confirmed pivot: scan forward causally. The first bar
    that closes >=0.20 ATR beyond the level = breakout held (stop, no
    failure). A bar that pokes <=0.50 ATR beyond but closes back inside =
    failed breakout. Observable geometry, not a signal.
    """
    out = []
    for p in pivots[-8:]:
        px = p["px"]
        for b in bars[p["i"]+1:]:
            if not atr: break
            if p["kind"] == "H":
                over = (b["h"]-px)/atr
                cx = (b["c"]-px)/atr
                if cx >= 0.20: break            # held: not a failure
                if 0 < over <= 0.50 and cx < 0:
                    out.append({"level": round(px, 2), "kind": "H",
                                "t": b["t"][:10],
                                "poke_atr": round(over, 2)})
                    break
            else:
                under = (px-b["l"])/atr
                cx = (b["c"]-px)/atr
                if cx <= -0.20: break
                if 0 < under <= 0.50 and cx > 0:
                    out.append({"level": round(px, 2), "kind": "L",
                                "t": b["t"][:10],
                                "poke_atr": round(under, 2)})
                    break
    return out

def contraction(bars, atr_series):
    """Volatility contraction: ATR14 now vs 20 bars ago + inside-bar count.
    Thesis 4.4: contraction evidence precedes any triangle/range read.
    """
    out = {"inside_bars_10": 0}
    if len(bars) >= 11:
        last10 = bars[-10:]
        out["inside_bars_10"] = sum(
            1 for i, b in enumerate(last10, start=len(bars)-10)
            if i > 0 and b["h"] <= bars[i-1]["h"] and b["l"] >= bars[i-1]["l"])
    if len(atr_series) > 21 and atr_series[-21]:
        out["atr_ratio_20b"] = round(atr_series[-1]/atr_series[-21], 2)
    return out

def displacement(bars, atr, n=20):
    """Largest single-bar range in ATR units over the last n bars, with
    direction and date. Thesis 4.4: 'breakout displacement' as continuous
    geometry, not a yes/no label.
    """
    if not atr or not bars: return None
    seg = bars[-n:]
    best = max(seg, key=lambda b: (b["h"]-b["l"]))
    return {"t": best["t"][:10], "range_atr": round((best["h"]-best["l"])/atr, 2),
            "direction": "up" if best["c"] >= best["o"] else "down"}

def fib_zones(pivots):
    """Retracement zones of the last completed swing. POLICY levels
    (LocationFirst) — per the thesis, Fib location is not a calibrated
    forecast. Up-swing: pullback zones below the high. Down-swing:
    bounce zones above the low.
    """
    if len(pivots) < 2: return None
    a, b = pivots[-2], pivots[-1]
    lo, hi = min(a["px"], b["px"]), max(a["px"], b["px"])
    rng = hi - lo
    if rng <= 0: return None
    lv = ({r: hi-r*rng for r in (0.382, 0.5, 0.618)} if b["px"] > a["px"]
          else {r: lo+r*rng for r in (0.382, 0.5, 0.618)})
    return {"swing": (f"{a['t'][:10]} {a['kind']} {round(a['px'],2)} -> "
                      f"{b['t'][:10]} {b['kind']} {round(b['px'],2)}"),
            "levels": {f"{r*100:.1f}%": round(px, 2) for r, px in lv.items()},
            "note": "policy levels, not calibrated forecasts"}


def primitives(bars):
    """Single-bar pattern primitives on the last two daily bars."""
    if len(bars) < 2: return {}
    b, p = bars[-1], bars[-2]
    up_streak = dn_streak = 0
    for i in range(len(bars)-1, 0, -1):
        if bars[i]["c"] > bars[i-1]["c"]: up_streak += 1
        else: break
    for i in range(len(bars)-1, 0, -1):
        if bars[i]["c"] < bars[i-1]["c"]: dn_streak += 1
        else: break
    return {
        "inside_bar": b["h"] <= p["h"] and b["l"] >= p["l"],
        "outside_bar": b["h"] > p["h"] and b["l"] < p["l"],
        "up_streak": up_streak, "down_streak": dn_streak,
    }

def rnd(x, n=2):
    return round(x, n) if x is not None else None

# ---------- main ----------

def _as_bar_list(raw):
    """Coerce a fetch payload to a bar list (dict payloads carry the
    series under "bars", which may be null). Anything else -> []."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        bars = raw.get("bars")
        return bars if isinstance(bars, list) else []
    return []


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbol", required=True)
    sym = ap.parse_args().symbol.upper()

    w = _as_bar_list(fetch(sym, "1W", 60)); d = _as_bar_list(fetch(sym, "1D", 260))
    h1 = _as_bar_list(fetch(sym, "1H", 120)); m10 = _as_bar_list(fetch(sym, "10Min", 150))

    # Guard (2026-10-13, T6): missing/short bars -> NO_VIEW, never a
    # crash and never a fabricated PASS-able chart. Crypto pairs (e.g.
    # SOLUSD) return an EMPTY series from the Alpaca stock-bars route;
    # the old code died with IndexError at atr[-1] (the wilder_atr call
    # site) and chart-gate staging surfaced only a bare traceback.
    # data_status() already declares NO_VIEW below 20 daily bars; the
    # same threshold applies here, plus any empty companion frame.
    if len(d) < 20 or not w or not h1 or not m10:
        counts = {"1W": len(w), "1D": len(d), "1H": len(h1), "10Min": len(m10)}
        missing = [tf for tf, n_ in counts.items() if n_ == 0]
        _kb = _load_kraken_bars()
        _route = ("Kraken OHLC route returned no usable bars"
                  if _kb is not None and _kb.is_kraken_symbol(sym)
                  else "stock-bars route returned no usable bars; "
                       "crypto pairs are not served by that route")
        detail = ("missing bars: " + ", ".join(
            f"{tf} series has {counts[tf]} bars" for tf in counts)
            + f" for {sym} ({_route})")
        doc = {
            "symbol": sym, "asof": None,
            "pass_a_version": PASS_A_VERSION,
            "data_status": "NO_VIEW",
            "stances": {"1W": "unresolved", "1D": "unresolved",
                        "1H": "unresolved", "10m": "unresolved"},
            "last_bar_provisional": None,
            "limitations": detail,
            "bars": counts,
            "missing_frames": missing,
            "last": None, "atr14": None, "atr50": None, "atr_pct": None,
        }
        print(json.dumps(doc, indent=1))
        return
    dc = [b["c"] for b in d]; dv = [b.get("v") or 0 for b in d]
    atr = wilder_atr(d); last_atr = atr[-1]
    atr50 = wilder_atr(d, 50)[-1]
    # Thesis 2.4: normalize location features against PREVIOUS ATR so the
    # reference scale is independent of the current bar's own range.
    atr_prev = atr[-2] if len(atr) > 1 and atr[-2] else last_atr
    last = d[-1]

    # weekly regime
    wc = [b["c"] for b in w]
    wma10, wma40 = sma(wc, 10)[-1], sma(wc, 40)[-1]
    wpiv = pivots(w, 3, 3)

    # daily structure
    dpiv = pivots(d)
    ema20 = ema(dc, 20)[-1]; ema50 = ema(dc, 50)[-1]
    ema200 = ema(dc, 200)[-1] if len(dc) >= 200 else None
    v20 = sum(dv[-21:-1])/20 if len(dv) > 21 else None
    rng = last["h"]-last["l"]
    loc_u = (last["c"]-last["l"])/rng if rng else None
    loc_s = 2*loc_u-1 if loc_u is not None else None

    # momentum layer (thesis A.1 contracts)
    rsi = rsi_wilder(dc)
    mline, msig, mhist = macd(dc)
    sk, sd = stoch_rsi(rsi)
    cc = cci(d)
    pdi, mdi, ax = adx_dmi(d)
    cm = cmf(d); mf = mfi(d)
    ob = obv(d)
    obv_slope = None
    if len(ob) > 21 and ob[-21] != 0:
        obv_slope = rnd((ob[-1]-ob[-21])/abs(ob[-21])*100)

    # swing levels worth testing: last 6 confirmed pivots (kind-aware,
    # previous-ATR scale per thesis 2.4)
    levels = [{"t": p["t"][:10], **level_tests(p["px"], p["kind"], last, atr_prev)}
              for p in dpiv[-6:]]

    # gaps on daily (previous-ATR scale)
    gaps = []
    for i in range(max(1, len(d)-10), len(d)):
        pc, o = d[i-1]["c"], d[i]["o"]
        g = (o-pc)/atr_prev if atr_prev else 0
        if abs(g) >= 0.50:
            gaps.append({"t": d[i]["t"][:10], "gap_atr": round(g, 2)})

    prim = primitives(d)

    # 1H rhythm
    h1c = [b["c"] for b in h1]
    h_ma20, h_ma50 = sma(h1c, 20)[-1], sma(h1c, 50)[-1]

    # 10m refinement
    m10c = [b["c"] for b in m10]
    m_ma20, m_ma50 = sma(m10c, 20)[-1], sma(m10c, 50)[-1]
    vw = session_vwap(m10)
    vw_days = sorted(vw)[-3:]

    prov = last_bar_provisional(last["t"])
    status = data_status(len(d), any(dv), prov, ema200 is not None, last["t"])
    stances = {
        "1W": frame_stance(wc[-1], wma10, wma40),
        "1D": frame_stance(last["c"], ema20, ema50, ema200),
        "1H": frame_stance(h1c[-1], h_ma20, h_ma50),
        "10m": frame_stance(m10c[-1], m_ma20, m_ma50),
    }

    doc = {
        "symbol": sym, "asof": last["t"][:10],
        "pass_a_version": PASS_A_VERSION,
        "data_status": status,
        "stances": stances,
        "versions": {
            "bars_hash": bar_payload_hash(w, d, h1, m10),
            "pass_a": PASS_A_VERSION,
        },
        "last_bar_provisional": prov,
        "conventions": {
            "rsi": "Wilder RMA alpha=1/14, SMA seed of first 14 changes; flat->50",
            "macd": "EMA12-EMA26, signal EMA9, hist=line-signal",
            "stochrsi": "14/3/3 on RSI; flat RSI window->50",
            "cci": "TP=(H+L+C)/3, 0.015*mean|dev|, n=20",
            "adx": "Wilder 14: +DM/-DM, RMA(TR), DX, RMA(DX)",
            "cmf": "sum(signed_loc*V)/sum(V), n=20; degenerate->0, no-vol->0",
            "mfi": "TP-flow grouped by TP direction, n=14; ties->pos, 0/0->50",
            "vwap": "regular-session 10m bars, typical-price weighted",
            "close_location": "unit=(C-L)/R; signed=2*unit-1",
            "level_scale": "level tests + gaps use PREVIOUS-bar ATR (thesis 2.4)",
            "ema_frame": "daily bars (thesis: 200ema = 200-day EMA)",
        },
        "last": {k: round(last[k], 2) for k in ("o", "h", "l", "c")},
        "atr14": rnd(last_atr),
        "atr50": rnd(atr50),
        "atr_pct": rnd(100*last_atr/last["c"]) if last_atr else None,
        "close_location_unit": rnd(loc_u),
        "close_location_signed": rnd(loc_s),
        "volume": {"last": dv[-1], "avg20": round(v20) if v20 else None,
                   "ratio": rnd(dv[-1]/v20) if v20 else None},
        "weekly": {"close": rnd(wc[-1]), "ma10": rnd(wma10), "ma40": rnd(wma40),
                   "above_ma10": wc[-1] > wma10 if wma10 else None,
                   "above_ma40": wc[-1] > wma40 if wma40 else None,
                   "pivots": [{"t": p["t"][:10], "avail_t": p["avail_t"][:10],
                               "kind": p["kind"], "px": rnd(p["px"])}
                               for p in wpiv[-6:]]},
        "daily": {"ema20": rnd(ema20), "ema50": rnd(ema50), "ema200": rnd(ema200),
                  "dist_ema20_atr": rnd((last["c"]-ema20)/last_atr) if ema20 and last_atr else None,
                  "rsi14": rnd(rsi[-1]),
                  "macd": {"line": rnd(mline[-1]), "signal": rnd(msig[-1]),
                           "hist": rnd(mhist[-1])},
                  "stochrsi": {"k": rnd(sk[-1]), "d": rnd(sd[-1])},
                  "cci20": rnd(cc[-1]),
                  "cmf20": rnd(cm[-1]), "mfi14": rnd(mf[-1]),
                  "adx14": rnd(ax[-1]), "plus_di": rnd(pdi[-1]), "minus_di": rnd(mdi[-1]),
                  "obv_slope20_pct": obv_slope,
                  "pivots": [{"t": p["t"][:10], "avail_t": p["avail_t"][:10],
                              "kind": p["kind"], "px": rnd(p["px"])}
                              for p in dpiv[-8:]],
                  "level_clusters": level_clusters(dpiv, d, last_atr),
                  "round_numbers": round_numbers(last["c"], last_atr),
                  "pivot_sequence": pivot_sequence(dpiv),
                  "double_bottom": double_bottom(dpiv, last_atr),
                  "reset_candidate": reset_candidate(
                      d, level_clusters(dpiv, d, last_atr), atr, last_atr,
                      prim["up_streak"]),
                  "ema_stack": ema_stack(last["c"], ema20, ema50, ema200),
                  "fib_zones": fib_zones(dpiv),
                  "rsi_divergence": rsi_divergence(dpiv, rsi),
                  "candle_anatomy": candle_anatomy(last, last_atr),
                  "failed_breakouts": failed_breakouts(d, dpiv, last_atr),
                  "contraction": contraction(d, atr),
                  "displacement_20b": displacement(d, last_atr),
                  "primitives": prim,
                  "unconfirmed_extremes": {
                      "recent_high": rnd(max(b["h"] for b in d[-6:])),
                      "recent_low": rnd(min(b["l"] for b in d[-6:]))}},
        "hourly": {"ma20": rnd(h_ma20), "ma50": rnd(h_ma50),
                   "above_ma20": h1c[-1] > h_ma20 if h_ma20 else None},
        "ten_min": {"ma20": rnd(m_ma20), "ma50": rnd(m_ma50),
                    "above_ma20": m10c[-1] > m_ma20 if m_ma20 else None,
                    "session_vwap": {day: vw[day] for day in vw_days},
                    "last_close_vs_vwap_atr": (
                        rnd((m10c[-1]-vw[vw_days[-1]])/last_atr)
                        if vw_days and vw[vw_days[-1]] and last_atr else None)},
        "level_tests": levels,
        "gaps_10d": gaps,
    }
    print(json.dumps(doc, indent=1))

if __name__ == "__main__":
    main()
