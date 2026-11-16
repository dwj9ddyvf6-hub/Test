"""FEED80-TIMING-20261114: desk swing-timing computation.

PROVENANCE, stated plainly: the aster_r19_timing_hour sleeves consume
a "swing report" ({swing: {confirmed, usesFutureData, score,
bearishConflict, invalidation, target, phenotype}}) that the v625
report supplied in the archive system. No v625 generator exists in
this estate (searched 2026-11-11 and again 2026-11-14), and the
Tensor engine on this desk is a different product (daily, v698) that
is never edited or relabeled. This module is the DESK's own swing
computation, written for this purpose: it computes the consumed
semantics causally from 1Hour bars and is served under its own
identity (the drop it feeds stamps source "desk-swing-timing-v1",
never "v625"). Its forward falsifier is the sleeves' own grading:
if the timing sleeves' resolved trades do not beat their no-signal
baseline, this reconstruction is wrong and comes out.

Method (causal by construction; a bar is used only at or after the
moment it completes):
  * Fractal pivots with k=3: a pivot high/low at bar i is *known*
    only at bar i+3. Nothing in the output references a bar after
    the confirmation bar of the swing it reports.
  * A bullish swing confirms at the first close above the most
    recent confirmed pivot high when the intervening confirmed
    pivot low is higher than the previous pivot low (HH + HL).
    invalidation = that pivot low; target = measured move,
    swing_high + (swing_high - invalidation). Bearish is the mirror
    (LL + LH, close below the pivot low; invalidation = pivot high;
    target = swing_low - (invalidation - swing_low)).
  * The report is the LATEST confirmed swing in either direction.
    A bullish report carries bearishConflict=True when, after its
    confirmation, a lower high and a lower low have both confirmed
    (a downgrade short of a full bearish swing, which would
    supersede the report instead).
  * score (0-10, this product's own scale, stated so the sleeves'
    >= 8 gate means the same thing every day): 4 for a confirmed
    swing; +2 when the archive cloud ingredients align at the
    confirmation bar (hourly EMA34 vs EMA50, the same pair the
    archive cloud_signal uses); +2 when the confirming close clears
    the swing point by >= 0.25 x ATR14; +1 when the swing range is
    >= 1.0 x ATR14; +1 when confirmation-bar volume >= the trailing
    20-bar mean volume.
  * phenotype: "TRANSITION" when the previous confirmed swing was
    the opposite direction, else "CONTINUATION" (the consumer
    special-cases only TRANSITION).
  * usesFutureData is False, and is a property of the construction,
    not a claim stamped after the fact.
"""
from __future__ import annotations

K = 3


def _ema(vals, n):
    if len(vals) < n:
        return None
    k = 2.0 / (n + 1)
    e = sum(vals[:n]) / n
    for v in vals[n:]:
        e = v * k + e * (1 - k)
    return e


def _atr14(bars, upto):
    if upto < 15:
        return None
    trs = []
    for i in range(1, upto + 1):
        h, l, pc = (float(bars[i]["h"]), float(bars[i]["l"]),
                    float(bars[i - 1]["c"]))
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:14]) / 14.0
    for tr in trs[14:]:
        atr = (atr * 13 + tr) / 14.0
    return atr


def _pivots(bars, k=K):
    """Confirmed pivots: (confirm_idx, pivot_idx, kind, price)."""
    out = []
    for i in range(k, len(bars) - k):
        hi = float(bars[i]["h"]); lo = float(bars[i]["l"])
        if all(hi > float(bars[j]["h"]) for j in range(i - k, i + k + 1) if j != i):
            out.append((i + k, i, "H", hi))
        if all(lo < float(bars[j]["l"]) for j in range(i - k, i + k + 1) if j != i):
            out.append((i + k, i, "L", lo))
    return out


