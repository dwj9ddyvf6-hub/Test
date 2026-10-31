#!/usr/bin/env python3
"""Static GEX single convention cross check (DEEP-PASS 3.2 item 13).

Ausar's Static GEX Lab (L04), adapted: one transparent convention,
computed from our own TastyTrade chain snapshots, published beside
the modelled inventory surfaces (the Gamma Ladder and Engines 8
and 11) as an independent cross check. The two families are
complements, not duplicates: the modelled family carries its own
sign convention machinery; this surface carries exactly one
stated convention and nothing else.

The convention, stated in full:
- Black-Scholes gamma per contract from spot, strike, time to
  expiry and that contract's implied volatility on the snapshot.
  Time to expiry follows the chain store's own convention
  (chain_content.t_years: expiry at 21:00 UTC on the expiry date,
  floored at one hour, counted from the end of the snapshot day).
  Rate 0.045 flat; dividend yield by underlying from
  chain_content.DIV_YIELD; multiplier 100.
- Dollar GEX per contract is gamma * sign * open interest *
  multiplier * spot^2 * 0.01, with calls positive and puts
  negative. That sign choice is the whole convention: it treats
  call open interest as positive exposure and put open interest
  as negative exposure, with no dealer inventory modelling.
- Call wall: the strike with the largest total call GEX. Put
  wall: the strike with the largest absolute total put GEX.
- Flip level: the spot where total GEX crosses zero, found on a
  101 point spot grid over plus or minus GRID_PCT percent of
  spot, linear interpolation between grid points, the crossing
  nearest spot. No crossing inside the grid means no flip level
  is published (null), never an extrapolated one.

The constant IV assumption, and its cure: on the grid, every
contract's implied volatility is held CONSTANT at its snapshot
value while spot moves. Gamma profiles are IV sensitive near the
money, so the flip level carries an IV sensitivity band: the
grid is recomputed with every IV scaled by IV_BAND_LOW (0.80)
and IV_BAND_HIGH (1.25), and the band is the range of the three
flip levels (central, low IV, high IV). Where a band leg finds
no crossing, that leg is null and the band is published over
the legs that exist, with the missing leg named.

Input discipline: a contract counts only when both its open
interest and its implied volatility are on the snapshot. A
contract missing either is excluded and counted, never zero
filled and never given an invented IV. The snapshot's IV is
itself MODELLED (Black-Scholes inversion of the indicative
quote midpoint, per chain_content.py); that basis travels with
every figure this module produces. Coverage counts are part of
the output, in the same weight as the figures.
"""

import math
from datetime import date, datetime, time as dtime, timezone

import chain_content as _cc

RATE = _cc.RATE
MULTIPLIER = 100
GRID_POINTS = 101
GRID_PCT = 10.0
IV_BAND_LOW = 0.80
IV_BAND_HIGH = 1.25


def bs_gamma(spot, strike, t_years, sigma, div=0.0):
    """Textbook Black-Scholes gamma (same for calls and puts)."""
    if spot <= 0 or strike <= 0 or t_years <= 0 or sigma <= 0:
        return None
    d1 = (math.log(spot / strike)
          + (RATE - div + 0.5 * sigma * sigma) * t_years) \
        / (sigma * math.sqrt(t_years))
    npdf = math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    return math.exp(-div * t_years) * npdf / (spot * sigma * math.sqrt(t_years))


def _contracts(rows, anchor):
    """Usable contracts from snapshot rows [occ, oi, volume, iv],
    plus coverage counts. Missing OI or IV excludes, never fills.
    Time to expiry is computed once per contract here: the grid
    search reuses it at every spot level, and it does not depend
    on the spot level."""
    usable, cov = [], {"contracts": 0, "counted": 0,
                       "excluded_no_oi": 0, "excluded_no_iv": 0}
    for occ, oi, _vol, iv in rows:
        cov["contracts"] += 1
        p = _cc.parse_occ(occ)
        if p is None:
            continue
        if oi is None:
            cov["excluded_no_oi"] += 1
            continue
        if iv is None:
            cov["excluded_no_iv"] += 1
            continue
        usable.append((p, float(oi), float(iv),
                       _cc.t_years(p["expiry"], anchor)))
        cov["counted"] += 1
    return usable, cov


