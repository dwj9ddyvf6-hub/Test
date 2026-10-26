#!/usr/bin/env python3
"""R4: Blowoff-as-standalone resurrection battery.

Pre-reg (frozen, binding): desk/research/resurrection/PRE_REG_R4_BLOWOFF_STANDALONE.md
Killed formulation: blowoff LONG as a FILTER vs naive breakout (THIN/HARDENED).
This battery tests the different claim: standalone blowoff longs vs
same-stock random-day control.

Signal is byte-identical to rsiobv.scan_exhaustion (imported verbatim for
RSI/OBV math; vectorized rolling-window logic verified byte-identical on a
sample before the run — see verify_detector()).
"""
import json
import math
import os
import random
import sys
from datetime import datetime, timezone

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import ttest_ind

REPO = "<workspace>/alpaca-swing-desk"
RES = os.path.join(REPO, "desk", "research")
sys.path.insert(0, os.path.join(RES))          # desk/research/rsiobv.py
sys.path.insert(0, os.path.join(RES, "resurrection", "code"))
from rsiobv import wilder_rsi, scan_exhaustion  # noqa: E402  (verbatim import)

RANGE_LOOKBACK = 144
RSI_PERIOD = 14
COST_NATIVE = 0.001    # 10bp RT
COST_SMCAP = 0.015     # 150bp RT primary for small-cap stratum
CTRL_SEED = 20261003   # frozen control seed (documented)
SIG_START, SIG_END = "2020-01-01", "2026-10-01"


def blowoff_indices_vec(closes, vols):
    """Vectorized scan_exhaustion BLOWOFF rising edges.

    Exact logic mirror: Wilder RSI(14) + OBV each >= trailing-144-bar
    min + 0.9*(max-min); flat windows skipped; windows containing RSI
    warmup (None) skipped; rising edge = first bar of each contiguous
    BLOWOFF run. Returns sorted list of bar indices.
    """
    n = len(closes)
    W = RANGE_LOOKBACK
    if n < W:
        return []
    c = np.asarray(closes, dtype=float)
    v = np.asarray(vols, dtype=float)
    rsi = np.array([np.nan if x is None else x
                    for x in wilder_rsi(list(c), RSI_PERIOD)], dtype=float)
    obv = np.zeros(n)
    run = 0.0
    for i in range(1, n):
        vv = v[i] or 0.0
        if c[i] > c[i - 1]:
            run += vv
        elif c[i] < c[i - 1]:
            run -= vv
        obv[i] = run
    rw = sliding_window_view(rsi, W)   # row k = window ending at bar k+W-1
    ow = sliding_window_view(obv, W)
    valid = ~np.isnan(rw).any(axis=1)  # == original's "any None -> skip"
    rmin, rmax = rw.min(axis=1), rw.max(axis=1)
    omin, omax = ow.min(axis=1), ow.max(axis=1)
    flat = (rmax == rmin) | (omax == omin)
    ii = np.arange(n - W + 1) + W - 1
    hit = (valid & ~flat
           & (rsi[ii] >= rmin + 0.9 * (rmax - rmin))
           & (obv[ii] >= omin + 0.9 * (omax - omin)))
    idx = ii[hit]
    if len(idx) == 0:
        return []
    edges = idx[np.concatenate([[True], np.diff(idx) != 1])]
    return [int(x) for x in edges]


def verify_detector(daily, n_sample=30, seed=7):
    """Byte-identity check: vectorized vs verbatim scan_exhaustion."""
    rng = random.Random(seed)
    syms = rng.sample(sorted(daily.keys()), min(n_sample, len(daily)))
    bad = 0
    for s in syms:
        bars = daily[s]
        dicts = [{"c": b["c"], "v": b["v"]} for b in bars]
        ref = sorted(e["index"] for e in scan_exhaustion(dicts)
                     if e["type"] == "BLOWOFF")
        got = blowoff_indices_vec([b["c"] for b in bars],
                                  [b["v"] for b in bars])
        if ref != got:
            bad += 1
            print(f"  MISMATCH {s}: ref {len(ref)} vs vec {len(got)}",
                  flush=True)
    print(f"detector verification: {len(syms)-bad}/{len(syms)} identical",
          flush=True)
    if bad:
        raise SystemExit("vectorized detector NOT byte-identical — aborting")


def load_daily():
    daily = {}
    with open(os.path.join(RES, "data", "breakout_universe_daily.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            bars = [{"date": b[0], "o": b[1], "h": b[2], "l": b[3],
                     "c": b[4], "v": b[5]} for b in r["bars"]]
            daily[r["s"]] = bars
    return daily


