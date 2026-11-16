"""PRZM print-tape bridge (CLEAR-THE-BOARD-20261114, WS3).

Builds the signed SPY options print tape the frozen PRZM recreation
spec (PRZM-RECREATION-SPEC-2026-10-29) consumes as
ctx.extra["przm_prints"], from REAL prints: Alpaca v1beta1 options
trades (the same source the morgue tape engine scores daily,
morgue/tape_card.py) plus latest quotes per traded contract
(feed=indicative, the account's served tier).

Per-print fields, each with its provenance:
  t, price, size   the trade itself (Alpaca v1beta1 options trades)
  is_call, strike  parsed from the print's OCC symbol
  sweep            trade conditions against the OPRA sweep codes
                   {S, b, d} (Alpaca's published condition table;
                   the morgue tape.py SWEEP_CODES carry the same set)
  bull, bought_at_ask, mid
                   side classified against the contract's latest
                   quote by the published Quant Data sentiment rule
                   the morgue tape carries (ask-side call / bid-side
                   put bullish; ask-side put / bid-side call bearish;
                   mid neutral). CAVEAT, the tape card's own: latest
                   quotes are not point-in-time, so some prints
                   misclassify; mid/unknown stay neutral and the
                   spec's weight filter sets them aside itself.
  delta            computed by the FROZEN SPEC'S OWN bs_delta
                   (sleeves/przm_zero.py) at the IV inverted from
                   the contract's quote mid where it inverts
                   cleanly; where it does not, iv=None and the
                   spec's own authored fallback (0.16) governs.
                   delta_source / iv_source stamp which happened.
  otm_frac         |strike - spot| / spot at the session spot.
  opening, closing NOT observable in the trade feed: the keys are
                   omitted, never fabricated (the spec reads them
                   with .get(), so absence = no multiplier).

Nothing here invents a print, a side, or a delta: a print whose
quote is absent keeps bull=None (weight 0 downstream) and its
delta still computes from the spec formula at the fallback IV.
"""
from __future__ import annotations

import math
import urllib.parse
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
DATA_URL = "https://data.alpaca.markets"

SWEEP_CODES = {"S", "b", "d"}
ASK_SIDES = {"ask", "above_ask"}
BID_SIDES = {"bid", "below_bid"}


def classify_side(price, bid, ask):
    """Coarse side from NBBO, then the 1.005x reclassification
    (InsiderFinance rule as recovered in morgue/tape.py)."""
    if not bid or not ask or ask <= 0:
        return "unknown"
    if price >= ask:
        return "above_ask" if price >= 1.005 * ask else "ask"
    if price <= bid:
        return "below_bid" if price <= bid / 1.005 else "bid"
    mid = (bid + ask) / 2.0
    if price == mid:
        return "mid"
    return "ask" if (ask - price) < (price - bid) else "bid"


def sentiment_sign(side, is_call):
    """Quant Data published rule (morgue/tape.py sentiment):
    ask-side call / bid-side put bullish (+1); ask-side put /
    bid-side call bearish (-1); mid/unknown neutral (None)."""
    if side in ASK_SIDES:
        return 1 if is_call else -1
    if side in BID_SIDES:
        return -1 if is_call else 1
    return None


def _occ_fields(occ):
    """OCC -> (is_call, expiry_date, strike) or None (parsed from
    the end, any root length)."""
    try:
        cp, digits, yymmdd = occ[-9], occ[-8:], occ[-15:-9]
        if cp not in ("C", "P") or not digits.isdigit() or not yymmdd.isdigit():
            return None
        from datetime import date
        expiry = date(2000 + int(yymmdd[:2]), int(yymmdd[2:4]),
                      int(yymmdd[4:6]))
        return (cp == "C"), expiry, int(digits) / 1000.0
    except (ValueError, IndexError):
        return None


def _invert_iv(price, spot, strike, t_years, is_call, bs_price):
    """Bisection IV inversion on the desk's Black-Scholes pricer;
    None when the quote mid does not invert cleanly."""
    if price is None or price <= 0 or t_years <= 0:
        return None
    lo, hi = 0.01, 5.0
    try:
        p_lo = bs_price(spot, strike, t_years, lo, is_call)
        p_hi = bs_price(spot, strike, t_years, hi, is_call)
    except Exception:
        return None
    if not (p_lo - 1e-9 <= price <= p_hi + 1e-9):
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if bs_price(spot, strike, t_years, mid, is_call) < price:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def build_prints(trades, quotes, spot, bs_price, bs_delta):
    """trades: [{symbol, t, p, s, c}] raw v1beta1 rows; quotes:
    {occ: (bid, ask)}; spot: session spot for the underlying.
    Returns spec-shaped print dicts (see module docstring)."""
    out = []
    for row in trades or []:
        occ = row.get("symbol") or ""
        fields = _occ_fields(occ)
        if fields is None:
            continue
        is_call, expiry, strike = fields
        try:
            t = datetime.fromisoformat(
                str(row["t"]).replace("Z", "+00:00")).timestamp()
            price = float(row["p"])
            size = float(row["s"])
        except (KeyError, TypeError, ValueError):
            continue
        conds = row.get("c") or []
        if isinstance(conds, str):
            conds = [conds]
        bid, ask = (quotes or {}).get(occ, (None, None))
        side = classify_side(price, bid, ask)
        bull = sentiment_sign(side, is_call)
        # time to the expiry's 16:00 ET close, in years
        close_dt = datetime.combine(expiry, dtime(16, 0), tzinfo=ET)
        t_years = max((close_dt.timestamp() - t) / (365.25 * 86400.0),
                      1e-7)
        iv = None
        iv_source = "spec_default"
        if bid and ask and ask > bid > 0:
            iv = _invert_iv((bid + ask) / 2.0, spot, strike, t_years,
                            is_call, bs_price)
            if iv is not None:
                iv_source = "quote_mid_inverted"
        delta = bs_delta(spot, strike, t_years, iv, is_call)
        out.append({
            "t": t, "bull": bull, "delta": delta, "price": price,
            "size": size, "is_call": is_call,
            "bought_at_ask": side in ASK_SIDES,
            "mid": side == "mid",
            "otm_frac": (abs(strike - spot) / spot) if spot else 0.0,
            "sweep": any(c in SWEEP_CODES for c in conds),
            "delta_source": "spec_bs_delta_v1",
            "iv_source": iv_source,
            "symbol": occ,
        })
    out.sort(key=lambda p: p["t"])
    return out


def fetch_trades_since(occs, start_iso, env, get_json, auth,
                       page_cap=8):
    """Bounded v1beta1 options-trades pull for the given OCCs from
    start_iso (mirrors morgue/tape_card.fetch_trades' request
    shape). Returns (rows, capped_batches)."""
    rows, capped = [], 0
    for i in range(0, len(occs), 200):
        batch = occs[i:i + 200]
        token, pages = None, 0
        while True:
            params = {"symbols": ",".join(batch), "start": start_iso,
                      "limit": 10000, "sort": "asc"}
            if token:
                params["page_token"] = token
            doc = get_json(f"{DATA_URL}/v1beta1/options/trades?"
                           + urllib.parse.urlencode(params),
                           headers=auth(env)) or {}
            for occ, rs in (doc.get("trades") or {}).items():
                for r in rs or []:
                    rows.append({"symbol": occ, **r})
            pages += 1
            token = doc.get("next_page_token")
            if not token:
                break
            if pages >= page_cap:
                capped += 1
                break
    return rows, capped