def compute_swing(bars):
    """Latest confirmed swing for one symbol's 1Hour bars (oldest
    first), or None when no swing has confirmed. Pure function of
    the bars given; appending later bars never rewrites a swing
    that was already confirmable from the earlier prefix."""
    if not bars or len(bars) < 40:
        return None
    pivs = _pivots(bars)
    if len(pivs) < 3:
        return None
    # Walk bars once, maintaining the last two confirmed pivot
    # highs/lows known AT each bar (a pivot counts only from its
    # confirmation bar on).
    by_confirm = {}
    for cidx, pidx, kind, price in pivs:
        by_confirm.setdefault(cidx, []).append((kind, price))
    phs, pls = [], []          # (price, pivot_idx) in confirm order
    swings = []                # confirmed swing records
    for j in range(len(bars)):
        for kind, price in by_confirm.get(j, []):
            (phs if kind == "H" else pls).append(price)
        close = float(bars[j]["c"])
        # bullish: close breaks the latest pivot high, and the
        # latest pivot low is higher than the one before it
        if len(phs) >= 1 and len(pls) >= 2 and pls[-1] > pls[-2]:
            if close > phs[-1] and (not swings or swings[-1]["confirm_idx"] < j
                                    ) and (not swings or swings[-1].get(
                                        "_ph") != phs[-1]):
                swings.append(_record(bars, j, "bullish", phs[-1], pls[-1],
                                      swings))
        # bearish mirror
        if len(pls) >= 1 and len(phs) >= 2 and phs[-1] < phs[-2]:
            if close < pls[-1] and (not swings or swings[-1]["confirm_idx"] < j
                                    ) and (not swings or swings[-1].get(
                                        "_pl") != pls[-1]):
                swings.append(_record(bars, j, "bearish", pls[-1], phs[-1],
                                      swings))
    if not swings:
        return None
    latest = swings[-1]
    # bearishConflict on a bullish report: a lower high AND a lower
    # low both confirmed after this swing's confirmation.
    conflict = False
    if latest["direction"] == "bullish":
        after = [(kind, price) for cidx, pidx, kind, price in pivs
                 if cidx > latest["confirm_idx"]]
        lh = any(kind == "H" and price < latest["_ph"] for kind, price in after)
        ll = any(kind == "L" and price < latest["invalidation"]
                 for kind, price in after)
        conflict = bool(lh and ll)
    # A swing whose invalidation a later close has crossed is a
    # FAILED swing; it stays the latest confirmed one (that is a
    # fact about the tape) but is marked, and the consumer's own
    # stop < entry < target geometry rejects it for entries.
    last_close = float(bars[-1]["c"])
    invalidated = (last_close < latest["invalidation"]
                   if latest["direction"] == "bullish"
                   else last_close > latest["invalidation"])
    out = {
        "confirmed": True,
        "usesFutureData": False,
        "direction": latest["direction"],
        "score": latest["score"],
        "bearishConflict": conflict,
        "invalidated": invalidated,
        "invalidation": latest["invalidation"],
        "target": latest["target"],
        "phenotype": latest["phenotype"],
        "confirmed_at": latest["confirmed_at"],
        "swing_high": latest.get("_ph"),
        "swing_low": latest.get("_pl"),
    }
    return out


def build_signals(bars_by_sym):
    """{SYM: {"swing": {...}}} for every symbol whose 1Hour bars
    confirm a swing; symbols without one are absent (the ingest
    producer drops malformed rows; absence here means no signal,
    never a repaired one)."""
    out = {}
    for sym, bars in (bars_by_sym or {}).items():
        sw = compute_swing(bars)
        if sw:
            out[sym] = {"swing": sw}
    return out


def _record(bars, j, direction, swing_point, invalidation, prior_swings):
    closes = [float(b["c"]) for b in bars[:j + 1]]
    atr = _atr14(bars, j) or 0.0
    close = closes[-1]
    if direction == "bullish":
        target = swing_point + (swing_point - invalidation)
        rng = swing_point - invalidation
        margin = close - swing_point
        cloud = (_ema(closes, 34) or 0) > (_ema(closes, 50) or 0)
    else:
        target = swing_point - (invalidation - swing_point)
        rng = invalidation - swing_point
        margin = swing_point - close
        cloud = (_ema(closes, 34) or 0) < (_ema(closes, 50) or 0)
    score = 4
    if cloud:
        score += 2
    if atr and margin >= 0.25 * atr:
        score += 2
    if atr and rng >= 1.0 * atr:
        score += 1
    vols = [float(b.get("v") or 0) for b in bars[max(0, j - 20):j + 1]]
    if len(vols) >= 21 and vols[-1] >= (sum(vols[:-1]) / 20.0) and vols[-1] > 0:
        score += 1
    phenotype = "CONTINUATION"
    if prior_swings and prior_swings[-1]["direction"] != direction:
        phenotype = "TRANSITION"
    return {
        "confirm_idx": j,
        "direction": direction,
        "score": score,
        "invalidation": float(invalidation),
        "target": float(target),
        "phenotype": phenotype,
        "confirmed_at": str(bars[j].get("t")),
        "_ph": float(swing_point) if direction == "bullish" else float(invalidation),
        "_pl": float(invalidation) if direction == "bullish" else float(swing_point),
    }
