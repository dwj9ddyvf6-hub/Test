"""Milkman 0DTE chain builder (CLEAR-THE-BOARD-20261114, WS3).

Builds the SPX/SPXW 0DTE chain payload mk_zerodte_spx consumes via
ctx.options_chain("SPX"), from REAL Alpaca indicative snapshots
(the account's served tier: real bid/ask, no greeks).

  spot   recovered from the chain itself by put-call parity:
         S = K*exp(-rT) + C_mid - P_mid per strike with both
         sides quoted, median across strikes (spot_source
         "put_call_parity_mid"). No external spot is invented.
  delta  COMPUTED per row, never copied: IV inverted from the
         row's own mid with the desk's call inversion
         (_implied_vol_call; a put's mid first converted by
         parity), delta = N(d1) for calls, N(d1)-1 for puts,
         stamped delta_source="bs_parity_indicative_v1". Rows
         whose mid does not invert keep delta None — the
         strategy's own fail-closed "no delta" path, exactly as
         authored. T is intraday (hours to the expiry's 16:00 ET
         close): the desk gamma convention (whole days, T<1d ->
         None) would void every 0DTE row by construction, so
         this builder uses the intraday T and says so.
  t      the quote's own timestamp (the strategy judges row
         freshness <= 180 s against it; stamping fetch time
         instead would fabricate freshness).

This is the sleeve's OWN producer payload (key
milkman_0dte_chain), deliberately NOT the shared options product:
the computed-delta question for the shared product (the gamma
pair) is a separate Triad decision, posed 2026-11-14.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
RISK_FREE = 0.04


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def parity_spot(pairs, t_years):
    """pairs: [(strike, call_mid, put_mid)] -> median parity spot
    or None."""
    vals = []
    for strike, c_mid, p_mid in pairs or []:
        if c_mid is None or p_mid is None:
            continue
        vals.append(strike * math.exp(-RISK_FREE * t_years)
                    + c_mid - p_mid)
    if not vals:
        return None
    vals.sort()
    n = len(vals)
    return vals[n // 2] if n % 2 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])


def build_chain(contracts, snapshots, underlying, expiry_iso, now):
    """contracts: Alpaca contract dicts for one expiry;
    snapshots: {OCC: raw snapshot}; returns the authored payload
    {underlying, expiry, fetched_at, spot, spot_source, chains,
    quotes} or None when no two-sided pair supports a parity
    spot."""
    from .producers import _implied_vol_call

    expiry_close = datetime.combine(
        datetime.fromisoformat(expiry_iso).date(), dtime(16, 0),
        tzinfo=ET)
    t_years = max((expiry_close - now).total_seconds(), 60.0) \
        / (365.25 * 86400.0)

    raw = {}
    for c in contracts or []:
        sym = c.get("symbol")
        snap = (snapshots or {}).get(sym) or {}
        lq = snap.get("latestQuote") or {}
        try:
            bid, ask = float(lq["bp"]), float(lq["ap"])
            strike = float(c["strike_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if bid < 0 or ask <= 0 or ask < bid:
            continue
        right = "call" if str(c.get("type")) == "call" else "put"
        raw[sym] = {"symbol": sym, "root": underlying,
                    "expiration": expiry_iso, "type": right,
                    "strike": strike, "bid": bid, "ask": ask,
                    "t": str(lq.get("t") or "")}
    by_strike = {}
    for row in raw.values():
        by_strike.setdefault(row["strike"], {})[row["type"]] = row
    pairs = [(k, v["call"]["bid"] + v["call"]["ask"],
              v["put"]["bid"] + v["put"]["ask"])
             for k, v in by_strike.items()
             if "call" in v and "put" in v]
    pairs = [(k, c / 2.0, p / 2.0) for k, c, p in pairs]
    spot = parity_spot(pairs, t_years)
    if spot is None:
        return None
    rows, quotes = [], {}
    for row in raw.values():
        mid = (row["bid"] + row["ask"]) / 2.0
        px = mid
        if row["type"] == "put":
            px = mid + spot - row["strike"] * math.exp(
                -RISK_FREE * t_years)
        iv = _implied_vol_call(px, spot, row["strike"], t_years) \
            if px > 0 else None
        delta = None
        if iv is not None:
            d1 = (math.log(spot / row["strike"])
                  + (RISK_FREE + 0.5 * iv * iv) * t_years) \
                / (iv * math.sqrt(t_years))
            delta = _ncdf(d1) if row["type"] == "call" \
                else _ncdf(d1) - 1.0
        out = dict(row)
        out["delta"] = delta
        if delta is not None:
            out["delta_source"] = "bs_parity_indicative_v1"
        rows.append(out)
        quotes[row["symbol"]] = {"bid": row["bid"], "ask": row["ask"]}
    rows.sort(key=lambda r: (r["strike"], r["type"]))
    return {"underlying": underlying, "expiry": expiry_iso,
            "fetched_at": now.isoformat(), "spot": spot,
            "spot_source": "put_call_parity_mid",
            "chains": {underlying: rows}, "quotes": quotes}
