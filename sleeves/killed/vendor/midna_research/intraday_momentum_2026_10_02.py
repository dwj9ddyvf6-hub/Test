#!/usr/bin/env python3
"""Intraday momentum replication study (Gao, Han, Li, Zhou 2018) — frozen tests.

Implements EXACTLY the frozen rules in intraday_momentum_prereg_2026-10-02.md:
- r_first[d] = c[d,09:55]/o[d,09:30] - 1 ; r_last[d] = c[d,15:55]/o[d,15:30] - 1
- Exclusions: half-days (no 15:55 ET bar), any missing window bar, zero-volume window.
- Test 1: OLS r_last = a + b*r_first (homoskedastic t-stat, two-sided).
- Test 2: trade every eligible day in sign(r_first) direction, enter open of the
  15:30 bar, exit close of the 15:55 bar, 5bp/side costs; gross+net+breakeven.
- Test 3: 10 frozen names, regression per name, gated on SPY Test1/Test2 clearing.

Usage: python3 intraday_momentum_2026-10-02.py <bars_json> [bars_json ...]
Outputs JSON to stdout (results), suitable for capture to
intraday_momentum_results_2026-10-02.json.
"""
import json, math, sys
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
COST_PER_SIDE = 0.0005
NAMES_10 = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "GOOGL", "AMD", "JPM", "XOM"]

FIRST_HM = ["09:30", "09:35", "09:40", "09:45", "09:50", "09:55"]
LAST_HM = ["15:30", "15:35", "15:40", "15:45", "15:50", "15:55"]

def et_dt(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ET)

def load_sessions(path):
    with open(path) as f:
        bars = json.load(f)
    sess = {}
    for b in bars:
        d = et_dt(b["t"])
        sess.setdefault(d.date().isoformat(), {})[d.strftime("%H:%M")] = b
    return bars, sess

def eligible_days(sess):
    """Return list of (date, daymap) passing frozen exclusions; record reasons."""
    ok, reasons = [], {"missing_bars": 0, "zero_volume": 0}
    for day in sorted(sess):
        m = sess[day]
        if not all(h in m for h in FIRST_HM + LAST_HM):
            reasons["missing_bars"] += 1
            continue
        v_first = sum(m[h].get("v") or 0 for h in FIRST_HM)
        v_last = sum(m[h].get("v") or 0 for h in LAST_HM)
        if v_first == 0 or v_last == 0:
            reasons["zero_volume"] += 1
            continue
        ok.append((day, m))
    return ok, reasons

def day_returns(m):
    rf = m["09:55"]["c"] / m["09:30"]["o"] - 1.0
    rl = m["15:55"]["c"] / m["15:30"]["o"] - 1.0
    return rf, rl

def ols_beta_t(xs, ys):
    """OLS y = a + b x; returns (beta, se_beta, t, r2, n). Homoskedastic SEs."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = sxy / sxx if sxx else float("nan")
    alpha = my - beta * mx
    resid = [y - (alpha + beta * x) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in resid)
    dof = n - 2
    sigma2 = sse / dof if dof > 0 else float("nan")
    se_beta = math.sqrt(sigma2 / sxx) if sxx and sigma2 >= 0 else float("nan")
    t = beta / se_beta if se_beta else float("nan")
    sst = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - sse / sst if sst else float("nan")
    return {"beta": beta, "t": t, "r2": r2, "n": n, "alpha": alpha}

def max_drawdown(curve):
    peak = curve[0]
    dd = 0.0
    for v in curve:
        peak = max(peak, v)
        dd = min(dd, v - peak)
    return -dd

def test1(rf, rl):
    return ols_beta_t(rf, rl)

def test2(days_rf, m_list):
    """Tradable: direction sign(r_first), enter 15:30 bar open, exit 15:55 bar close."""
    gross = []
    skipped_zero = 0
    for rf, m in zip(days_rf, m_list):
        if rf > 0:
            d = 1.0
        elif rf < 0:
            d = -1.0
        else:
            skipped_zero += 1
            continue
        px_in = m["15:30"]["o"]
        px_out = m["15:55"]["c"]
        gross.append(d * (px_out / px_in - 1.0))
    n = len(gross)
    net = [g - 2 * COST_PER_SIDE for g in gross]
    mean_net = sum(net) / n if n else float("nan")
    mean_gross = sum(gross) / n if n else float("nan")
    sd_net = math.sqrt(sum((x - mean_net) ** 2 for x in net) / (n - 1)) if n > 1 else float("nan")
    t_net = mean_net / (sd_net / math.sqrt(n)) if n and sd_net else float("nan")
    cum = [0.0]
    for x in net:
        cum.append(cum[-1] + x)
    return {
        "n_trades": n,
        "skipped_rf_zero": skipped_zero,
        "hit_rate_gross": sum(1 for g in gross if g > 0) / n if n else float("nan"),
        "hit_rate_net": sum(1 for x in net if x > 0) / n if n else float("nan"),
        "mean_gross_per_trade": mean_gross,
        "mean_net_per_trade": mean_net,
        "t_net_vs_zero": t_net,
        "cum_net_total": cum[-1],
        "max_drawdown_cum_net": max_drawdown(cum),
        "breakeven_cost_per_side": mean_gross / 2 if n else float("nan"),
        "cost_per_side_applied": COST_PER_SIDE,
    }

def analyze_symbol(path):
    bars, sess = load_sessions(path)
    all_dates = sorted(sess)
    ok, reasons = eligible_days(sess)
    rf, rl, maps = [], [], []
    for day, m in ok:
        f, l = day_returns(m)
        rf.append(f); rl.append(l); maps.append(m)
    t1 = test1(rf, rl) if len(rf) >= 30 else {"beta": float("nan"), "t": float("nan"), "r2": float("nan"), "n": len(rf)}
    t2 = test2(rf, maps)
    return {
        "n_bars": len(bars),
        "sessions_total": len(all_dates),
        "realized_first_session": all_dates[0],
        "realized_last_session": all_dates[-1],
        "eligible_days": len(ok),
        "exclusion_reasons": reasons,
        "test1_regression": t1,
        "test2_tradable": t2,
    }

def main(paths):
    out = {"instruments": {}, "test3_gate": None}
    for path in paths:
        sym = path.split("/")[-1].split("_")[0].upper()
        out["instruments"][sym] = analyze_symbol(path)
    spy = out["instruments"].get("SPY")
    if spy:
        t1 = spy["test1_regression"]
        t2 = spy["test2_tradable"]
        test1_clears = (t1["beta"] or 0) > 0 and (t1["t"] or 0) > 2.0
        test2_clears = (t2["mean_net_per_trade"] or 0) > 0 and (t2["t_net_vs_zero"] or 0) > 2.0
        out["test3_gate"] = {
            "test1_clears_on_spy": test1_clears,
            "test2_clears_on_spy": test2_clears,
            "gate_open": test1_clears or test2_clears,
            "t1_beta": t1["beta"], "t1_t": t1["t"], "t1_n": t1["n"],
            "t2_mean_net": t2["mean_net_per_trade"], "t2_t": t2["t_net_vs_zero"],
        }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main(sys.argv[1:])
