"""Chain analytics on one underlying's contract rows: pure functions, no I/O, no network (REA work package 5).

A row is {"strike","expiry","is_call","oi","gamma","iv","t"} (t in years) plus an optional "volume". rows_of() builds them
from the Map's own chain and snapshots, so gamma is the Map's gamma (the snapshot's, else Black-Scholes on the contract's IV).

  dex_profile      delta exposure by strike, total, and the 0-5 balance score (InsiderFinance A30)
  vex_profile      vanna exposure (Bullflow A48), charm_profile the delta decay a day brings
  max_pain         the strike that minimises the open interest's intrinsic value at an expiry (Quant Data A56)
  key_strikes      key gamma strike (most total gamma), key delta strike, anchor strike (most |net| gamma; B187, CX-sg-2)
  g_coordinate     call share of the chain's convexity, the fifth state coordinate (SqueezeMetrics A107)
  iv_surface_summary  ATM IV by expiry, the 30/60-day slope, 25-delta risk reversal, 15-delta strangle, 25-delta butterfly
  prob_touch_lognormal, finish_above, pop_from_breakevens  driftless-lognormal chances (OptionStrat A73, A74)

Signs follow the Map's convention (calls +, puts -, the vendor's published assumption about dealer inventory); a number that
cannot be computed is None with the reason beside it, never a constant."""
import math

from . import bs

DEX_SCALE = 100.0
FIVE = 5.0


def rows_of(chain, snaps, spot, underlying, now):
    """the Map's chain rows with gamma (snapshot, else Black-Scholes on the IV), iv, t and the snapshot volume; a contract
    with no gamma is dropped, as gex_profile drops it"""
    from . import map_gex as mg
    div = mg.DIV_YIELD.get(underlying, 0.0)
    out = []
    for c in chain:
        sn = snaps.get(c["symbol"]) or {}
        g, iv = sn.get("gamma"), sn.get("iv")
        t = mg.t_years(c["expiry"], now)
        if g is None and iv and 0 < iv <= 5.0:
            g = bs.gamma(spot, c["strike"], t, iv, bs.RATE, div)
        if g is None or not math.isfinite(g):
            continue
        out.append({**c, "gamma": float(g), "iv": iv, "t": t, "volume": sn.get("volume"), "div": div})
    return out


def _delta(r, spot):
    if not r.get("iv") or r["iv"] <= 0:
        return None
    return bs.delta(spot, r["strike"], r["t"], r["iv"], r["is_call"], bs.RATE, r.get("div", 0.0))


def dex_profile(rows, spot):
    """delta exposure per strike = sum(delta x OI x 100 x spot) (calls positive, puts negative as their deltas are), the
    total, and the balance score 0-5 = 5 x call share of absolute delta exposure (5 all calls, 0 all puts, 2.5 even).
    None-valued with the reason when no contract carries an IV."""
    by, call_abs, put_abs, used = {}, 0.0, 0.0, 0
    for r in rows:
        d = _delta(r, spot)
        if d is None:
            continue
        v = d * r["oi"] * DEX_SCALE * spot
        by[r["strike"]] = by.get(r["strike"], 0.0) + v
        if r["is_call"]:
            call_abs += abs(v)
        else:
            put_abs += abs(v)
        used += 1
    if not used or call_abs + put_abs <= 0:
        return {"net": None, "by_strike": {}, "balance": None, "contracts_used": 0,
                "reason": "no contract carried an implied volatility"}
    return {"net": sum(by.values()), "by_strike": by, "balance": FIVE * call_abs / (call_abs + put_abs),
            "call_abs": call_abs, "put_abs": put_abs, "contracts_used": used}


def vex_profile(rows, spot):
    """vanna exposure per 1 volatility point = vanna x OI x 100 x spot x 0.01, calls +, puts - (the Map's convention)"""
    by, used = {}, 0
    for r in rows:
        if not r.get("iv") or r["iv"] <= 0:
            continue
        v = bs.vanna(spot, r["strike"], r["t"], r["iv"], bs.RATE, r.get("div", 0.0)) * r["oi"] * 100.0 * spot * 0.01
        v = v if r["is_call"] else -v
        by[r["strike"]] = by.get(r["strike"], 0.0) + v
        used += 1
    if not used:
        return {"net": None, "by_strike": {}, "contracts_used": 0, "reason": "no contract carried an implied volatility"}
    return {"net": sum(by.values()), "by_strike": by, "contracts_used": used}


