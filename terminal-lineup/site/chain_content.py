#!/usr/bin/env python3
"""Chain content: measured OI/volume and MODELLED implied volatility.

One source of truth for the content half of the chain cure
(G5/G4/G10, 2026-10-29):

- Open interest is MEASURED: Alpaca's options contracts API carries
  per-contract open_interest with its own open_interest_date. The
  helper here never relabels it: the date travels with the value.
- Volume is MEASURED where the source carries it: Alpaca indicative
  snapshots carry a daily bar whose volume is that contract's
  traded volume for the session so far.
- Implied volatility is MODELLED, never measured: Alpaca indicative
  snapshots/quotes carry no greeks and no IV (verified live
  2026-10-29: snapshot keys are dailyBar/latestQuote/latestTrade/
  minuteBar/prevDailyBar only). IV here is inverted from the
  indicative quote midpoint with textbook Black-Scholes under the
  stated assumptions, and every stored or displayed figure built
  from it must carry the MODELLED label:

    rate r = 0.045 (flat, continuously compounded)
    dividend yield q by underlying: SPY 0.013, QQQ 0.005,
      IWM 0.014, anything else 0.0
    expiry at 21:00 UTC on the expiry date
    T = seconds to expiry / (365 * 86400), floored at one hour
    European exercise, no early exercise, no discrete dividends

  A midpoint at or below intrinsic value, a one-sided or crossed
  quote, or an inversion landing at/over the 500 percent ceiling
  yields no IV (None), never a fabricated number.

This module is pure except for the fetch helpers at the bottom,
which take an api_request callable so tests never touch a network.
"""

import math
import re
from datetime import date, datetime, time as dtime, timezone

RATE = 0.045
DIV_YIELD = {"SPY": 0.013, "QQQ": 0.005, "IWM": 0.014}
IV_CEILING = 5.0
ENRICH_EXPIRY_DAYS = 120        # contracts expiring within this
                                # window of the snapshot day are
                                # enriched; the rest stay layout-only
IV_MONEYNESS = (0.75, 1.25)     # IV inverted only inside this
                                # strike/spot band (skew/EM/pin band)

OCC_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")

IV_BASIS = "MODELLED"
IV_MODEL_WORDS = (
    "MODELLED Black-Scholes inversion of the Alpaca indicative "
    "quote midpoint; r=0.045 flat; dividend yield SPY 0.013, "
    "QQQ 0.005, IWM 0.014, else 0.0; expiry 21:00 UTC; European, "
    "no early exercise")


# ---- OCC parsing -------------------------------------------------------
def parse_occ(occ):
    m = OCC_RE.match(occ or "")
    if not m:
        return None
    yy, mm, dd = int(m.group(2)[:2]), int(m.group(2)[2:4]), int(m.group(2)[4:6])
    return {"underlying": m.group(1),
            "expiry": date(2000 + yy, mm, dd).isoformat(),
            "side": "call" if m.group(3) == "C" else "put",
            "is_call": m.group(3) == "C",
            "strike": int(m.group(4)) / 1000.0}


# ---- Black-Scholes (textbook; assumptions in the header) ---------------
def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _d1(spot, strike, t, sigma, div):
    return (math.log(spot / strike)
            + (RATE - div + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))


def bs_price(spot, strike, t, sigma, is_call, div=0.0):
    if t <= 0 or sigma <= 0:
        return max(spot - strike, 0.0) if is_call else max(strike - spot, 0.0)
    a = _d1(spot, strike, t, sigma, div)
    b = a - sigma * math.sqrt(t)
    q, df = math.exp(-div * t), math.exp(-RATE * t)
    if is_call:
        return spot * q * _ncdf(a) - strike * df * _ncdf(b)
    return strike * df * _ncdf(-b) - spot * q * _ncdf(-a)


