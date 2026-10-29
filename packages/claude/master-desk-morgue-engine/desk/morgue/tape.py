"""Layer 1 / THE TAPE — per-print flow scoring (Morgue Engine Slice 2).

Components, each stamped with its source and evidence grade:

- Heat Score + Unusual / Top Position / Golden Sweep tags
  (InsiderFinance, RECOVERED-VERBATIM bucket table; the vendor's ninth
  component is hard-coded to zero in their code and is omitted).
- Side reclassification (InsiderFinance, RECOVERED-VERBATIM): Ask side
  upgrades to Above Ask at price >= 1.005 x ask; Bid side downgrades to
  Below Bid at price <= bid / 1.005. Directional sign flips for puts.
- Algo Score tallies (FlowAlgo, RECOVERED-VERBATIM tallies; the sum is
  the extraction's inference — the shipped code never sums them).
  Ratio tallies scale x10 (OURS choice, named in the FlowAlgo SPEC as
  an open question); the shipped sub-1 floor bug is NOT copied.
  Computed twice: on the vendor's buys-only intake population and on
  all prints, so the intake bias is measured, not hidden.
- Sentiment sign (Quant Data, PUBLISHED): ask-side call / bid-side put
  bullish; ask-side put / bid-side call bearish; mid neutral.

Feed condition codes (Alpaca's published OPRA table): S = Intermarket
Sweep Order; b/d = ISO auction/cross (also sweeps); f,g,h,i,j,l,m,t,u
= multi-leg; A,C,E,G = cancels (excluded from scoring).

Ported from Silicon's research/morgue-engine/tape.py (2026-10-27) with one addition, the opening-or-closing heuristic
(open_close): public option prints say nothing of whether a trade opened or closed a position, so the engine asserts only
what the day's own numbers force. The scorers are pure; tape_card.py feeds them.
"""
from __future__ import annotations

SWEEP_CODES = {"S", "b", "d"}
MULTILEG_CODES = {"f", "g", "h", "i", "j", "l", "m", "t", "u"}
CANCEL_CODES = {"A", "C", "E", "G"}
HIGH_HEAT = 15  # vendor's "High Heat" display threshold (SPEC choice)


def is_sweep(condition: str | None) -> bool:
    return (condition or "") in SWEEP_CODES


def is_multileg(condition: str | None) -> bool:
    return (condition or "") in MULTILEG_CODES


def is_cancel(condition: str | None) -> bool:
    return (condition or "") in CANCEL_CODES


def classify_side(price: float, bid: float | None, ask: float | None) -> str:
    """Coarse side from NBBO, then the 1.005x reclassification."""
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


ASK_SIDES = {"ask", "above_ask"}
BID_SIDES = {"bid", "below_bid"}


def directional_sign(side: str, is_call: bool) -> int:
    """InsiderFinance A24: ask +1 / bid -1, flipped for puts."""
    if side in ASK_SIDES:
        s = 1
    elif side in BID_SIDES:
        s = -1
    else:
        return 0
    return s if is_call else -s


def sentiment(side: str, is_call: bool) -> str:
    """Quant Data A54 table (extremes fold into ask/bid, natural reading)."""
    s = directional_sign(side, is_call)
    return "bullish" if s > 0 else "bearish" if s < 0 else "neutral"


def _bucket(ratio: float | None, steps: list[tuple[float, float]]) -> float:
    if ratio is None:
        return 0.0
    pts = 0.0
    for threshold, points in steps:
        if ratio >= threshold:
            pts = points
    return pts


def heat_score(p: dict, base: dict) -> tuple[float, dict]:
    """p: print dict (premium, dte, sweep, size, otm_pct, oi).
    base: {avg_premium, avg_size, avg_oi} trailing baselines (may be
    missing -> that component scores 0). Returns (score, components)."""
    comp = {}
    avg_prem = base.get("avg_premium")
    comp["premium"] = _bucket(
        (p["premium"] / avg_prem) if avg_prem else None,
        [(1, 1), (3, 2), (5, 3), (10, 4)])
    dte = p["dte"]
    comp["dte"] = 3.0 if dte < 35 else 2.0 if dte <= 98 else 1.0
    comp["sweep"] = 2.0 if p["sweep"] else 0.0
    comp["size"] = 2.0 if p["size"] >= 10_000 else 1.0 if p["size"] >= 5_000 else 0.0
    comp["otm"] = _bucket(p["otm_pct"],
                          [(2, 1), (8, 2), (16, 3), (22, 4), (30, 5)]) * 1.5
    oi = p.get("oi") or 0
    comp["size_oi"] = _bucket((p["size"] / oi) if oi else None,
                              [(0.75, 1), (1.5, 2), (2.5, 3), (5, 4)])
    avg_size = base.get("avg_size")
    comp["size_avg"] = _bucket(
        (p["size"] / avg_size) if avg_size else None,
        [(4, 1), (6, 2), (8, 3), (10, 4)])
    avg_oi = base.get("avg_oi")
    comp["oi_avg"] = _bucket((oi / avg_oi) if (oi and avg_oi) else None,
                             [(5, 1), (10, 2)])
    return sum(comp.values()), comp


