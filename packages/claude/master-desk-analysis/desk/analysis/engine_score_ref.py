"""Reference scorer for the DEEP-2 analysis engine, as specified in out2/engine_spec.json (Addenda 2-19, 2-19b, 2-19c).

Pure Python: standard library and math only. It computes, for one stock on one screen date d:
  the own-volatility features (lrv1, lrv5, lrv22), ATR%, the 20-session median dollar volume and the tier,
  OW (same-session rank within tier, or the frozen fallback cutoff), the SEC-V veto probability P and the veto,
  the HAR volatility forecast, and momentum 6-1 with its within-tier percentile.

Conventions:
- Every window is a list ordered OLDEST FIRST that ENDS AT THE SCREEN DATE d (bars through d's close), all bars from
  the stock's current segment (no gap of more than 45 calendar days between consecutive bars).
- adj_* are split- and dividend-adjusted prices (Alpaca adjustment=all); raw_* are as traded (adjustment=raw).
- Sums are accumulated left to right in plain loops, as the research code does (Python's sum() would use compensated
  summation and differ in the last bits).

Self-test: python3 engine_score_ref.py engine_spec.json engine_vectors.csv
"""
import bisect
import csv
import datetime
import json
import math
import sys

TIERS = ("liquid", "small", "micro", "nano")


def load_spec(path):
    with open(path) as f:
        return json.load(f)


# ------------------------------------------------------------------ bars and segments
def in_one_segment(dates_iso):
    """True when no two consecutive dates (ISO strings, oldest first) are more than 45 calendar days apart"""
    ds = [datetime.date.fromisoformat(x) for x in dates_iso]
    return all((b - a).days <= 45 for a, b in zip(ds, ds[1:]))


def repair_bar(o, h, l, c):
    """the panel's bar repair: high = max(high, open, close), low = min(low, open, close)"""
    return max(h, o, c), min(l, o, c)


def log_returns(adj_close):
    return [math.log(adj_close[k] / adj_close[k - 1]) for k in range(1, len(adj_close))]


# ------------------------------------------------------------------ features
def own_vol(adj_close):
    """lrv1, lrv5, lrv22 at the last bar, from the last 23 adjusted closes (oldest first).
    lrv1 = log(max(|r_d|, 0.0005)); lrvW = 0.5 * log(max(var, 1e-8)) with var the one-pass sample variance (ddof 1)
    of the last W daily log returns r_k = log(c_k / c_{k-1})."""
    r = log_returns(adj_close)
    out = {"lrv1": math.log(max(abs(r[-1]), 5e-4))}
    for w in (5, 22):
        if len(r) < w:
            out["lrv%d" % w] = None
            continue
        s1 = 0.0
        s2 = 0.0
        for x in r[-w:]:
            s1 += x
            s2 += x * x
        var = (s2 - s1 * s1 / w) / (w - 1)
        out["lrv%d" % w] = 0.5 * math.log(max(var, 1e-8))
    return out


def atr_pct(adj_open, adj_high, adj_low, adj_close):
    """ATR% at the last bar: the simple mean of the last 14 true ranges divided by the last adjusted close.
    Needs the last 15 bars (oldest first): each true range uses the previous bar's close. Bars are repaired first."""
    hl = [repair_bar(o, h, l, c) for o, h, l, c in zip(adj_open, adj_high, adj_low, adj_close)]
    s = 0.0
    for k in range(len(adj_close) - 14, len(adj_close)):
        h, l = hl[k]
        p = adj_close[k - 1]
        s += max(h - l, max(abs(h - p), abs(l - p)))
    return s / 14.0 / adj_close[-1]


def dollar_volume_20(raw_close, raw_volume):
    """dv20: the median of raw close x raw volume over the last 20 bars (the mean of the two middle values)"""
    v = sorted(c * q for c, q in zip(raw_close[-20:], raw_volume[-20:]))
    return (v[9] + v[10]) / 2.0


def tier_of(raw_close_today, dv20):
    """liquid: raw close >= $5 and dv20 >= $20M; small: dv20 >= $5M; micro: $1M <= dv20 < $5M;
    nano: $0.1M <= dv20 < $1M; below $0.1M: not eligible (None)"""
    if raw_close_today >= 5 and dv20 >= 20e6:
        return "liquid"
    if dv20 >= 5e6:
        return "small"
    if dv20 >= 1e6:
        return "micro"
    if dv20 >= 1e5:
        return "nano"
    return None


def eligible(raw_close_today, raw_volume_today, dv20, bars_in_segment, atr_value):
    """screened on d: raw close >= $1, dv20 >= $100,000, at least 60 bars in the segment (d included), raw volume
    on d > 0, ATR (14-session mean true range) defined and > 0"""
    return (raw_close_today >= 1 and dv20 >= 1e5 and bars_in_segment >= 60 and raw_volume_today > 0
            and atr_value is not None and math.isfinite(atr_value) and atr_value > 0)


# ------------------------------------------------------------------ OW
def ow_same_session(lrv22_by_name, tier_by_name):
    """OW for every screened name of ONE session: 1 when the name's percentile rank of lrv22 within its tier is
    above 0.9, the percentile being the average rank of its ties divided by the tier's count of names with lrv22."""
    by_tier = {}
    for k, v in lrv22_by_name.items():
        if v is not None:
            by_tier.setdefault(tier_by_name[k], []).append((v, k))
    out = {}
    for items in by_tier.values():
        items.sort()
        n = len(items)
        i = 0
        while i < n:
            j = i
            while j + 1 < n and items[j + 1][0] == items[i][0]:
                j += 1
            pct = (i + 1 + j + 1) / 2.0 / n
            for q in range(i, j + 1):
                out[items[q][1]] = 1 if pct > 0.9 else 0
            i = j + 1
    return out