def t_years(expiry_iso, at_dt):
    """Years from at_dt (aware datetime) to 21:00 UTC on expiry,
    floored at one hour so an expiring-today contract still has a
    finite tenor after the close."""
    exp = datetime.combine(date.fromisoformat(expiry_iso),
                           dtime(21, 0), tzinfo=timezone.utc)
    secs = (exp - at_dt).total_seconds()
    return max(secs, 3600.0) / (365.0 * 86400.0)


def implied_vol(mid, spot, strike, t, is_call, div=0.0):
    """Invert Black-Scholes by bisection. None when the midpoint
    cannot be produced by any vol in (0, ceiling): at/below
    intrinsic, above the spot bound, or out of range."""
    if mid is None or spot <= 0 or strike <= 0 or t <= 0:
        return None
    intrinsic = (max(spot - strike, 0.0) if is_call
                 else max(strike - spot, 0.0))
    if mid <= intrinsic + 1e-9:
        return None
    lo, hi = 1e-4, IV_CEILING
    if not (bs_price(spot, strike, t, lo, is_call, div) - 1e-9
            <= mid
            <= bs_price(spot, strike, t, hi, is_call, div) + 1e-9):
        return None
    for _ in range(80):
        m = 0.5 * (lo + hi)
        if bs_price(spot, strike, t, m, is_call, div) < mid:
            lo = m
        else:
            hi = m
    out = 0.5 * (lo + hi)
    return out if out < IV_CEILING else None


def quote_mid(bid, ask):
    """Midpoint of a two-sided quote; None for one-sided, zero or
    crossed quotes (no honest midpoint exists)."""
    try:
        b, a = float(bid), float(ask)
    except (TypeError, ValueError):
        return None
    if b <= 0 or a <= 0 or a < b:
        return None
    return 0.5 * (b + a)


# ---- merging measured/modelled content into snapshot rows --------------
def merge_content(codes, oi_by_occ, volume_by_occ, iv_by_occ):
    """Rows in the consumer shape [occ, oi, volume, iv] plus a
    coverage count. Absent stays None, never a fabricated zero; an
    explicitly measured zero OI or volume stays zero."""
    rows = []
    cov = {"contracts": 0, "with_oi": 0, "with_volume": 0, "with_iv": 0}
    for code in sorted(codes):
        oi = (oi_by_occ or {}).get(code)
        vol = (volume_by_occ or {}).get(code)
        iv = (iv_by_occ or {}).get(code)
        rows.append([code, oi, vol, iv])
        cov["contracts"] += 1
        cov["with_oi"] += 1 if oi is not None else 0
        cov["with_volume"] += 1 if vol is not None else 0
        cov["with_iv"] += 1 if iv is not None else 0
    return rows, cov


def in_enrichment_window(occ, day_iso, spot):
    """True when a contract is inside the enrichment scope: expiry
    within ENRICH_EXPIRY_DAYS of the snapshot day. The IV band is
    applied separately by the caller (OI/volume cover the whole
    window; IV only the moneyness band)."""
    p = parse_occ(occ)
    if not p:
        return False
    d0 = date.fromisoformat(day_iso)
    d1 = date.fromisoformat(p["expiry"])
    return 0 <= (d1 - d0).days <= ENRICH_EXPIRY_DAYS


def in_iv_band(occ, spot):
    p = parse_occ(occ)
    if not p or not spot:
        return False
    return IV_MONEYNESS[0] <= p["strike"] / float(spot) <= IV_MONEYNESS[1]


# ---- derived figures (pure; used by Pin Watch and Expected Move) -------
def heaviest_strikes_by_expiry(rows):
    """{expiry: {strike, total_oi, call_oi, put_oi}}: the strike
    carrying the most open interest (calls + puts) per expiry,
    from snapshot rows [occ, oi, volume, iv]. Expiries with no
    measured OI at all are omitted, never zero-filled."""
    per = {}
    for occ, oi, _vol, _iv in rows:
        if oi is None:
            continue
        p = parse_occ(occ)
        if not p:
            continue
        slot = per.setdefault(p["expiry"], {})
        s = slot.setdefault(p["strike"], {"call": 0, "put": 0})
        s["call" if p["is_call"] else "put"] += oi
    out = {}
    for expiry, strikes in per.items():
        best_strike, best = None, None
        for strike, s in strikes.items():
            tot = s["call"] + s["put"]
            if best is None or tot > best[0]:
                best_strike, best = strike, (tot, s["call"], s["put"])
        if best is not None:
            out[expiry] = {"strike": best_strike, "total_oi": best[0],
                           "call_oi": best[1], "put_oi": best[2]}
    return out


