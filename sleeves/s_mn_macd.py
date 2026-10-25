"""s_mn_macd — Midna MACD port (Lazarus batch 8).

Catalog rule (SLEEVE-CATALOG-CONSOLIDATED §4.2): Trend/momentum, 1D,
entry "MACD crosses up", exit "MACD crosses down", 1 slot, $1,000.
Reading: classic MACD(12,26,9) on daily closes; a cross is evaluated
on the last two closed bars. One position at a time (slots=1); when
several names cross up the same session the strongest histogram wins
(deterministic tie-break: symbol order).
"""
from sleeves.laz8_common import (Intent, SleeveConfig, closes,
                                  ema_series, held_positions, qty_for, xstale_refused)

CONFIG = SleeveConfig(sleeve_id="s_mn_macd", cadence_s=300,
                      state_schema={"position": "dict|None"})
SLOT_BUDGET = 1000.0
MIN_BARS = 35


def macd_hist(vals):
    fast, slow = ema_series(vals, 12), ema_series(vals, 26)
    line = [f - s for f, s in zip(fast, slow)]
    sig = ema_series(line, 9)
    return [l - s for l, s in zip(line, sig)]


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    # Exit first: MACD cross down on a held name.
    for sym, pos in held.items():
        b = bars.get(sym) or []
        if len(b) < MIN_BARS:
            continue
        h = macd_hist(closes(b))
        if h[-2] >= 0 and h[-1] < 0:
            out.append(Intent(
                kind="exit", symbol=sym, qty_hint=int(abs(float(pos["qty"]))),
                side="sell", position_intent="sell_to_close",
                price_hint=float(b[-1]["c"]),
                reason=f"s_mn_macd exit: macd_cross_down hist {h[-2]:.4f}->{h[-1]:.4f}"))
    if out or held:
        return out
    best = None
    for sym in sorted(bars):
        b = bars[sym]
        if len(b) < MIN_BARS:
            continue
        h = macd_hist(closes(b))
        if h[-2] <= 0 and h[-1] > 0:
            if xstale_refused(context, "s_mn_macd", bars, sym):
                continue  # ENH20: dead feed, cross is stale
            if best is None or h[-1] > best[1]:
                best = (sym, h[-1], float(b[-1]["c"]))
    if best:
        q = qty_for(SLOT_BUDGET, best[2])
        if q > 0:
            out.append(Intent(
                kind="enter", symbol=best[0], qty_hint=q, side="buy",
                position_intent="buy_to_open", price_hint=best[2],
                reason=f"s_mn_macd entry: macd_cross_up hist={best[1]:.4f} slot_budget=1000"))
    return out
