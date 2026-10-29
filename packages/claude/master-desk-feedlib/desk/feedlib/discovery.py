"""Universe discovery — the old desk's weekly family watchlists (desk/universe_discovery.py, midna@7969b52),
ported verbatim in its pure functions; the fetch goes through the DataHub (cached, incremental).

  Layer 1  eligibility over the 1,838-name genome: 20d average dollar volume >= $500K, last close >= $1,
           >= 200 daily bars.
  Layer 2  family finders (meanrev / breakout / dipbuy / momentum), each family's top 60 by score.
Writes {generated_at_utc, eligibility, families, sleeve_family} to cache/family_watchlists.json.
Sleeves read it through load_family_universe(): older than 8 days or missing -> the sleeve's fallback universe
(discovery never breaks a sleeve). On the old desk only rsi_meanrev consumed it ("meanrev")."""
import json
import os
from datetime import datetime, timezone

MIN_DOLLAR_VOL_20D = 500_000
MIN_PRICE = 1.00
MIN_BARS = 200
WATCHLIST_MAX_AGE_DAYS = 8

SLEEVE_FAMILY = {"rsi_meanrev": "meanrev", "snapback": "meanrev", "donchian": "breakout", "gate_1h": "breakout",
                 "blowoff_1h": "breakout", "blowoff_d": "breakout", "beatendown": "dipbuy", "capitulation": "dipbuy",
                 "red_day_reversal": "dipbuy", "momentum": "momentum", "momentum_rotation": "momentum"}


def eligible(symbol, bars):
    if len(bars) < MIN_BARS:
        return None
    closes = [b["c"] for b in bars]
    if closes[-1] < MIN_PRICE:
        return None
    dvol = sum(b["c"] * b["v"] for b in bars[-20:]) / 20
    if dvol < MIN_DOLLAR_VOL_20D:
        return None
    return {"symbol": symbol, "dollar_vol_20d": round(dvol, 0), "last_close": round(closes[-1], 2)}


def _rsi(values, period):
    out = [None] * len(values)
    if len(values) < period + 1:
        return out
    gains, losses = [], []
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains) / period
    al = sum(losses) / period
    out[period] = 100 - 100 / (1 + ag / al) if al else 100.0
    for i in range(period + 1, len(values)):
        d = values[i] - values[i - 1]
        ag = (ag * (period - 1) + max(d, 0)) / period
        al = (al * (period - 1) + max(-d, 0)) / period
        out[i] = 100 - 100 / (1 + ag / al) if al else 100.0
    return out


def _atr_pct(bars, period=14):
    trs = []
    for i in range(max(1, len(bars) - period), len(bars)):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return (sum(trs) / len(trs)) / bars[-1]["c"] * 100 if trs else 0.0


def finder_meanrev(symbol, bars):
    closes = [b["c"] for b in bars]
    window = closes[-90:]
    rsi2 = _rsi(window, 2)
    oversold = sum(1 for r in rsi2 if r is not None and r < 10)
    bb_hits = 0
    for i in range(20, len(window)):
        w = window[i - 20:i]
        m = sum(w) / 20
        sd = (sum((x - m) ** 2 for x in w) / 20) ** 0.5
        if sd and (window[i] - (m - 2 * sd)) / (4 * sd) < 0:
            bb_hits += 1
    score = oversold + 0.5 * bb_hits
    if score <= 0:
        return None
    return {"symbol": symbol, "score": round(score, 1), "reason": f"RSI2<10 x{oversold}, %B<0 x{bb_hits} (90d)"}


def finder_breakout(symbol, bars):
    closes = [b["c"] for b in bars]
    highs = [b["h"] for b in bars]
    window_c, window_h = closes[-90:], highs[-90:]
    breaks = sum(1 for i in range(20, len(window_c)) if window_c[i] > max(window_h[i - 20:i]))
    atr = _atr_pct(bars)
    if breaks == 0 or atr < 1.0:
        return None
    score = breaks * (1 + min(atr, 10) / 10)
    return {"symbol": symbol, "score": round(score, 1), "reason": f"20d breakouts x{breaks}, ATR {atr:.1f}% (90d)"}