def _gex_at(usable, spot_level, div, iv_scale=1.0):
    """Total dollar GEX at one spot level, IV held constant
    (scaled by iv_scale for the sensitivity legs)."""
    total = 0.0
    for p, oi, iv, t in usable:
        g = bs_gamma(spot_level, p["strike"], t, iv * iv_scale, div)
        if g is None:
            continue
        sign = 1.0 if p["is_call"] else -1.0
        total += g * sign * oi * MULTIPLIER * spot_level ** 2 * 0.01
    return total


def _flip_on_grid(usable, spot, div, iv_scale=1.0):
    """Zero crossing of total GEX nearest spot on the 101 point
    grid, linear interpolation; None when the grid never crosses."""
    lo = spot * (1.0 - GRID_PCT / 100.0)
    hi = spot * (1.0 + GRID_PCT / 100.0)
    prev_s, prev_v = None, None
    crossings = []
    for i in range(GRID_POINTS):
        s = lo + (hi - lo) * i / (GRID_POINTS - 1)
        v = _gex_at(usable, s, div, iv_scale)
        if prev_v is not None and (prev_v == 0.0 or v == 0.0
                                   or (prev_v < 0) != (v < 0)):
            if v == prev_v:
                crossings.append(s)
            else:
                frac = prev_v / (prev_v - v)
                crossings.append(prev_s + frac * (s - prev_s))
        prev_s, prev_v = s, v
    if not crossings:
        return None
    return min(crossings, key=lambda c: abs(c - spot))


def static_gex_snapshot(rows, spot, day_iso, underlying):
    """The full static GEX cross check for one snapshot.

    rows: snapshot rows [occ, oi, volume, iv]; spot: the recorded
    price level; day_iso: the snapshot day; underlying: for the
    dividend yield. Returns a dict whose figures are null (with
    the reason carried in coverage) when nothing can be counted.
    """
    div = _cc.DIV_YIELD.get(underlying, 0.0)
    anchor = datetime.combine(date.fromisoformat(day_iso),
                               dtime(21, 0), tzinfo=timezone.utc)
    usable, cov = _contracts(rows, anchor)
    out = {"underlying": underlying, "day": day_iso, "spot": spot,
           "coverage": cov, "net_gex": None, "call_wall": None,
           "put_wall": None, "flip": None,
           "flip_iv_band": None, "per_strike": []}
    if not usable or not spot or spot <= 0:
        return out
    per_strike = {}
    for p, oi, iv, t in usable:
        g = bs_gamma(float(spot), p["strike"], t, iv, div)
        if g is None:
            continue
        sign = 1.0 if p["is_call"] else -1.0
        dollar = g * sign * oi * MULTIPLIER * float(spot) ** 2 * 0.01
        slot = per_strike.setdefault(p["strike"],
                                     {"strike": p["strike"],
                                      "call_gex": 0.0, "put_gex": 0.0})
        slot["call_gex" if p["is_call"] else "put_gex"] += dollar
    strikes = sorted(per_strike.values(), key=lambda s: s["strike"])
    for s in strikes:
        s["net_gex"] = s["call_gex"] + s["put_gex"]
        s["call_gex"] = round(s["call_gex"], 2)
        s["put_gex"] = round(s["put_gex"], 2)
        s["net_gex"] = round(s["net_gex"], 2)
    out["per_strike"] = strikes
    out["net_gex"] = round(sum(s["net_gex"] for s in strikes), 2)
    if strikes:
        out["call_wall"] = max(strikes, key=lambda s: s["call_gex"])["strike"]
        out["put_wall"] = max(
            strikes, key=lambda s: abs(s["put_gex"]))["strike"]
    flip = _flip_on_grid(usable, float(spot), div, 1.0)
    flip_lo = _flip_on_grid(usable, float(spot), div, IV_BAND_LOW)
    flip_hi = _flip_on_grid(usable, float(spot), div, IV_BAND_HIGH)
    out["flip"] = round(flip, 4) if flip is not None else None
    legs = {"central": out["flip"],
            "iv_x0.80": round(flip_lo, 4) if flip_lo is not None else None,
            "iv_x1.25": round(flip_hi, 4) if flip_hi is not None else None}
    present = [v for v in legs.values() if v is not None]
    out["flip_iv_band"] = {
        "legs": legs,
        "low": min(present) if present else None,
        "high": max(present) if present else None,
        "missing_legs": [k for k, v in legs.items() if v is None],
    }
    return out
