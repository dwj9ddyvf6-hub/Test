"""s_mn_opt_reversal — Midna Opt Reversal port (Lazarus batch 8).

Catalog rule (§4.2): Options, 1D, Shadow, entry "Reversal traded
with listed options", exit "Rotation exit", $1,000.
Reading: the s_mn_reversal rule (last month's worst large caps)
expressed in listed options — buy an ATM-ish call (21-75 DTE,
laz8_opt selection) on the single worst prior-21-session performer;
exit sell-to-close at the 21-session rotation. Catalog slots=1 for
the options form (the equity form runs 3).
"""
from sleeves.laz8_common import (Intent, SleeveConfig, closes,
                                  held_positions, sessions_held, xstale_refused)
from sleeves.laz8_opt import contracts_for, pick_option, underlying_of

CONFIG = SleeveConfig(sleeve_id="s_mn_opt_reversal", cadence_s=300,
                      state_schema={"position": "dict|None"})
BUDGET = 1000.0
LOOKBACK = 21
HOLD = 21


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    for occ, pos in held.items():
        und = underlying_of(occ)
        b = bars.get(und) or [] if und else []
        if b and sessions_held(b, pos.get("entry_date")) >= HOLD:
            out.append(Intent(
                kind="exit", symbol=occ, qty_hint=int(abs(float(pos["qty"]))),
                side="sell", position_intent="sell_to_close",
                reason=f"s_mn_opt_reversal exit: rotation_21_sessions occ={occ}"))
    if out or held:
        return out
    scored = []
    for sym in sorted(bars):
        b = bars[sym]
        if len(b) < LOOKBACK + 1:
            continue
        c = closes(b)
        scored.append((c[-1] / c[-1 - LOOKBACK] - 1.0, sym))
    if not scored:
        return out
    scored.sort()
    _, sym = scored[0]
    if xstale_refused(context, "s_mn_opt_reversal", bars, sym):
        return out  # ENH20
    spot = float(bars[sym][-1]["c"])
    picked = pick_option(context, sym, spot, "call")
    if not picked:
        return out
    occ, ask = picked
    n = contracts_for(BUDGET, ask)
    if n <= 0:
        return out
    out.append(Intent(
        kind="enter", symbol=occ, qty_hint=n, side="buy",
        position_intent="buy_to_open", price_hint=spot,
        reason=f"s_mn_opt_reversal entry: worst_large_cap underlying={sym} occ={occ} ask={ask:.2f}"))
    return out