def finder_dipbuy(symbol, bars):
    closes = [b["c"] for b in bars]
    window = closes[-90:]
    peak, max_dd, recoveries = window[0], 0.0, 0
    was_down = False
    for c in window:
        peak = max(peak, c)
        dd = (peak - c) / peak if peak else 0
        max_dd = max(max_dd, dd)
        if dd >= 0.08:
            was_down = True
        elif was_down and c / peak >= 0.97:
            recoveries += 1
            was_down = False
    if max_dd < 0.08:
        return None
    score = max_dd * 100 * (1 + recoveries)
    return {"symbol": symbol, "score": round(score, 1), "reason": f"maxDD {max_dd:.0%}, recoveries x{recoveries} (90d)"}


def finder_momentum(symbol, bars):
    closes = [b["c"] for b in bars]
    if len(closes) < 70:
        return None
    mom_60 = closes[-1] / closes[-61] - 1
    hi_252 = max(b["h"] for b in bars[-252:])
    dist_high = closes[-1] / hi_252 - 1
    if mom_60 < 0.10 or dist_high < -0.25:
        return None
    score = mom_60 * 100 + (dist_high + 0.25) * 100
    return {"symbol": symbol, "score": round(score, 1), "reason": f"60d {mom_60:+.0%}, {dist_high:+.0%} off 52w high"}


FINDERS = {"meanrev": finder_meanrev, "breakout": finder_breakout, "dipbuy": finder_dipbuy, "momentum": finder_momentum}


def build(bars_by_symbol, genome, now=None, top_n=60):
    """the old run() on already-fetched bars: eligibility, finders, top_n per family."""
    eligible_rows, cache = [], {}
    for sym in genome:
        bars = bars_by_symbol.get(sym) or []
        if not bars:
            continue
        fac = eligible(sym, bars)
        if fac:
            eligible_rows.append(fac)
            cache[sym] = bars
    families = {}
    for fam, fn in FINDERS.items():
        rows = [r for r in (fn(f["symbol"], cache[f["symbol"]]) for f in eligible_rows) if r]
        rows.sort(key=lambda r: r["score"], reverse=True)
        families[fam] = rows[:top_n]
    ts = datetime.fromtimestamp(now, tz=timezone.utc) if now else datetime.now(timezone.utc)
    return {"generated_at_utc": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "eligibility": {"gates": {"min_dollar_vol_20d": MIN_DOLLAR_VOL_20D, "min_price": MIN_PRICE,
                                      "min_bars": MIN_BARS},
                            "n_screened": len(genome), "n_eligible": len(eligible_rows)},
            "families": families, "sleeve_family": SLEEVE_FAMILY}


def run(hub, genome, path, now, source="equity_split", top_n=60, chunk=200):
    """fetch ~300 daily bars per genome symbol through the hub (incremental cache) and write the watchlist."""
    bars = {}
    for i in range(0, len(genome), chunk):
        bars.update(hub.bars(source, "1d", genome[i:i + chunk], 300))
    doc = build(bars, genome, now=now, top_n=top_n)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, indent=1)
    os.replace(tmp, path)
    return doc


def load_family_universe(path, family, fallback, now):
    """the old sleeve entry point: the family's watchlist, or the fallback when missing/stale (> 8 days)."""
    try:
        doc = json.load(open(path))
        gen = datetime.fromisoformat(doc["generated_at_utc"].replace("Z", "+00:00")).timestamp()
        if (now - gen) / 86400 > WATCHLIST_MAX_AGE_DAYS:
            return list(fallback), "stale"
        syms = [r["symbol"] for r in doc.get("families", {}).get(family, []) if r.get("symbol")]
        return (syms, "watchlist") if syms else (list(fallback), "empty")
    except (OSError, ValueError, KeyError):
        return list(fallback), "missing"
