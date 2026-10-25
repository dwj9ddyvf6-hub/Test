"""s_mn_kronos — Midna Kronos port (Lazarus batch 8).

Catalog rule (§4.2): ML forecaster, 1D, Shadow, entry "Buys the top
4 names forecast by the Kronos time-series model", exit "Rebalance
when the forecast changes, min 5-day hold", budget $2,000.
The Kronos model itself runs upstream (Midna branch signal files ->
midna_fires_v1.json, unreachable from this box, V3-SCOPE §3.4);
per §7.6 this lane is a FIRE-CONSUMER whose fires carry the forecast
ranking (symbol + rank/score). Desk-side management: hold the
forecast top 4 at $500 each; a held name that falls out of the
latest fresh forecast exits only after a 5-session minimum hold;
new top-4 names enter on rebalance. The catalog's "2 slots" cell
conflicts with "top 4 names" — the named rule wins; ledger records
it. No fresh forecast = fail closed (hold existing, no churn).
"""
from sleeves.laz8_common import (Intent, SleeveConfig, held_positions,
                                  qty_for, xstale_refused, sessions_held)

CONFIG = SleeveConfig(sleeve_id="s_mn_kronos", cadence_s=300,
                      state_schema={"position": "dict|None"})
TOP_N = 4
PER_NAME = 500.0
MIN_HOLD = 5
MAX_FIRE_AGE_DAYS = 7


def _forecast(context, session):
    from datetime import date
    fires = (context.extra or {}).get("fires") or []
    try:
        today = date.fromisoformat(str(session)[:10])
    except ValueError:
        return None
    rows = []
    for f in fires:
        if not isinstance(f, dict) or f.get("sleeve_id") != "s_mn_kronos":
            continue
        sym, fdate = f.get("symbol"), str(f.get("date") or "")[:10]
        if not sym or not fdate:
            continue
        try:
            age = (today - date.fromisoformat(fdate)).days
        except ValueError:
            continue
        if 0 <= age <= MAX_FIRE_AGE_DAYS:
            rows.append((fdate, sym, f.get("rank"), f.get("score")))
    if not rows:
        return None
    latest = max(r[0] for r in rows)
    rows = [r for r in rows if r[0] == latest]
    if all(r[2] is not None for r in rows):
        rows.sort(key=lambda r: int(r[2]))
    else:
        rows.sort(key=lambda r: -(float(r[3]) if r[3] is not None else 0.0))
    return [r[1] for r in rows[:TOP_N]]


def signal(bars, slice_state, context):
    held = held_positions(slice_state)
    top = _forecast(context, context.session)
    if top is None:
        return []  # fail closed: no fresh forecast, no entries or churn
    out = []
    for sym, pos in held.items():
        if sym not in top:
            b = bars.get(sym) or []
            if sessions_held(b, pos.get("entry_date")) >= MIN_HOLD:
                out.append(Intent(
                    kind="exit", symbol=sym,
                    qty_hint=int(abs(float(pos["qty"]))),
                    side="sell", position_intent="sell_to_close",
                    price_hint=float(b[-1]["c"]) if b else None,
                    reason="s_mn_kronos exit: forecast_changed min_hold_met"))
    slots = TOP_N - (len(held) - len(out))
    for sym in top:
        if slots <= 0:
            break
        if sym in held:
            continue
        b = bars.get(sym) or []
        if not b:
            continue
        if xstale_refused(context, "s_mn_kronos", bars, sym):
            continue  # ENH20
        px = float(b[-1]["c"])
        q = qty_for(PER_NAME, px)
        if q > 0:
            slots -= 1
            out.append(Intent(
                kind="enter", symbol=sym, qty_hint=q, side="buy",
                position_intent="buy_to_open", price_hint=px,
                reason="s_mn_kronos entry: kronos_forecast_top4"))
    return out