def deoverlap(idxs, gap=20):
    """Earliest kept; >=gap bars between kept signals."""
    kept = []
    for i in sorted(idxs):
        if not kept or i >= kept[-1] + gap:
            kept.append(i)
    return kept


def trade_ret(bars, sig, hold, cost):
    """LONG next bar open after signal; exit close of hold-th bar after entry."""
    ei, xi = sig + 1, sig + hold
    if xi >= len(bars):
        return None
    o, c = bars[ei]["o"], bars[xi]["c"]
    if not o or o <= 0:
        return None
    return c / o - 1.0 - cost


def eligible_indices(bars, hold):
    return [i for i, b in enumerate(bars)
            if SIG_START <= b["date"] <= SIG_END and i + hold < len(bars)
            and i + 1 < len(bars)]


def sample_control(rng, elig, n, gap=20):
    """n_i random eligible dates, greedy >=gap de-overlap (Annex 2)."""
    pool = elig[:]
    rng.shuffle(pool)
    kept = []
    for i in sorted(pool):
        if len(kept) >= n:
            break
        if not kept or all(abs(i - k) >= gap for k in kept):
            kept.append(i)
    return sorted(kept)


def welch(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return {"t": float("nan"), "p_two": float("nan")}
    t, p = ttest_ind(a, b, equal_var=False)
    return {"t": float(t), "p_two": float(p)}


def load_spy():
    rows = json.load(open(os.path.join(RES, "data", "spy_daily.json")))
    dates, closes = [], []
    for r in rows:
        d = r["t"][:10]
        dates.append(d)
        closes.append(r["c"])
    return dates, closes


def spy_regime_flags(dates, closes, sig_dates):
    """Trailing-60-trading-day SPY return <= 0 -> down. Returns dict date->bool(down)."""
    idx = {d: i for i, d in enumerate(dates)}
    out = {}
    for d in set(sig_dates):
        i = idx.get(d)
        if i is None:  # step back to nearest prior trading day
            cand = [x for x in dates if x <= d]
            if not cand:
                continue
            i = idx[cand[-1]]
        if i < 60:
            continue
        out[d] = (closes[i] / closes[i - 60] - 1.0) <= 0
    return out


# ------------------------------------------------------------------ main ---

def weekly_dollarvol_band(daily):
    """Per symbol: dict week_key(Friday date) -> weekly dollar volume,
    from daily bars. Used for point-in-time sub-M2 band assignment."""
    from datetime import date as ddate, timedelta
    band = {}
    for s, bars in daily.items():
        wk = {}
        for b in bars:
            d = ddate.fromisoformat(b["date"])
            fri = d + timedelta(days=(4 - d.weekday()) % 7)
            k = fri.isoformat()
            wk[k] = wk.get(k, 0.0) + (b["c"] or 0.0) * (b["v"] or 0.0)
        band[s] = wk
    return band


def in_subm2_band(band_wk, symbol, sig_date):
    """Trailing-52 completed weeks before signal week: 500K <= mean < 10M."""
    from datetime import date as ddate, timedelta
    wk = band_wk.get(symbol)
    if not wk:
        return None
    d = ddate.fromisoformat(sig_date)
    fri = d + timedelta(days=(4 - d.weekday()) % 7)
    vals = []
    for w in range(1, 53):
        k = (fri - timedelta(weeks=w)).isoformat()
        if k in wk:
            vals.append(wk[k])
    if len(vals) < 40:
        return None
    m = sum(vals) / len(vals)
    return 500_000 <= m < 10_000_000


def run_primary(daily, spy):
    rng = random.Random(CTRL_SEED)
    sig_rets, ctl_rets = [], []
    sig_down, ctl_down = [], []
    sig_dates_all = []
    per_sym_n = {}
    for s in sorted(daily):
        bars = daily[s]
        idx = [i for i in blowoff_indices_vec(
                   [b["c"] for b in bars], [b["v"] for b in bars])
               if SIG_START <= bars[i]["date"] <= SIG_END
               and i + 20 < len(bars)]
        kept = deoverlap(idx, 20)
        if not kept:
            continue
        per_sym_n[s] = len(kept)
        for i in kept:
            r = trade_ret(bars, i, 20, COST_NATIVE)
            sig_rets.append(r)
            sig_dates_all.append(bars[i]["date"])
        elig = eligible_indices(bars, 20)
        for j in sample_control(rng, elig, len(kept), 20):
            r = trade_ret(bars, j, 20, COST_NATIVE)
            ctl_rets.append(r)
            sig_dates_all.append(bars[j]["date"])
    regime = spy_regime_flags(*spy, sig_dates_all)
    # re-walk to tag regimes (keep ordering aligned)
    sig_rets, ctl_rets = [], []
    sig_down, ctl_down = [], []
    rng = random.Random(CTRL_SEED)
    for s in sorted(daily):
        bars = daily[s]
        idx = [i for i in blowoff_indices_vec(
                   [b["c"] for b in bars], [b["v"] for b in bars])
               if SIG_START <= bars[i]["date"] <= SIG_END
               and i + 20 < len(bars)]
        kept = deoverlap(idx, 20)
        if not kept:
            continue
        for i in kept:
            sig_rets.append(trade_ret(bars, i, 20, COST_NATIVE))
            sig_down.append(bool(regime.get(bars[i]["date"], False)))
        elig = eligible_indices(bars, 20)
        for j in sample_control(rng, elig, len(kept), 20):
            ctl_rets.append(trade_ret(bars, j, 20, COST_NATIVE))
            ctl_down.append(bool(regime.get(bars[j]["date"], False)))
    return {
        "sig": sig_rets, "ctl": ctl_rets,
        "sig_down": sig_down, "ctl_down": ctl_down,
        "n_symbols": len(per_sym_n),
    }


def run_smallcap(daily):
    band_wk = weekly_dollarvol_band(daily)
    rng = random.Random(CTRL_SEED)
    out = {}
    for cost, tag in ((COST_SMCAP, "150bp"), (COST_NATIVE, "10bp_sens")):
        sig, ctl = [], []
        rng_c = random.Random(CTRL_SEED)
        for s in sorted(daily):
            bars = daily[s]
            idx = [i for i in blowoff_indices_vec(
                       [b["c"] for b in bars], [b["v"] for b in bars])
                   if SIG_START <= bars[i]["date"] <= SIG_END
                   and i + 20 < len(bars)
                   and in_subm2_band(band_wk, s, bars[i]["date"])]
            kept = deoverlap(idx, 20)
            if not kept:
                continue
            for i in kept:
                sig.append(trade_ret(bars, i, 20, cost))
            elig = [i for i in eligible_indices(bars, 20)
                    if in_subm2_band(band_wk, s, bars[i]["date"])]
            for j in sample_control(rng_c, elig, len(kept), 20):
                ctl.append(trade_ret(bars, j, 20, cost))
        out[tag] = {"sig": sig, "ctl": ctl}
    return out


def run_horizons(daily):
    rng = random.Random(CTRL_SEED)
    out = {}
    for hold, tag in ((40, "40d"), (65, "13w")):
        sig, ctl = [], []
        for s in sorted(daily):
            bars = daily[s]
            idx = [i for i in blowoff_indices_vec(
                       [b["c"] for b in bars], [b["v"] for b in bars])
                   if SIG_START <= bars[i]["date"] <= SIG_END
                   and i + hold < len(bars)]
            kept = deoverlap(idx, 20)
            if not kept:
                continue
            for i in kept:
                sig.append(trade_ret(bars, i, hold, COST_NATIVE))
            elig = eligible_indices(bars, hold)
            for j in sample_control(rng, elig, len(kept), 20):
                ctl.append(trade_ret(bars, j, hold, COST_NATIVE))
        out[tag] = {"sig": sig, "ctl": ctl}
    return out


def run_weekly_transfer():
    """Momentum transfer: weekly RSI(14)+OBV top-decile (144w) -> 13w forwards."""
    wk = json.load(open(os.path.join(
        RES, "weekly-phenotypes", "weekly_bars_dev.json")))
    rng = random.Random(CTRL_SEED)
    sig, ctl = [], []
    WSTART, WEND = "2019-01-01", "2022-03-31"
    HOLD = 13
    for s in sorted(wk):
        bars = wk[s]
        closes = [b["c"] for b in bars]
        vols = [b.get("v") or 0 for b in bars]
        idx = blowoff_indices_vec(closes, vols)
        dstr = [datetime.fromtimestamp(b["t"], timezone.utc).strftime("%Y-%m-%d")
                for b in bars]
        kidx = [i for i in idx
                if WSTART <= dstr[i] <= WEND and i + HOLD < len(bars)
                and bars[i + 1].get("o")]
        kept = deoverlap(kidx, 20)
        for i in kept:
            o, c = bars[i + 1]["o"], bars[i + HOLD]["c"]
            sig.append(c / o - 1.0 - COST_NATIVE)
        elig = [i for i in range(len(bars))
                if WSTART <= dstr[i] <= WEND and i + HOLD < len(bars)
                and bars[i + 1].get("o")]
        for j in sample_control(rng, elig, len(kept), 20):
            o, c = bars[j + 1]["o"], bars[j + HOLD]["c"]
            ctl.append(c / o - 1.0 - COST_NATIVE)
    return {"sig": sig, "ctl": ctl}


def run_1h_transfer():
    """Tensor-1H transfer: 1H blowoff (144 bars) -> 20-bar forwards, 42 symbols."""
    import glob
    rng = random.Random(CTRL_SEED)
    sig, ctl = [], []
    HOLD = 20
    for path in sorted(glob.glob(os.path.join(
            RES, "stop-tolerance", "data", "bars_1h_*.json"))):
        bars = json.load(open(path))
        closes = [b["c"] for b in bars]
        vols = [b.get("v") or 0 for b in bars]
        idx = blowoff_indices_vec(closes, vols)
        kidx = [i for i in idx if i + HOLD < len(bars) and bars[i + 1].get("o")]
        kept = deoverlap(kidx, 20)
        for i in kept:
            o, c = bars[i + 1]["o"], bars[i + HOLD]["c"]
            sig.append(c / o - 1.0 - COST_NATIVE)
        elig = [i for i in range(len(bars))
                if i + HOLD < len(bars) and bars[i + 1].get("o")]
        for j in sample_control(rng, elig, len(kept), 20):
            o, c = bars[j + 1]["o"], bars[j + HOLD]["c"]
            ctl.append(c / o - 1.0 - COST_NATIVE)
    return {"sig": sig, "ctl": ctl}


def summ(name, sig, ctl):
    s = np.asarray(sig, dtype=float)
    c = np.asarray(ctl, dtype=float)
    w = welch(s, c)
    return {"n_sig": int(len(s)), "n_ctl": int(len(c)),
            "mean_sig": round(float(np.mean(s)), 4),
            "mean_ctl": round(float(np.mean(c)), 4),
            "welch_t": round(w["t"], 3),
            "p_two": round(w["p_two"], 4) if w["p_two"] == w["p_two"] else None}


def main():
    print("loading daily universe...", flush=True)
    daily = load_daily()
    print(f"symbols: {len(daily)}", flush=True)
    verify_detector(daily)
    spy = load_spy()

    print("PRIMARY: standalone blowoff vs random-day...", flush=True)
    p = run_primary(daily, spy)
    stats = {"primary": summ("primary", p["sig"], p["ctl"])}
    stats["primary"]["n_symbols"] = p["n_symbols"]

    sd = [r for r, d in zip(p["sig"], p["sig_down"]) if d]
    cd = [r for r, d in zip(p["ctl"], p["ctl_down"]) if d]
    su = [r for r, d in zip(p["sig"], p["sig_down"]) if not d]
    cu = [r for r, d in zip(p["ctl"], p["ctl_down"]) if not d]
    stats["down_regime"] = summ("down", sd, cd)
    stats["up_regime"] = summ("up", su, cu)

    print("SECONDARY: small-cap transfer...", flush=True)
    sc = run_smallcap(daily)
    stats["smallcap_150bp"] = summ("sc150", sc["150bp"]["sig"], sc["150bp"]["ctl"])
    stats["smallcap_10bp_sens"] = summ("sc10", sc["10bp_sens"]["sig"],
                                      sc["10bp_sens"]["ctl"])

    print("SECONDARY: horizons...", flush=True)
    hz = run_horizons(daily)
    stats["horizon_40d"] = summ("40d", hz["40d"]["sig"], hz["40d"]["ctl"])
    stats["horizon_13w"] = summ("13w", hz["13w"]["sig"], hz["13w"]["ctl"])

    print("TRANSFER: weekly momentum...", flush=True)
    wt = run_weekly_transfer()
    stats["weekly_transfer"] = summ("weekly", wt["sig"], wt["ctl"])

    print("TRANSFER: tensor 1H...", flush=True)
    ht = run_1h_transfer()
    stats["h1_transfer"] = summ("h1", ht["sig"], ht["ctl"])

    t, m = stats["primary"]["welch_t"], stats["primary"]["mean_sig"]
    verdict = "SURVIVES" if (m > 0 and t > 2.0) else "BURIED"
    stats["verdict"] = verdict
    stats["meta"] = {"ctrl_seed": CTRL_SEED, "cost_native_bp": 10,
                     "cost_smcap_bp": 150, "sig_window": [SIG_START, SIG_END]}

    out = os.path.join(RES, "resurrection", "r4_blowoff_stats.json")
    with open(out, "w") as fh:
        json.dump(stats, fh, indent=2)
    print(json.dumps(stats, indent=2)[:2000], flush=True)
    print("VERDICT:", verdict, flush=True)
    return stats


if __name__ == "__main__":
    main()
