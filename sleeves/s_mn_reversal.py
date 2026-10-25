"""s_mn_reversal — Midna Reversal port (Lazarus batch 8).

Catalog rule (§4.2): Mean reversion, 1D, US large caps, entry "Buys
last month's worst large caps", exit "Monthly rotation / 21
sessions", 3 slots, $3,000. Reading: rank the traded universe by
prior-21-session return, buy the 3 worst at $1,000 each; a position
exits once it has been held 21 sessions (the monthly rotation), at
which evaluation the sleeve re-ranks and refills. Universe = the
bars the snapshot carries (producer-defined large-cap set); the
catalog names no tickers (ledger).
"""
from sleeves.laz8_common import (Intent, SleeveConfig, closes,
                                  held_positions, qty_for, xstale_refused,
                                  sessions_held)

CONFIG = SleeveConfig(sleeve_id="s_mn_reversal", cadence_s=300,
                      state_schema={"position": "dict|None"})
SLOTS = 3
PER_SLOT = 1000.0
LOOKBACK = 21
HOLD = 21


def _ret21(b):
    if len(b) < LOOKBACK + 1:
        return None
    c = closes(b)
    return c[-1] / c[-1 - LOOKBACK] - 1.0


def worst_names(bars, exclude=()):
    scored = []
    for sym in sorted(bars):
        if sym in exclude:
            continue
        r = _ret21(bars[sym])
        if r is not None:
            scored.append((r, sym))
    scored.sort()
    return [sym for _, sym in scored[:SLOTS]]


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    out = []
    rotating = False
    for sym, pos in held.items():
        b = bars.get(sym) or []
        if sessions_held(b, pos.get("entry_date")) >= HOLD:
            rotating = True
            out.append(Intent(
                kind="exit", symbol=sym, qty_hint=int(abs(float(pos["qty"]))),
                side="sell", position_intent="sell_to_close",
                price_hint=float(b[-1]["c"]) if b else None,
                reason="s_mn_reversal exit: monthly_rotation_21_sessions"))
    if held and not rotating:
        return out  # mid-hold: no churn until the rotation date
    open_slots = SLOTS - (len(held) - sum(1 for i in out if i.kind == "exit"))
    if open_slots <= 0:
        return out
    for sym in worst_names(bars, exclude=set(held)):
        if open_slots <= 0:
            break
        if xstale_refused(context, "s_mn_reversal", bars, sym):
            continue  # ENH20
        px = float(bars[sym][-1]["c"])
        q = qty_for(PER_SLOT, px)
        if q > 0:
            open_slots -= 1
            out.append(Intent(
                kind="enter", symbol=sym, qty_hint=q, side="buy",
                position_intent="buy_to_open", price_hint=px,
                reason=f"s_mn_reversal entry: worst_large_cap ret21={_ret21(bars[sym]):.4f}"))
    return out