def charm_profile(rows, spot):
    """delta-notional change per calendar day = charm / 365 x OI x 100 x spot, summed (calls and puts as their charms are)"""
    by, used = {}, 0
    for r in rows:
        if not r.get("iv") or r["iv"] <= 0:
            continue
        v = bs.charm(spot, r["strike"], r["t"], r["iv"], r["is_call"], bs.RATE, r.get("div", 0.0)) / 365.0 \
            * r["oi"] * 100.0 * spot
        by[r["strike"]] = by.get(r["strike"], 0.0) + v
        used += 1
    if not used:
        return {"net": None, "by_strike": {}, "contracts_used": 0, "reason": "no contract carried an implied volatility"}
    return {"net": sum(by.values()), "by_strike": by, "contracts_used": used}


def max_pain(rows, expiry=None):
    """{"strike","expiry","pain"} the strike minimising the sum over contracts of OI x intrinsic value at that settle, over
    the strikes listed at the expiry (the earliest expiry when none is named); ties go to the lower strike. None when the
    expiry has no open interest."""
    exps = sorted({r["expiry"] for r in rows if r["oi"] > 0})
    if not exps:
        return None
    expiry = expiry or exps[0]
    rs = [r for r in rows if r["expiry"] == expiry and r["oi"] > 0]
    if not rs:
        return None
    best = None
    for k in sorted({r["strike"] for r in rs}):
        pain = sum(r["oi"] * (max(k - r["strike"], 0.0) if r["is_call"] else max(r["strike"] - k, 0.0)) * 100.0
                   for r in rs)
        if best is None or pain < best[1]:
            best = (k, pain)
    return {"strike": best[0], "expiry": expiry, "pain": best[1]}


def key_strikes(rows, spot):
    """key gamma strike = most total gamma (|call| + |put| dollar gamma), anchor strike = most |net| gamma (B187: the
    call wall and the key strike can differ), key delta strike = most |delta exposure|. Each None without data."""
    from . import map_gex as mg
    tot, net = {}, {}
    for r in rows:
        v = mg.contract_gex(r["gamma"], r["oi"], spot, r["is_call"])
        tot[r["strike"]] = tot.get(r["strike"], 0.0) + abs(v)
        net[r["strike"]] = net.get(r["strike"], 0.0) + v
    dex = dex_profile(rows, spot)["by_strike"]

    def top(d):
        return max(sorted(d), key=lambda k: abs(d[k])) if d else None
    return {"key_gamma": top(tot), "anchor": top(net), "key_delta": top(dex)}


def g_coordinate(rows):
    """call share of the chain's convexity = sum(call gamma x OI) / sum(gamma x OI); None for a chain with none"""
    c = sum(r["gamma"] * r["oi"] for r in rows if r["is_call"])
    a = sum(r["gamma"] * r["oi"] for r in rows)
    return None if a <= 0 else c / a


# ---- the IV surface -----------------------------------------------------------------------------------------------------

def _interp(pts, x):
    """linear interpolation in sorted (x, y); None outside the span"""
    pts = sorted(pts)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    if len(pts) == 1 and pts[0][0] == x:
        return pts[0][1]
    return None


def _atm(rs, spot):
    by = {}
    for r in rs:
        by.setdefault(r["strike"], []).append(r["iv"])
    return _interp([(k, sum(v) / len(v)) for k, v in by.items()], spot)


def _delta_iv(rs, spot, is_call, target):
    pts = []
    for r in rs:
        if r["is_call"] != is_call:
            continue
        d = _delta(r, spot)
        if d is not None:
            pts.append((abs(d), r["iv"]))
    return _interp(pts, target)


