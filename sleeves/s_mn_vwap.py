"""s_mn_vwap — Midna VWAP port (Lazarus batch 8).

Catalog rule (§4.2): Trend/momentum, 1D, entry "Price crosses above
VWAP", exit "Price crosses below VWAP", 1 slot, $1,000.
Reading: VWAP is the 20-session rolling VWAP on daily bars (typical
price x volume / volume) — the desk's standing daily-bar VWAP form
(cf. ema_vwap's 20-day rolling anchor). Crosses use the last two
closed bars. Related-only to ema_vwap (catalog §5.1): that sleeve
buys deep below the anchor; this one trades the cross itself.
"""
from sleeves.laz8_common import Intent, SleeveConfig, held_positions, qty_for, xstale_refused

CONFIG = SleeveConfig(sleeve_id="s_mn_vwap", cadence_s=300,
                      state_schema={"position": "dict|None"})
SLOT_BUDGET = 1000.0
WINDOW = 20


def rolling_vwap(bars, i, window=WINDOW):
    if i + 1 < window:
        return None
    pv = vol = 0.0
    for b in bars[i - window + 1:i + 1]:
        v = float(b.get("v") or 0)
        if v <= 0:
            return None
        pv += ((float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0) * v
        vol += v
    return pv / vol if vol else None


def _cross(bars):
    """(up, down) cross flags on the last closed bar vs rolling VWAP."""
    if len(bars) < WINDOW + 1:
        return (False, False)
    v_prev = rolling_vwap(bars, len(bars) - 2)
    v_last = rolling_vwap(bars, len(bars) - 1)
    if v_prev is None or v_last is None:
        return (False, False)
    c_prev, c_last = float(bars[-2]["c"]), float(bars[-1]["c"])
    return (c_prev <= v_prev and c_last > v_last,
            c_prev >= v_prev and c_last < v_last)


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    for sym, pos in held.items():
        b = bars.get(sym) or []
        _, down = _cross(b)
        if down:
            out.append(Intent(
                kind="exit", symbol=sym, qty_hint=int(abs(float(pos["qty"]))),
                side="sell", position_intent="sell_to_close",
                price_hint=float(b[-1]["c"]),
                reason="s_mn_vwap exit: price_cross_below_vwap20"))
    if out or held:
        return out
    for sym in sorted(bars):
        up, _ = _cross(bars[sym])
        if up and xstale_refused(context, "s_mn_vwap", bars, sym):
            continue  # ENH20
        if up:
            px = float(bars[sym][-1]["c"])
            q = qty_for(SLOT_BUDGET, px)
            if q > 0:
                out.append(Intent(
                    kind="enter", symbol=sym, qty_hint=q, side="buy",
                    position_intent="buy_to_open", price_hint=px,
                    reason="s_mn_vwap entry: price_cross_above_vwap20 slot_budget=1000"))
            break
    return out