def chain_expected_move(rows, spot, day_iso):
    """The priced move from the freshest chain content: for the
    nearest expiry after the snapshot day, the at-the-money
    strike's MODELLED IV (call/put average where both exist)
    turned into a one-standard-deviation move, spot * IV * sqrt(T)
    with T to that expiry from the snapshot day's close (21:00 UTC
    anchor on the snapshot day). Returns None when no ATM IV is on
    record. The IV is modelled, so the move is labelled modelled
    by the caller."""
    by_expiry = {}
    for occ, _oi, _vol, iv in rows:
        if iv is None:
            continue
        p = parse_occ(occ)
        if p and p["expiry"] > day_iso:
            by_expiry.setdefault(p["expiry"], []).append((p, iv))
    if not by_expiry:
        return None
    expiry = min(by_expiry)
    cands = by_expiry[expiry]
    atm_strike = min((p["strike"] for p, _ in cands),
                     key=lambda k: abs(k - spot))
    ivs = [iv for p, iv in cands if p["strike"] == atm_strike]
    if not ivs:
        return None
    atm_iv = sum(ivs) / len(ivs)
    anchor = datetime.combine(date.fromisoformat(day_iso),
                              dtime(21, 0), tzinfo=timezone.utc)
    t = t_years(expiry, anchor)
    pts = float(spot) * atm_iv * math.sqrt(t)
    return {"expiry": expiry, "atm_strike": atm_strike,
            "atm_iv": round(atm_iv, 4), "iv_basis": IV_BASIS,
            "points": round(pts, 2),
            "pct": round(pts / float(spot) * 100.0, 2),
            "upper": round(float(spot) + pts, 2),
            "lower": round(float(spot) - pts, 2)}


def skew_pair(rows, spot, day_iso):
    """The skew figure Skew Lens needs, from snapshot rows: for
    the nearest expiry at least 7 days out, the MODELLED put IV
    at the strike closest to 10 percent below spot minus the
    MODELLED call IV at the strike closest to 10 percent above
    spot, each required inside the 9-11 percent band and carrying
    its side from the OCC code itself. None when no matched pair
    exists."""
    by_expiry = {}
    for occ, _oi, _vol, iv in rows:
        if iv is None:
            continue
        p = parse_occ(occ)
        if p:
            by_expiry.setdefault(p["expiry"], []).append((p, iv))
    for expiry in sorted(by_expiry):
        if (date.fromisoformat(expiry)
                - date.fromisoformat(day_iso)).days < 7:
            continue
        entries = by_expiry[expiry]
        puts = [(abs(p["strike"] - 0.90 * spot), p, iv)
                for p, iv in entries if not p["is_call"]]
        calls = [(abs(p["strike"] - 1.10 * spot), p, iv)
                 for p, iv in entries if p["is_call"]]
        if not puts or not calls:
            continue
        _, pp, piv = min(puts)
        _, cp, civ = min(calls)
        if not (0.09 <= abs(pp["strike"] / spot - 1.0) <= 0.11):
            continue
        if not (0.09 <= abs(cp["strike"] / spot - 1.0) <= 0.11):
            continue
        return {"expiry": expiry, "put_strike": pp["strike"],
                "put_iv": round(piv, 4), "call_strike": cp["strike"],
                "call_iv": round(civ, 4),
                "skew_points": round((piv - civ) * 100.0, 2),
                "iv_basis": IV_BASIS}
    return None