def iv_surface_summary(rows, spot):
    """ATM IV per expiry (by calendar days), the 30- and 60-day ATM IV (linear in days between the bracketing expiries) and
    their slope, and for the expiry nearest 30 days the 25-delta risk reversal (call IV minus put IV), the 15-delta strangle
    (mean wing IV minus ATM) and the 25-delta butterfly. Fields are None where the chain cannot give them."""
    usable = [r for r in rows if r.get("iv") and 0 < r["iv"] <= 5.0]
    by_exp = {}
    for r in usable:
        by_exp.setdefault(round(r["t"] * 365.0), []).append(r)
    term = []
    for days in sorted(by_exp):
        a = _atm(by_exp[days], spot)
        if a is not None:
            term.append((days, a))
    iv30, iv60 = _interp(term, 30), _interp(term, 60)
    out = {"atm_by_expiry": [{"days": d, "atm_iv": v} for d, v in term], "iv30": iv30, "iv60": iv60,
           "slope_30_60": (None if iv30 is None or iv60 is None else iv60 - iv30), "rr25": None, "strangle15": None,
           "butterfly25": None, "wing_days": None}
    if term:
        d0 = min((d for d, _ in term), key=lambda d: abs(d - 30))
        rs = by_exp[d0]
        atm = dict(term)[d0]
        c25, p25 = _delta_iv(rs, spot, True, 0.25), _delta_iv(rs, spot, False, 0.25)
        c15, p15 = _delta_iv(rs, spot, True, 0.15), _delta_iv(rs, spot, False, 0.15)
        out["wing_days"] = d0
        if c25 is not None and p25 is not None:
            out["rr25"] = c25 - p25
            out["butterfly25"] = (c25 + p25) / 2.0 - atm
        if c15 is not None and p15 is not None:
            out["strangle15"] = (c15 + p15) / 2.0 - atm
    if not term:
        out["reason"] = "no expiry carried an at-the-money implied volatility"
    return out


def iv_rank(history, current, min_rows=60):
    """percent of the prior stored 30-day IVs at or below `current` (point in time: history is earlier rows only); None
    with the reason under min_rows"""
    h = [x for x in history if isinstance(x, (int, float)) and math.isfinite(x)]
    if current is None or len(h) < min_rows:
        return {"rank": None, "n": len(h), "reason": f"needs {min_rows} stored sessions, {len(h)} so far"}
    return {"rank": 100.0 * sum(1 for x in h if x <= current) / len(h), "n": len(h)}


# ---- chances under a driftless lognormal ----------------------------------------------------------------------------------

def _ncdf(x):
    return bs.ncdf(x)


def finish_above(spot, level, iv, days):
    """P(S_T > level) under a driftless lognormal (the model N(d2) with the -sigma^2/2 drift); None for bad inputs"""
    if spot <= 0 or level <= 0 or iv <= 0 or days <= 0:
        return None
    s = iv * math.sqrt(days / 365.0)
    return _ncdf((math.log(spot / level) - 0.5 * s * s) / s)


def prob_touch_lognormal(spot, target, iv, days):
    """P(the path touches `target` before `days`) for a driftless log-price (zero drift in the log): 2 x P(finish beyond)
    by the reflection principle, 1 when the target is the spot. A model beside the measured touch rate, never the headline."""
    if spot <= 0 or target <= 0 or iv <= 0 or days <= 0:
        return None
    if target == spot:
        return 1.0
    s = iv * math.sqrt(days / 365.0)
    z = abs(math.log(target / spot)) / s
    return min(1.0, 2.0 * (1.0 - _ncdf(z)))


def pop_from_breakevens(spot, breakevens, profit_above, iv, days):
    """probability of profit of a structure from its breakevens: `breakevens` ascending; `profit_above` True when the payoff
    is positive above the highest breakeven (a long call, a bull call spread), False when it is positive below the lowest
    (a long put); two breakevens with profit_above=None is a range structure profitable BETWEEN them (a condor), and a
    profit_above=None with two is the only supported form of that. None for no breakeven or bad inputs."""
    be = sorted(b for b in breakevens if b and b > 0)
    if not be:
        return None
    if profit_above is None:
        if len(be) != 2:
            return None
        lo, hi = finish_above(spot, be[0], iv, days), finish_above(spot, be[1], iv, days)
        return None if lo is None or hi is None else lo - hi
    p = finish_above(spot, be[-1] if profit_above else be[0], iv, days)
    if p is None:
        return None
    return p if profit_above else 1.0 - p