def ow_frozen(lrv22, tier, spec):
    """the fallback: 1 when lrv22 is above the tier's frozen cutoff"""
    return 1 if lrv22 > spec["ow"]["frozen_cutoffs"]["lrv22"][tier] else 0


# ------------------------------------------------------------------ the veto (SEC-V)
def veto_probability(ow, lrv1, lrv5, lrv22, tier, spec):
    """P(lose5) of the SEC-V logistic: z = intercept + sum_k coef_k * (x_k - mean_k) / sd_k; P = 1 / (1 + exp(-z))"""
    v = spec["veto"]
    x = {"OW": float(ow), "lrv1": lrv1, "lrv5": lrv5, "lrv22": lrv22,
         "tier_small": 1.0 if tier == "small" else 0.0, "tier_micro": 1.0 if tier == "micro" else 0.0,
         "tier_nano": 1.0 if tier == "nano" else 0.0}
    z = v["intercept_std"]
    for name in v["features"]:
        z += v["coef_std"][name] * ((x[name] - v["mean"][name]) / v["sd"][name])
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def veto(p, tier, spec):
    """(flag, applied): flag = P >= the tier's threshold; applied only in small, micro and nano (liquid is recorded,
    never vetoed)"""
    flag = p >= spec["veto"]["thresholds"][tier]
    return flag, (flag and tier in spec["veto"]["applies_to"])


# ------------------------------------------------------------------ HAR and TILT
def har_forecast(lrv1, lrv5, lrv22, log_atr_pct, tier, spec):
    """yhat = forecast of lrv20 (log sample std of the next 20 daily log returns); sigma_mean = exp(yhat + s2/2), the
    lognormal mean of RV20; var_mean = exp(2 yhat + 2 s2), the variance forecast the validation's QLIKE used"""
    h = spec["har"]["by_tier"][tier]
    c = h["coef"]
    y = h["intercept"]
    y += c["lrv1"] * lrv1
    y += c["lrv5"] * lrv5
    y += c["lrv22"] * lrv22
    y += c["log_atr_pct"] * log_atr_pct
    s2 = h["s2"]
    return {"yhat": y, "sigma_mean": math.exp(y + s2 / 2.0), "var_mean": math.exp(2.0 * y + 2.0 * s2)}


def momentum_6_1(adj_close):
    """ln(c[d-21] / c[d-126]); needs at least 127 adjusted closes ending at d (else None)"""
    if len(adj_close) < 127:
        return None
    return math.log(adj_close[-22] / adj_close[-127])


def share_at_or_below(values_by_name):
    """within ONE session x tier: each name's share of names (with a defined value) whose value is <= its own"""
    vals = sorted(v for v in values_by_name.values() if v is not None)
    n = len(vals)
    return {k: (bisect.bisect_right(vals, v) / n if v is not None else None) for k, v in values_by_name.items()}


# ------------------------------------------------------------------ one row from its windows
def score_row(adj_open, adj_high, adj_low, adj_close, raw_close, raw_volume, ow, spec):
    """windows: the last 23 adjusted bars and the last 20 raw bars, oldest first, ending at d; ow: the name's OW"""
    f = own_vol(adj_close[-23:])
    a = atr_pct(adj_open[-15:], adj_high[-15:], adj_low[-15:], adj_close[-15:])
    dv = dollar_volume_20(raw_close, raw_volume)
    t = tier_of(raw_close[-1], dv)
    out = {**f, "atr_pct": a, "log_atr_pct": math.log(a), "dv20": dv, "tier": t}
    if t is None:
        return out
    p = veto_probability(ow, f["lrv1"], f["lrv5"], f["lrv22"], t, spec)
    flag, applied = veto(p, t, spec)
    out.update({"p": p, "veto": flag, "veto_applied": applied})
    out.update(har_forecast(f["lrv1"], f["lrv5"], f["lrv22"], out["log_atr_pct"], t, spec))
    return out


def _floats(s):
    return [float(x) for x in s.split()]


def selftest(spec_path, vectors_path):
    spec = load_spec(spec_path)
    worst, bad, n = {}, 0, 0
    with open(vectors_path) as f:
        for row in csv.DictReader(f):
            n += 1
            got = score_row(_floats(row["adj_open"]), _floats(row["adj_high"]), _floats(row["adj_low"]),
                            _floats(row["adj_close"]), _floats(row["raw_close"]), _floats(row["raw_volume"]),
                            int(row["ow"]), spec)
            if got["tier"] != row["tier"]:
                bad += 1
                continue
            for k in ("lrv1", "lrv5", "lrv22", "atr_pct", "dv20", "p", "yhat", "sigma_mean", "var_mean"):
                d = abs(got[k] - float(row[k])) / max(1.0, abs(float(row[k])))
                worst[k] = max(worst.get(k, 0.0), d)
            if str(got["veto"]) != row["veto"] or str(got["veto_applied"]) != row["veto_applied"]:
                bad += 1
            if ow_frozen(got["lrv22"], got["tier"], spec) != int(row["ow_frozen"]):
                bad += 1
    print("rows %d, mismatched tier / veto / OW_frozen: %d; max relative differences: %s" % (n, bad, worst))
    return bad == 0 and all(v < 1e-9 for v in worst.values())


if __name__ == "__main__":
    ok = selftest(sys.argv[1], sys.argv[2])
    print("SELFTEST PASS" if ok else "SELFTEST FAIL")
    sys.exit(0 if ok else 1)