def tags(p: dict) -> dict:
    top = bool(p.get("oi")) and p["size"] >= p["oi"]
    return {
        "unusual": p["otm_pct"] >= 10 and p["dte"] <= 35,
        "top_position": top,
        "golden_sweep": bool(p["sweep"] and top and p["premium"] >= 1_000_000),
    }


def _premium_tally(premium: float) -> int:
    bands = [5_000, 15_000, 30_000, 50_000, 75_000, 100_000, 150_000,
             250_000, 500_000, 1_000_000]
    t = 0
    for b in bands:
        if premium >= b:
            t += 1
    return t


def _ratio_tally(num: float, den: float | None) -> float:
    if not den:
        return 0.0
    if num >= den:
        return 10.0
    return round(num / den * 10.0, 2)


def _range_tally(spot: float, hi52: float | None, lo52: float | None) -> int:
    if not hi52 or not lo52 or spot <= 0:
        return 0
    dh = (hi52 - spot) / hi52 * 100.0
    for pct, pts in ((1, 10), (3, 8), (5, 6), (7, 4)):
        if dh <= pct:
            return pts
    dl = (spot - lo52) / lo52 * 100.0
    for pct, pts in ((1, 10), (2, 8), (3, 6), (4, 4)):
        if dl <= pct:
            return pts
    return 2


def algo_score(p: dict, ctx: dict) -> tuple[float, dict]:
    """ctx: {day_volume, oi, spot, hi52, lo52}. Returns (sum, tallies)."""
    tallies = {
        "premium": _premium_tally(p["premium"]),
        "vol_oi": _ratio_tally(ctx.get("day_volume") or 0, ctx.get("oi")),
        "qty_oi": _ratio_tally(p["size"], ctx.get("oi")),
        "qty_vol": _ratio_tally(p["size"], ctx.get("day_volume")),
        "type": 10 if p["sweep"] else 5,
        "range": _range_tally(ctx.get("spot") or 0, ctx.get("hi52"),
                              ctx.get("lo52")),
    }
    return sum(tallies.values()), tallies


def buys_only_intake(side: str) -> bool:
    """FlowAlgo A36 intake: ask-side prints only (bias declared)."""
    return side in ASK_SIDES


def open_close(size: float, cum_vol_after: float, oi: float | None, ask_before: float, bid_before: float,
               side: str) -> str:
    """The opening-or-closing heuristic, from the day's own numbers only (a print never says which it was):
    - likely_closing: a bid-side print no larger than the day's earlier ask-side volume on the contract (or the reverse):
      it can be the earlier buyers selling out, so the position it offsets was opened today;
    - likely_opening: the day's contract volume now exceeds the prior-close open interest: volume beyond the open
      interest cannot all be closing trades, so new positions exist;
    - unclear otherwise (including a mid or unknown side): the engine does not guess."""
    if side in BID_SIDES and ask_before >= size > 0:
        return "likely_closing"
    if side in ASK_SIDES and bid_before >= size > 0:
        return "likely_closing"
    if oi and cum_vol_after > oi:
        return "likely_opening"
    return "unclear"


def week52_context(spot: float, hi52: float | None, lo52: float | None) -> str | None:
    """where the underlying sits in its 52-week range, the words the Algo Score's range tally uses: near_high (within
    7% of the high), near_low (within 4% of the low), else mid; None without a range"""
    if not hi52 or not lo52 or spot <= 0:
        return None
    if (hi52 - spot) / hi52 * 100.0 <= 7:
        return "near_high"
    if (spot - lo52) / lo52 * 100.0 <= 4:
        return "near_low"
    return "mid"
